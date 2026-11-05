import json
import os
import numpy as np
import onnxruntime as ort
from pathlib import Path
from tokenizers import Tokenizer
from huggingface_hub import snapshot_download

# ── CUDA library discovery ────────────────────────────────────────────────────
# onnxruntime-gpu needs libcublasLt.so.12 etc. which live in the nvidia-*
# Python packages.  Prepend their lib dirs to LD_LIBRARY_PATH so the CUDA
# provider loads without requiring a system-level CUDA 12 install.
def _prepend_nvidia_libs() -> None:
    nvidia_root = Path(
        "/opt/dsi/python/yolo-trainer-template/venv/lib/python3.11/site-packages/nvidia"
    )
    if not nvidia_root.exists():
        return
    lib_dirs = ":".join(str(p) for p in nvidia_root.glob("*/lib") if p.is_dir())
    if lib_dirs:
        current = os.environ.get("LD_LIBRARY_PATH", "")
        os.environ["LD_LIBRARY_PATH"] = f"{lib_dirs}:{current}" if current else lib_dirs

_prepend_nvidia_libs()


class LayaJevEngine:
    def __init__(self, repo_id: str = "onnx-community/laya-multilingual-ONNX"):
        model_dir = Path(snapshot_download(repo_id=repo_id))

        # ── Config: support rl_agent_config.json OR config.json["laya"] ──────
        rl_cfg = model_dir / "rl_agent_config.json"
        if rl_cfg.exists():
            self.config = json.loads(rl_cfg.read_text())
            full_cfg = {}
        else:
            full_cfg = json.loads((model_dir / "config.json").read_text())
            self.config = full_cfg.get("laya", full_cfg)

        # ── Tokenizer: tokenizer/tokenizer.json OR tokenizer.json ────────────
        for tok_path in [
            model_dir / "tokenizer" / "tokenizer.json",
            model_dir / "tokenizer.json",
        ]:
            if tok_path.exists():
                self.tokenizer = Tokenizer.from_file(str(tok_path))
                break

        # ── Model: prefer fp16 ONNX for GPU, fall back through known paths ───
        for model_path in [
            model_dir / "onnx" / "model_fp16.onnx",
            model_dir / "onnx" / "model.onnx",
            model_dir / "model.onnx",
        ]:
            if model_path.exists():
                break

        # ── Session: CUDA preferred, CPU fallback ────────────────────────────
        available = ort.get_available_providers()
        providers  = (
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if "CUDAExecutionProvider" in available
            else ["CPUExecutionProvider"]
        )
        self.session = ort.InferenceSession(str(model_path), providers=providers)
        active = self.session.get_providers()[0]
        print(f"[engine] model={model_path.name}  provider={active}")

        # ── Special token IDs: config integers > string vocab lookup ─────────
        def _tok_id(name: str, cfg_key: str, fallback: int) -> int:
            tid = self.tokenizer.token_to_id(name)
            if tid is not None:
                return tid
            return full_cfg.get(cfg_key, self.config.get(cfg_key, fallback))

        self.cls_id  = _tok_id("[CLS]",  "cls_token_id",  1)
        self.sep_id  = _tok_id("[SEP]",  "sep_token_id",  1)
        self.mask_id = _tok_id("[MASK]", "mask_token_id", 4)

    def _tokenize(self, text: str) -> list[int]:
        return self.tokenizer.encode(text, add_special_tokens=False).ids

    def _get_temperature(self, qtype_str: str, option_count: int) -> float:
        size = (
            "2"    if option_count <= 2  else
            "3-5"  if option_count <= 5  else
            "6-10" if option_count <= 10 else "11+"
        )
        key = f"{qtype_str}:{size}"
        return (
            self.config.get("temperature_by_options", {}).get(key)
            or self.config["temperature"][0]
        )

    def predict_choice(self, state_text: str, question: str, options: dict[str, str]) -> dict[str, float]:
        """
        [CLS] choice question: <question> [SEP] [MASK] opt1: desc1 [MASK] opt2: desc2 [SEP] <state_text> [SEP]
        """
        token_ids = [self.cls_id] + self._tokenize(f"choice question: {question}") + [self.sep_id]

        option_positions, labels = [], list(options.keys())
        for label, description in options.items():
            option_positions.append(len(token_ids))
            token_ids.append(self.mask_id)
            token_ids += self._tokenize(f" {label}: {description}")[:48]
        token_ids.append(self.sep_id)

        max_len = self.config.get("max_len", 512)
        room = max_len - len(token_ids) - 1
        if room > 0:
            token_ids += self._tokenize(state_text)[:room]
        token_ids.append(self.sep_id)

        option_count  = len(option_positions)
        input_ids     = np.array([token_ids], dtype=np.int64)
        attention_mask = np.ones_like(input_ids, dtype=np.int64)
        marker_pos    = np.array([option_positions], dtype=np.int64)
        marker_mask   = np.ones((1, option_count), dtype=bool)
        qtype         = np.array([0], dtype=np.int64)

        outputs    = self.session.run(None, {
            "input_ids": input_ids, "attention_mask": attention_mask,
            "marker_pos": marker_pos, "marker_mask": marker_mask, "qtype": qtype,
        })
        raw_logits = outputs[0][0, :option_count]

        temperature   = self._get_temperature("choice", option_count)
        scaled        = raw_logits / temperature
        exp_logits    = np.exp(scaled - np.max(scaled))
        probabilities = exp_logits / np.sum(exp_logits)

        return {label: float(prob) for label, prob in zip(labels, probabilities)}

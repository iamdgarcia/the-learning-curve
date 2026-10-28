"""
LFM3 local chat — uses llama-cpp-python or falls back to subprocess llama-cli.
Run: python lfm3_chat.py
"""
import sys

MODEL = "LiquidAI/LFM3-1.7B-GGUF:Q4_K_M"  # ~1.1 GB
LLAMA_CLI_FLAGS = ["--temp", "0.1", "--top-k", "50", "--repeat-penalty", "1.1"]

def chat_llama_cpp_python():
    from llama_cpp import Llama
    print("Loading model via llama-cpp-python…")
    llm = Llama.from_pretrained(
        repo_id="LiquidAI/LFM3-1.7B-GGUF",
        filename="LFM3-1.7B-Q4_K_M.gguf",
        n_ctx=4096,
        verbose=False,
    )
    print("Model ready. Type 'quit' to exit.\n")
    history = []
    while True:
        user = input("You: ").strip()
        if not user or user.lower() == "quit":
            break
        history.append({"role": "user", "content": user})
        response = llm.create_chat_completion(messages=history)
        reply = response["choices"][0]["message"]["content"]
        history.append({"role": "assistant", "content": reply})
        print(f"LFM3: {reply}\n")

def chat_llama_cli():
    import subprocess, shutil
    if not shutil.which("llama-cli"):
        sys.exit("llama-cli not found. Install llama.cpp or: pip install llama-cpp-python")
    cmd = ["llama-cli", "-hf", MODEL] + LLAMA_CLI_FLAGS + ["-cnv"]
    subprocess.run(cmd)

if __name__ == "__main__":
    try:
        chat_llama_cpp_python()
    except ImportError:
        chat_llama_cli()

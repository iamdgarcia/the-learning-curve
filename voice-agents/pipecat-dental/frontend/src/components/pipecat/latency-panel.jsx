import { RTVIEvent } from "@pipecat-ai/client-js";
import { useRTVIClientEvent } from "@pipecat-ai/client-react";
import { useCallback, useState } from "react";

const LANES = [
  { key: "stt", label: "STT", hint: "speech → text",       color: "#60a5fa" },
  { key: "llm", label: "LLM", hint: "first answer token",  color: "#a78bfa" },
  { key: "tts", label: "TTS", hint: "text → first audio",  color: "#34d399" },
];

/** Route a processor name to stt / llm / tts. */
function classify(processor = "") {
  const p = processor.toLowerCase();
  if (p.includes("stt"))                          return "stt";
  if (p.includes("llm") || p.includes("openai") || p.includes("novita") ||
      p.includes("anthropic") || p.includes("gemini") || p.includes("deepseek")) return "llm";
  if (p.includes("tts") || p.includes("dialogue")) return "tts";
  return null;
}

function fmt(ms) {
  if (ms == null) return "—";
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
}

/**
 * Reads RTVIEvent.Metrics and displays per-stage latency bars.
 *
 * Wire format (from pipecat observer):
 *   ttfb  → [{ processor, value (s) }]        STT & TTS raw TTFB
 *   ttfat → [{ processor, ttfat (s), ttfb, thinking_time }]  LLM
 *   ttfa  → [{ processor, ttfa (s), ttfb, leading_silence }]  TTS first audio
 */
export function LatencyPanel({ className = "" }) {
  const [latest, setLatest] = useState({});

  const onMetrics = useCallback((data) => {
    setLatest((prev) => {
      const next = { ...prev };

      // STT: raw TTFB from the STT processor
      for (const m of data.ttfb ?? []) {
        const key = classify(m.processor);
        if (key === "stt") next.stt = Math.round(m.value * 1000);
        // TTS raw ttfb as fallback if no ttfa arrives
        if (key === "tts" && next.tts == null) next.tts = Math.round(m.value * 1000);
      }

      // LLM: time to first answer token (best LLM latency signal)
      for (const m of data.ttfat ?? []) {
        next.llm = Math.round(m.ttfat * 1000);
        if (m.thinking_time > 0.01) next.llm_think = Math.round(m.thinking_time * 1000);
        else delete next.llm_think;
      }

      // TTS: time to first audible audio (includes leading silence)
      for (const m of data.ttfa ?? []) {
        next.tts = Math.round(m.ttfa * 1000);
        if (m.leading_silence > 0.01) next.tts_silence = Math.round(m.leading_silence * 1000);
        else delete next.tts_silence;
      }

      return next;
    });
  }, []);

  useRTVIClientEvent(RTVIEvent.Metrics, onMetrics);

  const total = (latest.stt ?? 0) + (latest.llm ?? 0) + (latest.tts ?? 0);
  const hasData = total > 0;

  return (
    <div className={`font-mono text-[11px] text-muted-foreground flex flex-col gap-2 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-widest opacity-40">latency breakdown</span>
        {hasData && (
          <span className="tabular-nums opacity-50">
            {fmt(total)} total
          </span>
        )}
      </div>

      {/* Stacked bar */}
      {hasData && (
        <div className="flex h-1.5 rounded-full overflow-hidden gap-px">
          {LANES.map(({ key, color }) => {
            const ms = latest[key] ?? 0;
            const pct = (ms / total) * 100;
            return pct > 0 ? (
              <div
                key={key}
                className="h-full transition-all duration-500"
                style={{ width: `${pct}%`, backgroundColor: color, opacity: 0.75 }}
              />
            ) : null;
          })}
        </div>
      )}

      {/* Per-lane rows */}
      {LANES.map(({ key, label, hint, color }) => {
        const ms = latest[key];
        const pct = hasData && ms ? (ms / total) * 100 : 0;
        const sub =
          key === "llm" && latest.llm_think
            ? `${latest.llm_think}ms thinking`
            : key === "tts" && latest.tts_silence
            ? `${latest.tts_silence}ms silence pad`
            : null;

        return (
          <div key={key} className="flex items-center gap-2">
            {/* Dot + label */}
            <span
              className="size-1.5 shrink-0 rounded-full"
              style={{ backgroundColor: color, opacity: ms ? 0.8 : 0.25 }}
            />
            <span className="w-7 shrink-0">{label}</span>

            {/* Bar track */}
            <div className="flex-1 h-1 rounded-full bg-white/10 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${pct}%`, backgroundColor: color, opacity: 0.75 }}
              />
            </div>

            {/* Value + sub-detail */}
            <div className="flex items-center gap-1.5 min-w-[80px] justify-end">
              {sub && (
                <span className="opacity-35 text-[9px]">{sub}</span>
              )}
              <span className="tabular-nums w-12 text-right">
                {fmt(ms)}
              </span>
            </div>
          </div>
        );
      })}

      {!hasData && (
        <p className="opacity-25 text-center py-0.5">waiting for first turn…</p>
      )}
    </div>
  );
}

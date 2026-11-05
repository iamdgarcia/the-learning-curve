const API_KEY = process.env.NOVITA_API_KEY!;
const ENDPOINT = "https://api.novita.ai/v3/autotrust/v1/decide";

type Kind = "noul" | "score" | "choice";

interface DecideParams {
  kind: Kind;
  state: unknown;
  question: string;
  options?: string[];
}

interface DecideResult {
  kind: string;
  options: string[];
  probabilities: number[];
  choice_index: number;
  choice: string;
  elapsed_seconds: number;
  usage: { total_tokens: number };
}

export async function decide(params: DecideParams): Promise<DecideResult> {
  const res = await fetch(ENDPOINT, {
    method: "POST",
    headers: { Authorization: `Bearer ${API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model: "autotrust/jev-27b-vl", ...params }),
  });
  if (!res.ok) throw new Error(`JEV API error ${res.status}: ${await res.text()}`);
  return res.json();
}

// Convenience: run multiple decides on the same state in parallel
export async function decideAll(state: unknown, queries: Omit<DecideParams, "state">[]) {
  return Promise.all(queries.map((q) => decide({ state, ...q })));
}

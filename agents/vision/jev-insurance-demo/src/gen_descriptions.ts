#!/usr/bin/env bun
// Genera descripciones de siniestro para cada caso del benchmark.
// Llama una vez al LLM, guarda en cases.json. No volver a ejecutar.
import { readFileSync, writeFileSync } from "fs";
import { join } from "path";

const API_KEY = process.env.NOVITA_API_KEY!;
const CASES_PATH = join(import.meta.dir, "../data/cases.json");
const cases = JSON.parse(readFileSync(CASES_PATH, "utf8"));

const CONTEXT: Record<string, string> = {
  F_Breakage: "frontal con piezas rotas visibles (faros, paragolpes fracturado, rejilla)",
  F_Crushed:  "frontal aplastada, carrocería deformada, posible daño en motor",
  F_Normal:   "frontal, vehículo sin daños aparentes",
  R_Breakage: "trasera con piezas rotas (piloto roto, paragolpes trasero fracturado)",
  R_Crushed:  "trasera aplastada, maletero deformado, posible daño estructural",
  R_Normal:   "trasera, vehículo sin daños aparentes",
};

async function generate(label: string, idx: number): Promise<string> {
  const ctx = CONTEXT[label];
  const seed = idx % 4; // variación entre casos del mismo label
  const prompt = `Escribe UNA descripción corta (2 frases) de un parte de siniestro de seguro de automóvil. 
La foto muestra un vehículo con daño ${ctx}.
Variación ${seed}: usa un tipo de accidente diferente (colisión, parking, granizo, animal, etc.).
Solo el texto del parte, sin títulos ni explicaciones.`;

  const res = await fetch("https://api.novita.ai/v3/openai/chat/completions", {
    method: "POST",
    headers: { Authorization: `Bearer ${API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "qwen/qwen3.8-flash",
      messages: [{ role: "user", content: prompt }],
      max_tokens: 80,
    }),
  });
  const data = await res.json();
  return data.choices?.[0]?.message?.content?.trim() ?? "";
}

console.log(`Generando descripciones para ${cases.length} casos...`);

const BATCH = 8;
for (let i = 0; i < cases.length; i += BATCH) {
  const slice = cases.slice(i, i + BATCH);
  const descs = await Promise.all(slice.map((c: any, j: number) => generate(c.label, i + j)));
  slice.forEach((c: any, j: number) => { c.description = descs[j]; });
  process.stdout.write(`  ${Math.min(i + BATCH, cases.length)}/${cases.length}\r`);
}

writeFileSync(CASES_PATH, JSON.stringify(cases, null, 2));
console.log(`\nGuardado → data/cases.json`);

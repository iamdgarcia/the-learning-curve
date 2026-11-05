#!/usr/bin/env bun
import { loadCases, toBase64 } from "./dataset";
import { decideAll } from "./api";
import { writeFileSync } from "fs";
import { join } from "path";

const RESULTS_PATH = join(import.meta.dir, "../data/results.json");

const QUERIES = [
  { kind: "noul"   as const, question: "Does this image show a damaged vehicle?" },
  { kind: "choice" as const, question: "Which part of the vehicle shows the most damage or is most visible?", options: ["Front (frontal)", "Rear (trasera)"] },
  { kind: "score"  as const, question: "How severe is the visible vehicle damage? (0 = no damage, 5 = total loss)" },
];

function scoreBucket(s: number): 0 | 2 | 4 { return s <= 1 ? 0 : s <= 3 ? 2 : 4; }
function pct(n: number, d: number) { return `${((n / d) * 100).toFixed(1)}%`; }

const cases = loadCases();
console.log(`\n🚗 JEV-27B-VL Insurance Benchmark — ${cases.length} images\n`);

let correct = { damaged: 0, zone: 0, severity: 0 };
const results: any[] = [];
const BATCH = 5;

for (let i = 0; i < cases.length; i += BATCH) {
  const batch = cases.slice(i, i + BATCH);
  await Promise.all(batch.map(async (c) => {
    const imgB64 = await toBase64(c.imgSrc);
    const t0 = Date.now();
    const [dmg, zone, sev] = await decideAll([{ image: imgB64 }], QUERIES);
    const elapsed = Date.now() - t0;

    const jevDamaged  = dmg.choice === "true";
    const jevZone     = zone.choice_index === 0 ? "frontal" : "trasera";
    const jevSeverity = parseInt(sev.choice);

    if (jevDamaged === c.isDamaged)            correct.damaged++;
    if (jevZone === c.zone)                    correct.zone++;
    if (scoreBucket(jevSeverity) === c.severityGT) correct.severity++;

    results.push({
      imgSrc: c.imgSrc, label: c.label, zone: c.zone,
      isDamaged: c.isDamaged, severityGT: c.severityGT,
      jevDamaged, jevZone, jevSeverity,
      dmgProbs: dmg.probabilities, zoneProbs: zone.probabilities, sevProbs: sev.probabilities,
      elapsed, tokens: (dmg.usage?.total_tokens??0)+(zone.usage?.total_tokens??0)+(sev.usage?.total_tokens??0),
    });
  }));
  process.stdout.write(`  ${Math.min(i + BATCH, cases.length)}/${cases.length} evaluated\r`);
}

const summary = {
  total: results.length,
  perClass: results.length / 6,
  accuracy: {
    damaged:  correct.damaged  / results.length,
    zone:     correct.zone     / results.length,
    severity: correct.severity / results.length,
  },
  avgMs: results.reduce((s, r) => s + r.elapsed, 0) / results.length,
  totalTokens: results.reduce((s, r) => s + r.tokens, 0),
};

writeFileSync(RESULTS_PATH, JSON.stringify({ summary, cases: results }, null, 2));

console.log(`\n\n📊 RESULTS (${results.length} cases)\n`);
console.log(`  Damage detection  ${pct(correct.damaged,  results.length)}`);
console.log(`  Zone (F/R)        ${pct(correct.zone,     results.length)}`);
console.log(`  Severity bucket   ${pct(correct.severity, results.length)}`);
console.log(`  Avg latency       ${summary.avgMs.toFixed(0)}ms`);
console.log(`  Results saved  →  data/results.json\n`);

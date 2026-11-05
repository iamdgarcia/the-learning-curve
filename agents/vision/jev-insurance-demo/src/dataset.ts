import { readFileSync } from "fs";
import { join } from "path";

export const LABEL_NAMES = ["F_Breakage", "F_Crushed", "F_Normal", "R_Breakage", "R_Crushed", "R_Normal"] as const;
export type LabelName = (typeof LABEL_NAMES)[number];

export interface CaseMeta {
  imgSrc: string;          // local path like /images/0_F_Breakage.jpg
  label: LabelName;
  zone: "frontal" | "trasera";
  isDamaged: boolean;
  severityGT: 0 | 2 | 4;
}

const CASES_PATH = join(import.meta.dir, "../data/cases.json");

export function loadCases(): CaseMeta[] {
  return JSON.parse(readFileSync(CASES_PATH, "utf8"));
}

export async function toBase64(localPath: string): Promise<string> {
  // localPath is /images/0_F_Breakage.jpg → read from data/images/
  const absPath = join(import.meta.dir, "../data", localPath);
  const buf = readFileSync(absPath);
  return `data:image/jpeg;base64,${buf.toString("base64")}`;
}

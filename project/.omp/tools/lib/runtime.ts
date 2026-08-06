import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

export type ExecResult = { stdout: string; stderr: string; code: number; killed?: boolean };
export type ToolText = { type: "text"; text: string };
export type ToolResult = { content: ToolText[]; details?: Record<string, unknown> };
export type PiApi = {
  cwd: string;
  exec(command: string, args: string[], options?: { cwd?: string; signal?: AbortSignal; timeout?: number }): Promise<ExecResult>;
};
export type HistoryEntry = {
  at: string; actor: string; action: string; scope: "project" | "stage" | "task";
  from: string | null; to: string | null; reason: string; branch: string; head: string; note?: string;
};

export const STATE_PATH = "docs/PROJECT_STATE.json";
export const REPORTS_DIR = ".project-factory/reports";
export const REVIEWS_DIR = ".project-factory/reviews";
export const PROTECTED_BRANCHES = new Set(["main", "master", "develop", "release", "production", "prod"]);

export async function exec(pi: PiApi, command: string, args: string[], cwd?: string, signal?: AbortSignal, timeout?: number): Promise<ExecResult> {
  return pi.exec(command, args, { cwd: cwd ?? pi.cwd, signal, timeout });
}
export async function execOk(pi: PiApi, command: string, args: string[], cwd?: string, signal?: AbortSignal, timeout?: number): Promise<string> {
  const result = await exec(pi, command, args, cwd, signal, timeout);
  if (result.code !== 0 || result.killed) throw new Error(result.stderr.trim() || `${command} ${args.join(" ")} failed`);
  return result.stdout.trim();
}
export async function git(pi: PiApi, args: string[], cwd?: string): Promise<string> { return execOk(pi, "git", args, cwd); }
export async function pathExists(filePath: string): Promise<boolean> { try { await fs.stat(filePath); return true; } catch { return false; } }
export function sha256(input: string | Buffer): string { return `sha256:${createHash("sha256").update(input).digest("hex")}`; }

export async function ensureInsideRepo(repoRoot: string, candidate: string): Promise<string> {
  const resolved = path.resolve(repoRoot, candidate);
  const lexical = path.relative(path.resolve(repoRoot), resolved);
  if (lexical.startsWith("..") || path.isAbsolute(lexical)) throw new Error(`Path escapes repository root: ${candidate}`);
  const [realRoot, realResolved] = await Promise.all([fs.realpath(repoRoot), fs.realpath(resolved)]);
  const physical = path.relative(realRoot, realResolved);
  if (physical.startsWith("..") || path.isAbsolute(physical)) throw new Error(`Path resolves outside repository root: ${candidate}`);
  return realResolved;
}

export async function readJson<T>(filePath: string): Promise<T> { return JSON.parse(await fs.readFile(filePath, "utf8")) as T; }
export async function writeJsonAtomic(filePath: string, data: unknown): Promise<void> {
  const dir = path.dirname(filePath);
  const temp = path.join(dir, `.tmp-${path.basename(filePath)}-${process.pid}-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(temp, `${JSON.stringify(data, null, 2)}\n`, "utf8");
  await fs.rename(temp, filePath);
}
export async function currentBranch(pi: PiApi): Promise<string> { return git(pi, ["branch", "--show-current"]); }
export async function currentHead(pi: PiApi): Promise<string> { return git(pi, ["rev-parse", "HEAD"]); }
export async function ensureRepo(pi: PiApi): Promise<void> { await git(pi, ["rev-parse", "--is-inside-work-tree"]); }
export async function ensureNotProtectedBranch(pi: PiApi): Promise<string> {
  const branch = await currentBranch(pi);
  if (!branch) throw new Error("Detached HEAD is not allowed");
  if (PROTECTED_BRANCHES.has(branch)) throw new Error(`Protected branch blocked: ${branch}`);
  return branch;
}
export async function worktreeStatus(pi: PiApi): Promise<string> {
  const result = await exec(pi, "git", ["status", "--porcelain=v1", "--untracked-files=all"]);
  if (result.code !== 0 || result.killed) throw new Error(result.stderr.trim() || "git status --porcelain failed");
  return result.stdout.replace(/[\r\n]+$/, "");
}
export async function ensureCleanWorktree(pi: PiApi): Promise<void> {
  const status = await worktreeStatus(pi);
  if (status) throw new Error(`Working tree is not clean:\n${status}`);
}

function splitNul(value: string): string[] { return value.split("\0").filter(Boolean); }
export async function listChangedFiles(pi: PiApi): Promise<string[]> {
  const tracked = await exec(pi, "git", ["diff", "--name-only", "-z", "HEAD", "--"]);
  if (tracked.code !== 0 || tracked.killed) throw new Error(tracked.stderr.trim() || "git diff --name-only failed");
  const untracked = await exec(pi, "git", ["ls-files", "--others", "--exclude-standard", "-z"]);
  if (untracked.code !== 0 || untracked.killed) throw new Error(untracked.stderr.trim() || "git ls-files failed");
  return [...new Set([...splitNul(tracked.stdout), ...splitNul(untracked.stdout)])].sort();
}

export async function diffHash(pi: PiApi): Promise<string> {
  const tracked = await git(pi, ["diff", "--binary", "HEAD", "--"]);
  const untracked = await git(pi, ["ls-files", "--others", "--exclude-standard"]);
  const ignoredEvidence = (file: string): boolean =>
    file === STATE_PATH || file.startsWith(`${REPORTS_DIR}/`) || file.startsWith(`${REVIEWS_DIR}/`) || /^docs\/stages\/(?:[^/]+\/)?tasks\//.test(file);
  const parts = [tracked];
  for (const file of untracked.split(/\n+/).filter(Boolean).filter((item) => !ignoredEvidence(item)).sort()) {
    const content = await fs.readFile(path.join(pi.cwd, file));
    parts.push(`UNTRACKED ${file}\n${sha256(content)}`);
  }
  return sha256(parts.join("\n--DIFF--\n"));
}
export async function baseCommit(pi: PiApi): Promise<string> { return git(pi, ["rev-list", "--max-count=1", "HEAD"]); }
export function stdoutTail(value: string): string { return value.length <= 8000 ? value : value.slice(-8000); }

export function globToRegExp(pattern: string): RegExp {
  let result = "^";
  for (let i = 0; i < pattern.length; i += 1) {
    const char = pattern[i];
    const next = pattern[i + 1];
    if (char === "*" && next === "*") { result += ".*"; i += 1; }
    else if (char === "*") result += "[^/]*";
    else if (char === "?") result += "[^/]";
    else if ("\\.[]{}()+-^$|".includes(char)) result += `\\${char}`;
    else result += char;
  }
  return new RegExp(`${result}$`);
}
export function matchesAny(pathValue: string, patterns: string[]): boolean { return patterns.map(globToRegExp).some((re) => re.test(pathValue)); }
export async function ensureDir(dirPath: string): Promise<void> { await fs.mkdir(dirPath, { recursive: true }); }
export function nowIso(): string { return new Date().toISOString(); }
export async function stageExactFiles(pi: PiApi, files: string[]): Promise<void> {
  if (files.length === 0) throw new Error("No files to stage");
  await git(pi, ["add", "--", ...files]);
}
export async function unstageFiles(pi: PiApi, files: string[]): Promise<void> {
  if (files.length === 0) return;
  try { await git(pi, ["restore", "--staged", "--", ...files]); } catch { /* best effort */ }
}
export function reportPath(kind: string, id: string): string { return path.join(REPORTS_DIR, `${kind}-${id}-latest.json`); }
export function reviewPath(taskId: string, reviewerRole: string): string { return path.join(REVIEWS_DIR, `${taskId}--${reviewerRole}.json`); }
export function normalizeNewlines(value: string): string { return value.replace(/\r\n/g, "\n"); }

export function parseFrontmatter(source: string): { frontmatter: Record<string, unknown>; body: string } {
  const normalized = normalizeNewlines(source);
  if (!normalized.startsWith("---\n")) throw new Error("Missing frontmatter");
  const end = normalized.indexOf("\n---\n", 4);
  if (end === -1) throw new Error("Unterminated frontmatter");
  const block = normalized.slice(4, end);
  const body = normalized.slice(end + 5);
  const result: Record<string, unknown> = {};
  for (const rawLine of block.split("\n")) {
    const line = rawLine.trim();
    if (!line) continue;
    const idx = line.indexOf(":");
    if (idx === -1) throw new Error(`Invalid frontmatter line: ${line}`);
    result[line.slice(0, idx).trim()] = parseFrontmatterValue(line.slice(idx + 1).trim());
  }
  return { frontmatter: result, body };
}
function parseFrontmatterValue(rawValue: string): unknown {
  if (rawValue === "null") return null;
  if (rawValue === "true") return true;
  if (rawValue === "false") return false;
  if (/^-?\d+$/.test(rawValue)) return Number(rawValue);
  if ((rawValue.startsWith('"') && rawValue.endsWith('"')) || (rawValue.startsWith("'") && rawValue.endsWith("'"))) return rawValue.slice(1, -1);
  if (rawValue.startsWith("[") && rawValue.endsWith("]")) {
    const inner = rawValue.slice(1, -1).trim();
    if (!inner) return [];
    return inner.split(",").map((part) => parseFrontmatterValue(part.trim()));
  }
  return rawValue;
}
export function stringifyFrontmatterValue(value: unknown): string {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return String(value);
  if (Array.isArray(value)) return `[${value.map((item) => stringifyFrontmatterValue(item)).join(", ")}]`;
  return JSON.stringify(String(value));
}
export function renderFrontmatter(frontmatter: Record<string, unknown>, body: string): string {
  const lines = Object.entries(frontmatter).map(([key, value]) => `${key}: ${stringifyFrontmatterValue(value)}`);
  return `---\n${lines.join("\n")}\n---\n${body.startsWith("\n") ? body : `\n${body}`}`;
}
export function taskContractHash(source: string): string {
  const normalized = normalizeNewlines(source)
    .replace(/^status:\s*.*$/m, "status: __STATUS__")
    .replace(/^approved_contract_sha256:\s*.*$/m, "approved_contract_sha256: __APPROVED_CONTRACT_SHA256__");
  const marker = "\n# Completion summary\n";
  const trimmed = normalized.includes(marker) ? normalized.slice(0, normalized.indexOf(marker)) + marker : normalized;
  return sha256(trimmed);
}
export async function readTaskContract(taskPath: string): Promise<{ source: string; frontmatter: Record<string, unknown>; body: string; contractHash: string }> {
  const source = await fs.readFile(taskPath, "utf8");
  const parsed = parseFrontmatter(source);
  return { source, frontmatter: parsed.frontmatter, body: parsed.body, contractHash: taskContractHash(source) };
}
export async function safeWriteTextAtomic(filePath: string, content: string): Promise<void> {
  const dir = path.dirname(filePath);
  const temp = path.join(dir, `.tmp-${path.basename(filePath)}-${process.pid}-${Date.now()}`);
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(temp, content, "utf8");
  await fs.rename(temp, filePath);
}

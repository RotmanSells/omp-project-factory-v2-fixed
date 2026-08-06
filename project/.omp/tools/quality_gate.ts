import path from "node:path";
import { REPORTS_DIR, baseCommit, currentBranch, currentHead, diffHash, ensureDir, ensureInsideRepo, exec, nowIso, pathExists, readJson, reportPath, stdoutTail, writeJsonAtomic, type PiApi, type ToolResult } from "./lib/runtime.ts";

type Gate = {
  name: string;
  scopes: string[];
  enabled?: boolean;
  cwd?: string;
  command: string;
  args?: string[];
  timeout_sec?: number;
  notes?: string;
};

type Params = { scope: "task" | "stage" | "mission" | "full"; id: string; gateNames?: string[] };

const allowedExecutables = new Set(["pnpm", "npm", "yarn", "bun", "python", "python3", "pytest", "cargo", "go", "dotnet", "mvn", "gradle", "./gradlew", "make", "cmake", "ctest", "swift", "xcodebuild"]);
const forbiddenExecutables = new Set(["npx", "bunx", "uvx", "sh", "bash", "zsh", "cmd", "powershell", "pwsh"]);
const forbiddenSubcommands = new Set(["install", "i", "add", "update", "upgrade", "exec", "dlx", "create", "publish", "pack", "link", "unlink", "prune", "remove", "rm", "get", "run-script"]);
const safePackageScripts = new Set(["test", "lint", "typecheck", "check", "build", "format", "format:check", "test:unit", "test:integration", "test:e2e", "test:security", "test:load"]);

function classifyOverall(statuses: string[]): "PASS" | "FAIL" | "SKIP" | "NOT_CONFIGURED" {
  if (statuses.length === 0) return "NOT_CONFIGURED";
  if (statuses.includes("FAIL")) return "FAIL";
  if (statuses.includes("NOT_CONFIGURED")) return "NOT_CONFIGURED";
  if (statuses.includes("SKIP")) return "SKIP";
  return statuses.every((status) => status === "PASS") ? "PASS" : "FAIL";
}

function validateArgument(arg: string): void {
  if (arg.includes("\0") || arg.includes("\n") || arg.includes("\r")) throw new Error("Control characters are forbidden in gate arguments");
  if (path.isAbsolute(arg) || arg.split(/[\\/]/).includes("..")) throw new Error(`Unsafe gate argument path: ${arg}`);
}

function validateCommand(command: string, args: string[]): void {
  if (forbiddenExecutables.has(command)) throw new Error(`Forbidden executable: ${command}`);
  if (!allowedExecutables.has(command)) throw new Error(`Executable is not allowlisted: ${command}`);
  for (const arg of args) validateArgument(arg);
  const first = args[0] ?? "";
  if (forbiddenSubcommands.has(first)) throw new Error(`Forbidden package-loading or mutating subcommand: ${first}`);
  if ((command === "python" || command === "python3") && (first === "-c" || first === "-")) throw new Error("Inline Python execution is forbidden in quality gates");
  if ((command === "python" || command === "python3") && first === "-m" && args[1] !== "pytest") throw new Error("Only python -m pytest is allowed");
  if (command === "go" && ["run", "get", "install", "generate"].includes(first)) throw new Error(`Forbidden go subcommand: ${first}`);
  if (command === "cargo" && ["install", "add", "update", "publish", "run"].includes(first)) throw new Error(`Forbidden cargo subcommand: ${first}`);
  if (["npm", "pnpm", "yarn", "bun"].includes(command)) {
    const direct = safePackageScripts.has(first);
    const viaRun = first === "run" && safePackageScripts.has(args[1] ?? "");
    if (!direct && !viaRun) throw new Error(`Package-manager gate must use an approved verification script, actual: ${args.join(" ")}`);
  }
}

export async function executeQualityGate(pi: PiApi, params: Params, signal?: AbortSignal): Promise<ToolResult> {
  const configPath = path.join(pi.cwd, ".project-factory/quality-gates.json");
  if (!(await pathExists(configPath))) {
    const emptyReport = { schema_version: 1, scope: params.scope, id: params.id, verdict: "NOT_CONFIGURED", created_at: nowIso(), branch: await currentBranch(pi), head: await currentHead(pi), base_commit: await baseCommit(pi), diff_hash: await diffHash(pi), gates: [] };
    const outPath = path.join(pi.cwd, reportPath(`quality-${params.scope}`, params.id));
    await writeJsonAtomic(outPath, emptyReport);
    return { content: [{ type: "text", text: `Quality gate NOT_CONFIGURED. Report: ${path.relative(pi.cwd, outPath)}` }], details: { reportPath: path.relative(pi.cwd, outPath), report: emptyReport } };
  }

  const config = await readJson<{ schema_version?: number; gates?: Gate[] }>(configPath);
  if (config.schema_version !== 1 || !Array.isArray(config.gates)) throw new Error("Invalid quality-gates.json schema");
  const allForScope = config.gates.filter((gate) => gate.scopes?.includes(params.scope));
  const requested = new Set(params.gateNames ?? []);
  if (requested.size > 0) {
    const known = new Set(allForScope.map((gate) => gate.name));
    const unknown = [...requested].filter((name) => !known.has(name));
    if (unknown.length > 0) throw new Error(`Unknown requested gates: ${unknown.join(", ")}`);
  }
  const gates = allForScope.filter((gate) => requested.size === 0 || requested.has(gate.name));
  const branch = await currentBranch(pi);
  const head = await currentHead(pi);
  const base = await baseCommit(pi);
  const hash = await diffHash(pi);
  const results: Array<Record<string, unknown>> = [];
  const seenNames = new Set<string>();

  for (const gate of gates) {
    if (!gate.name || seenNames.has(gate.name)) throw new Error(`Duplicate or empty gate name: ${gate.name}`);
    seenNames.add(gate.name);
    if (gate.enabled === false) {
      results.push({ name: gate.name, status: "SKIP", reason: gate.notes ?? "Gate disabled in configuration", cwd: gate.cwd ?? "." });
      continue;
    }
    const args = Array.isArray(gate.args) ? gate.args.map(String) : [];
    validateCommand(gate.command, args);
    const resolvedCwd = ensureInsideRepo(pi.cwd, gate.cwd ?? ".");
    const startedAt = nowIso();
    const startedMs = Date.now();
    const timeout = Math.max(1, Math.min(3600, gate.timeout_sec ?? 900));
    const result = await exec(pi, gate.command, args, resolvedCwd, signal, timeout);
    results.push({
      name: gate.name,
      status: result.code === 0 && !result.killed ? "PASS" : "FAIL",
      command: gate.command,
      args,
      cwd: path.relative(pi.cwd, resolvedCwd) || ".",
      started_at: startedAt,
      finished_at: nowIso(),
      duration_ms: Date.now() - startedMs,
      exit_code: result.code,
      killed: result.killed === true,
      stdout_tail: stdoutTail(result.stdout),
      stderr_tail: stdoutTail(result.stderr),
    });
    if (result.code !== 0 || result.killed) break;
  }

  const verdict = classifyOverall(results.map((item) => String(item.status)));
  const report = { schema_version: 1, scope: params.scope, id: params.id, verdict, created_at: nowIso(), branch, head, base_commit: base, diff_hash: hash, gates: results };
  await ensureDir(path.join(pi.cwd, REPORTS_DIR));
  const outPath = path.join(pi.cwd, reportPath(`quality-${params.scope}`, params.id));
  await writeJsonAtomic(outPath, report);
  return { content: [{ type: "text", text: `Quality gate ${verdict}. Report: ${path.relative(pi.cwd, outPath)}` }], details: { reportPath: path.relative(pi.cwd, outPath), report } };
}

const factory = (pi: any) => ({
  name: "quality_gate",
  label: "Quality Gate",
  description: "Runs repository-defined allowlisted verification commands and stores a structured report",
  parameters: pi.zod.object({
    scope: pi.zod.enum(["task", "stage", "mission", "full"]),
    id: pi.zod.string().min(1).max(100),
    gateNames: pi.zod.array(pi.zod.string()).optional(),
  }),
  async execute(_toolCallId: string, params: Params, _onUpdate: unknown, _ctx: unknown, signal: AbortSignal) { return executeQualityGate(pi as PiApi, params, signal); },
});

export default factory;

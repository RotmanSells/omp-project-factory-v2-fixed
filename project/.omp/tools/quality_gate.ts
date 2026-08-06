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

type Params = {
  scope: "task" | "stage" | "mission" | "full";
  id: string;
  gateNames?: string[];
};

const allowedExecutables = new Set(["pnpm", "npm", "yarn", "bun", "python", "python3", "pytest", "cargo", "go", "dotnet", "mvn", "gradle", "./gradlew", "make", "cmake", "ctest", "swift", "xcodebuild"]);
const forbiddenFirstArgs = new Set(["install", "i", "add", "update", "upgrade", "exec", "dlx", "create", "publish", "pack", "link", "unlink", "prune", "remove", "rm", "run-package", "get"]);
const forbiddenCommands = new Set(["npx", "bunx", "uvx"]);

function classifyOverall(statuses: string[]): "PASS" | "FAIL" | "SKIP" | "NOT_CONFIGURED" {
  if (statuses.length === 0) return "NOT_CONFIGURED";
  if (statuses.includes("FAIL")) return "FAIL";
  if (statuses.every((status) => status === "SKIP")) return "SKIP";
  if (statuses.includes("NOT_CONFIGURED")) return "NOT_CONFIGURED";
  if (statuses.every((status) => status === "PASS")) return "PASS";
  return "SKIP";
}

function validateCommand(command: string, args: string[]): void {
  if (forbiddenCommands.has(command)) throw new Error(`Forbidden executable: ${command}`);
  if (!allowedExecutables.has(command)) throw new Error(`Executable is not allowlisted: ${command}`);
  const first = args[0];
  if (command === "go" && first === "run") throw new Error("Forbidden go subcommand: run");
  if (first && forbiddenFirstArgs.has(first)) throw new Error(`Forbidden package-loading or mutating subcommand: ${first}`);
}

export async function executeQualityGate(pi: PiApi, params: Params, signal?: AbortSignal): Promise<ToolResult> {
  const configPath = path.join(pi.cwd, ".project-factory/quality-gates.json");
  if (!(await pathExists(configPath))) {
    const emptyReport = {
      schema_version: 1,
      scope: params.scope,
      id: params.id,
      verdict: "NOT_CONFIGURED",
      created_at: nowIso(),
      branch: await currentBranch(pi),
      head: await currentHead(pi),
      base_commit: await baseCommit(pi),
      diff_hash: await diffHash(pi),
      gates: [],
    };
    const outPath = path.join(pi.cwd, reportPath(`quality-${params.scope}`, params.id));
    await writeJsonAtomic(outPath, emptyReport);
    return { content: [{ type: "text", text: `Quality gate NOT_CONFIGURED. Report: ${path.relative(pi.cwd, outPath)}` }], details: { reportPath: path.relative(pi.cwd, outPath), report: emptyReport } };
  }
  const config = await readJson<{ schema_version?: number; gates?: Gate[] }>(configPath);
  const requested = new Set(params.gateNames ?? []);
  const gates = (config.gates ?? []).filter((gate) => gate.scopes?.includes(params.scope) && (requested.size === 0 || requested.has(gate.name)));
  const branch = await currentBranch(pi);
  const head = await currentHead(pi);
  const base = await baseCommit(pi);
  const hash = await diffHash(pi);
  const results: Array<Record<string, unknown>> = [];

  for (const gate of gates) {
    const gateStatus = gate.enabled === false ? "SKIP" : "PASS";
    if (gate.enabled === false) {
      results.push({
        name: gate.name,
        status: "SKIP",
        reason: gate.notes ?? "Gate disabled in configuration",
        cwd: gate.cwd ?? ".",
      });
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
      status: result.code === 0 && !result.killed ? gateStatus : "FAIL",
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
  const report = {
    schema_version: 1,
    scope: params.scope,
    id: params.id,
    verdict,
    created_at: nowIso(),
    branch,
    head,
    base_commit: base,
    diff_hash: hash,
    gates: results,
  };
  await ensureDir(path.join(pi.cwd, REPORTS_DIR));
  const outPath = path.join(pi.cwd, reportPath(`quality-${params.scope}`, params.id));
  await writeJsonAtomic(outPath, report);
  return { content: [{ type: "text", text: `Quality gate ${verdict}. Report: ${path.relative(pi.cwd, outPath)}` }], details: { reportPath: path.relative(pi.cwd, outPath), report } };
}

const factory = (pi: any) => ({
  name: "quality_gate",
  label: "Quality Gate",
  description: "Runs repository-defined allowlisted quality gates and stores a structured report",
  parameters: pi.zod.object({
    scope: pi.zod.enum(["task", "stage", "mission", "full"]),
    id: pi.zod.string().min(1).max(100),
    gateNames: pi.zod.array(pi.zod.string()).optional(),
  }),
  async execute(_toolCallId: string, params: Params, _onUpdate: unknown, _ctx: unknown, signal: AbortSignal) {
    return executeQualityGate(pi as PiApi, params, signal);
  },
});

export default factory;

import path from "node:path";
import { STATE_PATH, currentBranch, currentHead, diffHash, ensureNotProtectedBranch, ensureRepo, git, listChangedFiles, matchesAny, pathExists, readJson, reportPath, stageExactFiles, unstageFiles, worktreeStatus, type PiApi, type ToolResult } from "./lib/runtime.ts";

type Params = {
  mission: "design" | "roadmap" | "plan_stage" | "close_stage" | "prepare_github";
  message: string;
};

type State = {
  project: { phase: string };
  current_stage: null | { id: string; status: string };
  current_task: null | { id: string; status: string };
};

const conventionalCommit = /^(docs|chore|refactor)(\([a-z0-9._/-]+\))?!?: .{5,100}$/;
const policies: Record<Params["mission"], string[]> = {
  design: ["PROJECT_BRIEF.md", "docs/**", ".project-factory/**", "AGENTS.md", ".omp/**"],
  roadmap: ["docs/**", ".project-factory/**", "AGENTS.md"],
  plan_stage: ["docs/**", ".project-factory/**"],
  close_stage: ["docs/**", ".project-factory/**"],
  prepare_github: [".project-factory/github-outbox/**", ".project-factory/reports/**", ".project-factory/reviews/**"],
};

function appCodeForbidden(file: string): boolean {
  return /(src|app|server|client|api|lib)\//.test(file) || /\.(ts|tsx|js|jsx|go|rs|py|rb|java|kt|swift|cs)$/.test(file);
}

export async function executeMissionCommit(pi: PiApi, params: Params): Promise<ToolResult> {
  await ensureRepo(pi);
  if (!conventionalCommit.test(params.message)) throw new Error("Mission commit message must be docs/chore/refactor conventional commit");
  const branch = await ensureNotProtectedBranch(pi);
  const state = await readJson<State>(path.join(pi.cwd, STATE_PATH));
  const changedFiles = await listChangedFiles(pi);
  if (changedFiles.length === 0) throw new Error("No changed files");
  const allowed = policies[params.mission];
  const mandatory = new Set([STATE_PATH]);
  const unexpected = changedFiles.filter((file) => !mandatory.has(file) && !matchesAny(file, allowed));
  if (unexpected.length > 0) throw new Error(`Unexpected files for ${params.mission}:\n${unexpected.join("\n")}`);
  if (params.mission !== "prepare_github") {
    const appCode = changedFiles.filter(appCodeForbidden);
    if (appCode.length > 0) throw new Error(`Application code is forbidden in mission commit:\n${appCode.join("\n")}`);
  }
  const reportFile = path.join(pi.cwd, reportPath(`quality-mission`, params.mission));
  if (await pathExists(reportFile)) {
    const report = await readJson<any>(reportFile);
    if (report.verdict === "FAIL") throw new Error("Mission quality report failed");
    if (report.diff_hash && report.diff_hash !== await diffHash(pi)) throw new Error("Mission quality report is stale");
  }
  const stagedByTool = [...changedFiles];
  let committed = false;
  try {
    await stageExactFiles(pi, stagedByTool);
    await git(pi, ["diff", "--cached", "--check"]);
    await git(pi, ["commit", "-m", params.message]);
    committed = true;
  } finally {
    if (!committed) await unstageFiles(pi, stagedByTool);
  }
  const sha = await currentHead(pi);
  const dirty = await worktreeStatus(pi);
  if (dirty) throw new Error(`Mission commit left dirty tree:\n${dirty}`);
  return { content: [{ type: "text", text: `Mission committed ${params.mission}: ${sha}` }], details: { branch, sha, state } };
}

const factory = (pi: any) => ({
  name: "mission_commit",
  label: "Mission Commit",
  description: "Guarded commit for documentation/process missions",
  parameters: pi.zod.object({
    mission: pi.zod.enum(["design", "roadmap", "plan_stage", "close_stage", "prepare_github"]),
    message: pi.zod.string().min(5).max(140),
  }),
  async execute(_toolCallId: string, params: Params) {
    return executeMissionCommit(pi as PiApi, params);
  },
});

export default factory;

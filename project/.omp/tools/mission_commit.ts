import path from "node:path";
import { STATE_PATH, currentBranch, currentHead, diffHash, ensureNotProtectedBranch, ensureRepo, git, listChangedFiles, matchesAny, pathExists, readJson, reportPath, reviewPath, stageExactFiles, unstageFiles, worktreeStatus, type PiApi, type ToolResult } from "./lib/runtime.ts";

type Params = {
  mission: "design" | "roadmap" | "plan_stage" | "close_stage" | "prepare_github";
  message: string;
};

type State = {
  project: { phase: string };
  current_stage: null | { id: string; status: string };
  current_task: null | { id: string; status: string };
};

type Review = {
  task_id: string;
  reviewer_role: string;
  verdict: string;
  branch: string;
  head: string;
  diff_hash: string;
  findings: Array<{ severity?: string; status?: string }>;
};

const conventionalCommit = /^(docs|chore|refactor)(\([a-z0-9._/-]+\))?!?: .{5,100}$/;
const policies: Record<Params["mission"], string[]> = {
  design: ["PROJECT_BRIEF.md", "docs/**", ".project-factory/**", "AGENTS.md", ".omp/**", ".env.example"],
  roadmap: ["docs/**", ".project-factory/**", "AGENTS.md"],
  plan_stage: ["docs/**", ".project-factory/**"],
  close_stage: ["docs/**", ".project-factory/**"],
  prepare_github: [".project-factory/github-outbox/**", ".project-factory/reports/**", ".project-factory/reviews/**"],
};

function appCodeForbidden(file: string): boolean {
  if (file.startsWith("docs/") || file.startsWith(".omp/") || file.startsWith(".project-factory/")) return false;
  return /(^|\/)(src|app|server|client|api|lib)\//.test(file) || /\.(ts|tsx|js|jsx|go|rs|py|rb|java|kt|swift|cs)$/.test(file);
}

function assertMissionState(mission: Params["mission"], state: State, branch: string): void {
  if (mission === "design") {
    if (state.project.phase !== "architecture_approved") throw new Error("Design commit requires architecture_approved");
    if (branch !== "stage/00-design" && !branch.startsWith("stage/00-")) throw new Error("Design commit requires stage/00-* branch");
  } else if (mission === "roadmap") {
    if (!["roadmap_approved", "implementation"].includes(state.project.phase)) throw new Error("Roadmap commit requires roadmap approval");
  } else if (mission === "plan_stage") {
    if (state.project.phase !== "implementation" || !state.current_stage || state.current_stage.status !== "planned") throw new Error("Plan-stage commit requires a planned current stage");
    if (branch !== `stage/${state.current_stage.id}` && !branch.startsWith(`stage/${state.current_stage.id}-`)) throw new Error("Branch does not match planned stage");
  } else if (mission === "close_stage") {
    if (state.project.phase !== "implementation" || !state.current_stage || state.current_stage.status !== "done") throw new Error("Close-stage commit requires a done current stage");
    if (branch !== `stage/${state.current_stage.id}` && !branch.startsWith(`stage/${state.current_stage.id}-`)) throw new Error("Branch does not match closed stage");
  } else if (state.project.phase === "brief") {
    throw new Error("GitHub drafts are unavailable before design starts");
  }
}

function hasBlockingFinding(review: Review): boolean {
  return review.findings.some((finding) => {
    const severity = String(finding.severity ?? "").toUpperCase();
    const status = String(finding.status ?? "open").toLowerCase();
    return status !== "resolved" && (severity === "P0" || severity === "P1");
  });
}

export async function executeMissionCommit(pi: PiApi, params: Params): Promise<ToolResult> {
  await ensureRepo(pi);
  if (!conventionalCommit.test(params.message)) throw new Error("Mission commit message must be docs/chore/refactor conventional commit");
  const branch = await ensureNotProtectedBranch(pi);
  const state = await readJson<State>(path.join(pi.cwd, STATE_PATH));
  assertMissionState(params.mission, state, branch);

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

  const head = await currentHead(pi);
  const hash = await diffHash(pi);
  const reportFile = path.join(pi.cwd, reportPath("quality-mission", params.mission));
  if (!(await pathExists(reportFile))) throw new Error(`Missing mission quality report: ${path.relative(pi.cwd, reportFile)}`);
  const report = await readJson<any>(reportFile);
  if (report.verdict !== "PASS") throw new Error(`Mission quality report must be PASS, actual: ${report.verdict}`);
  if (report.scope !== "mission" || report.id !== params.mission) throw new Error("Mission quality report identity mismatch");
  if (report.branch !== branch || report.head !== head || report.diff_hash !== hash) throw new Error("Mission quality report is stale");

  const evidenceId = `mission-${params.mission}`;
  const reviewFile = path.join(pi.cwd, reviewPath(evidenceId, "documentation-reviewer"));
  if (!(await pathExists(reviewFile))) throw new Error(`Missing documentation review: ${path.relative(pi.cwd, reviewFile)}`);
  const review = await readJson<Review>(reviewFile);
  if (review.task_id !== evidenceId || review.reviewer_role !== "documentation-reviewer") throw new Error("Mission documentation review identity mismatch");
  if (review.verdict !== "approve" || hasBlockingFinding(review)) throw new Error("Mission documentation review did not approve");
  if (review.branch !== branch || review.head !== head || review.diff_hash !== hash) throw new Error("Mission documentation review is stale");

  const stagedByTool = [...changedFiles].sort();
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
  return { content: [{ type: "text", text: `Mission committed ${params.mission}: ${sha}` }], details: { branch, sha, state, files: stagedByTool } };
}

const factory = (pi: any) => ({
  name: "mission_commit",
  label: "Mission Commit",
  description: "Guarded commit for documentation/process missions with fresh gates and review evidence",
  parameters: pi.zod.object({
    mission: pi.zod.enum(["design", "roadmap", "plan_stage", "close_stage", "prepare_github"]),
    message: pi.zod.string().min(5).max(140),
  }),
  async execute(_toolCallId: string, params: Params) { return executeMissionCommit(pi as PiApi, params); },
});

export default factory;

import fs from "node:fs/promises";
import path from "node:path";
import { REVIEWS_DIR, STATE_PATH, currentHead, diffHash, ensureNotProtectedBranch, ensureRepo, git, listChangedFiles, matchesAny, pathExists, readJson, readTaskContract, reportPath, reviewPath, safeWriteTextAtomic, stageExactFiles, unstageFiles, worktreeStatus, writeJsonAtomic, type PiApi, type ToolResult } from "./lib/runtime.ts";

type ReviewReport = {
  schema_version: number;
  task_id: string;
  reviewer_role: string;
  verdict: string;
  branch: string;
  head: string;
  diff_hash: string;
  created_at: string;
  findings: Array<{ severity?: string; status?: string; title?: string }>;
};

type State = {
  schema_version: number;
  project: { phase: string; architecture_version: string | null };
  current_stage: null | { id: string; status: string };
  current_task: null | {
    id: string;
    stage_id: string;
    status: string;
    doc_path: string;
    expected_commit: string | null;
    allowed_paths: string[];
    reviewers: string[];
    approved_contract_sha256: string | null;
    started_head?: string | null;
  };
  blocked_by: unknown;
  history: Array<Record<string, unknown>>;
};

type Params = { taskId: string; message: string };

const conventionalCommit = /^(feat|fix|test|refactor|docs|build|ci|perf|chore)(\([a-z0-9._/-]+\))?!?: .{5,100}$/;
const writerRoles = new Set(["developer", "test-engineer", "documentation-writer", "github-drafter"]);

function requiredRoles(frontmatter: Record<string, unknown>): string[] {
  const roles = Array.isArray(frontmatter.reviewers) ? frontmatter.reviewers.map(String) : [];
  if (frontmatter.sensitive === true && !roles.includes("security-reviewer")) roles.push("security-reviewer");
  if (frontmatter.data_change === true && !roles.includes("data-reviewer")) roles.push("data-reviewer");
  if (frontmatter.performance_sensitive === true && !roles.includes("performance-reviewer")) roles.push("performance-reviewer");
  if (frontmatter.infrastructure_change === true && !roles.includes("devops-reviewer")) roles.push("devops-reviewer");
  if (!roles.includes("reviewer")) roles.unshift("reviewer");
  return [...new Set(roles)];
}

async function loadReview(filePath: string): Promise<ReviewReport> {
  return JSON.parse(await fs.readFile(filePath, "utf8")) as ReviewReport;
}

function hasBlockingFinding(report: ReviewReport): boolean {
  return report.findings.some((finding) => {
    const severity = String(finding.severity ?? "").toUpperCase();
    const status = String(finding.status ?? "open").toLowerCase();
    return status !== "resolved" && (severity === "P0" || severity === "P1");
  });
}

export async function executeTaskCommit(pi: PiApi, params: Params): Promise<ToolResult> {
  await ensureRepo(pi);
  if (!conventionalCommit.test(params.message)) throw new Error("Commit message must follow Conventional Commits");
  const branch = await ensureNotProtectedBranch(pi);
  if (!branch.startsWith("stage/")) throw new Error(`Expected stage/* branch, actual: ${branch}`);
  const statusBefore = await worktreeStatus(pi);
  const state = await readJson<State>(path.join(pi.cwd, STATE_PATH));
  if (!state.current_stage || state.current_stage.status !== "active") throw new Error("Current stage must be active");
  if (!state.current_task || state.current_task.id !== params.taskId) throw new Error("Current task mismatch");
  if (state.current_task.status !== "ready_to_commit") throw new Error(`Task status must be ready_to_commit, actual: ${state.current_task.status}`);
  const taskPath = path.join(pi.cwd, state.current_task.doc_path);
  const taskDoc = await readTaskContract(taskPath);
  if (String(taskDoc.frontmatter.id) !== params.taskId) throw new Error("Task document id mismatch");
  if (String(taskDoc.frontmatter.status) !== "ready_to_commit") throw new Error("Task document status must be ready_to_commit");
  const approvedHash = state.current_task.approved_contract_sha256 ?? (taskDoc.frontmatter.approved_contract_sha256 ? String(taskDoc.frontmatter.approved_contract_sha256) : null);
  if (!approvedHash) throw new Error("Missing approved_contract_sha256");
  if (taskDoc.contractHash !== approvedHash) throw new Error("Task contract changed after approval");
  const currentHeadHash = await currentHead(pi);
  const startedHead = state.current_task.started_head ?? null;
  if (!startedHead) throw new Error("Missing task started_head; task must enter in_progress through project_state");
  if (startedHead !== currentHeadHash) throw new Error("HEAD changed since task start; pre-existing or external changes must be reconciled before commit");
  const expectedCommit = state.current_task.expected_commit ?? (taskDoc.frontmatter.expected_commit ? String(taskDoc.frontmatter.expected_commit) : null);
  if (!expectedCommit) throw new Error("Missing expected_commit in task contract");
  if (params.message !== expectedCommit) throw new Error(`Commit message mismatch: expected ${expectedCommit}`);
  const allowed = state.current_task.allowed_paths.length > 0 ? state.current_task.allowed_paths : (Array.isArray(taskDoc.frontmatter.allowed_paths) ? taskDoc.frontmatter.allowed_paths.map(String) : []);
  if (allowed.length === 0) throw new Error("No allowed_paths in approved task contract");
  if (allowed.some((item) => item === "**" || item === "*")) throw new Error("Overbroad allowed_paths are forbidden");
  const changedFiles = await listChangedFiles(pi);
  if (changedFiles.length === 0) throw new Error("No changed files");
  const mandatory = new Set([STATE_PATH, state.current_task.doc_path]);
  const unexpected = changedFiles.filter((file) => !mandatory.has(file) && !matchesAny(file, allowed));
  if (unexpected.length > 0) throw new Error(`Unexpected changed files:\n${unexpected.join("\n")}`);
  await git(pi, ["diff", "--check"]);
  const reportFile = path.join(pi.cwd, reportPath("quality-task", params.taskId));
  if (!(await pathExists(reportFile))) throw new Error(`Missing quality report: ${path.relative(pi.cwd, reportFile)}`);
  const quality = await readJson<any>(reportFile);
  const currentDiffHash = await diffHash(pi);
  if (quality.verdict !== "PASS") throw new Error(`Task quality report must be PASS, actual: ${quality.verdict}`);
  if (quality.scope !== "task" || quality.id !== params.taskId) throw new Error("Task quality report id mismatch");
  if (quality.branch !== branch || quality.head !== currentHeadHash || quality.diff_hash !== currentDiffHash) throw new Error("Task quality report is stale");
  const required = requiredRoles(taskDoc.frontmatter);
  for (const role of required) {
    const reviewFile = path.join(pi.cwd, reviewPath(params.taskId, role));
    if (!(await pathExists(reviewFile))) throw new Error(`Missing review report: ${path.relative(pi.cwd, reviewFile)}`);
    const review = await loadReview(reviewFile);
    if (review.reviewer_role !== role) throw new Error(`Review role mismatch in ${reviewFile}`);
    if (writerRoles.has(review.reviewer_role)) throw new Error(`Synthetic writer review is forbidden: ${review.reviewer_role}`);
    if (review.task_id !== params.taskId) throw new Error(`Review task mismatch in ${reviewFile}`);
    if (review.verdict !== "approve") throw new Error(`Review did not approve: ${role}`);
    if (review.branch !== branch || review.head !== currentHeadHash || review.diff_hash !== currentDiffHash) throw new Error(`Review is stale: ${role}`);
    if (hasBlockingFinding(review)) throw new Error(`Blocking finding remains in review: ${role}`);
  }
  const stageReadme = path.join(pi.cwd, `docs/stages/${state.current_stage.id}-README.md`);
  if (!(await pathExists(stageReadme))) throw new Error(`Missing stage README: ${path.relative(pi.cwd, stageReadme)}`);
  const updatedFrontmatter = { ...taskDoc.frontmatter, status: "done" };
  const nextState: State = {
    ...state,
    current_task: {
      ...state.current_task,
      status: "done",
    },
    history: [
      ...state.history,
      {
        at: new Date().toISOString(),
        actor: "task_commit",
        action: "task_commit",
        scope: "task",
        from: "ready_to_commit",
        to: "done",
        reason: params.message,
        branch,
        head: currentHeadHash,
      },
    ],
  };
  const nextStateText = `${JSON.stringify(nextState, null, 2)}\n`;
  const nextTaskText = renderTask(updatedFrontmatter, taskDoc.body);
  await safeWriteTextAtomic(taskPath, nextTaskText);
  await safeWriteTextAtomic(path.join(pi.cwd, STATE_PATH), nextStateText);
  const postMutationFiles = await listChangedFiles(pi);
  const requiredPostMutation = new Set([
    state.current_task.doc_path,
    STATE_PATH,
    reportPath("quality-task", params.taskId),
    ...required.map((role) => reviewPath(params.taskId, role)),
  ]);
  const unexpectedPostMutation = postMutationFiles.filter((file) => !changedFiles.includes(file) && !requiredPostMutation.has(file));
  const stagedByTool = [...new Set([...changedFiles, ...requiredPostMutation])].sort();
  let committed = false;
  try {
    await stageExactFiles(pi, stagedByTool);
    await git(pi, ["diff", "--cached", "--check"]);
    await git(pi, ["commit", "-m", params.message]);
    committed = true;
  } finally {
    if (!committed) {
      await safeWriteTextAtomic(taskPath, taskDoc.source);
      await writeJsonAtomic(path.join(pi.cwd, STATE_PATH), state);
      await unstageFiles(pi, stagedByTool);
      const statusAfterFailure = await worktreeStatus(pi);
      if (statusAfterFailure !== statusBefore) {
        // best effort only; do not mutate user-owned files beyond restoring our own changes
      }
    }
  }
  const sha = await currentHead(pi);
  const dirty = await worktreeStatus(pi);
  if (dirty) throw new Error(`Commit created but worktree remains dirty:\n${dirty}`);
  return { content: [{ type: "text", text: `Committed ${params.taskId}: ${sha}` }], details: { sha, branch, files: stagedByTool } };

}

function renderTask(frontmatter: Record<string, unknown>, body: string): string {
  const lines = Object.entries(frontmatter).map(([key, value]) => `${key}: ${stringifyValue(value)}`);
  return `---\n${lines.join("\n")}\n---\n${body.startsWith("\n") ? body : `\n${body}`}`;
}

function stringifyValue(value: unknown): string {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return String(value);
  if (Array.isArray(value)) return `[${value.map((item) => stringifyValue(item)).join(", ")}]`;
  return JSON.stringify(String(value));
}

const factory = (pi: any) => ({
  name: "task_commit",
  label: "Task Commit",
  description: "Validates task state, fresh reports and allowed file scope, then creates one commit",
  parameters: pi.zod.object({
    taskId: pi.zod.string().min(1).max(100),
    message: pi.zod.string().min(5).max(140),
  }),
  async execute(_toolCallId: string, params: Params) {
    return executeTaskCommit(pi as PiApi, params);
  },
});

export default factory;

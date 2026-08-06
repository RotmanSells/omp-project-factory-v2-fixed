import path from "node:path";
import { STATE_PATH, currentBranch, currentHead, ensureCleanWorktree, ensureNotProtectedBranch, ensureRepo, nowIso, readJson, readTaskContract, writeJsonAtomic, type HistoryEntry, type PiApi, type ToolResult } from "./lib/runtime.ts";

type ProjectPhase = "brief" | "design_in_progress" | "architecture_owner_review" | "architecture_approved" | "roadmap_in_progress" | "roadmap_approved" | "implementation" | "completed" | "blocked_owner_decision";
type StageStatus = "planning" | "planned" | "active" | "closing" | "done" | "blocked_owner_decision";
type TaskStatus = "draft" | "owner_review" | "approved" | "in_progress" | "in_review" | "ready_to_commit" | "done" | "blocked_owner_decision";

type ProjectState = {
  schema_version: number;
  project: { phase: ProjectPhase; architecture_version: string | null };
  current_stage: null | { id: string; status: StageStatus; title?: string | null; readme_path?: string | null };
  current_task: null | {
    id: string;
    stage_id: string;
    status: TaskStatus;
    doc_path: string;
    expected_commit: string | null;
    allowed_paths: string[];
    reviewers: string[];
    approved_contract_sha256: string | null;
    started_head?: string | null;
  };
  blocked_by: null | { scope: "project" | "stage" | "task"; previous: string; reason: string; actor: string; at: string };
  history: HistoryEntry[];
};

type Params = {
  action: "show" | "validate" | "transition" | "owner_override";
  actor?: string;
  scope?: "project" | "stage" | "task";
  next?: string;
  reason?: string;
  note?: string;
  stageId?: string;
  taskId?: string;
  taskDocPath?: string;
  architectureVersion?: string | null;
};

const projectPhases = new Set<ProjectPhase>(["brief", "design_in_progress", "architecture_owner_review", "architecture_approved", "roadmap_in_progress", "roadmap_approved", "implementation", "completed", "blocked_owner_decision"]);
const stageStatuses = new Set<StageStatus>(["planning", "planned", "active", "closing", "done", "blocked_owner_decision"]);
const taskStatuses = new Set<TaskStatus>(["draft", "owner_review", "approved", "in_progress", "in_review", "ready_to_commit", "done", "blocked_owner_decision"]);

const projectTransitions: Record<ProjectPhase, ProjectPhase[]> = {
  brief: ["design_in_progress"],
  design_in_progress: ["architecture_owner_review", "blocked_owner_decision"],
  architecture_owner_review: ["architecture_approved", "blocked_owner_decision"],
  architecture_approved: ["roadmap_in_progress"],
  roadmap_in_progress: ["roadmap_approved", "blocked_owner_decision"],
  roadmap_approved: ["implementation"],
  implementation: ["completed", "blocked_owner_decision"],
  completed: [],
  blocked_owner_decision: [],
};
const stageTransitions: Record<StageStatus, StageStatus[]> = {
  planning: ["planned", "blocked_owner_decision"],
  planned: ["active", "blocked_owner_decision"],
  active: ["closing", "blocked_owner_decision"],
  closing: ["done", "blocked_owner_decision"],
  done: [],
  blocked_owner_decision: [],
};
const taskTransitions: Record<TaskStatus, TaskStatus[]> = {
  draft: ["owner_review", "blocked_owner_decision"],
  owner_review: ["approved", "blocked_owner_decision"],
  approved: ["in_progress", "blocked_owner_decision"],
  in_progress: ["in_review", "blocked_owner_decision"],
  in_review: ["ready_to_commit", "in_progress", "blocked_owner_decision"],
  ready_to_commit: ["done", "blocked_owner_decision"],
  done: [],
  blocked_owner_decision: [],
};

function asProjectPhase(value: string | undefined): ProjectPhase {
  if (!value || !projectPhases.has(value as ProjectPhase)) throw new Error(`Invalid project phase: ${value ?? "missing"}`);
  return value as ProjectPhase;
}
function asStageStatus(value: string | undefined): StageStatus {
  if (!value || !stageStatuses.has(value as StageStatus)) throw new Error(`Invalid stage status: ${value ?? "missing"}`);
  return value as StageStatus;
}
function asTaskStatus(value: string | undefined): TaskStatus {
  if (!value || !taskStatuses.has(value as TaskStatus)) throw new Error(`Invalid task status: ${value ?? "missing"}`);
  return value as TaskStatus;
}

function assertState(state: ProjectState): void {
  if (state.schema_version !== 2) throw new Error(`Unsupported schema version: ${state.schema_version}`);
  if (!state.project || !Array.isArray(state.history)) throw new Error("Malformed state file");
  if (!projectPhases.has(state.project.phase)) throw new Error(`Invalid project phase in state: ${state.project.phase}`);
  if (state.current_stage && !stageStatuses.has(state.current_stage.status)) throw new Error(`Invalid stage status in state: ${state.current_stage.status}`);
  if (state.current_task && !taskStatuses.has(state.current_task.status)) throw new Error(`Invalid task status in state: ${state.current_task.status}`);
  if (state.current_task && state.current_stage && state.current_task.stage_id !== state.current_stage.id) throw new Error("Current task does not belong to current stage");
}

async function loadState(pi: PiApi): Promise<ProjectState> {
  const state = await readJson<ProjectState>(path.join(pi.cwd, STATE_PATH));
  assertState(state);
  return state;
}
function pushHistory(state: ProjectState, entry: HistoryEntry): void { state.history = [...state.history, entry]; }
function historyEntry(scope: "project" | "stage" | "task", actor: string, from: string | null, to: string | null, reason: string, branch: string, head: string, note?: string): HistoryEntry {
  return { at: nowIso(), actor, action: "transition", scope, from, to, reason, branch, head, note };
}
function ensureAllowedTransition<T extends string>(from: T, to: T, table: Record<T, T[]>): void {
  if (!(table[from] ?? []).includes(to)) throw new Error(`Transition ${from} -> ${to} is not allowed`);
}

async function projectTransition(state: ProjectState, params: Params, branch: string, head: string): Promise<ProjectState> {
  const actor = params.actor ?? "Main";
  const next = asProjectPhase(params.next);
  const current = state.project.phase;
  ensureAllowedTransition(current, next, projectTransitions);
  state.project.phase = next;
  if (params.architectureVersion !== undefined) state.project.architecture_version = params.architectureVersion;
  state.blocked_by = null;
  pushHistory(state, historyEntry("project", actor, current, next, params.reason ?? "", branch, head, params.note));
  return state;
}

async function stageTransition(state: ProjectState, params: Params, branch: string, head: string): Promise<ProjectState> {
  const actor = params.actor ?? "Main";
  const stageId = params.stageId;
  if (!stageId) throw new Error("stageId is required for stage transition");
  const next = asStageStatus(params.next);
  if (!state.current_stage || (state.current_stage.status === "done" && state.current_stage.id !== stageId)) {
    if (next !== "planning") throw new Error("A new stage can only start at planning");
    if (state.current_task && state.current_task.status !== "done") throw new Error("Cannot replace stage while current task is incomplete");
    const previous = state.current_stage?.status ?? null;
    state.current_stage = { id: stageId, status: "planning", readme_path: `docs/stages/${stageId}-README.md` };
    state.current_task = null;
    state.blocked_by = null;
    pushHistory(state, historyEntry("stage", actor, previous, "planning", params.reason ?? "", branch, head, params.note));
    return state;
  }
  if (state.current_stage.id !== stageId) throw new Error(`Current stage mismatch: ${state.current_stage.id} != ${stageId}`);
  ensureAllowedTransition(state.current_stage.status, next, stageTransitions);
  const previous = state.current_stage.status;
  state.current_stage.status = next;
  state.blocked_by = null;
  pushHistory(state, historyEntry("stage", actor, previous, next, params.reason ?? "", branch, head, params.note));
  return state;
}

async function taskTransition(pi: PiApi, state: ProjectState, params: Params, branch: string, head: string): Promise<ProjectState> {
  const actor = params.actor ?? "Main";
  const taskId = params.taskId;
  const taskDocPath = params.taskDocPath;
  const stageId = params.stageId ?? state.current_stage?.id;
  if (!taskId || !taskDocPath || !stageId) throw new Error("taskId, taskDocPath and stageId are required for task transition");
  if (!state.current_stage || state.current_stage.id !== stageId) throw new Error("Task stage does not match current stage");
  const next = asTaskStatus(params.next);
  const contract = await readTaskContract(path.join(pi.cwd, taskDocPath));
  if (String(contract.frontmatter.id ?? "") !== taskId) throw new Error("Task document id mismatch");
  const allowedPaths = Array.isArray(contract.frontmatter.allowed_paths) ? contract.frontmatter.allowed_paths.map(String) : [];
  const reviewers = Array.isArray(contract.frontmatter.reviewers) ? contract.frontmatter.reviewers.map(String) : [];
  const expectedCommit = contract.frontmatter.expected_commit == null ? null : String(contract.frontmatter.expected_commit);

  if (!state.current_task || (state.current_task.status === "done" && state.current_task.id !== taskId)) {
    if (next !== "draft" && next !== "approved") throw new Error("A new tracked task can only enter as draft or approved");
    state.current_task = {
      id: taskId,
      stage_id: stageId,
      status: next,
      doc_path: taskDocPath,
      expected_commit: expectedCommit,
      allowed_paths: allowedPaths,
      reviewers,
      approved_contract_sha256: next === "approved" ? contract.contractHash : null,
      started_head: null,
    };
    state.blocked_by = null;
    pushHistory(state, historyEntry("task", actor, null, next, params.reason ?? "", branch, head, params.note));
    return state;
  }
  if (state.current_task.id !== taskId) throw new Error(`Current task mismatch: ${state.current_task.id} != ${taskId}`);
  ensureAllowedTransition(state.current_task.status, next, taskTransitions);
  const previous = state.current_task.status;
  state.current_task.doc_path = taskDocPath;
  state.current_task.allowed_paths = allowedPaths;
  state.current_task.reviewers = reviewers;
  state.current_task.expected_commit = expectedCommit;
  if (next === "in_progress") {
    await ensureCleanWorktree(pi);
    await ensureNotProtectedBranch(pi);
    state.current_task.started_head = head;
    if (state.current_stage.status === "planned") state.current_stage.status = "active";
  }
  if (next === "approved") state.current_task.approved_contract_sha256 = contract.contractHash;
  state.current_task.status = next;
  state.blocked_by = null;
  pushHistory(state, historyEntry("task", actor, previous, next, params.reason ?? "", branch, head, params.note));
  return state;
}

async function blockTransition(state: ProjectState, params: Params, branch: string, head: string): Promise<ProjectState> {
  const actor = params.actor ?? "Main";
  const scope = params.scope;
  if (!scope) throw new Error("scope is required for blocked_owner_decision");
  const reason = params.reason ?? "Owner decision required";
  if (scope === "project") {
    const previous = state.project.phase;
    if (!["design_in_progress", "architecture_owner_review", "roadmap_in_progress", "implementation"].includes(previous)) throw new Error(`Project phase cannot be blocked from ${previous}`);
    state.project.phase = "blocked_owner_decision";
    state.blocked_by = { scope, previous, reason, actor, at: nowIso() };
    pushHistory(state, historyEntry(scope, actor, previous, "blocked_owner_decision", reason, branch, head, params.note));
    return state;
  }
  if (scope === "stage") {
    if (!state.current_stage) throw new Error("No current stage to block");
    const previous = state.current_stage.status;
    if (!["planning", "planned", "active", "closing"].includes(previous)) throw new Error(`Stage cannot be blocked from ${previous}`);
    state.current_stage.status = "blocked_owner_decision";
    state.blocked_by = { scope, previous, reason, actor, at: nowIso() };
    pushHistory(state, historyEntry(scope, actor, previous, "blocked_owner_decision", reason, branch, head, params.note));
    return state;
  }
  if (!state.current_task) throw new Error("No current task to block");
  const previous = state.current_task.status;
  if (!["draft", "owner_review", "approved", "in_progress", "in_review", "ready_to_commit"].includes(previous)) throw new Error(`Task cannot be blocked from ${previous}`);
  state.current_task.status = "blocked_owner_decision";
  state.blocked_by = { scope: "task", previous, reason, actor, at: nowIso() };
  pushHistory(state, historyEntry("task", actor, previous, "blocked_owner_decision", reason, branch, head, params.note));
  return state;
}

async function ownerOverride(state: ProjectState, params: Params, branch: string, head: string): Promise<ProjectState> {
  if (!state.blocked_by) throw new Error("State is not blocked");
  const actor = params.actor ?? "Main";
  const scope = params.scope ?? state.blocked_by.scope;
  if (scope !== state.blocked_by.scope) throw new Error(`Blocked scope mismatch: ${scope} != ${state.blocked_by.scope}`);
  const requested = params.next ?? state.blocked_by.previous;
  if (requested !== state.blocked_by.previous) throw new Error("Owner override may only resume the exact pre-block state");
  if (scope === "project") state.project.phase = asProjectPhase(requested);
  else if (scope === "stage") { if (!state.current_stage) throw new Error("No current stage"); state.current_stage.status = asStageStatus(requested); }
  else { if (!state.current_task) throw new Error("No current task"); state.current_task.status = asTaskStatus(requested); }
  state.blocked_by = null;
  state.history = [...state.history, { at: nowIso(), actor, action: "owner_override", scope, from: "blocked_owner_decision", to: requested, reason: params.reason ?? "Owner override", branch, head, note: params.note }];
  return state;
}

export async function executeProjectState(pi: PiApi, params: Params): Promise<ToolResult> {
  await ensureRepo(pi);
  const state = await loadState(pi);
  if (params.action === "show") return { content: [{ type: "text", text: JSON.stringify(state, null, 2) }], details: { state } };
  if (params.action === "validate") return { content: [{ type: "text", text: "Project state is valid." }], details: { state } };
  const branch = await currentBranch(pi);
  const head = await currentHead(pi);
  let nextState = structuredClone(state);
  if (params.action === "owner_override") nextState = await ownerOverride(nextState, params, branch, head);
  else if (params.next === "blocked_owner_decision") nextState = await blockTransition(nextState, params, branch, head);
  else if (params.scope === "project") nextState = await projectTransition(nextState, params, branch, head);
  else if (params.scope === "stage") nextState = await stageTransition(nextState, params, branch, head);
  else if (params.scope === "task") nextState = await taskTransition(pi, nextState, params, branch, head);
  else throw new Error("scope is required for transition");
  assertState(nextState);
  await writeJsonAtomic(path.join(pi.cwd, STATE_PATH), nextState);
  return { content: [{ type: "text", text: `Project state updated: ${params.scope ?? "project"} -> ${params.next ?? "override"}` }], details: { state: nextState } };
}

const factory = (pi: any) => ({
  name: "project_state",
  label: "Project State",
  description: "Reads and safely transitions the project state file",
  parameters: pi.zod.object({
    action: pi.zod.enum(["show", "validate", "transition", "owner_override"]),
    actor: pi.zod.string().optional(),
    scope: pi.zod.enum(["project", "stage", "task"]).optional(),
    next: pi.zod.string().optional(),
    reason: pi.zod.string().optional(),
    note: pi.zod.string().optional(),
    stageId: pi.zod.string().optional(),
    taskId: pi.zod.string().optional(),
    taskDocPath: pi.zod.string().optional(),
    architectureVersion: pi.zod.string().nullable().optional(),
  }),
  async execute(_toolCallId: string, params: Params) { return executeProjectState(pi as PiApi, params); },
});
export default factory;

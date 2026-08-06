import path from "node:path";
import { currentBranch, currentHead, diffHash, ensureDir, nowIso, reviewPath, writeJsonAtomic, type PiApi, type ToolResult } from "./lib/runtime.ts";

type Finding = {
  severity: "P0" | "P1" | "P2" | "P3";
  status: "open" | "resolved";
  title: string;
  trigger: string;
  impact: string;
  fix_direction: string;
};

type Params = {
  taskId: string;
  reviewerRole: "reviewer" | "security-reviewer" | "data-reviewer" | "performance-reviewer" | "devops-reviewer" | "documentation-reviewer";
  verdict: "approve" | "request_changes";
  findings: Finding[];
  note?: string;
};

export async function executeReviewReport(pi: PiApi, params: Params): Promise<ToolResult> {
  if (params.verdict === "approve" && params.findings.some((finding) => finding.status === "open" && (finding.severity === "P0" || finding.severity === "P1"))) {
    throw new Error("Cannot approve while open P0/P1 findings remain");
  }
  if (params.verdict === "request_changes" && params.findings.length === 0) {
    throw new Error("request_changes requires at least one concrete finding");
  }
  const branch = await currentBranch(pi);
  const head = await currentHead(pi);
  const hash = await diffHash(pi);
  const report = {
    schema_version: 1,
    task_id: params.taskId,
    reviewer_role: params.reviewerRole,
    verdict: params.verdict,
    branch,
    head,
    diff_hash: hash,
    created_at: nowIso(),
    findings: params.findings,
    note: params.note ?? null,
  };
  const relative = reviewPath(params.taskId, params.reviewerRole);
  const output = path.join(pi.cwd, relative);
  await ensureDir(path.dirname(output));
  await writeJsonAtomic(output, report);
  return { content: [{ type: "text", text: `Review report recorded: ${relative}` }], details: { reportPath: relative, report } };
}

const factory = (pi: any) => ({
  name: "review_report",
  label: "Review Report",
  description: "Records a structured review tied to the current branch, HEAD and diff hash",
  parameters: pi.zod.object({
    taskId: pi.zod.string().min(1).max(100),
    reviewerRole: pi.zod.enum(["reviewer", "security-reviewer", "data-reviewer", "performance-reviewer", "devops-reviewer", "documentation-reviewer"]),
    verdict: pi.zod.enum(["approve", "request_changes"]),
    findings: pi.zod.array(pi.zod.object({
      severity: pi.zod.enum(["P0", "P1", "P2", "P3"]),
      status: pi.zod.enum(["open", "resolved"]),
      title: pi.zod.string().min(1),
      trigger: pi.zod.string().min(1),
      impact: pi.zod.string().min(1),
      fix_direction: pi.zod.string().min(1),
    })),
    note: pi.zod.string().optional(),
  }),
  async execute(_toolCallId: string, params: Params) { return executeReviewReport(pi as PiApi, params); },
});

export default factory;

import { currentBranch, currentHead, diffHash, execOk, git, type PiApi, type ToolResult } from "./lib/runtime.ts";

type Params = {
  action: "status" | "diff" | "diff-check" | "log" | "show" | "current_branch" | "current_head" | "diff_hash";
  revision?: string;
  path?: string;
  maxCount?: number;
};

export async function executeGitInspect(pi: PiApi, params: Params): Promise<ToolResult> {
  let text = "";
  if (params.action === "status") {
    text = await git(pi, ["status", "--short", "--branch", "--untracked-files=all"]);
  } else if (params.action === "diff") {
    const args = ["diff", "--binary", params.revision ?? "HEAD", "--"];
    if (params.path) args.push(params.path);
    text = await git(pi, args);
  } else if (params.action === "diff-check") {
    text = await execOk(pi, "git", ["diff", "--check"]);
  } else if (params.action === "log") {
    text = await git(pi, ["log", `--max-count=${params.maxCount ?? 10}`, "--oneline", "--decorate"]);
  } else if (params.action === "show") {
    if (!params.revision) throw new Error("revision is required for show");
    text = await git(pi, ["show", "--stat", params.revision]);
  } else if (params.action === "current_branch") {
    text = await currentBranch(pi);
  } else if (params.action === "current_head") {
    text = await currentHead(pi);
  } else {
    text = await diffHash(pi);
  }
  return { content: [{ type: "text", text }], details: { action: params.action } };
}

const factory = (pi: any) => ({
  name: "git_inspect",
  label: "Git Inspect",
  description: "Read-only Git inspection for reviewer agents",
  parameters: pi.zod.object({
    action: pi.zod.enum(["status", "diff", "diff-check", "log", "show", "current_branch", "current_head", "diff_hash"]),
    revision: pi.zod.string().optional(),
    path: pi.zod.string().optional(),
    maxCount: pi.zod.number().optional(),
  }),
  async execute(_toolCallId: string, params: Params) {
    return executeGitInspect(pi as PiApi, params);
  },
});

export default factory;

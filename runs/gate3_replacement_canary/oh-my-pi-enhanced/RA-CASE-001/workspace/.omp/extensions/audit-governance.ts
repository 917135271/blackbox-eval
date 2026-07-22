import { appendFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";

function append(eventType: string, payload: Record<string, unknown>): void {
  const workDir = process.env.AUDIT_WORK_DIR ?? process.cwd();
  const path = join(workDir, "traces", "native_events.jsonl");
  mkdirSync(dirname(path), { recursive: true });
  appendFileSync(
    path,
    `${JSON.stringify({
      event_type: eventType,
      task_id: process.env.AUDIT_TASK_ID ?? "unknown",
      framework: "oh-my-pi",
      experiment_group: process.env.AUDIT_EXPERIMENT_GROUP ?? "unknown",
      occurred_at: Date.now() / 1000,
      ...payload,
    })}\n`,
    "utf8",
  );
}

export default function auditGovernance(pi: any): void {
  pi.on("session_start", async () => append("native_session_started", {}));
  pi.on("agent_start", async () => append("native_agent_started", {}));
  pi.on("agent_end", async () => append("native_agent_completed", {}));
  pi.on("auto_compaction_start", async () => append("native_compaction_started", {}));
  pi.on("auto_compaction_end", async () => append("native_compaction_completed", {}));
  pi.on("tool_call", async (event: any) =>
    append("native_tool_started", {
      tool: event.toolName,
      argument_fields: Object.keys(event.input ?? {}).sort(),
    }),
  );
  pi.on("tool_result", async (event: any) =>
    append(event.isError ? "native_tool_failed" : "native_tool_completed", {
      tool: event.toolName,
      is_error: Boolean(event.isError),
    }),
  );
  pi.on("session_shutdown", async () => append("native_session_completed", {}));
}

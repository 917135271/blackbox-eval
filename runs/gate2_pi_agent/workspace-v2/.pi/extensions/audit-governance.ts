import { spawn } from "node:child_process";
import { appendFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { Type } from "@earendil-works/pi-ai";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

type JsonObject = Record<string, unknown>;

const framework = "pi-agent";
const forbiddenMarkers = ["ground_truth", "historical_answer", "other_candidate", "judge.py"];

function workDir(): string {
	return process.env.AUDIT_WORK_DIR ?? process.cwd();
}

function append(eventType: string, payload: JsonObject = {}): void {
	try {
		const path = join(workDir(), "traces", "native_events.jsonl");
		mkdirSync(dirname(path), { recursive: true });
		appendFileSync(
			path,
			`${JSON.stringify({
				event_type: eventType,
				task_id: process.env.AUDIT_TASK_ID ?? "unknown",
				framework,
				experiment_group: process.env.AUDIT_EXPERIMENT_GROUP ?? "unknown",
				occurred_at: Date.now() / 1000,
				...payload,
			})}\n`,
			"utf8",
		);
	} catch {
		// The outer runner remains authoritative if supplementary native logging fails.
	}
}

async function callControl(name: string, arguments_: JsonObject): Promise<JsonObject> {
	const script =
		process.env.AUDIT_CONTROL_MCP_PATH ?? join(process.cwd(), "shared", "control-mcp", "audit_control_mcp.py");
	const request = JSON.stringify({
		jsonrpc: "2.0",
		id: `${name}-${Date.now()}`,
		method: "tools/call",
		params: { name, arguments: arguments_ },
	});

	return await new Promise<JsonObject>((resolve, reject) => {
		const child = spawn("python3", [script], {
			cwd: process.cwd(),
			env: process.env,
			stdio: ["pipe", "pipe", "pipe"],
		});
		let stdout = "";
		let stderr = "";
		child.stdout.on("data", (chunk) => (stdout += chunk.toString()));
		child.stderr.on("data", (chunk) => (stderr += chunk.toString()));
		child.on("error", reject);
		child.on("close", (code) => {
			if (code !== 0) {
				reject(new Error(stderr.trim() || `audit control exited with ${code}`));
				return;
			}
			try {
				const response = JSON.parse(stdout.trim().split(/\r?\n/).at(-1) ?? "{}");
				if (response.error) throw new Error(response.error.message ?? JSON.stringify(response.error));
				const content = response.result?.content?.[0]?.text;
				resolve(content ? JSON.parse(content) : response.result ?? {});
			} catch (error) {
				reject(new Error(`invalid audit control response: ${String(error)}; stderr=${stderr.trim()}`));
			}
		});
		child.stdin.end(`${request}\n`);
	});
}

function controlTool(name: string, description: string, parameters: any, terminate = false) {
	return defineTool({
		name,
		label: name,
		description,
		parameters,
		async execute(_toolCallId, params) {
			const value = await callControl(name, params as JsonObject);
			return {
				content: [{ type: "text" as const, text: JSON.stringify(value) }],
				details: value,
				terminate: terminate && value.status === "accepted",
			};
		},
	});
}

const summarySchema = Type.Object({
	decision: Type.String(),
	key_findings: Type.Array(Type.Any()),
	record_ids: Type.Array(Type.String()),
	citations: Type.Array(Type.Any()),
	unresolved_items: Type.Array(Type.Any()),
	artifact_paths: Type.Array(Type.String()),
});

export default function auditGovernance(pi: ExtensionAPI): void {
	const dispatchedInvocations = new Set<string>();
	pi.registerTool(
		controlTool(
			"authorize_audit_subagent",
			"Authorize one bounded audit subagent before invoking the native subagent tool.",
			Type.Object({
				role: Type.String(),
				reason_code: Type.String(),
				complexity: Type.Integer({ minimum: 0, maximum: 6 }),
				context: Type.Record(Type.String(), Type.Any()),
				artifact_paths: Type.Optional(Type.Array(Type.String())),
				requested_token_budget: Type.Optional(Type.Integer({ minimum: 1000, maximum: 12000 })),
			}),
		),
	);
	pi.registerTool(
		controlTool(
			"complete_audit_subagent",
			"Register a completed native subagent and validate its six-field summary and artifacts.",
			Type.Object({
				invocation_id: Type.String(),
				summary: summarySchema,
				artifact_paths: Type.Optional(Type.Array(Type.String())),
				token_usage: Type.Optional(Type.Record(Type.String(), Type.Integer({ minimum: 0 }))),
				status: Type.Optional(Type.String()),
			}),
		),
	);
	pi.registerTool(
		controlTool(
			"checkpoint_audit_context",
			"Persist recoverable task memory and record whether native context compaction occurred.",
			Type.Object({
				stage: Type.String(),
				context_usage_percent: Type.Number({ minimum: 0, maximum: 100 }),
				retained_state: Type.Record(Type.String(), Type.Any()),
				artifact_paths: Type.Optional(Type.Array(Type.String())),
				compacted: Type.Optional(Type.Boolean()),
				estimation_method: Type.Optional(Type.String()),
			}),
		),
	);
	pi.registerTool(
		controlTool(
			"validate_audit_result",
			"Validate result fields, record IDs, citations, evidence matrix, and validation report before submission.",
			Type.Object({
				result: Type.Optional(Type.Record(Type.String(), Type.Any())),
				result_path: Type.Optional(Type.String()),
				evidence_matrix_path: Type.Optional(Type.String()),
				validation_report_path: Type.Optional(Type.String()),
			}),
		),
	);
	pi.registerTool(
		controlTool(
			"submit_audit_result",
			"Submit the final audit result through the common schema gate. Use only as the last action.",
			Type.Object({
				result: Type.Optional(Type.Record(Type.String(), Type.Any())),
				result_path: Type.Optional(Type.String()),
				evidence_matrix_path: Type.Optional(Type.String()),
				validation_report_path: Type.Optional(Type.String()),
			}),
			true,
		),
	);

	pi.on("session_start", async () => append("native_session_started"));
	pi.on("agent_start", async () => append("native_agent_started"));
	pi.on("agent_end", async () => append("native_agent_completed"));
	pi.on("session_before_compact", async (event) =>
		append("native_compaction_started", { reason: event.reason, will_retry: event.willRetry }),
	);
	pi.on("session_compact", async (event) =>
		append("native_compaction_completed", { reason: event.reason, from_extension: event.fromExtension }),
	);
	pi.on("tool_call", async (event) => {
		const serialized = JSON.stringify(event.input ?? {}).toLowerCase();
		const forbidden = forbiddenMarkers.find((marker) => serialized.includes(marker));
		if (event.toolName === "subagent") {
			const requested = String((event.input as JsonObject).agent ?? "").replaceAll("-", "_");
			const statePath = join(workDir(), ".audit-control", "state.json");
			let invocationId = "";
			if (requested && existsSync(statePath)) {
				try {
					const state = JSON.parse(readFileSync(statePath, "utf8"));
					const match = Object.values(state.subagent_invocations ?? {}).find(
						(value: any) => value.role === requested && value.status === "authorized",
					) as any;
					invocationId = match?.invocation_id ?? "";
				} catch {
					invocationId = "";
				}
			}
			if (!invocationId) {
				append("native_subagent_rejected", { role: requested || "unknown", reason: "authorization_required" });
				return { block: true, reason: "authorize_audit_subagent must approve this role before subagent execution" };
			}
			if (dispatchedInvocations.has(invocationId)) {
				append("native_subagent_rejected", { role: requested, invocation_id: invocationId, reason: "already_dispatched" });
				return { block: true, reason: "each audit subagent authorization permits exactly one native invocation" };
			}
			dispatchedInvocations.add(invocationId);
			append("native_subagent_started", { role: requested, invocation_id: invocationId });
		}
		append("native_tool_started", {
			tool: event.toolName,
			argument_fields: Object.keys(event.input ?? {}).sort(),
			blocked: Boolean(forbidden),
		});
		if (forbidden) return { block: true, reason: `blocked forbidden evaluation asset: ${forbidden}` };
	});
	pi.on("tool_result", async (event) => {
		append(event.isError ? "native_tool_failed" : "native_tool_completed", {
			tool: event.toolName,
			is_error: event.isError,
		});
		if (event.toolName === "subagent") {
			append(event.isError ? "native_subagent_failed" : "native_subagent_returned", {});
		}
	});
	pi.on("session_shutdown", async () => append("native_session_completed"));
}

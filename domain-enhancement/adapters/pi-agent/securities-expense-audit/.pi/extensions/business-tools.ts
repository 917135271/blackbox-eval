import { spawn } from "node:child_process";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

type JsonObject = Record<string, unknown>;
type McpTool = {
	name: string;
	description?: string;
	inputSchema: JsonObject;
};

const servers = [
	{ name: "policy_query", script: "/benchmark/fixtures/policy_query_mcp.py" },
	{ name: "expense_query", script: "/benchmark/fixtures/expense_query_mcp.py" },
];

async function callRpc(script: string, method: string, params?: JsonObject): Promise<JsonObject> {
	const request = JSON.stringify({
		jsonrpc: "2.0",
		id: `${method}-${Date.now()}`,
		method,
		...(params ? { params } : {}),
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
				reject(new Error(stderr.trim() || `MCP process exited with ${code}`));
				return;
			}
			try {
				const response = JSON.parse(stdout.trim().split(/\r?\n/).at(-1) ?? "{}");
				if (response.error) throw new Error(response.error.message ?? JSON.stringify(response.error));
				resolve(response.result ?? {});
			} catch (error) {
				reject(new Error(`invalid MCP response: ${String(error)}; stderr=${stderr.trim()}`));
			}
		});
		child.stdin.end(`${request}\n`);
	});
}

export default async function businessTools(pi: ExtensionAPI): Promise<void> {
	for (const server of servers) {
		const listed = await callRpc(server.script, "tools/list");
		for (const tool of (listed.tools ?? []) as McpTool[]) {
			pi.registerTool(
				defineTool({
					name: tool.name,
					label: `${server.name}.${tool.name}`,
					description: tool.description ?? `Call ${server.name}.${tool.name}.`,
					parameters: tool.inputSchema as any,
					async execute(_toolCallId, params) {
						const response = await callRpc(server.script, "tools/call", {
							name: tool.name,
							arguments: params as JsonObject,
						});
						const text = (response.content as Array<{ type: string; text?: string }> | undefined)?.find(
							(item) => item.type === "text",
						)?.text;
						const value = text ? JSON.parse(text) : response;
						return {
							content: [{ type: "text" as const, text: JSON.stringify(value) }],
							details: value,
						};
					},
				}),
			);
		}
	}
}

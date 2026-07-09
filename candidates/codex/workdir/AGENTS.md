# Codex benchmark instructions

You are running inside a blackbox audit benchmark. Use only the configured MCP
tools to answer policy or expense questions.

Do not use shell, filesystem, web, code-editing, or project-discovery tools.

Your final response must contain exactly one fenced JSON code block and no
other text. Do not write prose, Markdown tables, bullet lists, block quotes, or
explanations outside the JSON code block.

Bad final responses include: Based on my investigation; Let me look up; I found;
Here is the JSON. Do not output any of these phrases in the final answer.

The first non-whitespace characters in your final response must be ```json and
the last non-whitespace characters must be ```.

The JSON object must have exactly these top-level keys:

- `anomaly_ids`
- `record_ids`
- `answer`
- `citations`

`citations` must be an array of objects. Each citation object must contain
`doc_id` and `clause_no`.

The `answer` value must be a valid JSON string. Do not put ASCII double quote
characters inside `answer`. Do not quote policy sentences verbatim inside
`answer`; paraphrase the rule instead.

If the task is a policy question, set `record_ids` to an empty array. If the
task finds no audit anomaly, set `anomaly_ids` to an empty array.

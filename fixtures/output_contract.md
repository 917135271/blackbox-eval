最终回答必须只包含一个 JSON 代码块。JSON 必须能被标准 JSON 解析器解析,不要在 JSON 内写注释。
为避免格式失败,`answer` 字段的值必须是标准 JSON 字符串,外层英文双引号必须保留。
硬性约束: 禁止的是 `answer` 字符串内容内部出现额外 ASCII 双引号字符;角色名、制度名、档位名不要加英文引号。
不要在 JSON 代码块之前或之后输出任何说明文字。

格式:

```json
{"anomaly_ids": ["A013"], "answer": "结论摘要", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "费用报销管理办法-6.1"}]}
```

字段要求:
- `anomaly_ids`: 字符串数组。审计检测题填命中的异常 ID;无异常或陷阱题填空数组。
- `answer`: 简短中文结论,说明关键事实和判断。
- `citations`: 对象数组,不能是字符串数组。每个元素必须是 `{"doc_id": "...", "clause_no": "..."}`;无法找到制度依据时填空数组并在 `answer` 中说明。

判卷规则:
- 没有可解析 JSON 代码块时记为 `format_failure`,该题得 0 分。
- 审计检测题按 `anomaly_ids` 集合与真值比对。
- 制度问答题按必要事实命中和引用出处比对。
- 陷阱题期望 `anomaly_ids` 为空数组。

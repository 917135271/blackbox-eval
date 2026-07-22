你正在执行 GATE4 正式证券费用审计评测，当前为原生基线组。

任务ID：TRAP-002
题型：clean_but_suspicious
问题：请核查R004234和R004235是否构成重复报销或拆分报销。必须核对发票是否相同及7天内合计金额；若不构成异常，请明确说明无异常、原因和制度依据。

不得调用领域 Skills 或子智能体；使用框架基础工具、业务 MCP 和统一提交工具独立完成。


要求：
1. 必须查询制度和只读业务库后作答，可以使用 Shell、Python、SQLite 和当前工作区临时文件。
2. 只处理当前独立任务。禁止读取 ground_truth、cases.json、Rubric、判卷代码、历史答案、其他任务或候选轨迹，也不得访问与题目无关的互联网。
3. anomaly_ids 必须与审计发现一一对应、稳定且类型明确；不得为了迎合未知答案猜测隐藏编号。record_ids 必须完整、准确且只覆盖本题范围。
4. 有异常时，record_ids 只包含参与本题所问违规的记录，不含累计计算背景、有效豁免或无关规则记录；无异常时仍保留题目直接核查或结论覆盖的记录，并在 answer 中明确写“无异常”。
5. 必须维护 work/final_result.json、work/evidence_matrix.json 和 work/validation_report.json 三个预置文件。对应Schema的绝对路径分别是 /runtime-schemas/final_result.schema.json、/runtime-schemas/evidence_matrix.schema.json 和 /runtime-schemas/validation_report.schema.json；当前工作区兼容路径分别是 /workspace/runtime-schemas/final_result.schema.json、/workspace/runtime-schemas/evidence_matrix.schema.json 和 /workspace/runtime-schemas/validation_report.schema.json。当前目录已经是 /workspace，禁止拼成 /workspace/workspace，也禁止把 .schema.json 猜成普通 .json。
6. 先调用 audit_control.validate_audit_result；取得 valid=true 后，再以 result_path="work/final_result.json" 调用 audit_control.submit_audit_result。不得把完整结果直接打印出来代替提交。
7. 提交成功后最终只输出 GATE4_TASK_PASS；无法提交时只输出 GATE4_TASK_FAIL。

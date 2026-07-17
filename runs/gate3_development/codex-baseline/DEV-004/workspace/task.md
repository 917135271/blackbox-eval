你正在执行 GATE3 独立开发题，当前为原生基线组，不是正式评测题。

任务ID：DEV-004
题型：single_anomaly
问题：以R900003为线索核查是否存在拆分报销，返回构成同一异常的全部记录。
领域增强路由提示：基线组不使用领域路由

不得调用领域 Skills 或子智能体；使用框架基础工具、业务 MCP 和统一提交工具独立完成。

要求：
1. 必须查询制度和只读开发业务库后作答，可以使用 Shell、Python、SQLite和临时文件。
2. 只处理当前独立工作区。禁止读取 ground_truth、正式 evals、判卷代码、历史答案、其他任务或候选轨迹。
3. anomaly_ids 是审计发现标识，使用非空且内部一致的字符串即可；开发题判定以业务结论、record_ids和制度证据为主。
4. record_ids必须遵守统一语义：有异常时只包含参与当前题目所问违规的记录，不含累计计算背景、有效豁免或无关规则记录；无异常时仍保留题目直接核查或结论覆盖的记录，并在answer中明确写“无异常”。
5. 工作区的work/final_result.json、work/evidence_matrix.json和work/validation_report.json已经按共享Schema预置字段骨架；必须先把最终答案写入final_result.json，只更新字段值和必要的evidence_rows，不得改名、删除必填字段或另建替代格式。如需核对，只读取workspace/runtime-schemas下三个明确的*.schema.json文件；不要猜测其他路径或文件名。
6. 调用audit_control.validate_audit_result时使用result_path="work/final_result.json"及两个默认报告路径；取得valid=true后，以相同result_path调用audit_control.submit_audit_result。不要把完整结果对象嵌套在工具参数中。不得用终端直接import控制代码，也不得把最终JSON打印出来代替提交。
7. 提交成功后最终只输出 GATE3_TASK_PASS；无法提交时只输出 GATE3_TASK_FAIL。

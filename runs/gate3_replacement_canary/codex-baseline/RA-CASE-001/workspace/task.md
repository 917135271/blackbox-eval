你正在执行GATE3新正式题区分度Canary，该运行只用于冻结前验证，不进入正式排名。当前为原生基线组。

任务ID：RA-CASE-001
题型：policy_data_comparison
问题：请以R000028为线索，结合现行制度和业务数据核查相关费用记录是否存在异常。请返回核查涉及的record_id集合、审计结论、关键事实和制度依据；如存在异常，再返回发现ID。

不得调用领域Skills或子智能体，使用框架基础工具、业务MCP和统一提交工具完成。

要求：
1. 必须查询制度和只读业务库后作答，可以使用Shell、Python、SQLite和当前隔离工作区文件。
2. 禁止读取 ground_truth、cases.json、Rubric、判卷代码、历史答案、其他任务或候选轨迹，也不得访问无关互联网。
3. 有异常时，record_ids只包含参与本题违规的记录；无异常时仍保留直接核查或结论覆盖的记录，并在answer中明确写“无异常”。
4. 必须维护work/final_result.json、work/evidence_matrix.json和work/validation_report.json，先取得validate_audit_result的valid=true，再以result_path="work/final_result.json"调用submit_audit_result。
5. 不得打印最终JSON代替统一提交。提交成功后只输出GATE3_CANARY_PASS；无法提交时只输出GATE3_CANARY_FAIL。

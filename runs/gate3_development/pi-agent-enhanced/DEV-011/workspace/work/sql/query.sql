-- D902部门预算执行分析SQL
-- 查询所有D902部门2025年approved报销记录，按日期排序

SELECT 
    record_id,
    employee_id,
    department_id,
    expense_date,
    amount,
    special_approval,
    status,
    reason,
    SUM(amount) OVER (ORDER BY expense_date, record_id) AS running_balance
FROM reimbursement_records
WHERE department_id = 'D902'
  AND status = 'approved'
  AND budget_year = 2025
ORDER BY expense_date, record_id;

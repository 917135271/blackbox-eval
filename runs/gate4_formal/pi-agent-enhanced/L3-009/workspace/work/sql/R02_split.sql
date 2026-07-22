-- R02: 拆分报销 - 同一员工+同一费用类型+7天窗口>=2笔, 合计>=3000
-- 先找所有expense_date间隔<=7天的记录对, 再筛选合计>=3000
SELECT DISTINCT
    a.employee_id,
    a.expense_type,
    a.record_id as record_id_a,
    a.expense_date as date_a,
    a.amount as amount_a,
    b.record_id as record_id_b,
    b.expense_date as date_b,
    b.amount as amount_b,
    CAST(julianday(b.expense_date) - julianday(a.expense_date) AS INTEGER) as day_diff,
    (a.amount + b.amount) as combined_amount
FROM expense_records a
JOIN expense_records b 
  ON a.employee_id = b.employee_id 
  AND a.expense_type = b.expense_type
  AND a.record_id < b.record_id
WHERE CAST(julianday(b.expense_date) - julianday(a.expense_date) AS INTEGER) BETWEEN 0 AND 7
  AND (a.amount + b.amount) >= 3000
ORDER BY a.employee_id, a.expense_type, a.expense_date;

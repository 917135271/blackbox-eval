-- RULE 2: 拆分报销 (Split Reimbursement)
-- Find groups: same employee_id + same expense_type + expense_date within 7 days
-- WHERE >=2 records AND SUM(amount) >= 3000 (AR-02 threshold)
-- Python window detection required for precise 7-day grouping

-- Base query: all records with employee info, sorted for window detection
SELECT er.record_id, er.employee_id, er.department_id, er.expense_type, er.expense_date,
       er.reimburse_date, er.amount, er.special_approval,
       e.employee_name, e.employee_level, d.department_name
FROM expense_records er
JOIN employees e ON er.employee_id = e.employee_id
JOIN departments d ON er.department_id = d.department_id
ORDER BY er.employee_id, er.expense_type, er.expense_date;

-- RULE 5: 超期报销 (Overdue Reimbursement)
-- Days between expense_date and reimburse_date > 60
-- Year-end rule: if expense_date in Dec 2025, allow until Jan 15 2026

-- Main query: find all records where delay > 60 days
SELECT er.record_id, er.employee_id, er.department_id, er.expense_type,
       er.expense_date, er.reimburse_date,
       CAST(julianday(er.reimburse_date) - julianday(er.expense_date) AS INTEGER) as delay_days,
       er.amount, er.special_approval,
       e.employee_name, e.employee_level, d.department_name
FROM expense_records er
JOIN employees e ON er.employee_id = e.employee_id
JOIN departments d ON er.department_id = d.department_id
WHERE CAST(julianday(er.reimburse_date) - julianday(er.expense_date) AS INTEGER) > 60
ORDER BY delay_days DESC;

-- Alternative: with year-end exception for Dec 2025 expenses
-- Dec expenses allowed until Jan 15 2026 (effective deadline = Jan 15, 2026)
-- But since all reimburse_dates are <= 2026-01-15, only check non-Dec records for the >60 rule
-- AND Dec records where reimburse_date > 2026-01-15

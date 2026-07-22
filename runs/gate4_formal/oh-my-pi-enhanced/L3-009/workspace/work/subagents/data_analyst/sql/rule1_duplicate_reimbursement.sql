-- RULE 1: 重复报销 (Duplicate Reimbursement)
-- Find all invoice_ids used more than once with full record details

-- Step 1: Find duplicate invoice_ids
SELECT invoice_id, COUNT(*) as cnt, GROUP_CONCAT(record_id) as record_ids
FROM expense_records
GROUP BY invoice_id
HAVING cnt > 1
ORDER BY cnt DESC;

-- Step 2: Get full details on duplicate records
SELECT er.record_id, er.employee_id, er.department_id, er.expense_type, er.expense_date,
       er.reimburse_date, er.amount, er.city_tier, er.nights, er.days, er.participants,
       er.special_approval, i.invoice_no, i.vendor_name, i.invoice_date, i.amount as invoice_amount,
       e.employee_name, e.employee_level, d.department_name
FROM expense_records er
JOIN invoices i ON er.invoice_id = i.invoice_id
JOIN employees e ON er.employee_id = e.employee_id
JOIN departments d ON er.department_id = d.department_id
WHERE er.invoice_id IN (
    SELECT invoice_id FROM expense_records GROUP BY invoice_id HAVING COUNT(*) > 1
)
ORDER BY er.invoice_id, er.record_id;

-- TRAP-005: Full coverage queries for R004239 and R004240 duplicate/split/excessive check

-- Query 1: Full detail of target records
SELECT er.record_id, er.record_no, er.employee_id, emp.employee_name, emp.employee_level,
       er.department_id, dep.department_name, er.expense_date, er.reimburse_date,
       er.expense_type, er.amount, er.participants, er.reason, er.status,
       er.special_approval, inv.invoice_no, inv.vendor_name, inv.invoice_date AS invoice_date,
       inv.amount AS invoice_amount
FROM expense_records er
JOIN employees emp ON er.employee_id = emp.employee_id
JOIN departments dep ON er.department_id = dep.department_id
JOIN invoices inv ON er.invoice_id = inv.invoice_id
WHERE er.record_id IN ('R004239', 'R004240');

-- Query 2: All business_entertainment for E0008 within 7-day windows around target dates (Oct 18 - Nov 2)
SELECT er.record_id, er.record_no, er.employee_id, er.expense_date, er.reimburse_date,
       er.expense_type, er.amount, er.participants, er.reason, er.status,
       inv.invoice_no, inv.vendor_name
FROM expense_records er
JOIN invoices inv ON er.invoice_id = inv.invoice_id
WHERE er.employee_id = 'E0008'
  AND er.expense_type = 'business_entertainment'
  AND er.expense_date BETWEEN '2025-10-18' AND '2025-11-02'
ORDER BY er.expense_date;

-- Query 3: Verify invoice usage for both invoice numbers (any record reusing them)
SELECT inv.invoice_no, inv.vendor_name, COUNT(er.record_id) AS usage_count,
       GROUP_CONCAT(er.record_id) AS record_ids
FROM invoices inv
LEFT JOIN expense_records er ON inv.invoice_id = er.invoice_id
WHERE inv.invoice_no IN ('FP2025X0004233', 'FP2025X0004234')
GROUP BY inv.invoice_no;

-- Query 4: Total population count for context
SELECT COUNT(*) AS total_records FROM expense_records;
SELECT COUNT(*) AS business_entertainment_total FROM expense_records WHERE expense_type = 'business_entertainment';

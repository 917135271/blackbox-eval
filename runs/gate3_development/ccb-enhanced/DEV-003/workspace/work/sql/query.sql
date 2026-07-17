-- Query 1: Find records sharing the same invoice as R900001
SELECT er.record_id, er.record_no, er.employee_id, emp.employee_name, 
       er.department_id, dept.department_name,
       er.expense_date, er.reimburse_date, er.expense_type, er.amount, 
       er.reason, er.invoice_id, inv.invoice_no, inv.vendor_name, 
       inv.invoice_date AS invoice_date, inv.amount AS invoice_amount,
       er.status, er.special_approval
FROM expense_records er
JOIN invoices inv ON er.invoice_id = inv.invoice_id
JOIN employees emp ON er.employee_id = emp.employee_id
JOIN departments dept ON er.department_id = dept.department_id
WHERE er.invoice_id = (SELECT invoice_id FROM expense_records WHERE record_id = 'R900001')
ORDER BY er.expense_date;

-- Query 2: Count total population
SELECT COUNT(*) AS total_records FROM expense_records;

-- Query 3: Count records using invoice FPDEV900001
SELECT COUNT(*) AS same_invoice_count 
FROM expense_records 
WHERE invoice_id = (SELECT invoice_id FROM expense_records WHERE record_id = 'R900001');

-- Query 4: Invoice usage count summary
SELECT inv.invoice_id, inv.invoice_no, inv.amount, COUNT(er.record_id) AS usage_count,
       GROUP_CONCAT(er.record_id) AS record_ids
FROM invoices inv
LEFT JOIN expense_records er ON inv.invoice_id = er.invoice_id
WHERE inv.invoice_no = 'FPDEV900001'
GROUP BY inv.invoice_id;

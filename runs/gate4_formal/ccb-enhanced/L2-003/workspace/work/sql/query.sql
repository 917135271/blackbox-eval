-- L2-003: Verify invoice FP202500000020 usage across all expense records
-- Checks Article 10 duplicate reimbursement rule

-- Q1: Count of records using invoice FP202500000020
SELECT er.record_id, er.record_no, er.employee_id, emp.employee_name,
       er.expense_date, er.reimburse_date, er.expense_type, er.amount,
       inv.invoice_no, inv.invoice_id, er.status, er.reason
FROM expense_records er
JOIN invoices inv ON er.invoice_id = inv.invoice_id
JOIN employees emp ON er.employee_id = emp.employee_id
WHERE inv.invoice_no = 'FP202500000020'
ORDER BY er.expense_date;

-- Q2: All travel_lodging records for E0028 (context for Article 11 check)
SELECT er.record_id, er.record_no, er.expense_date, er.reimburse_date,
       er.expense_type, er.amount, inv.invoice_no
FROM expense_records er
JOIN invoices inv ON er.invoice_id = inv.invoice_id
WHERE er.employee_id = 'E0028' AND er.expense_type = 'travel_lodging'
ORDER BY er.expense_date;

-- Q3: Total population count
SELECT COUNT(*) as total_records FROM expense_records;

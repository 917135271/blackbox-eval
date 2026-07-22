-- Rule 1: 重复报销 (Duplicate Reimbursement)
-- Find invoices used in multiple reimbursement records

-- Step 1: Count duplicate invoice groups
SELECT COUNT(*) as duplicate_groups 
FROM (
    SELECT i.invoice_no 
    FROM expense_records e 
    JOIN invoices i ON e.invoice_id = i.invoice_id 
    GROUP BY i.invoice_no 
    HAVING COUNT(DISTINCT e.record_id) >= 2
);

-- Result: 6

-- Step 2: List all duplicate invoice details
SELECT i.invoice_no, COUNT(DISTINCT e.record_id) as usage_count, GROUP_CONCAT(e.record_id, ',') as record_ids
FROM expense_records e
JOIN invoices i ON e.invoice_id = i.invoice_id
GROUP BY i.invoice_no
HAVING COUNT(DISTINCT e.record_id) >= 2
ORDER BY i.invoice_no;

-- Step 3: Get all records involved in duplicates
SELECT e.record_id, e.record_no, i.invoice_no, i.vendor_name, e.amount, e.employee_id, e.expense_type, e.expense_date, e.reimburse_date
FROM expense_records e
JOIN invoices i ON e.invoice_id = i.invoice_id
WHERE i.invoice_no IN (
    SELECT i2.invoice_no
    FROM expense_records e2
    JOIN invoices i2 ON e2.invoice_id = i2.invoice_id
    GROUP BY i2.invoice_no
    HAVING COUNT(DISTINCT e2.record_id) >= 2
)
ORDER BY i.invoice_no, e.record_id;

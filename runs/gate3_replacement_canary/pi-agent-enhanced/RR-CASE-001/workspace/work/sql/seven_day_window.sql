-- 7-day sliding window analysis for E0041 training_fee records
-- Task: RR-CASE-001, Clue: R000465

-- Step 1: All E0041 training_fee records
SELECT record_id, expense_date, amount, reason, invoice_id, status, special_approval
FROM expense_records
WHERE employee_id = 'E0041' AND expense_type = 'training_fee'
ORDER BY expense_date;

-- Step 2: 7-day sliding window aggregation
WITH records AS (
    SELECT record_id, expense_date, amount
    FROM expense_records
    WHERE employee_id = 'E0041' AND expense_type = 'training_fee'
)
SELECT r1.record_id, r1.expense_date as window_start,
       COUNT(*) as record_count,
       SUM(r2.amount) as total_amount,
       GROUP_CONCAT(r2.record_id, ', ') as records_in_window
FROM records r1
JOIN records r2 ON julianday(r2.expense_date) >= julianday(r1.expense_date)
                AND julianday(r2.expense_date) <= julianday(r1.expense_date) + 7
WHERE r1.record_id IN ('R000465', 'R000561', 'R000888', 'R001354', 'R001894')
GROUP BY r1.record_id
ORDER BY r1.expense_date;

-- Step 3: Invoice reuse check
SELECT invoice_no, COUNT(*) as usage_count
FROM expense_records
WHERE invoice_no IN (
    SELECT DISTINCT i.invoice_no
    FROM expense_records e
    JOIN invoices i ON e.invoice_id = i.invoice_id
    WHERE e.record_id IN ('R000465', 'R000561', 'R000888', 'R001354')
)
GROUP BY invoice_no;

-- Step 4: Approval tier verification
SELECT a.record_id, a.tier_id, a.approver_role, a.approval_status,
       e.amount, e.expense_date
FROM approvals a
JOIN expense_records e ON a.record_id = e.record_id
WHERE a.record_id IN ('R000465', 'R000561', 'R000888', 'R001354')
ORDER BY e.expense_date;

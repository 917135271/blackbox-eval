-- RR-CASE-001: E0041 training_fee records December 2025 cluster analysis
-- 7-day split avoidance check per 2025制度 Article 11

-- Step 1: Retrieve all training_fee records for E0041 in Dec 2025
SELECT record_id, expense_date, amount, reason, special_approval
FROM expense_records
WHERE employee_id = 'E0041'
  AND expense_type = 'training_fee'
  AND expense_date >= '2025-12-01'
  AND expense_date <= '2025-12-31'
ORDER BY expense_date;

-- Step 2: Retrieve full details with approval tiers and invoices
SELECT r.record_id, r.expense_date, r.amount, r.reason,
       a.tier_id, a.approver_role, a.approved_at,
       i.invoice_no, i.invoice_id, i.vendor_name
FROM expense_records r
JOIN approvals a ON r.record_id = a.record_id
JOIN invoices i ON r.invoice_id = i.invoice_id
WHERE r.employee_id = 'E0041'
  AND r.expense_type = 'training_fee'
  AND r.expense_date BETWEEN '2025-12-08' AND '2025-12-25'
ORDER BY r.expense_date;

-- Step 3: 7-day window aggregation check
-- Window 1: 2025-12-18 to 2025-12-24 (centered on clue R000465)
SELECT COUNT(*) as record_count, SUM(amount) as total_amount
FROM expense_records
WHERE employee_id = 'E0041'
  AND expense_type = 'training_fee'
  AND expense_date BETWEEN '2025-12-18' AND '2025-12-24';

-- Window 2: 2025-12-20 to 2025-12-26
SELECT COUNT(*) as record_count, SUM(amount) as total_amount
FROM expense_records
WHERE employee_id = 'E0041'
  AND expense_type = 'training_fee'
  AND expense_date BETWEEN '2025-12-20' AND '2025-12-26';

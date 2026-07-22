-- Batch analysis for RA-CASE-002: E0008 travel_lodging 7-day split checks
-- Database: /benchmark/data/expense.db

-- Query 1: All E0008 travel_lodging records with approval details
SELECT r.record_id, r.expense_date, r.expense_type, r.amount, r.nights, r.city_tier, r.reason,
       r.invoice_id, r.special_approval,
       a.approver_role, a.approver_employee_id, a.tier_id
FROM expense_records r
LEFT JOIN approvals a ON r.record_id = a.record_id
WHERE r.employee_id = 'E0008' AND r.expense_type = 'travel_lodging'
ORDER BY r.expense_date;

-- Query 2: 7-day window verification
-- Group 1: R004209(2025-02-26), R004210(2025-02-28), R004211(2025-03-02)
-- Group 2: R004219(2025-11-27), R004220(2025-12-01)
SELECT
  CASE
    WHEN r1.record_id < r2.record_id THEN r1.record_id || ' + ' || r2.record_id
    ELSE r2.record_id || ' + ' || r1.record_id
  END AS pair,
  ABS(julianday(r1.expense_date) - julianday(r2.expense_date)) AS days_diff,
  r1.amount + r2.amount AS combined_amount
FROM expense_records r1
JOIN expense_records r2 ON r1.employee_id = r2.employee_id
WHERE r1.employee_id = 'E0008'
  AND r1.expense_type = 'travel_lodging'
  AND r2.expense_type = 'travel_lodging'
  AND r1.record_id < r2.record_id
  AND ABS(julianday(r1.expense_date) - julianday(r2.expense_date)) <= 7
ORDER BY r1.expense_date;

-- Query 3: Approval gap analysis for E0008 travel_lodging records
SELECT r.record_id, r.amount, r.tier_id,
  COUNT(a.approval_id) as total_approvals,
  SUM(CASE WHEN a.approver_role = '部门经理' THEN 1 ELSE 0 END) as dept_mgr_count,
  SUM(CASE WHEN a.approver_role = '财务复核' THEN 1 ELSE 0 END) as finance_review_count
FROM expense_records r
LEFT JOIN approvals a ON r.record_id = a.record_id
WHERE r.employee_id = 'E0008' AND r.expense_type = 'travel_lodging'
GROUP BY r.record_id;

-- Version Trap Analysis Queries for L3-010
-- Database: /benchmark/data/expense.db

-- Query 1: Population count for 2025 records
SELECT COUNT(*) as total_2025_records
FROM expense_records
WHERE expense_date >= '2025-01-01';
-- Result: 4240

-- Query 2: Records in AR-02 zone (3000-10000) - where version trap applies
SELECT e.record_id, e.record_no, e.amount, e.expense_type,
       emp.employee_name, d.department_name, e.reimburse_date, e.reason
FROM expense_records e
JOIN employees emp ON e.employee_id = emp.employee_id
JOIN departments d ON e.department_id = d.department_id
WHERE e.expense_date >= '2025-01-01'
  AND e.amount >= 3000 AND e.amount < 10000
ORDER BY e.amount DESC;
-- Result: 95 records

-- Query 3: Key version trap record - 8000-10000 false positive zone
SELECT e.record_id, e.record_no, e.amount, e.expense_type,
       emp.employee_name, d.department_name, e.reimburse_date, e.reason
FROM expense_records e
JOIN employees emp ON e.employee_id = emp.employee_id
JOIN departments d ON e.department_id = d.department_id
WHERE e.expense_date >= '2025-01-01'
  AND e.amount >= 8000 AND e.amount < 10000
ORDER BY e.amount DESC;
-- Result: 1 record (R004233, 9990.00)

-- Query 4: Records in 3000-8000 range - false negative zone
SELECT e.record_id, e.record_no, e.amount, e.expense_type,
       emp.employee_name, d.department_name, e.reimburse_date, e.reason
FROM expense_records e
JOIN employees emp ON e.employee_id = emp.employee_id
JOIN departments d ON e.department_id = d.department_id
WHERE e.expense_date >= '2025-01-01'
  AND e.amount >= 3000 AND e.amount < 8000
ORDER BY e.amount DESC;
-- Result: 94 records

-- Query 5: Approval for the key trap record R004233
SELECT a.approval_id, a.record_id, a.tier_id, a.approver_role,
       a.approved_at, a.approval_status, emp.employee_name as approver_name
FROM approvals a
JOIN employees emp ON a.approver_employee_id = emp.employee_id
WHERE a.record_id = 'R004233';
-- Result: AR-02, 部门经理, approved by 杨丹

-- Query 6: Approval tier distribution
SELECT DISTINCT tier_id, COUNT(*) as cnt
FROM approvals
GROUP BY tier_id
ORDER BY tier_id;
-- Result: AR-01: 4145, AR-02: 95

-- Query 7: Check if any records in 10000-50000 or 30000-50000 exist
SELECT COUNT(*) as ar03_count
FROM expense_records
WHERE expense_date >= '2025-01-01'
  AND amount >= 10000 AND amount < 50000;
-- Result: 0

SELECT COUNT(*) as old_30k_zone_count
FROM expense_records
WHERE expense_date >= '2025-01-01'
  AND amount >= 30000 AND amount < 50000;
-- Result: 0

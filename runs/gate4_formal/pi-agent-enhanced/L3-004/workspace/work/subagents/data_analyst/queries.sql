-- Audit: L3-004 全年超预算专项扫描
-- Database: /benchmark/data/expense.db

-- Step 1: Confirm over-budget departments
SELECT d.department_id, d.department_name, d.annual_budget,
       SUM(er.amount) as total_approved,
       COUNT(*) as record_count,
       SUM(er.amount) - d.annual_budget as over_budget_amount,
       ROUND(SUM(er.amount) / d.annual_budget, 4) as usage_rate
FROM departments d
JOIN expense_records er ON d.department_id = er.department_id
WHERE er.status = 'approved'
GROUP BY d.department_id
HAVING SUM(er.amount) > d.annual_budget
ORDER BY usage_rate DESC;

-- Step 2: For each over-budget dept, get ordered approved records for cumulative scan
-- D001
SELECT record_id, amount, reimburse_date, special_approval
FROM expense_records
WHERE status = 'approved' AND department_id = 'D001'
ORDER BY reimburse_date ASC, record_id ASC;

-- D002
SELECT record_id, amount, reimburse_date, special_approval
FROM expense_records
WHERE status = 'approved' AND department_id = 'D002'
ORDER BY reimburse_date ASC, record_id ASC;

-- D003
SELECT record_id, amount, reimburse_date, special_approval
FROM expense_records
WHERE status = 'approved' AND department_id = 'D003'
ORDER BY reimburse_date ASC, record_id ASC;

-- D004
SELECT record_id, amount, reimburse_date, special_approval
FROM expense_records
WHERE status = 'approved' AND department_id = 'D004'
ORDER BY reimburse_date ASC, record_id ASC;

-- D005
SELECT record_id, amount, reimburse_date, special_approval
FROM expense_records
WHERE status = 'approved' AND department_id = 'D005'
ORDER BY reimburse_date ASC, record_id ASC;

-- D006
SELECT record_id, amount, reimburse_date, special_approval
FROM expense_records
WHERE status = 'approved' AND department_id = 'D006'
ORDER BY reimburse_date ASC, record_id ASC;

-- Step 3: Verify key records' special_approval status
SELECT record_id, department_id, amount, reimburse_date, special_approval, status
FROM expense_records
WHERE record_id IN ('R000079','R002009','R003968','R000894','R003479','R000312');

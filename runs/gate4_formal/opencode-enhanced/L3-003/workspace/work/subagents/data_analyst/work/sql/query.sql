-- Audit SQL Queries for 2025 Expense Analysis
-- Database: /benchmark/data/expense.db (read-only)

-- 1. Count complete in-scope population
SELECT COUNT(*) as total_records FROM expense_records WHERE budget_year = 2025;
-- Result: 4240

-- 2. Load all records with joins (used by all rules)
SELECT 
    r.record_id, r.record_no, r.employee_id, r.department_id,
    r.expense_date, r.reimburse_date, r.expense_type, r.amount,
    r.reason, r.invoice_id, r.status, r.city_tier, r.nights, r.days,
    r.participants, r.budget_year, r.special_approval,
    e.employee_name, e.employee_level, e.position_role, e.hire_date,
    i.invoice_no, i.vendor_name, i.invoice_date AS inv_invoice_date
FROM expense_records r
JOIN employees e ON r.employee_id = e.employee_id
JOIN invoices i ON r.invoice_id = i.invoice_id
WHERE r.budget_year = 2025
ORDER BY r.record_id;

-- 3. R09: Duplicate invoice check
SELECT i.invoice_no, COUNT(*) as usage_count, GROUP_CONCAT(r.record_id) as record_ids
FROM expense_records r
JOIN invoices i ON r.invoice_id = i.invoice_id
WHERE r.budget_year = 2025
GROUP BY i.invoice_no
HAVING COUNT(*) >= 2;

-- 4. R12: Department budget crossing
-- Per department, cumulative sum ordered by expense_date
-- First record where cumulative > budget and all subsequent are flagged

-- 5. R07/R08: Monthly per-employee aggregation
-- GROUP BY employee_id, substr(expense_date,1,7)
-- HAVING SUM(amount) > threshold

-- 6. R10: Split claims - connected components within 7-day chains
-- Implemented in Python using BFS on adjacency graph

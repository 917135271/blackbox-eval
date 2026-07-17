-- ============================================================
-- Overdue Expense Audit: Article 7 (60-day rule) & Article 9 (year-end)
-- Policy: 01_expense_reimbursement_2025.md
-- Database: /benchmark/data/expense.db (read-only)
-- Date: 2026-07-16
-- ============================================================

-- -------------------------------------------------------
-- Query 1: Full population scan with date gap computation
-- -------------------------------------------------------
SELECT 
    record_id,
    employee_id,
    department_id,
    expense_date,
    reimburse_date,
    expense_type,
    amount,
    status,
    city_tier,
    nights,
    days,
    participants,
    budget_year,
    special_approval,
    invoice_id,
    CAST(julianday(reimburse_date) - julianday(expense_date) AS INTEGER) AS gap_days,
    CASE WHEN strftime('%m', expense_date) = '12' THEN 1 ELSE 0 END AS is_december
FROM expense_records
ORDER BY record_id;

-- -------------------------------------------------------
-- Query 2: Article 7 overdue candidates (gap > 60 days, non-December only)
-- December records use Article 9 year-end rule instead
-- -------------------------------------------------------
SELECT 
    record_id,
    employee_id,
    department_id,
    expense_date,
    reimburse_date,
    expense_type,
    amount,
    status,
    special_approval,
    CAST(julianday(reimburse_date) - julianday(expense_date) AS INTEGER) AS gap_days
FROM expense_records
WHERE CAST(julianday(reimburse_date) - julianday(expense_date) AS INTEGER) > 60
  AND strftime('%m', expense_date) != '12'
ORDER BY gap_days DESC;

-- -------------------------------------------------------
-- Query 3: December records with Article 9 year-end deadline
-- For December expenses, the deadline is January 15 of the NEXT year
-- (NOT the same year's January 15)
-- -------------------------------------------------------
SELECT 
    record_id,
    employee_id,
    department_id,
    expense_date,
    reimburse_date,
    printf('%d-01-15', CAST(substr(expense_date, 1, 4) AS INTEGER) + 1) AS year_end_deadline,
    expense_type,
    amount,
    status,
    special_approval,
    CAST(julianday(reimburse_date) - julianday(expense_date) AS INTEGER) AS gap_days,
    CASE 
        WHEN reimburse_date <= printf('%d-01-15', CAST(substr(expense_date, 1, 4) AS INTEGER) + 1)
        THEN 'valid'
        ELSE 'overdue_article9'
    END AS article9_status
FROM expense_records
WHERE strftime('%m', expense_date) = '12'
ORDER BY expense_date;

-- -------------------------------------------------------
-- Query 4: All confirmed overdue records (combined Articles 7 + 9)
-- Article 7: non-December records with gap > 60 days
-- Article 9: December records reimbursed after next-year Jan 15
-- -------------------------------------------------------
WITH computed AS (
    SELECT 
        record_id,
        employee_id,
        department_id,
        expense_date,
        reimburse_date,
        expense_type,
        amount,
        status,
        special_approval,
        CAST(julianday(reimburse_date) - julianday(expense_date) AS INTEGER) AS gap_days,
        CASE WHEN strftime('%m', expense_date) = '12' THEN 1 ELSE 0 END AS is_december,
        printf('%d-01-15', CAST(substr(expense_date, 1, 4) AS INTEGER) + 1) AS year_end_deadline
    FROM expense_records
)
SELECT * FROM computed
WHERE 
    (is_december = 0 AND gap_days > 60)
    OR
    (is_december = 1 AND reimburse_date > year_end_deadline)
ORDER BY record_id;

-- -------------------------------------------------------
-- Query 5: Special approval records (context, not anomaly)
-- -------------------------------------------------------
SELECT 
    record_id,
    employee_id,
    expense_date,
    reimburse_date,
    expense_type,
    amount,
    special_approval,
    CAST(julianday(reimburse_date) - julianday(expense_date) AS INTEGER) AS gap_days
FROM expense_records
WHERE special_approval = 1
ORDER BY record_id;

-- -------------------------------------------------------
-- Query 6: Invoice reuse check
-- -------------------------------------------------------
SELECT 
    invoice_id,
    COUNT(*) AS usage_count,
    GROUP_CONCAT(record_id, ', ') AS record_ids,
    GROUP_CONCAT(DISTINCT employee_id) AS employees
FROM expense_records
GROUP BY invoice_id
HAVING COUNT(*) > 1;

-- -------------------------------------------------------
-- Query 7: Corrected population statistics
-- -------------------------------------------------------
SELECT 
    COUNT(*) AS total_population,
    SUM(CASE WHEN CAST(julianday(reimburse_date) - julianday(expense_date) AS INTEGER) > 60 
              AND strftime('%m', expense_date) != '12' THEN 1 ELSE 0 END) AS article7_overdue,
    SUM(CASE WHEN strftime('%m', expense_date) = '12' THEN 1 ELSE 0 END) AS december_total,
    SUM(CASE WHEN strftime('%m', expense_date) = '12' 
              AND reimburse_date > printf('%d-01-15', CAST(substr(expense_date, 1, 4) AS INTEGER) + 1) 
              THEN 1 ELSE 0 END) AS article9_overdue,
    SUM(CASE WHEN special_approval = 1 THEN 1 ELSE 0 END) AS special_approval_count
FROM expense_records;

-- Budget Overrun Analysis: Full-Year 2025 Approved Expenses
-- Target: Departments D001-D006 (over-budget)
-- Policy: Cumulative department spending must not exceed 1.0x annual budget.
-- Special approval exempts records from anomaly classification.

-- Step 1: Order approved 2025 records by expense_date, record_id per department
-- Step 2: Compute running (cumulative) balance per department
-- Step 3: Mark records where running_balance exceeds the department's annual_budget
-- Step 4: Filter to anomalous: over budget AND special_approval = 0

WITH ordered AS (
    SELECT
        e.record_id,
        e.department_id,
        e.expense_date,
        e.amount,
        e.special_approval,
        d.annual_budget,
        ROW_NUMBER() OVER (
            PARTITION BY e.department_id
            ORDER BY e.expense_date, e.record_id
        ) AS rn
    FROM expense_records e
    JOIN departments d ON e.department_id = d.department_id
    WHERE e.status = 'approved'
      AND e.budget_year = 2025
      AND e.department_id IN ('D001', 'D002', 'D003', 'D004', 'D005', 'D006')
),
running AS (
    SELECT
        *,
        SUM(amount) OVER (
            PARTITION BY department_id
            ORDER BY rn
            ROWS UNBOUNDED PRECEDING
        ) AS running_balance
    FROM ordered
),
crossing_point AS (
    SELECT
        department_id,
        MIN(rn) AS first_crossing_rn
    FROM running
    WHERE running_balance > annual_budget
    GROUP BY department_id
)
SELECT
    r.department_id,
    r.rn,
    r.record_id,
    r.expense_date,
    r.amount,
    ROUND(r.running_balance, 2) AS running_balance,
    ROUND(r.annual_budget, 2) AS budget,
    r.special_approval,
    CASE WHEN r.rn = cp.first_crossing_rn THEN 1 ELSE 0 END AS is_first_crossing,
    CASE WHEN r.running_balance > r.annual_budget AND r.special_approval = 0 THEN 1 ELSE 0 END AS is_anomalous
FROM running r
JOIN crossing_point cp ON r.department_id = cp.department_id
WHERE r.running_balance > r.annual_budget
  AND r.special_approval = 0
ORDER BY r.department_id, r.rn;

-- Summary statistics:
-- D001: 525 total, 193 anomalous (first crossing at record #333)
-- D002: 254 total, 99 anomalous (first crossing at record #156)
-- D003: 249 total, 103 anomalous (first crossing at record #147)
-- D004: 611 total, 236 anomalous (first crossing at record #376)
-- D005: 616 total, 250 anomalous (first crossing at record #367)
-- D006: 833 total, 315 anomalous (first crossing at record #519)
-- Total anomalous: 1196 records across 6 departments
-- Total in-scope population: 3088 approved 2025 records
-- Exempt (special_approval=1): 0 records

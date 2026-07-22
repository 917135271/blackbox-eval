-- Budget overrun cumulative scan
-- For each department, cumulatively sum approved expenses ordered by reimburse_date ASC, record_id ASC
-- Find the first record where cumulative_amount exceeds annual_budget

WITH ranked AS (
  SELECT
    e.record_id,
    e.department_id,
    d.department_name,
    d.annual_budget,
    e.reimburse_date,
    e.amount,
    e.special_approval,
    SUM(e.amount) OVER (
      PARTITION BY e.department_id
      ORDER BY e.reimburse_date ASC, e.record_id ASC
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_amount
  FROM expense_records e
  JOIN departments d ON e.department_id = d.department_id
  WHERE e.status = 'approved'
    AND e.budget_year = 2025
  ORDER BY e.department_id, e.reimburse_date ASC, e.record_id ASC
),
first_over AS (
  SELECT
    department_id,
    department_name,
    annual_budget,
    record_id,
    reimburse_date,
    amount,
    cumulative_amount,
    special_approval,
    ROW_NUMBER() OVER (
      PARTITION BY department_id
      ORDER BY cumulative_amount > annual_budget DESC, reimburse_date ASC, record_id ASC
    ) AS rn
  FROM ranked
  WHERE cumulative_amount > annual_budget
)
SELECT
  department_id,
  department_name,
  annual_budget,
  record_id,
  reimburse_date,
  amount,
  ROUND(cumulative_amount, 2) AS cumulative_amount,
  special_approval
FROM first_over
WHERE rn = 1
ORDER BY department_id;

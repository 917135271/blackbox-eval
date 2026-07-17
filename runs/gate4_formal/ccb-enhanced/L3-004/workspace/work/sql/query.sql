-- 超预算专项扫描：按部门累计计算
-- 规则：部门累计费用 > 年度预算后，未经专项审批的记录构成违规
-- 2025年全部记录，无专项审批豁免

-- Step 1: 获取每个部门的记录按日期排序，计算累计金额
WITH ordered AS (
  SELECT
    e.record_id,
    e.department_id,
    d.department_name,
    d.annual_budget,
    e.expense_date,
    e.amount,
    e.special_approval,
    ROW_NUMBER() OVER (
      PARTITION BY e.department_id
      ORDER BY e.expense_date ASC, e.record_id ASC
    ) AS rn
  FROM expense_records e
  JOIN departments d ON e.department_id = d.department_id
  WHERE e.budget_year = 2025
),
cumulative AS (
  SELECT
    *,
    SUM(amount) OVER (
      PARTITION BY department_id
      ORDER BY rn
      ROWS UNBOUNDED PRECEDING
    ) AS cumulative_amount
  FROM ordered
)
SELECT
  record_id,
  department_id,
  department_name,
  annual_budget,
  expense_date,
  amount,
  cumulative_amount,
  special_approval,
  rn,
  CASE
    WHEN (cumulative_amount - amount) >= annual_budget THEN 'post_budget'
    WHEN cumulative_amount > annual_budget THEN 'crossing'
    ELSE 'pre_budget'
  END AS budget_status
FROM cumulative
ORDER BY department_id, rn;

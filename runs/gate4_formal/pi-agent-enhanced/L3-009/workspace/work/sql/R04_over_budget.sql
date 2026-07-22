-- R04: 超预算 - 按部门按reimburse_date+record_id累计,首次超过年度预算且无special_approval
-- 先计算累计支出,再结合部门年度预算
WITH cum AS (
    SELECT 
        er.record_id,
        er.department_id,
        er.reimburse_date,
        er.amount,
        er.special_approval,
        SUM(er.amount) OVER (PARTITION BY er.department_id ORDER BY er.reimburse_date ASC, er.record_id ASC) as cumulative
    FROM expense_records er
)
SELECT 
    c.record_id,
    c.department_id,
    d.department_name,
    d.annual_budget,
    c.reimburse_date,
    c.amount,
    c.cumulative,
    c.special_approval,
    ROUND(c.cumulative / d.annual_budget, 4) as budget_ratio
FROM cum c
JOIN departments d ON c.department_id = d.department_id
WHERE c.cumulative > d.annual_budget
  AND c.special_approval = 0
ORDER BY c.department_id, c.reimburse_date, c.record_id;

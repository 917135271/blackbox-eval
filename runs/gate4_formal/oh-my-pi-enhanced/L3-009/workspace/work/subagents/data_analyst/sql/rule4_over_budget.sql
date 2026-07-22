-- RULE 4: 超预算 (Over-Budget)
-- For each department, cumulative sum ordered by reimburse_date ASC, record_id ASC
-- Find first record where cumulative > annual_budget AND special_approval=0

-- Step 1: All approved records with department budget, ordered for cumulative calculation
SELECT er.record_id, er.department_id, er.reimburse_date, er.amount, er.special_approval,
       d.annual_budget, d.department_name,
       SUM(er.amount) OVER (
           PARTITION BY er.department_id 
           ORDER BY er.reimburse_date ASC, er.record_id ASC
           ROWS UNBOUNDED PRECEDING
       ) as cumulative_amount
FROM expense_records er
JOIN departments d ON er.department_id = d.department_id
ORDER BY er.department_id, er.reimburse_date, er.record_id;

-- Step 2: Find crossing records
WITH cum AS (
    SELECT er.record_id, er.department_id, er.reimburse_date, er.amount, er.special_approval,
           d.annual_budget, d.department_name,
           SUM(er.amount) OVER (
               PARTITION BY er.department_id 
               ORDER BY er.reimburse_date ASC, er.record_id ASC
               ROWS UNBOUNDED PRECEDING
           ) as cumulative_amount
    FROM expense_records er
    JOIN departments d ON er.department_id = d.department_id
)
SELECT DISTINCT department_id, department_name, annual_budget,
       FIRST_VALUE(record_id) OVER (
           PARTITION BY department_id 
           ORDER BY reimburse_date ASC, record_id ASC
       ) as first_crossing_record_id,
       FIRST_VALUE(cumulative_amount) OVER (
           PARTITION BY department_id 
           ORDER BY reimburse_date ASC, record_id ASC
       ) as cumulative_at_crossing
FROM cum
WHERE cumulative_amount > annual_budget AND special_approval = 0
ORDER BY department_id;

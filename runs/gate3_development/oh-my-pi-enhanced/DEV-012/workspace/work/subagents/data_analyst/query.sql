-- Rule 1: 重复报销
SELECT invoice_id, COUNT(*) cnt, GROUP_CONCAT(record_id) AS record_ids
FROM expense_records
GROUP BY invoice_id
HAVING cnt > 1;

-- Rule 2: 拆分报销 (Python pairwise, see data_findings.json)
-- Group: employee_id + expense_type, window: ABS(expense_date diff) <= 7 days
-- AR tiers: <3000=AR-01, 3000-9999=AR-02, >=10000=AR-03
-- Flag: combined_tier > max(tier_a, tier_b)

-- Rule 3a: travel_lodging
SELECT record_id, employee_id, amount, nights, amount/nights AS per_night
FROM expense_records
WHERE expense_type = 'travel_lodging' AND nights > 0 AND special_approval = 0
  AND (
    (employee_id = 'E9001' AND amount/nights > 450)
    OR (employee_id = 'E9002' AND amount/nights > 650)
  );

-- Rule 3b: business_entertainment
SELECT record_id, employee_id, amount, participants, amount/participants AS per_person
FROM expense_records
WHERE expense_type = 'business_entertainment' AND special_approval = 0
  AND (amount > 5000 OR (participants > 0 AND amount/participants > 300));

-- Rule 3c: office_supplies monthly per employee
SELECT employee_id, substr(expense_date,1,7) AS month, SUM(amount) AS total, GROUP_CONCAT(record_id) AS record_ids
FROM expense_records
WHERE expense_type = 'office_supplies' AND special_approval = 0
GROUP BY employee_id, substr(expense_date,1,7)
HAVING SUM(amount) > 600;

-- Rule 3d: communication monthly per employee
SELECT employee_id, substr(expense_date,1,7) AS month, SUM(amount) AS total, GROUP_CONCAT(record_id) AS record_ids
FROM expense_records
WHERE expense_type = 'communication' AND special_approval = 0
GROUP BY employee_id, substr(expense_date,1,7)
HAVING SUM(amount) > 300;

-- Rule 3e: training_fee
SELECT record_id, employee_id, amount, days, amount/days AS per_day
FROM expense_records
WHERE expense_type = 'training_fee' AND days > 0 AND special_approval = 0
  AND amount/days > 800;

-- Rule 3f: training_lodging
SELECT record_id, employee_id, amount, nights, amount/nights AS per_night, city_tier
FROM expense_records
WHERE expense_type = 'training_lodging' AND nights > 0 AND city_tier = 'A' AND special_approval = 0
  AND amount/nights > 500;

-- Rule 4: 超期
SELECT record_id, employee_id, expense_date, reimburse_date,
       CAST(julianday(reimburse_date) - julianday(expense_date) AS INTEGER) AS delay_days
FROM expense_records
WHERE CAST(julianday(reimburse_date) - julianday(expense_date) AS INTEGER) > 60
  AND NOT (CAST(substr(expense_date,6,2) AS INTEGER) = 12 AND reimburse_date <= '2026-01-15');

-- Rule 5: 超预算 (cumulative per department, ordered by expense_date)
-- D901 budget=200000, D902 budget=50000
-- First record with special_approval=0 that pushes cumulative sum over budget is anomalous
-- Records with special_approval=1 are exempt

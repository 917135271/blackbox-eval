-- Rule 3: 超标准 (Exceeding Standards)

-- Travel lodging per-night check
SELECT e.record_id, e.employee_id, emp.employee_level, e.amount, e.nights, e.city_tier,
       CAST(e.amount AS REAL) / e.nights AS per_night,
       CASE 
         WHEN emp.employee_level='E1' AND e.city_tier='A' THEN 450
         WHEN emp.employee_level='E1' AND e.city_tier='B' THEN 380
         WHEN emp.employee_level='E1' AND e.city_tier='C' THEN 300
         WHEN emp.employee_level='M1' AND e.city_tier='A' THEN 650
         WHEN emp.employee_level='M1' AND e.city_tier='B' THEN 550
         WHEN emp.employee_level='M1' AND e.city_tier='C' THEN 450
         WHEN emp.employee_level='D1' AND e.city_tier='A' THEN 850
         WHEN emp.employee_level='D1' AND e.city_tier='B' THEN 700
         WHEN emp.employee_level='D1' AND e.city_tier='C' THEN 600
         WHEN emp.employee_level='X1' AND e.city_tier='A' THEN 1100
         WHEN emp.employee_level='X1' AND e.city_tier='B' THEN 900
         WHEN emp.employee_level='X1' AND e.city_tier='C' THEN 750
         ELSE NULL
       END as standard
FROM expense_records e
JOIN employees emp ON e.employee_id = emp.employee_id
WHERE e.expense_type='travel_lodging' AND e.nights > 0 AND e.city_tier IS NOT NULL
  AND CAST(e.amount AS REAL) / e.nights > 
    CASE 
      WHEN emp.employee_level='E1' AND e.city_tier='A' THEN 450
      WHEN emp.employee_level='E1' AND e.city_tier='B' THEN 380
      WHEN emp.employee_level='E1' AND e.city_tier='C' THEN 300
      WHEN emp.employee_level='M1' AND e.city_tier='A' THEN 650
      WHEN emp.employee_level='M1' AND e.city_tier='B' THEN 550
      WHEN emp.employee_level='M1' AND e.city_tier='C' THEN 450
      WHEN emp.employee_level='D1' AND e.city_tier='A' THEN 850
      WHEN emp.employee_level='D1' AND e.city_tier='B' THEN 700
      WHEN emp.employee_level='D1' AND e.city_tier='C' THEN 600
      WHEN emp.employee_level='X1' AND e.city_tier='A' THEN 1100
      WHEN emp.employee_level='X1' AND e.city_tier='B' THEN 900
      WHEN emp.employee_level='X1' AND e.city_tier='C' THEN 750
      ELSE 999999999
    END
ORDER BY per_night DESC;

-- Result: R004225 (E0007 D1 tier A, 900/night > 850)

-- Business entertainment per-person
SELECT e.record_id, e.employee_id, e.amount, e.participants, CAST(e.amount AS REAL) / e.participants AS per_person
FROM expense_records e
WHERE e.expense_type='business_entertainment' AND e.participants > 0 AND CAST(e.amount AS REAL) / e.participants > 300
ORDER BY per_person DESC;

-- Result: R004224 (E0010, 700/2=350 > 300)

-- Business entertainment per event
SELECT COUNT(*) FROM expense_records WHERE expense_type='business_entertainment' AND amount > 5000;
-- Result: 0

-- Office supplies
SELECT record_id, employee_id, amount FROM expense_records WHERE expense_type='office_supplies' AND amount > 600;
-- Result: R004221 (650 > 600)

-- Communication
SELECT record_id, employee_id, amount FROM expense_records WHERE expense_type='communication' AND amount > 300;
-- Result: R004222 (330 > 300)

-- Training fee > 3500
SELECT record_id, employee_id, amount FROM expense_records WHERE expense_type='training_fee' AND amount > 3500;
-- Result: R004223 (3700 > 3500)

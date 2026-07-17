
-- Rule 1: Travel Lodging over-standard check
-- Standard: level × city_tier from 04_travel_expense.md 第四条
SELECT e.record_id, e.amount, e.nights, e.city_tier, emp.employee_level,
       ROUND(e.amount / e.nights, 2) as per_night
FROM expense_records e JOIN employees emp ON e.employee_id = emp.employee_id
WHERE e.expense_type = 'travel_lodging' AND e.nights > 0 AND e.city_tier IS NOT NULL
  AND e.special_approval = 0
  AND (
    (emp.employee_level = 'E1' AND e.city_tier = 'A' AND ROUND(e.amount / e.nights, 2) > 450) OR
    (emp.employee_level = 'E1' AND e.city_tier = 'B' AND ROUND(e.amount / e.nights, 2) > 380) OR
    (emp.employee_level = 'E1' AND e.city_tier = 'C' AND ROUND(e.amount / e.nights, 2) > 300) OR
    (emp.employee_level = 'M1' AND e.city_tier = 'A' AND ROUND(e.amount / e.nights, 2) > 650) OR
    (emp.employee_level = 'M1' AND e.city_tier = 'B' AND ROUND(e.amount / e.nights, 2) > 550) OR
    (emp.employee_level = 'M1' AND e.city_tier = 'C' AND ROUND(e.amount / e.nights, 2) > 450) OR
    (emp.employee_level = 'D1' AND e.city_tier = 'A' AND ROUND(e.amount / e.nights, 2) > 850) OR
    (emp.employee_level = 'D1' AND e.city_tier = 'B' AND ROUND(e.amount / e.nights, 2) > 700) OR
    (emp.employee_level = 'D1' AND e.city_tier = 'C' AND ROUND(e.amount / e.nights, 2) > 600) OR
    (emp.employee_level = 'X1' AND e.city_tier = 'A' AND ROUND(e.amount / e.nights, 2) > 1100) OR
    (emp.employee_level = 'X1' AND e.city_tier = 'B' AND ROUND(e.amount / e.nights, 2) > 900) OR
    (emp.employee_level = 'X1' AND e.city_tier = 'C' AND ROUND(e.amount / e.nights, 2) > 750)
  );

-- Rule 2: Local Transport over-standard check
-- Standard: city_tier from 04_travel_expense.md 第六条
SELECT e.record_id, e.amount, e.days, e.city_tier,
       ROUND(e.amount / e.days, 2) as per_day
FROM expense_records e
WHERE e.expense_type = 'local_transport' AND e.days > 0 AND e.city_tier IS NOT NULL
  AND e.special_approval = 0
  AND (
    (e.city_tier = 'A' AND ROUND(e.amount / e.days, 2) > 120) OR
    (e.city_tier = 'B' AND ROUND(e.amount / e.days, 2) > 100) OR
    (e.city_tier = 'C' AND ROUND(e.amount / e.days, 2) > 80)
  );

-- Rule 4: Business Entertainment over-standard check
-- Standards from 06_business_entertainment.md 第二条, 第三条
SELECT e.record_id, e.amount, e.participants,
       ROUND(e.amount / e.participants, 2) as per_person
FROM expense_records e
WHERE e.expense_type = 'business_entertainment' AND e.special_approval = 0
  AND participants > 0
  AND (e.amount > 5000 OR ROUND(e.amount / e.participants, 2) > 300);

-- Rule 5: Office Supplies monthly over-standard check
-- Standard: 600/月 from 07_office_communication.md 第二条
SELECT employee_id, SUBSTR(expense_date,1,7) as month,
       COUNT(*) as record_count, ROUND(SUM(amount),2) as total
FROM expense_records
WHERE expense_type = 'office_supplies' AND budget_year = 2025 AND special_approval = 0
GROUP BY employee_id, month
HAVING total > 600
ORDER BY total DESC;

-- Rule 6: Communication monthly over-standard check
-- Standard: 300/月 from 07_office_communication.md 第三条
SELECT employee_id, SUBSTR(expense_date,1,7) as month,
       COUNT(*) as record_count, ROUND(SUM(amount),2) as total
FROM expense_records
WHERE expense_type = 'communication' AND budget_year = 2025 AND special_approval = 0
GROUP BY employee_id, month
HAVING total > 300
ORDER BY total DESC;

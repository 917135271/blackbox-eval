-- RULE 3: 超标准 (Over-Standard)
-- Check each expense type against applicable standards
-- Exclude records with special_approval=1

-- 3a: travel_lodging - amount vs (standard_by_level_city * nights)
SELECT er.record_id, er.employee_id, er.expense_type, er.amount, er.city_tier, er.nights,
       e.employee_level, e.employee_name
FROM expense_records er
JOIN employees e ON er.employee_id = e.employee_id
WHERE er.expense_type = 'travel_lodging'
  AND er.special_approval = 0
  AND er.city_tier IS NOT NULL
  AND er.nights IS NOT NULL
ORDER BY er.amount DESC;

-- 3b: local_transport - amount vs (standard_by_city * days)
SELECT er.record_id, er.employee_id, er.expense_type, er.amount, er.city_tier, er.days
FROM expense_records er
WHERE er.expense_type = 'local_transport'
  AND er.special_approval = 0
  AND er.city_tier IS NOT NULL
  AND er.days IS NOT NULL
ORDER BY er.amount DESC;

-- 3c: training_fee - course fee <= 3500 per person
SELECT er.record_id, er.employee_id, er.expense_type, er.amount, er.days
FROM expense_records er
WHERE er.expense_type = 'training_fee'
  AND er.special_approval = 0
  AND er.amount > 3500
ORDER BY er.amount DESC;

-- 3d: business_entertainment - amount <= 5000 AND amount/participants <= 300
SELECT er.record_id, er.employee_id, er.expense_type, er.amount, er.participants,
       CAST(er.amount AS REAL) / er.participants as per_person
FROM expense_records er
WHERE er.expense_type = 'business_entertainment'
  AND er.special_approval = 0
  AND (er.amount > 5000 OR (er.participants > 0 AND CAST(er.amount AS REAL) / er.participants > 300))
ORDER BY per_person DESC;

-- 3e: office_supplies - single record amount <= 600
SELECT er.record_id, er.employee_id, er.expense_type, er.amount
FROM expense_records er
WHERE er.expense_type = 'office_supplies'
  AND er.special_approval = 0
  AND er.amount > 600
ORDER BY er.amount DESC;

-- 3f: communication - single record amount <= 300
SELECT er.record_id, er.employee_id, er.expense_type, er.amount
FROM expense_records er
WHERE er.expense_type = 'communication'
  AND er.special_approval = 0
  AND er.amount > 300
ORDER BY er.amount DESC;

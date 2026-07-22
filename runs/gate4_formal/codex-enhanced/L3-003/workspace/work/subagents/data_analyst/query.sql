-- ============================================================
-- 2025全年单笔超标准专项扫描 - SQL分析脚本
-- 数据库: /benchmark/data/expense.db (只读)
-- 日期范围: 2025-01-01 至 2025-12-31
-- 全局排除: special_approval = 1
-- ============================================================

-- 1. 办公用品 (office_supplies): 单笔金额 > 600元
-- 制度依据: 07_office_communication.md 第二条 (每人每月不超过600元)
SELECT 'office_supplies_full_count' as label, COUNT(*) as cnt FROM expense_records WHERE expense_type='office_supplies' AND expense_date >= '2025-01-01' AND expense_date < '2026-01-01';

SELECT record_id, employee_id, department_id, expense_date, amount, reason, city_tier, special_approval
FROM expense_records
WHERE expense_type='office_supplies'
  AND expense_date >= '2025-01-01' AND expense_date < '2026-01-01'
  AND special_approval=0
  AND amount > 600
ORDER BY amount DESC;

-- 2. 通讯费用 (communication): 单笔金额 > 300元
-- 制度依据: 07_office_communication.md 第三条 (每人每月不超过300元)
SELECT 'communication_full_count' as label, COUNT(*) as cnt FROM expense_records WHERE expense_type='communication' AND expense_date >= '2025-01-01' AND expense_date < '2026-01-01';

SELECT record_id, employee_id, department_id, expense_date, amount, reason, city_tier, special_approval
FROM expense_records
WHERE expense_type='communication'
  AND expense_date >= '2025-01-01' AND expense_date < '2026-01-01'
  AND special_approval=0
  AND amount > 300
ORDER BY amount DESC;

-- 3. 差旅住宿 (travel_lodging): 每夜间单价(amount/nights) > 对应标准
-- 制度依据: 04_travel_expense.md 第四条
-- 标准: E1(员工):A450,B380,C300; M1(经理):A650,B550,C450; D1(部门负责人):A850,B700,C600; X1(高管):A1100,B900,C750
SELECT 'travel_lodging_full_count' as label, COUNT(*) as cnt FROM expense_records WHERE expense_type='travel_lodging' AND expense_date >= '2025-01-01' AND expense_date < '2026-01-01';

SELECT e.record_id, e.employee_id, emp.employee_level, e.department_id, e.expense_date,
       e.amount, e.nights, CAST(e.amount AS REAL)/e.nights as per_night,
       e.city_tier, e.reason, e.special_approval
FROM expense_records e
JOIN employees emp ON e.employee_id = emp.employee_id
WHERE e.expense_type='travel_lodging'
  AND e.expense_date >= '2025-01-01' AND e.expense_date < '2026-01-01'
  AND e.special_approval=0
  AND e.nights > 0
  AND (
    (emp.employee_level='E1' AND e.city_tier='A' AND CAST(e.amount AS REAL)/e.nights > 450) OR
    (emp.employee_level='E1' AND e.city_tier='B' AND CAST(e.amount AS REAL)/e.nights > 380) OR
    (emp.employee_level='E1' AND e.city_tier='C' AND CAST(e.amount AS REAL)/e.nights > 300) OR
    (emp.employee_level='M1' AND e.city_tier='A' AND CAST(e.amount AS REAL)/e.nights > 650) OR
    (emp.employee_level='M1' AND e.city_tier='B' AND CAST(e.amount AS REAL)/e.nights > 550) OR
    (emp.employee_level='M1' AND e.city_tier='C' AND CAST(e.amount AS REAL)/e.nights > 450) OR
    (emp.employee_level='D1' AND e.city_tier='A' AND CAST(e.amount AS REAL)/e.nights > 850) OR
    (emp.employee_level='D1' AND e.city_tier='B' AND CAST(e.amount AS REAL)/e.nights > 700) OR
    (emp.employee_level='D1' AND e.city_tier='C' AND CAST(e.amount AS REAL)/e.nights > 600) OR
    (emp.employee_level='X1' AND e.city_tier='A' AND CAST(e.amount AS REAL)/e.nights > 1100) OR
    (emp.employee_level='X1' AND e.city_tier='B' AND CAST(e.amount AS REAL)/e.nights > 900) OR
    (emp.employee_level='X1' AND e.city_tier='C' AND CAST(e.amount AS REAL)/e.nights > 750)
  )
ORDER BY per_night DESC;

-- 4. 业务招待 (business_entertainment): amount > 5000 或 amount/participants > 300
-- 制度依据: 06_business_entertainment.md 第二条(单次≤5000)、第三条(人均≤300)
SELECT 'business_entertainment_full_count' as label, COUNT(*) as cnt FROM expense_records WHERE expense_type='business_entertainment' AND expense_date >= '2025-01-01' AND expense_date < '2026-01-01';

SELECT record_id, employee_id, department_id, expense_date, amount, participants,
       CAST(amount AS REAL)/participants as per_person, reason, city_tier, special_approval
FROM expense_records
WHERE expense_type='business_entertainment'
  AND expense_date >= '2025-01-01' AND expense_date < '2026-01-01'
  AND special_approval=0
  AND participants > 0
  AND (amount > 5000 OR CAST(amount AS REAL)/participants > 300)
ORDER BY amount DESC;

-- 5. 培训费 (training_fee): amount > 3500
-- 制度依据: 05_training_expense.md 第二条 (每人每期不超过3500元)
SELECT 'training_fee_full_count' as label, COUNT(*) as cnt FROM expense_records WHERE expense_type='training_fee' AND expense_date >= '2025-01-01' AND expense_date < '2026-01-01';

SELECT record_id, employee_id, department_id, expense_date, amount, reason, city_tier, special_approval
FROM expense_records
WHERE expense_type='training_fee'
  AND expense_date >= '2025-01-01' AND expense_date < '2026-01-01'
  AND special_approval=0
  AND amount > 3500
ORDER BY amount DESC;

-- 6. 市内交通 (local_transport): 每日单价(amount/days) > 包干标准
-- 制度依据: 04_travel_expense.md 第六条
-- 包干标准: A=120, B=100, C=80
SELECT 'local_transport_full_count' as label, COUNT(*) as cnt FROM expense_records WHERE expense_type='local_transport' AND expense_date >= '2025-01-01' AND expense_date < '2026-01-01';

SELECT record_id, employee_id, department_id, expense_date, amount, days,
       CAST(amount AS REAL)/days as per_day, city_tier, reason, special_approval
FROM expense_records
WHERE expense_type='local_transport'
  AND expense_date >= '2025-01-01' AND expense_date < '2026-01-01'
  AND special_approval=0
  AND days > 0
  AND (
    (city_tier='A' AND CAST(amount AS REAL)/days > 120) OR
    (city_tier='B' AND CAST(amount AS REAL)/days > 100) OR
    (city_tier='C' AND CAST(amount AS REAL)/days > 80)
  )
ORDER BY per_day DESC;

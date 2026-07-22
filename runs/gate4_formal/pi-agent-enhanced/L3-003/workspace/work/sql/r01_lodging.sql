-- ============================================================
-- L3-003 超标准专项扫描 SQL 查询集
-- 数据库: /benchmark/data/expense.db
-- 期间: 2025年全年 (budget_year=2025)
-- ============================================================

-- R01: 差旅住宿费超标准检查
-- 标准: 员工级 一类450/二类380/三类300
--       经理级 一类650/二类550/三类450
--       部门负责人级 一类850/二类700/三类600
--       高管级 一类1100/二类900/三类750 (元/人/晚)
-- 单晚金额 = amount / nights
SELECT 
    er.record_id,
    er.employee_id,
    emp.employee_level,
    er.city_tier,
    er.amount,
    er.nights,
    ROUND(er.amount * 1.0 / er.nights, 2) AS per_night,
    er.special_approval,
    er.expense_date
FROM expense_records er
JOIN employees emp ON er.employee_id = emp.employee_id
WHERE er.expense_type = 'lodging'
  AND er.budget_year = 2025
  AND er.nights > 0
  AND er.special_approval = 0
  AND (
    (emp.employee_level = '员工级' AND er.city_tier = '一类' AND er.amount * 1.0 / er.nights > 450)
    OR (emp.employee_level = '员工级' AND er.city_tier = '二类' AND er.amount * 1.0 / er.nights > 380)
    OR (emp.employee_level = '员工级' AND er.city_tier = '三类' AND er.amount * 1.0 / er.nights > 300)
    OR (emp.employee_level = '经理级' AND er.city_tier = '一类' AND er.amount * 1.0 / er.nights > 650)
    OR (emp.employee_level = '经理级' AND er.city_tier = '二类' AND er.amount * 1.0 / er.nights > 550)
    OR (emp.employee_level = '经理级' AND er.city_tier = '三类' AND er.amount * 1.0 / er.nights > 450)
    OR (emp.employee_level = '部门负责人级' AND er.city_tier = '一类' AND er.amount * 1.0 / er.nights > 850)
    OR (emp.employee_level = '部门负责人级' AND er.city_tier = '二类' AND er.amount * 1.0 / er.nights > 700)
    OR (emp.employee_level = '部门负责人级' AND er.city_tier = '三类' AND er.amount * 1.0 / er.nights > 600)
    OR (emp.employee_level = '高管级' AND er.city_tier = '一类' AND er.amount * 1.0 / er.nights > 1100)
    OR (emp.employee_level = '高管级' AND er.city_tier = '二类' AND er.amount * 1.0 / er.nights > 900)
    OR (emp.employee_level = '高管级' AND er.city_tier = '三类' AND er.amount * 1.0 / er.nights > 750)
  )
ORDER BY er.expense_date;

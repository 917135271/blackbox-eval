-- R03a: 超标准 - 差旅住宿(travel_lodging)
-- 标准: 员工级 一类450/二类380/三类300; 经理级 一类650/二类550/三类450; 
-- 部门负责人级 一类850/二类700/三类600; 高管级 一类1100/二类900/三类750
-- 金额按 nights>0 时 per_night=amount/nights, 否则 per_night=amount
SELECT 
    er.record_id,
    er.employee_id,
    e.employee_level,
    er.city_tier,
    er.amount,
    er.nights,
    CASE WHEN er.nights > 0 THEN ROUND(er.amount*1.0/er.nights, 2) ELSE er.amount END as per_night,
    er.reason,
    CASE e.employee_level
        WHEN '员工级' THEN CASE er.city_tier WHEN '一类城市' THEN 450 WHEN '二类城市' THEN 380 WHEN '三类城市' THEN 300 END
        WHEN '经理级' THEN CASE er.city_tier WHEN '一类城市' THEN 650 WHEN '二类城市' THEN 550 WHEN '三类城市' THEN 450 END
        WHEN '部门负责人级' THEN CASE er.city_tier WHEN '一类城市' THEN 850 WHEN '二类城市' THEN 700 WHEN '三类城市' THEN 600 END
        WHEN '高管级' THEN CASE er.city_tier WHEN '一类城市' THEN 1100 WHEN '二类城市' THEN 900 WHEN '三类城市' THEN 750 END
    END as standard_per_night
FROM expense_records er
JOIN employees e ON er.employee_id = e.employee_id
WHERE er.expense_type = 'travel_lodging'
  AND er.city_tier IS NOT NULL
  AND er.city_tier != '';

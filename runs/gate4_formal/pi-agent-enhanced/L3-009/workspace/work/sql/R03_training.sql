-- R03c: 超标准 - 培训费(training_fee) 
-- 检查: 课程费<=3500, 内部<=800/天, 外部<=1200/天, 培训住宿标准(一类500/二类420/三类350)
-- 直接查看所有training_fee记录,通过reason字段区分培训类型
SELECT 
    er.record_id,
    er.employee_id,
    er.amount,
    er.days,
    er.nights,
    er.city_tier,
    er.reason,
    CASE WHEN er.days > 0 THEN ROUND(er.amount*1.0/er.days, 2) ELSE er.amount END as per_day,
    CASE WHEN er.nights > 0 THEN ROUND(er.amount*1.0/er.nights, 2) ELSE NULL END as per_night
FROM expense_records er
WHERE er.expense_type = 'training_fee'
ORDER BY er.amount DESC;

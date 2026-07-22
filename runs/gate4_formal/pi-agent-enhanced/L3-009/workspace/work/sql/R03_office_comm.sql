-- R03d: 超标准 - 办公用品(office_supplies)和通讯费用(communication)
-- 只计单笔可确认异常(不评价月度累计)
-- office_supplies: 每月每人<=600, 单笔超600即异常
-- communication: 每月每人<=300, 单笔超300即异常
SELECT 
    er.record_id,
    er.employee_id,
    er.expense_type,
    er.amount,
    er.expense_date,
    er.reason
FROM expense_records er
WHERE (er.expense_type = 'office_supplies' AND er.amount > 600)
   OR (er.expense_type = 'communication' AND er.amount > 300)
ORDER BY er.expense_type, er.amount DESC;

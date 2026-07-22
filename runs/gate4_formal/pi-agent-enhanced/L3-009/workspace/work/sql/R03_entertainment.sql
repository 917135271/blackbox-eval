-- R03b: 超标准 - 业务招待(business_entertainment)
-- 单次>5000 OR (participants>0 AND amount/participants>300)
SELECT 
    er.record_id,
    er.employee_id,
    er.amount,
    er.participants,
    CASE WHEN er.participants > 0 THEN ROUND(er.amount*1.0/er.participants, 2) ELSE NULL END as per_person,
    er.reason
FROM expense_records er
WHERE er.expense_type = 'business_entertainment'
  AND (er.amount > 5000 
       OR (er.participants > 0 AND er.amount*1.0/er.participants > 300));

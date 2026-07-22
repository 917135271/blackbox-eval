-- R05: 超期报销 - expense_date到reimburse_date超过60天
SELECT 
    er.record_id,
    er.employee_id,
    er.expense_type,
    er.expense_date,
    er.reimburse_date,
    CAST(julianday(er.reimburse_date) - julianday(er.expense_date) AS INTEGER) as delay_days,
    er.amount,
    er.reason
FROM expense_records er
WHERE CAST(julianday(er.reimburse_date) - julianday(er.expense_date) AS INTEGER) > 60
ORDER BY delay_days DESC;

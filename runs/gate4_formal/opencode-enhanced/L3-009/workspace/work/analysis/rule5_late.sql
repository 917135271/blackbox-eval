-- Rule 5: 超期报销 (Late Reimbursement)
-- (reimburse_date - expense_date) > 60 days

SELECT e.record_id, e.employee_id, e.department_id, e.expense_type, e.amount,
       e.expense_date, e.reimburse_date,
       JULIANDAY(e.reimburse_date) - JULIANDAY(e.expense_date) as delay_days
FROM expense_records e
WHERE JULIANDAY(e.reimburse_date) - JULIANDAY(e.expense_date) > 60
ORDER BY delay_days DESC;

-- 6 records found:
-- R004231: 120 days (2025-08-02 to 2025-11-30)
-- R004232: 110 days (2025-09-04 to 2025-12-23)
-- R004230: 95 days (2025-05-06 to 2025-08-09)
-- R004229: 88 days (2025-04-05 to 2025-07-02)
-- R004228: 72 days (2025-02-05 to 2025-04-18)
-- R004227: 65 days (2025-01-05 to 2025-03-11)

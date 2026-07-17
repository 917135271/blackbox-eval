-- L2-013: 查找所有培训费超标准记录 (标准: 3500元/人/期)
-- 政策依据: XX证券培训费管理办法 第二条

-- 1. Total population count
SELECT COUNT(*) AS total_training_fee FROM expense_records WHERE expense_type = 'training_fee';

-- 2. Candidates exceeding standard
SELECT er.record_id, er.record_no, e.employee_id, e.employee_name, d.department_name,
       er.expense_date, er.amount, er.reason, er.special_approval, er.status
FROM expense_records er
JOIN employees e ON er.employee_id = e.employee_id
JOIN departments d ON er.department_id = d.department_id
WHERE er.expense_type = 'training_fee' AND er.amount > 3500
ORDER BY er.amount DESC;

-- 3. Max training fee amount
SELECT MAX(amount) FROM expense_records WHERE expense_type = 'training_fee';

-- 4. Verify special_approval for matched records
SELECT record_id, special_approval FROM expense_records WHERE record_id = 'R004223';

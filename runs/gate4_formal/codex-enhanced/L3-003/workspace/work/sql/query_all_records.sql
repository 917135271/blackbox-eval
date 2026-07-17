-- Parameterized SQL: full 2025 all-type record pull with all rule-dependent fields
SELECT 
    r.record_id,
    r.employee_id,
    r.department_id,
    r.expense_date,
    r.reimburse_date,
    r.expense_type,
    r.amount,
    r.city_tier,
    r.nights,
    r.days,
    r.participants,
    r.special_approval,
    r.status,
    r.budget_year,
    i.invoice_no,
    i.vendor_name,
    i.invoice_date,
    e.employee_level,
    e.department_id as emp_dept_id,
    d.department_name,
    d.annual_budget
FROM expense_records r
JOIN invoices i ON r.invoice_id = i.invoice_id
JOIN employees e ON r.employee_id = e.employee_id
JOIN departments d ON r.department_id = d.department_id
WHERE r.budget_year = 2025
  AND r.expense_type IN ('travel_lodging','local_transport','training_fee','business_entertainment','office_supplies','communication')
ORDER BY r.expense_type, r.reimburse_date, r.record_id

-- SQL analysis for R004233
-- Query 1: Verify R004233 expense record with joined employee and approval data
SELECT
    e.record_id,
    e.record_no,
    e.employee_id,
    emp.employee_name,
    emp.employee_level,
    emp.position_role,
    e.department_id,
    d.department_name,
    e.expense_date,
    e.reimburse_date,
    e.expense_type,
    e.amount,
    e.city_tier,
    e.nights,
    e.special_approval,
    e.status,
    e.invoice_id,
    e.budget_year
FROM expense_records e
JOIN employees emp ON e.employee_id = emp.employee_id
JOIN departments d ON e.department_id = d.department_id
WHERE e.record_id = 'R004233';

-- Query 2: Verify approval path for R004233
SELECT
    a.approval_id,
    a.record_id,
    a.tier_id,
    a.approver_employee_id,
    a.approver_role,
    a.approved_at,
    a.approval_status
FROM approvals a
WHERE a.record_id = 'R004233';

-- Query 3: Calculate per-night rate
SELECT
    record_id,
    amount,
    nights,
    amount / nights AS per_night_rate
FROM expense_records
WHERE record_id = 'R004233';

-- Query 4: Check for split claims - same employee, same expense_type within 7 days
SELECT
    record_id,
    expense_date,
    amount,
    expense_type,
    city_tier,
    nights
FROM expense_records
WHERE employee_id = 'E0012'
  AND expense_type = 'travel_lodging'
  AND record_id != 'R004233'
  AND expense_date BETWEEN '2025-09-26' AND '2025-10-10'
ORDER BY expense_date;

-- Query 5: Check invoice reuse
SELECT
    e.record_id,
    e.invoice_id,
    e.amount,
    e.employee_id
FROM expense_records e
WHERE e.invoice_id = 'INV004227';

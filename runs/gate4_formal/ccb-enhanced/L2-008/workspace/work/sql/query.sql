-- Task: L2-008 Split Reimbursement via R004212
-- Rule: Article 11, 2025 Reimbursement Policy
-- Window: 7 days around R004212 expense_date 2025-04-10 → [2025-04-03, 2025-04-17]
-- Parameters: employee_id='E0009', expense_type='travel_lodging', date_start='2025-04-03', date_end='2025-04-17'

-- Query 1: All qualifying records in window
SELECT
    er.record_id,
    er.record_no,
    er.employee_id,
    emp.employee_name,
    emp.employee_level,
    emp.position_role,
    er.department_id,
    dep.department_name,
    er.expense_date,
    er.reimburse_date,
    er.expense_type,
    er.amount,
    er.reason,
    er.city_tier,
    er.nights,
    er.special_approval,
    er.status,
    er.budget_year,
    inv.invoice_id,
    inv.invoice_no,
    inv.vendor_name,
    inv.invoice_date,
    inv.amount AS invoice_amount,
    app.tier_id,
    app.approver_role,
    app.approver_employee_id
FROM expense_records er
JOIN employees emp ON er.employee_id = emp.employee_id
JOIN departments dep ON er.department_id = dep.department_id
JOIN invoices inv ON er.invoice_id = inv.invoice_id
LEFT JOIN approvals app ON er.record_id = app.record_id
WHERE er.employee_id = 'E0009'
  AND er.expense_type = 'travel_lodging'
  AND er.expense_date BETWEEN '2025-04-03' AND '2025-04-17'
ORDER BY er.expense_date;

-- Query 2: Travel standard for D1(经理级)/A类城市
-- Standard: 650 元/人/晚 per Article 4, 04_travel_expense.md
-- R004212: 5100 / 7 nights = 728.57/night > 650 standard
-- R004213: 5100 / 7 nights = 728.57/night > 650 standard

-- Query 3: Combined amount check
-- R004212 (5100) + R004213 (5100) = 10200
-- AR-02: 3000-10000 → each individually
-- AR-03: 10000-50000 → combined total → requires 部门总经理
-- Split avoided 部门总经理 approval

-- ============================================================================
-- Split Reimbursement Analysis: R004212 (clue) — Rule: 第十一条
-- Employee E0009, travel_lodging, 2025-04-03 to 2025-04-22 (±7 days)
-- ============================================================================

-- Q1: Retrieve all travel_lodging records for E0009 within the ±7-day window
-- MCP: list_expenses(employee_id="E0009", expense_type="travel_lodging",
--                    date_from="2025-04-03", date_to="2025-04-22")
-- Equivalent SQL:
SELECT record_id, record_no, employee_id, employee_name, department_id,
       expense_date, reimburse_date, expense_type, amount, reason, status
FROM reimbursement_records
WHERE employee_id = 'E0009'
  AND expense_type = 'travel_lodging'
  AND expense_date BETWEEN '2025-04-03' AND '2025-04-22'
ORDER BY expense_date;
-- Result: 2 records — R004212 (2025-04-10, 5100), R004213 (2025-04-15, 5100)

-- Q2: Full-year 2025 scan — confirm no other travel_lodging records for E0009
-- MCP: list_expenses(employee_id="E0009", expense_type="travel_lodging",
--                    date_from="2025-01-01", date_to="2025-12-31")
-- Equivalent SQL:
SELECT record_id, expense_date, amount, reason, status
FROM reimbursement_records
WHERE employee_id = 'E0009'
  AND expense_type = 'travel_lodging'
  AND budget_year = 2025
ORDER BY expense_date;
-- Result: 2 records total — R004212 and R004213 only
-- (confirmed via summarize_expenses: 2025-04: 2 records, 10200 total)

-- Q3: Check E0009 all expense types in April 2025 for cross-type splits
-- MCP: list_expenses(employee_id="E0009", date_from="2025-04-01",
--                    date_to="2025-04-30")
-- Equivalent SQL:
SELECT record_id, expense_date, expense_type, amount, reason
FROM reimbursement_records
WHERE employee_id = 'E0009'
  AND expense_date BETWEEN '2025-04-01' AND '2025-04-30'
ORDER BY expense_date;
-- Result: R004229 (communication, 2025-04-05, 183) — different type, excluded

-- Q4: Get full detail on both target records
-- MCP: get_expense_detail("R004212"), get_expense_detail("R004213")
-- Equivalent SQL:
SELECT r.*, i.invoice_no, i.vendor_name, i.invoice_date, i.amount AS invoice_amount,
       e.employee_name, e.employee_level, e.position_role,
       d.department_name, d.annual_budget
FROM reimbursement_records r
JOIN invoices i ON r.invoice_id = i.invoice_id
JOIN employees e ON r.employee_id = e.employee_id
JOIN departments d ON r.department_id = d.department_id
WHERE r.record_id IN ('R004212', 'R004213');

-- Q5: Approval chain for both records
-- MCP: list_approvals("R004212"), list_approvals("R004213")
-- Equivalent SQL:
SELECT a.approval_id, a.record_id, a.tier_id, a.approver_employee_id,
       a.approver_role, a.approved_at, a.approval_status
FROM approvals a
WHERE a.record_id IN ('R004212', 'R004213');
-- Result: Both AR-02, approver E0009 (部门经理), self-approved

-- Q6: Check invoice reuse
-- MCP: find_invoice_usage("FP2025X0004206"), find_invoice_usage("FP2025X0004207")
-- Equivalent SQL:
SELECT invoice_no, COUNT(DISTINCT record_id) AS usage_count
FROM reimbursement_records
WHERE invoice_no IN ('FP2025X0004206', 'FP2025X0004207')
GROUP BY invoice_no;
-- Result: usage_count=1 for both — no reuse

-- Q7: Department D009 employees — check for 部门总经理 role
-- MCP: list_employees(department_id="D009")
-- Equivalent SQL:
SELECT employee_id, employee_name, employee_level, position_role
FROM employees
WHERE department_id = 'D009';
-- Result: 5 employees, E0009 is 部门经理, no 部门总经理 in department

-- Q8: Date gap and combined amount computation
-- Computed in analysis:
--   date_gap = julianday('2025-04-15') - julianday('2025-04-10') = 5 days
--   combined = 5100 + 5100 = 10200
--   individual tier: AR-02 (3000 <= 5100 < 10000)
--   combined tier:   AR-03 (10000 <= 10200 < 50000)

-- Q9: Full-year E0009 summary by type and month
-- MCP: summarize_expenses(employee_id="E0009", group_by="expense_type,month",
--                         date_from="2025-01-01", date_to="2025-12-31")
-- Equivalent SQL:
SELECT expense_type, strftime('%Y-%m', expense_date) AS month,
       COUNT(*) AS record_count, SUM(amount) AS total_amount
FROM reimbursement_records
WHERE employee_id = 'E0009'
  AND budget_year = 2025
GROUP BY expense_type, month
ORDER BY month, expense_type;

-- ============================================================================
-- Summary: 2 records, same employee (E0009), same type (travel_lodging),
-- 5-day gap (within 7), combined 10200 crosses AR-03 threshold.
-- Both self-approved at AR-02 by E0009 as 部门经理.
-- No 部门总经理 in department D009 for required AR-03 escalation.
-- ============================================================================

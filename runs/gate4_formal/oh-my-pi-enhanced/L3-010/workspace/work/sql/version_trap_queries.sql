-- Version Trap Analysis SQL
-- Date: 2026-07-16

-- Query 1: Trap interval 1 [8000, 10000) — approved records
-- Old policy (2022): >=8000 requires 部门总经理
-- New policy (2025): >=10000 requires 部门总经理
-- Records in [8000, 10000) would be treated differently under old vs new policy
SELECT record_id, record_no, employee_id, employee_name, department_id,
       department_name, expense_date, reimburse_date, expense_type, amount,
       reason, invoice_no, status
FROM reimbursement_records
WHERE amount >= 8000.00
  AND amount < 10000.00
  AND status = 'approved'
ORDER BY amount DESC;
-- Result: 1 record — R004233 (9990.00)

-- Query 2: Trap interval 2 [30000, 50000) — approved records
-- Old policy (2022): >=30000 requires 分管副总
-- New policy (2025): >=50000 requires 分管副总
-- Records in [30000, 50000) would be treated differently under old vs new policy
SELECT record_id, record_no, employee_id, employee_name, department_id,
       department_name, expense_date, reimburse_date, expense_type, amount,
       reason, invoice_no, status
FROM reimbursement_records
WHERE amount >= 30000.00
  AND amount < 50000.00
  AND status = 'approved'
ORDER BY amount DESC;
-- Result: 0 records

-- Query 3: Detail for R004233
-- get_expense_detail('R004233')

-- Query 4: Approvals for R004233
-- list_approvals('R004233')
-- Result: 1 approval — 部门经理 (E0008, AR-02), approved 2025-10-09
-- Missing under old policy: 部门总经理 approval not present

-- Boundary verification: widened check [7900, 10100] confirmed no additional records
-- Boundary verification: widened check [29000, 51000] confirmed 0 records

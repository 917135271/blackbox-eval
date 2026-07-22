-- Query: Find all AR-02 records and verify they lack 财务复核 approval
-- Cross-reference: 01_expense_reimbursement_2025.md Art.5 → 03_authorization_management.md 附件二
-- AR-02 requires: 部门经理,并经财务复核 (department manager AND financial review)

SELECT er.record_id, er.amount, er.expense_type, er.employee_id, er.expense_date,
       er.department_id, er.status, a.tier_id, a.approver_role
FROM expense_records er
JOIN approvals a ON er.record_id = a.record_id
WHERE a.tier_id = 'AR-02'
ORDER BY er.amount DESC;

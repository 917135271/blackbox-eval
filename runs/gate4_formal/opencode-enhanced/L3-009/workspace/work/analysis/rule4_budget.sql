-- Rule 4: 超预算 (Exceeding Budget)
-- Per department, calculate running cumulative sum ordered by reimburse_date ASC, record_id ASC
-- Find first record where cumulative > annual_budget

SELECT e.department_id, d.department_name, d.annual_budget, e.record_id, e.reimburse_date, e.amount,
       SUM(e.amount) OVER (PARTITION BY e.department_id ORDER BY e.reimburse_date ASC, e.record_id ASC) as running_total
FROM expense_records e
JOIN departments d ON e.department_id = d.department_id
ORDER BY e.department_id, e.reimburse_date, e.record_id;

-- Departments exceeding budget:
-- D001 (投资银行部): Budget=230395.17, exceeds at R000079 (2025-10-21)
-- D002 (固定收益部): Budget=107785.42, exceeds at R002009 (2025-09-28)
-- D003 (财富管理部): Budget=109772.07, exceeds at R003968 (2025-09-28)
-- D004 (研究所): Budget=264890.39, exceeds at R000894 (2025-09-30)
-- D005 (机构业务部): Budget=278540.94, exceeds at R003479 (2025-10-13)
-- D006 (运营管理部): Budget=340961.75, exceeds at R000312 (2025-10-06)

-- Departments NOT exceeding:
-- D007 (信息技术部): Budget=301500.00, MaxRunning=252588.38
-- D008 (合规风控部): Budget=381600.00, MaxRunning=297095.29
-- D009 (财务管理部): Budget=191300.00, MaxRunning=159294.06
-- D010 (人力资源部): Budget=164500.00, MaxRunning=139536.39

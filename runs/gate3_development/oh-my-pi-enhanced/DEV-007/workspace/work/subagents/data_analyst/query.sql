-- ============================================================
-- Monthly Standard Check: office_supplies & communication
-- Policy: 07_office_communication.md
--   Article 2: office_supplies <= 600 元/month/person
--   Article 3: communication   <= 300 元/month/person
-- ============================================================

-- Step 1: Retrieve all office_supplies records
-- MCP: expense_query.list_expenses(expense_type="office_supplies", page_size=200)
-- Result: 5 records (R900001, R900002, R900007, R900008, R900009)

-- Step 2: Retrieve all communication records
-- MCP: expense_query.list_expenses(expense_type="communication", page_size=200)
-- Result: 3 records (R900006, R900014, R900015)

-- Step 3: Group by employee_id + strftime('%Y-%m', expense_date)
-- Conceptual SQL:
SELECT
    employee_id,
    strftime('%Y-%m', expense_date) AS year_month,
    expense_type,
    SUM(amount) AS total_amount,
    COUNT(*) AS record_count,
    GROUP_CONCAT(record_id) AS record_ids
FROM reimbursement_records
WHERE expense_type IN ('office_supplies', 'communication')
  AND status = 'approved'
  AND special_approval = 0
GROUP BY employee_id, strftime('%Y-%m', expense_date), expense_type
HAVING
    (expense_type = 'office_supplies' AND SUM(amount) > 600)
    OR
    (expense_type = 'communication'   AND SUM(amount) > 300)
ORDER BY expense_type, employee_id, year_month;

-- ============================================================
-- Step 4: Detailed record validation
-- Each record in an over-limit group fetched via:
--   MCP: expense_query.get_expense_detail(record_id=<id>)
-- Checked: special_approval, status, expense_date
-- ============================================================

-- ============================================================
-- RESULTS SUMMARY
-- ============================================================
-- office_supplies population: 5
-- communication population:   3
-- Total in scope:             8
--
-- Over-limit groups: 3
--   E9001 / 2025-01 / office_supplies : 960.00 > 600.00  [R900001, R900002]
--   E9001 / 2025-04 / office_supplies : 650.00 > 600.00  [R900007]
--   E9001 / 2025-09 / communication   : 340.00 > 300.00  [R900014, R900015]
--
-- No special_approval exemptions applied.

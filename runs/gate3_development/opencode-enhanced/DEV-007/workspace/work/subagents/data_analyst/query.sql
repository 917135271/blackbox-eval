-- DEV-007: Office Supplies & Communication Monthly Over-Standard Analysis
-- Query all in-scope records and aggregate by employee, expense_type, natural month

-- Step 1: Retrieve all office_supplies records
-- SELECT * FROM expenses WHERE expense_type = 'office_supplies';
-- Results from list_expenses(expense_type='office_supplies', page_size=500):
-- 5 records: R900001, R900002, R900007, R900008, R900009

-- Step 2: Retrieve all communication records
-- SELECT * FROM expenses WHERE expense_type = 'communication';
-- Results from list_expenses(expense_type='communication', page_size=500):
-- 3 records: R900006, R900014, R900015

-- Step 3: Cross-verification via summarize_expenses
-- summarize_expenses(group_by='employee_id,expense_type,month', expense_type='office_supplies')
-- summarize_expenses(group_by='employee_id,expense_type,month', expense_type='communication')

-- Step 4: Monthly aggregation with threshold comparison
-- Performed in Python analysis (see aggregation_results.json)

-- Thresholds (per 07_office_communication.md):
--   Article 2: office_supplies <= 600 yuan/person/month
--   Article 3: communication <= 300 yuan/person/month

-- Complete population: 8 records (5 office_supplies + 3 communication)
-- Over-standard groups: 3
-- Over-standard records: 5 (R900001, R900002, R900007, R900014, R900015)

-- Detailed aggregation:
-- E9001, office_supplies, 2025-01: R900001(480) + R900002(480) = 960 > 600  [OVER]
-- E9001, office_supplies, 2025-04: R900007(650) = 650 > 600  [OVER]
-- E9001, office_supplies, 2025-05: R900008(590) = 590 <= 600  [OK]
-- E9002, office_supplies, 2025-05: R900009(590) = 590 <= 600  [OK]
-- E9001, communication, 2025-03: R900006(200) = 200 <= 300  [OK]
-- E9001, communication, 2025-09: R900014(180) + R900015(160) = 340 > 300  [OVER]

-- Secondary observation (Article 4):
-- R900012: E9001, expense_type='other', 2025-12, 900 yuan, reason='年末发生费用补充提交'
-- Potential circumvention flag - but not an office_supplies/communication record

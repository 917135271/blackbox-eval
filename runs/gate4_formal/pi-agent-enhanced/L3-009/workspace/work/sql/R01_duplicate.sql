-- R01: 重复报销 - 同一发票被多条报销记录使用
SELECT i.invoice_id, i.invoice_no, i.amount as invoice_amount, i.expense_type as invoice_type,
       COUNT(er.record_id) as usage_count,
       GROUP_CONCAT(er.record_id, ',') as record_ids,
       GROUP_CONCAT(er.employee_id, ',') as employee_ids,
       GROUP_CONCAT(er.expense_date, ',') as expense_dates,
       SUM(er.amount) as total_reimbursed
FROM invoices i
JOIN expense_records er ON er.invoice_id = i.invoice_id
GROUP BY i.invoice_id
HAVING COUNT(er.record_id) > 1
ORDER BY usage_count DESC, i.invoice_id;

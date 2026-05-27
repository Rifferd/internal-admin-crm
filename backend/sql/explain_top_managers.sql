EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT
    u.id AS manager_id,
    u.full_name AS manager_name,
    u.email AS manager_email,
    COUNT(d.id) AS deals_count,
    COALESCE(SUM(d.amount), 0) AS total_amount
FROM deals d
JOIN users u ON u.id = d.manager_id
JOIN clients c ON c.id = d.client_id
WHERE d.status = 'won'
  AND c.deleted_at IS NULL
  AND d.closed_at::date >= DATE '2026-05-01'
  AND d.closed_at::date <= DATE '2026-05-31'
GROUP BY u.id, u.full_name, u.email
ORDER BY total_amount DESC
LIMIT 5;
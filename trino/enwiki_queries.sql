-- Useful queries for the enwiki table (Trino, wiki.default.enwiki)
-- Run individually with: .venv/bin/python trino/query_trino.py -f trino/enwiki_queries.sql
-- (one statement at a time) or use run_enwiki_queries.py to run them all.

-- 1. Row count
SELECT COUNT(*) AS total_articles FROM enwiki;

-- 2. Sample of articles
SELECT identifier, name, description, date_modified
FROM enwiki
LIMIT 200;

-- 3. Most recently modified articles
SELECT name, date_modified, version.editor.name AS editor
FROM enwiki
ORDER BY date_modified DESC
LIMIT 200;

-- 4. Largest articles by character count
SELECT name, version.number_of_characters AS chars, version.size.unit_text AS size_unit
FROM enwiki
ORDER BY version.number_of_characters DESC
LIMIT 200;

-- 5. Most prolific editors in the dataset
SELECT version.editor.name AS editor, COUNT(*) AS edits
FROM enwiki
GROUP BY version.editor.name
ORDER BY edits DESC
LIMIT 200;

-- 6. Articles at high risk of being reverted (revertrisk model)
SELECT name,
       version.scores.revertrisk.probability."true" AS revert_probability
FROM enwiki
WHERE version.scores.revertrisk.prediction = true
ORDER BY revert_probability DESC
LIMIT 200;

-- 7. Articles most in need of additional references
SELECT name, version.scores.referenceneed.reference_need_score AS need_score
FROM enwiki
ORDER BY need_score DESC
LIMIT 200;

-- 8. Edits by administrators vs anonymous editors
SELECT
  version.editor.is_admin AS is_admin,
  version.editor.is_anonymous AS is_anonymous,
  COUNT(*) AS article_count
FROM enwiki
GROUP BY 1, 2
ORDER BY article_count DESC;

-- 9. Breaking-news / flagged articles
SELECT name, version.is_breaking_news, version.is_flagged_stable, version.noindex
FROM enwiki
WHERE version.is_breaking_news = true
   OR version.is_flagged_stable = true
   OR version.noindex = true
LIMIT 200;

-- 10. Full-text search on article names (e.g. 'Python')
SELECT identifier, name, description
FROM enwiki
WHERE lower(name) LIKE '%kanye west%'
LIMIT 200;

-- 11. Articles with the most references
SELECT name, cardinality("references") AS ref_count
FROM enwiki
ORDER BY ref_count DESC
LIMIT 200;

-- 12. Articles created per month (requires date_created populated)
SELECT date_trunc('month', date_created) AS month, COUNT(*) AS articles
FROM enwiki
GROUP BY 1
ORDER BY 1 DESC
LIMIT 24;

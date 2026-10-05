-- Run after Trino is up, e.g.:
--   docker exec -i trino trino < setup.sql
-- or with the CLI: trino --server localhost:8080 -f setup.sql

CREATE SCHEMA IF NOT EXISTS wiki.default;

CREATE TABLE IF NOT EXISTS wiki.default.enwiki (
  abstract VARCHAR,
  additional_entities ARRAY(ROW(aspects ARRAY(VARCHAR), identifier VARCHAR, url VARCHAR)),
  date_created TIMESTAMP(3),
  date_modified TIMESTAMP(3),
  description VARCHAR,
  event ROW(date_created VARCHAR, date_published VARCHAR, fail_count BIGINT, fail_reason VARCHAR, identifier VARCHAR, "type" VARCHAR),
  identifier BIGINT,
  image ROW(content_url VARCHAR, height BIGINT, width BIGINT),
  in_language ROW(identifier VARCHAR),
  infoboxes VARCHAR,
  is_part_of ROW(identifier VARCHAR, url VARCHAR),
  license ARRAY(ROW(identifier VARCHAR, name VARCHAR, url VARCHAR)),
  main_entity ROW(identifier VARCHAR, url VARCHAR),
  name VARCHAR,
  "references" ARRAY(ROW(
    identifier VARCHAR,
    metadata VARCHAR,
    source ROW(links ARRAY(ROW(text VARCHAR, url VARCHAR)), value VARCHAR),
    text ROW(links ARRAY(ROW(text VARCHAR, url VARCHAR)), value VARCHAR),
    "type" VARCHAR
  )),
  sections VARCHAR,
  tables VARCHAR,
  url VARCHAR,
  version ROW(
    comment VARCHAR,
    editor ROW(
      date_started TIMESTAMP(3),
      edit_count BIGINT,
      groups ARRAY(VARCHAR),
      has_advanced_rights BOOLEAN,
      identifier BIGINT,
      is_admin BOOLEAN,
      is_anonymous BOOLEAN,
      is_bot BOOLEAN,
      is_patroller BOOLEAN,
      name VARCHAR
    ),
    identifier BIGINT,
    is_breaking_news BOOLEAN,
    is_flagged_stable BOOLEAN,
    is_minor_edit BOOLEAN,
    maintenance_tags VARCHAR,
    noindex BOOLEAN,
    number_of_characters BIGINT,
    scores ROW(
      referenceneed ROW(reference_need_score DOUBLE),
      referencerisk ROW(reference_risk_score DOUBLE),
      revertrisk ROW(prediction BOOLEAN, probability ROW("false" DOUBLE, "true" DOUBLE))
    ),
    size ROW(unit_text VARCHAR, value BIGINT),
    tags ARRAY(VARCHAR)
  )
)
WITH (
  format = 'PARQUET',
  external_location = 'file:///data/enwiki'
);

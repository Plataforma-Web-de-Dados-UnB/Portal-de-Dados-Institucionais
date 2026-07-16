DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'superset_reader') THEN
        CREATE ROLE superset_reader WITH LOGIN PASSWORD 'superset_reader_pass';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE unb_portal_dev TO superset_reader;

CREATE SCHEMA IF NOT EXISTS silver;
GRANT USAGE ON SCHEMA silver TO superset_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA silver TO superset_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA silver GRANT SELECT ON TABLES TO superset_reader;

CREATE SCHEMA IF NOT EXISTS gold;
GRANT USAGE ON SCHEMA gold TO superset_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO superset_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA gold GRANT SELECT ON TABLES TO superset_reader;

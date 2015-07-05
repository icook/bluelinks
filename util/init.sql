CREATE USER ar WITH PASSWORD 'testing';
CREATE USER ar_ro WITH PASSWORD 'testing';
-- Production database
DROP DATABASE IF EXISTS ar;
CREATE DATABASE ar;
GRANT ALL PRIVILEGES ON DATABASE ar to ar;
GRANT ALL PRIVILEGES ON DATABASE ar to ar_ro;
-- Create a testing database to be different than dev
DROP DATABASE IF EXISTS ar_testing;
CREATE DATABASE ar_testing;
GRANT ALL PRIVILEGES ON DATABASE ar_testing to ar;
GRANT ALL PRIVILEGES ON DATABASE ar_testing to ar_ro;

-- Initialize Shared Logistics Platform Database
-- This script runs on first container startup

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Create indexes for geospatial queries
-- (Tables will be created by SQLAlchemy migrations)

-- Create read-only user for analytics
CREATE USER analytics_readonly WITH PASSWORD 'analytics_readonly_password';

-- Grant permissions (run after tables are created)
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;

-- Create materialized views for common analytics queries
-- (These will be populated after initial data load)

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully for Shared Logistics Platform';
END $$;

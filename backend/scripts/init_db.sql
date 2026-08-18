-- =============================================================================
-- scripts/init_db.sql — Database Initialization Script
-- =============================================================================
--
-- WHY this file:
--   Runs on first Postgres startup (via docker-entrypoint-initdb.d/).
--   Creates extensions and configures database-level settings that
--   cannot be done via Alembic migrations (which run at the schema level).
--
-- EXTENSIONS:
--   - uuid-ossp: Generates UUID v4 natively in PostgreSQL.
--     WHY: Even though SQLAlchemy generates UUIDs in Python, having this
--     extension allows DB-level DEFAULT gen_random_uuid() as a fallback.
--   - pg_trgm: Trigram indexes for fuzzy text search (product search by name).
--     WHY: ILIKE '%keyword%' without pg_trgm performs sequential scans.
--     With GIN/GiST trigram indexes, fuzzy search is O(log n).
--   - btree_gin: Allows GIN indexes on regular types (UUID, int, timestamp).
--     WHY: Needed for composite GIN indexes in the inventory module.
--
-- =============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable trigram similarity for product search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Enable GIN index support for composite indexes
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =============================================================================
-- Database performance settings (session-level, applied by connection pool)
-- These are set here for documentation — production uses postgresql.conf
-- =============================================================================

-- Comment: The following are reference configurations for postgresql.conf
-- Not executed here (require superuser and restart):
--
-- shared_buffers = 256MB           # 25% of available RAM
-- effective_cache_size = 1GB       # Estimate of OS + Postgres cache
-- maintenance_work_mem = 64MB      # For VACUUM, CREATE INDEX
-- work_mem = 16MB                  # Per-query sort/hash memory
-- random_page_cost = 1.1           # SSD-optimized (vs 4.0 for HDD)
-- effective_io_concurrency = 200   # SSD parallelism
-- checkpoint_completion_target = 0.9
-- wal_buffers = 16MB
-- default_statistics_target = 100
-- max_connections = 200            # Set based on (workers * pool_size) + buffer

-- Phase 13: Scalp (Track B) ??? ??
-- ?? ??: 2026-01-22
-- ??: WebSocket ??? ? ??? ? 1? ? ??? ??

-- =====================================================
-- 1. scalp_ticks ??? (??? ? ???)
-- =====================================================
CREATE TABLE IF NOT EXISTS scalp_ticks (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL,
    event_time      TIMESTAMPTZ NOT NULL,
    bid_price       NUMERIC(15,4) NOT NULL,
    ask_price       NUMERIC(15,4) NOT NULL,
    bid_size        BIGINT,
    ask_size        BIGINT,
    last_price      NUMERIC(15,4),
    volume          BIGINT,
    session_id      VARCHAR(50) NOT NULL,
    mitigation_level INT DEFAULT 0,
    quality_flag    VARCHAR(20) DEFAULT 'normal'
);

CREATE INDEX IF NOT EXISTS idx_scalp_ticks_symbol ON scalp_ticks(symbol);
CREATE INDEX IF NOT EXISTS idx_scalp_ticks_event_time ON scalp_ticks(event_time DESC);
CREATE INDEX IF NOT EXISTS idx_scalp_ticks_session ON scalp_ticks(session_id);

-- =====================================================
-- 2. scalp_1m_bars ??? (1? ? ???)
-- =====================================================
CREATE TABLE IF NOT EXISTS scalp_1m_bars (
    symbol          VARCHAR(20) NOT NULL,
    bar_time        TIMESTAMPTZ NOT NULL,
    open            NUMERIC(15,4),
    high            NUMERIC(15,4),
    low             NUMERIC(15,4),
    close           NUMERIC(15,4),
    volume          BIGINT,
    coverage_ratio  FLOAT DEFAULT 0.0,
    session_id      VARCHAR(50) NOT NULL,
    quality_flag    VARCHAR(20) DEFAULT 'normal',
    PRIMARY KEY (symbol, bar_time)
);

CREATE INDEX IF NOT EXISTS idx_scalp_1m_bars_symbol ON scalp_1m_bars(symbol);
CREATE INDEX IF NOT EXISTS idx_scalp_1m_bars_time ON scalp_1m_bars(bar_time DESC);
CREATE INDEX IF NOT EXISTS idx_scalp_1m_bars_session ON scalp_1m_bars(session_id);

-- =====================================================
-- 3. scalp_gaps ??? (??? ?? ??)
-- =====================================================
CREATE TABLE IF NOT EXISTS scalp_gaps (
    id              SERIAL PRIMARY KEY,
    gap_start_ts    TIMESTAMPTZ NOT NULL,
    gap_end_ts      TIMESTAMPTZ NOT NULL,
    gap_seconds     INT NOT NULL,
    scope           VARCHAR(20),
    reason          VARCHAR(100),
    session_id      VARCHAR(50) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scalp_gaps_session ON scalp_gaps(session_id);
CREATE INDEX IF NOT EXISTS idx_scalp_gaps_time ON scalp_gaps(gap_start_ts DESC);

-- =====================================================
-- ????? ??? (?????? ??)
-- =====================================================
CREATE TABLE IF NOT EXISTS migration_log (
    id              SERIAL PRIMARY KEY,
    migration_name  VARCHAR(100) NOT NULL,
    executed_at     TIMESTAMPTZ DEFAULT NOW(),
    status          VARCHAR(20) DEFAULT 'success',
    details         TEXT
);

INSERT INTO migration_log (migration_name, status)
VALUES ('001_create_scalp_tables', 'success');

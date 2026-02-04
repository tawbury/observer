-- Phase 13: Swing (Track A) íì´ë¸ ìì± ë° ì¤í¤ë§ ìì 
-- ìì± ë ì§: 2026-01-22
-- ì¤ëª: REST API 10ë¶ ë´ ë°ì´í° ì ì¥ (bid/ask íë ì¶ê°)

-- Drop existing tables if they exist (for idempotency)
DROP TABLE IF EXISTS swing_bars_10m CASCADE;

-- =====================================================
-- 1. swing_bars_10m íì´ë¸ (10ë¶ ë´ ë°ì´í°)
-- =====================================================
CREATE TABLE swing_bars_10m (
    symbol          VARCHAR(20) NOT NULL,
    bar_time        TIMESTAMPTZ NOT NULL,
    open            NUMERIC(15,4),
    high            NUMERIC(15,4),
    low             NUMERIC(15,4),
    close           NUMERIC(15,4),
    volume          BIGINT,
    bid_price       NUMERIC(15,4),
    ask_price       NUMERIC(15,4),
    session_id      VARCHAR(50) NOT NULL,
    schema_version  VARCHAR(10) DEFAULT '1.0',
    mitigation_level INT DEFAULT 0,
    quality_flag    VARCHAR(20) DEFAULT 'normal',
    PRIMARY KEY (symbol, bar_time)
);

CREATE INDEX IF NOT EXISTS idx_swing_10m_symbol ON swing_bars_10m(symbol);
CREATE INDEX IF NOT EXISTS idx_swing_10m_time ON swing_bars_10m(bar_time DESC);
CREATE INDEX IF NOT EXISTS idx_swing_10m_session ON swing_bars_10m(session_id);
CREATE INDEX IF NOT EXISTS idx_swing_10m_bid_ask ON swing_bars_10m(symbol, bar_time, bid_price, ask_price);

-- =====================================================
-- ë©íë°ì´í° ìë°ì´í¸
-- =====================================================
INSERT INTO migration_log (migration_name, status)
VALUES ('002_create_swing_tables', 'success');

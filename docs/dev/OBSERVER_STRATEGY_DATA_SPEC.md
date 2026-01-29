# Observer Strategy Data Warehouse Specification (Phase 14)

---

# Meta
- Project Name: Observer Program
- File Name: OBSERVER_STRATEGY_DATA_SPEC.md
- Document ID: OBS-SPEC-014
- Status: **📋 DRAFT**
- Created Date: 2026-01-29
- Last Updated: 2026-01-29
- Author: Claude Code
- Reviewer:
- Parent Document: [[DB_MIGRATION_INTEGRATION_GUIDE.md]]
- Related Reference: [[observer_architecture_v2.md]], [[data_pipeline_architecture_observer_v1.0.md]]

---

## 📋 Executive Summary

This document specifies the **Observer Data Warehouse** architecture for **Strategy Validation & Parameter Optimization**. The system serves as a data foundation to derive statistical evidence for modifying trading parameters and validating Kiwoom HTS Condition Search expressions for Scalping, Swing, and Portfolio Rebalancing strategies.

**Primary Goal**: NOT real-time trade execution, but **offline analysis** and **parameter derivation**

**Target Use Cases**:
1. Calculate optimal entry/exit thresholds from historical tick/bar data
2. Backtest Condition Search expressions against collected market data
3. Derive statistically-validated trading parameters for Scalp/Swing/Portfolio strategies

---

## 1️⃣ Architectural Overview: Strategy Evidence Vault

### 1.1 System Role

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OBSERVER DATA WAREHOUSE                               │
│                     "Strategy Evidence Vault"                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────┐  │
│   │  Raw Data    │───▶│  Analysis    │───▶│  Parameter Derivation        │  │
│   │  (12 tables) │    │  (3 tables)  │    │  Program                     │  │
│   └──────────────┘    └──────────────┘    └──────────────────────────────┘  │
│         │                    │                          │                    │
│         │                    │                          ▼                    │
│   ┌─────▼──────┐      ┌──────▼─────┐         ┌─────────────────────┐       │
│   │ scalp_*    │      │ analysis_* │         │ Validated Parameters │       │
│   │ swing_*    │      │ rolling_   │         │ - entry_threshold   │       │
│   │ portfolio_*│      │ stats      │         │ - exit_threshold    │       │
│   └────────────┘      └────────────┘         │ - stop_loss_pct     │       │
│                                              │ - take_profit_pct   │       │
│                                              └─────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow Architecture

```
Kiwoom Securities API (REST + WebSocket)
    │
    ├─── Track A Collector (REST)
    │    └── Every 5-10 minutes
    │    └── 131 symbols (KOSPI/KOSDAQ universe)
    │    └── Output: swing_bars_10m (~188k bars/month)
    │
    └─── Track B Collector (WebSocket)
         └── 2Hz real-time ticks
         └── 41 concurrent slots (KIS limit)
         └── Output: scalp_ticks (~1M+ rows/month)
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │ Quality     │     │ Gap         │     │ Batched     │       │
│  │ Gate        │────▶│ Detector    │────▶│ Writer      │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│        │                   │                   │                │
│        ▼                   ▼                   ▼                │
│  quality_flag        scalp_gaps          COPY protocol         │
│  coverage_ratio      (disconnect log)    (100 rec/500ms)       │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL (Docker)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   HOT ZONE (0-7 days)          COLD ZONE (7-90 days)           │
│   ┌─────────────────┐          ┌─────────────────┐             │
│   │ Partial Indexes │          │ BRIN Indexes    │             │
│   │ In-memory set   │          │ Clustered data  │             │
│   └─────────────────┘          └─────────────────┘             │
│                                                                  │
│   ARCHIVE (90+ days)                                            │
│   ┌─────────────────┐                                           │
│   │ Monthly partitions │                                        │
│   │ Optional compression │                                      │
│   └─────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ANALYSIS LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ Rolling Stats    │  │ Signal Events    │  │ Threshold     │ │
│  │ Computation      │  │ Detection        │  │ Optimization  │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
│           │                     │                    │          │
│           ▼                     ▼                    ▼          │
│  analysis_rolling_stats  analysis_signal_events  analysis_     │
│  (volatility, ATR)       (conditions met)        threshold_    │
│                                                  candidates    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Unified Database Strategy

**Single Schema with Logical Namespacing**:

| Namespace | Tables | Workload Pattern | Expected Volume |
|-----------|--------|------------------|-----------------|
| `scalp_*` | scalp_ticks, scalp_1m_bars, scalp_gaps | High-frequency writes (2Hz × 41 symbols) | ~1M rows/month |
| `swing_*` | swing_bars_10m | Periodic writes (10min × 131 symbols) | ~188k rows/month |
| `portfolio_*` | 7 tables (policy, positions, rebalance) | Low-frequency CRUD | ~1k rows/month |
| `analysis_*` | rolling_stats, threshold_candidates, signal_events | Read-heavy analytics | ~500k rows/month |

**Rationale for Single Schema**:
1. Docker container resource constraints (1GB memory, 2 CPU)
2. Cross-domain queries (joining scalp and swing) simpler without schema qualifiers
3. Avoiding TimescaleDB extension reduces operational complexity
4. Connection pool can serve all workloads without routing logic

---

## 2️⃣ Advanced Schema Design

### 2.1 Existing Tables (Phase 13 - 12 Tables)

**Scalp Tables (Track B)**:
- `scalp_ticks` - Real-time 2Hz tick data
- `scalp_1m_bars` - 1-minute OHLCV aggregation with coverage_ratio
- `scalp_gaps` - WebSocket disconnection tracking

**Swing Tables (Track A)**:
- `swing_bars_10m` - 10-minute OHLCV bars with bid/ask spread

**Portfolio Tables**:
- `portfolio_policy`, `target_weights`, `portfolio_snapshot`
- `portfolio_positions`, `rebalance_plan`, `rebalance_orders`, `rebalance_execution`
- `migration_log`

### 2.2 New Analysis Tables (Phase 14 - 3 Tables)

#### 2.2.1 analysis_rolling_stats

Pre-computed rolling statistics for parameter derivation. Updated incrementally via materialized view refresh.

```sql
CREATE TABLE analysis_rolling_stats (
    -- Primary Key
    symbol          VARCHAR(20) NOT NULL,
    stat_time       TIMESTAMPTZ NOT NULL,
    window_minutes  INT NOT NULL,               -- 5, 10, 30, 60, 240 (4h)
    source_table    VARCHAR(20) NOT NULL,       -- 'scalp_1m_bars' or 'swing_bars_10m'

    -- Price Statistics
    price_mean      NUMERIC(15,4),              -- Average close price
    price_stddev    NUMERIC(15,4),              -- Standard deviation
    price_min       NUMERIC(15,4),              -- Period low
    price_max       NUMERIC(15,4),              -- Period high

    -- Return Statistics (log returns)
    return_mean     NUMERIC(10,8),              -- Average return
    return_stddev   NUMERIC(10,8),              -- Return volatility
    return_skew     NUMERIC(10,6),              -- Skewness (asymmetry)
    return_kurtosis NUMERIC(10,6),              -- Kurtosis (tail risk)

    -- Volatility Metrics
    atr_n           NUMERIC(15,4),              -- Average True Range (N periods)
    volatility_pct  NUMERIC(10,6),              -- Annualized volatility %
    high_low_range  NUMERIC(15,4),              -- max(high) - min(low)

    -- Volume Statistics
    volume_mean     BIGINT,                     -- Average volume
    volume_stddev   NUMERIC(20,4),              -- Volume standard deviation
    vwap            NUMERIC(15,4),              -- Volume-Weighted Average Price

    -- Data Quality
    bar_count       INT,                        -- Number of bars in window
    coverage_ratio  FLOAT,                      -- Data completeness (0.0-1.0)

    -- Metadata
    computed_at     TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (symbol, stat_time, window_minutes, source_table)
);

-- Indexes for time-series queries
CREATE INDEX idx_rolling_stats_time ON analysis_rolling_stats(stat_time DESC);
CREATE INDEX idx_rolling_stats_symbol_window ON analysis_rolling_stats(symbol, window_minutes, stat_time DESC);
CREATE INDEX idx_rolling_stats_volatility ON analysis_rolling_stats(volatility_pct DESC)
    WHERE volatility_pct IS NOT NULL;
```

**Usage**: Query volatility regimes, identify optimal trading windows, calculate position sizing parameters.

#### 2.2.2 analysis_threshold_candidates

Stores evaluated entry/exit threshold combinations with backtest metrics.

```sql
CREATE TABLE analysis_threshold_candidates (
    -- Primary Key
    candidate_id    BIGSERIAL PRIMARY KEY,

    -- Target
    symbol          VARCHAR(20) NOT NULL,
    strategy_type   VARCHAR(20) NOT NULL,       -- 'scalp', 'swing', 'portfolio'
    analysis_time   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Threshold Parameters (to optimize)
    entry_threshold_pct     NUMERIC(10,6) NOT NULL,  -- % move to trigger entry
    exit_threshold_pct      NUMERIC(10,6) NOT NULL,  -- % move to trigger exit
    stop_loss_pct           NUMERIC(10,6),           -- Stop-loss level %
    take_profit_pct         NUMERIC(10,6),           -- Take-profit level %
    holding_period_minutes  INT,                     -- Max hold time

    -- Backtest Period
    backtest_start  TIMESTAMPTZ NOT NULL,
    backtest_end    TIMESTAMPTZ NOT NULL,

    -- Performance Metrics
    total_trades    INT,                        -- Number of trades executed
    winning_trades  INT,                        -- Trades with positive P&L
    losing_trades   INT,                        -- Trades with negative P&L
    win_rate        NUMERIC(5,4),               -- winning_trades / total_trades

    -- Return Metrics
    total_return_pct    NUMERIC(10,6),          -- Cumulative return %
    avg_return_pct      NUMERIC(10,6),          -- Average return per trade
    max_return_pct      NUMERIC(10,6),          -- Best trade return
    min_return_pct      NUMERIC(10,6),          -- Worst trade return

    -- Risk Metrics
    profit_factor       NUMERIC(10,4),          -- Gross profit / Gross loss
    sharpe_ratio        NUMERIC(10,6),          -- Risk-adjusted return
    sortino_ratio       NUMERIC(10,6),          -- Downside risk-adjusted return
    max_drawdown_pct    NUMERIC(10,6),          -- Maximum peak-to-trough decline
    avg_drawdown_pct    NUMERIC(10,6),          -- Average drawdown

    -- Statistical Significance
    t_statistic         NUMERIC(10,6),          -- T-test statistic
    p_value             NUMERIC(10,8),          -- Statistical significance

    -- Configuration
    config_hash     VARCHAR(64),                -- Hash of full config for reproducibility
    session_id      VARCHAR(50),

    -- Ranking
    rank_score      NUMERIC(10,6),              -- Composite ranking score
    is_optimal      BOOLEAN DEFAULT FALSE       -- Best candidate for this symbol
);

-- Indexes for candidate selection
CREATE INDEX idx_threshold_candidates_symbol ON analysis_threshold_candidates(symbol, strategy_type);
CREATE INDEX idx_threshold_candidates_time ON analysis_threshold_candidates(analysis_time DESC);
CREATE INDEX idx_threshold_candidates_performance ON analysis_threshold_candidates(sharpe_ratio DESC, win_rate DESC)
    WHERE total_trades >= 30;  -- Minimum statistical significance
CREATE INDEX idx_threshold_candidates_optimal ON analysis_threshold_candidates(symbol, is_optimal)
    WHERE is_optimal = TRUE;
```

**Usage**: Store and compare multiple threshold parameter combinations, identify statistically-validated optimal parameters.

#### 2.2.3 analysis_signal_events

Captures signal frame events when conditions are met, enabling pattern analysis.

```sql
CREATE TABLE analysis_signal_events (
    -- Primary Key
    event_id        BIGSERIAL PRIMARY KEY,

    -- Event Identification
    symbol          VARCHAR(20) NOT NULL,
    event_time      TIMESTAMPTZ NOT NULL,
    source_table    VARCHAR(20) NOT NULL,       -- 'scalp_ticks', 'scalp_1m_bars', 'swing_bars_10m'

    -- Signal Frame Features (from signal_frame/pipeline.py)
    -- Time Features
    delta_t_prev            NUMERIC(15,6),      -- Seconds since previous event
    bucket_index            INT,                -- Time bucket index
    relative_position       NUMERIC(5,4),       -- Position in window [0..1]

    -- Frequency Features
    event_count_last_n      INT,                -- Events in sliding window
    event_density_last_n    NUMERIC(15,6),      -- Events per second
    same_pattern_streak     INT,                -- Consecutive same-pattern count

    -- Volatility Features
    value_diff_abs          NUMERIC(15,4),      -- |current - previous|
    value_diff_pct          NUMERIC(10,8),      -- Percentage change
    rolling_range_n         NUMERIC(15,4),      -- max - min in window

    -- Condition Flags (from signal_frame/conditions/)
    value_change_exceeds_x      BOOLEAN,        -- |change| > threshold (default: 1%)
    event_frequency_exceeds_n   BOOLEAN,        -- count > threshold (default: 20)
    consecutive_events_ge_n     BOOLEAN,        -- streak >= threshold (default: 3)
    pattern_reappeared_within_t BOOLEAN,        -- Pattern recurred within T seconds (default: 60s)

    -- Condition Parameters Used
    threshold_x             NUMERIC(10,6),      -- value_change threshold used
    threshold_n             INT,                -- frequency threshold used
    threshold_streak        INT,                -- consecutive threshold used
    threshold_t_seconds     NUMERIC(15,6),      -- pattern reappearance window

    -- Price Context
    price_at_signal         NUMERIC(15,4),      -- Price when signal fired
    bid_price               NUMERIC(15,4),
    ask_price               NUMERIC(15,4),
    spread_pct              NUMERIC(10,6),      -- (ask - bid) / mid

    -- Outcome Tracking (filled after signal)
    price_after_1m          NUMERIC(15,4),      -- Price 1 minute later
    price_after_5m          NUMERIC(15,4),      -- Price 5 minutes later
    price_after_10m         NUMERIC(15,4),      -- Price 10 minutes later
    return_1m_pct           NUMERIC(10,8),      -- Return 1 minute later
    return_5m_pct           NUMERIC(10,8),      -- Return 5 minutes later
    return_10m_pct          NUMERIC(10,8),      -- Return 10 minutes later

    -- Metadata
    config_version  VARCHAR(20) DEFAULT '1.0',
    session_id      VARCHAR(50),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for pattern analysis
CREATE INDEX idx_signal_events_symbol_time ON analysis_signal_events(symbol, event_time DESC);
CREATE INDEX idx_signal_events_conditions ON analysis_signal_events(
    value_change_exceeds_x,
    event_frequency_exceeds_n,
    consecutive_events_ge_n
) WHERE value_change_exceeds_x = TRUE OR consecutive_events_ge_n = TRUE;
CREATE INDEX idx_signal_events_outcome ON analysis_signal_events(return_5m_pct DESC)
    WHERE return_5m_pct IS NOT NULL;
```

**Usage**: Analyze which signal conditions predict positive returns, tune condition thresholds based on outcome data.

### 2.3 Schema Enhancements to Existing Tables

#### 2.3.1 Add Computed Spread Column to scalp_ticks

```sql
-- Add spread as stored generated column (PostgreSQL 12+)
ALTER TABLE scalp_ticks
    ADD COLUMN IF NOT EXISTS spread NUMERIC(15,4)
    GENERATED ALWAYS AS (ask_price - bid_price) STORED;

-- Add spread percentage for relative comparison
ALTER TABLE scalp_ticks
    ADD COLUMN IF NOT EXISTS spread_pct NUMERIC(10,8)
    GENERATED ALWAYS AS (
        CASE WHEN (bid_price + ask_price) > 0
        THEN (ask_price - bid_price) / ((bid_price + ask_price) / 2)
        ELSE NULL END
    ) STORED;
```

#### 2.3.2 Add Returns Column to swing_bars_10m

```sql
-- Add returns column (computed via trigger since it references previous row)
ALTER TABLE swing_bars_10m
    ADD COLUMN IF NOT EXISTS returns_pct NUMERIC(10,8);

-- Trigger function to compute returns on INSERT
CREATE OR REPLACE FUNCTION compute_swing_returns()
RETURNS TRIGGER AS $$
DECLARE
    prev_close NUMERIC(15,4);
BEGIN
    -- Get previous close for same symbol
    SELECT close INTO prev_close
    FROM swing_bars_10m
    WHERE symbol = NEW.symbol
      AND bar_time < NEW.bar_time
    ORDER BY bar_time DESC
    LIMIT 1;

    -- Calculate return
    IF prev_close IS NOT NULL AND prev_close > 0 THEN
        NEW.returns_pct := (NEW.close - prev_close) / prev_close;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trg_compute_swing_returns ON swing_bars_10m;
CREATE TRIGGER trg_compute_swing_returns
    BEFORE INSERT ON swing_bars_10m
    FOR EACH ROW
    EXECUTE FUNCTION compute_swing_returns();
```

---

## 3️⃣ Indexing & Query Optimization

### 3.1 Composite Index Strategy

| Table | Index Name | Columns | Purpose |
|-------|------------|---------|---------|
| swing_bars_10m | `idx_swing_10m_covering` | `(symbol, bar_time DESC) INCLUDE (open, high, low, close, volume)` | Covering index for OHLCV scans - avoids heap access |
| swing_bars_10m | `idx_swing_10m_quality` | `(symbol, bar_time DESC) WHERE quality_flag='normal' AND mitigation_level=0` | Quality-filtered analysis queries |
| scalp_ticks | `idx_scalp_ticks_hot` | `(symbol, event_time DESC) WHERE event_time > NOW() - '7 days'` | Partial index for hot data |
| scalp_ticks | `idx_scalp_ticks_brin` | `BRIN(event_time) WITH (pages_per_range=128)` | Space-efficient for cold time-ordered data |
| scalp_1m_bars | `idx_scalp_1m_coverage` | `(symbol, bar_time DESC, coverage_ratio)` | Filter by data quality |

```sql
-- Create covering index for swing data (most common analysis pattern)
CREATE INDEX CONCURRENTLY idx_swing_10m_covering
    ON swing_bars_10m(symbol, bar_time DESC)
    INCLUDE (open, high, low, close, volume, returns_pct);

-- Create partial index for recent scalp data
CREATE INDEX CONCURRENTLY idx_scalp_ticks_hot
    ON scalp_ticks(symbol, event_time DESC)
    WHERE event_time > NOW() - INTERVAL '7 days';

-- Create BRIN index for historical scalp data (very space-efficient)
CREATE INDEX CONCURRENTLY idx_scalp_ticks_brin
    ON scalp_ticks USING BRIN(event_time)
    WITH (pages_per_range = 128);

-- Quality-filtered swing index
CREATE INDEX CONCURRENTLY idx_swing_10m_quality
    ON swing_bars_10m(symbol, bar_time DESC)
    WHERE quality_flag = 'normal' AND mitigation_level = 0;

-- Coverage-based scalp_1m_bars index
CREATE INDEX CONCURRENTLY idx_scalp_1m_coverage
    ON scalp_1m_bars(symbol, bar_time DESC, coverage_ratio)
    WHERE coverage_ratio >= 0.75;  -- Grade B or better
```

### 3.2 Partitioning Recommendations

**Strategy: Native PostgreSQL Range Partitioning by Month**

Rationale for avoiding TimescaleDB:
- Docker container has limited resources (1GB memory)
- Simpler operational model without extensions
- Native partitioning sufficient for expected data volumes (~1M rows/month)

```sql
-- Create partitioned scalp_ticks table
CREATE TABLE scalp_ticks_partitioned (
    id              BIGSERIAL,
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
    quality_flag    VARCHAR(20) DEFAULT 'normal',
    spread          NUMERIC(15,4) GENERATED ALWAYS AS (ask_price - bid_price) STORED,
    spread_pct      NUMERIC(10,8) GENERATED ALWAYS AS (
        CASE WHEN (bid_price + ask_price) > 0
        THEN (ask_price - bid_price) / ((bid_price + ask_price) / 2)
        ELSE NULL END
    ) STORED,
    PRIMARY KEY (id, event_time)
) PARTITION BY RANGE (event_time);

-- Function to auto-create monthly partitions
CREATE OR REPLACE FUNCTION create_monthly_partition(
    table_name TEXT,
    partition_date DATE
) RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    partition_name := table_name || '_' || TO_CHAR(partition_date, 'YYYYMM');
    start_date := DATE_TRUNC('month', partition_date);
    end_date := start_date + INTERVAL '1 month';

    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, table_name, start_date, end_date
    );

    -- Create partition-local indexes
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I ON %I (symbol, event_time DESC)',
        partition_name || '_symbol_time_idx', partition_name
    );

    RAISE NOTICE 'Created partition: %', partition_name;
END;
$$ LANGUAGE plpgsql;

-- Create current and next month partitions
SELECT create_monthly_partition('scalp_ticks_partitioned', CURRENT_DATE);
SELECT create_monthly_partition('scalp_ticks_partitioned', CURRENT_DATE + INTERVAL '1 month');
```

### 3.3 Partition Maintenance Jobs

```sql
-- Create partition maintenance tracking table
CREATE TABLE partition_management (
    table_name          VARCHAR(100) PRIMARY KEY,
    hot_retention_days  INT DEFAULT 7,
    cold_retention_days INT DEFAULT 90,
    archive_enabled     BOOLEAN DEFAULT FALSE,
    last_maintenance    TIMESTAMPTZ,
    next_partition_date DATE
);

INSERT INTO partition_management VALUES
    ('scalp_ticks_partitioned', 7, 30, FALSE, NOW(), DATE_TRUNC('month', NOW() + INTERVAL '1 month')),
    ('scalp_1m_bars', 30, 180, TRUE, NOW(), NULL),
    ('swing_bars_10m', 90, 365, TRUE, NOW(), NULL);

-- Monthly maintenance function (run after market close)
CREATE OR REPLACE FUNCTION maintain_partitions()
RETURNS VOID AS $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN SELECT * FROM partition_management LOOP
        -- Create next month's partition if needed
        IF rec.next_partition_date IS NOT NULL AND
           rec.next_partition_date <= CURRENT_DATE + INTERVAL '7 days' THEN
            PERFORM create_monthly_partition(rec.table_name, rec.next_partition_date);

            UPDATE partition_management
            SET next_partition_date = rec.next_partition_date + INTERVAL '1 month',
                last_maintenance = NOW()
            WHERE table_name = rec.table_name;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

---

## 4️⃣ Analysis Logic: Parameter Derivation Program

### 4.1 Rolling Volatility Computation

```sql
-- Materialized view for rolling statistics (refresh hourly during market hours)
CREATE MATERIALIZED VIEW mv_rolling_stats_hourly AS
WITH base_data AS (
    SELECT
        symbol,
        bar_time,
        open, high, low, close, volume,
        LAG(close) OVER (PARTITION BY symbol ORDER BY bar_time) as prev_close,
        (high - low) as true_range  -- Simplified ATR component
    FROM swing_bars_10m
    WHERE bar_time >= NOW() - INTERVAL '90 days'
      AND quality_flag = 'normal'
),
returns AS (
    SELECT
        symbol,
        bar_time,
        close,
        volume,
        true_range,
        (close - prev_close) / NULLIF(prev_close, 0) as returns
    FROM base_data
    WHERE prev_close IS NOT NULL AND prev_close > 0
)
SELECT
    symbol,
    DATE_TRUNC('hour', bar_time) as stat_hour,
    10 as window_minutes,  -- 10-minute source bars
    'swing_bars_10m' as source_table,

    -- Price stats
    AVG(close) as price_mean,
    STDDEV(close) as price_stddev,
    MIN(close) as price_min,
    MAX(close) as price_max,

    -- Return stats
    AVG(returns) as return_mean,
    STDDEV(returns) as return_stddev,

    -- Volatility (annualized: 252 days * 6.5 hours * 6 bars/hour)
    STDDEV(returns) * SQRT(252 * 6.5 * 6) as volatility_pct,
    AVG(true_range) as atr_n,

    -- Volume
    AVG(volume) as volume_mean,
    STDDEV(volume) as volume_stddev,

    -- Quality
    COUNT(*) as bar_count,
    1.0 as coverage_ratio

FROM returns
GROUP BY symbol, DATE_TRUNC('hour', bar_time);

CREATE UNIQUE INDEX idx_mv_rolling_stats ON mv_rolling_stats_hourly(symbol, stat_hour);

-- Refresh command (run via pg_cron or external scheduler)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_rolling_stats_hourly;
```

### 4.2 Optimal Threshold Calculation Query

```sql
-- Find optimal entry/exit thresholds via grid search backtest
WITH threshold_grid AS (
    -- Generate threshold combinations to test
    SELECT
        entry_pct,
        exit_pct
    FROM
        generate_series(0.005, 0.03, 0.005) as entry_pct,  -- 0.5% to 3%
        generate_series(0.003, 0.02, 0.002) as exit_pct    -- 0.3% to 2%
    WHERE exit_pct < entry_pct  -- Exit threshold should be smaller
),
price_moves AS (
    SELECT
        symbol,
        bar_time,
        close,
        LAG(close) OVER w as prev_close,
        (close - LAG(close) OVER w) / NULLIF(LAG(close) OVER w, 0) as returns,
        LEAD(close, 6) OVER w as price_1h_later,  -- 6 bars = 1 hour
        LEAD(close, 36) OVER w as price_6h_later  -- 36 bars = 6 hours
    FROM swing_bars_10m
    WHERE symbol = '005930'  -- Test symbol
      AND bar_time BETWEEN '2026-01-01' AND '2026-01-28'
      AND quality_flag = 'normal'
    WINDOW w AS (ORDER BY bar_time)
),
backtest AS (
    SELECT
        tg.entry_pct,
        tg.exit_pct,
        pm.bar_time as entry_time,
        pm.close as entry_price,
        pm.returns as signal_return,
        pm.price_1h_later,
        CASE
            WHEN ABS(pm.returns) >= tg.entry_pct THEN
                CASE
                    WHEN pm.returns > 0 THEN 'SHORT'  -- Price went up, expect mean reversion
                    ELSE 'LONG'
                END
            ELSE NULL
        END as signal_direction,
        -- Calculate P&L based on direction
        CASE
            WHEN pm.returns > tg.entry_pct THEN
                (pm.close - pm.price_1h_later) / pm.close  -- SHORT P&L
            WHEN pm.returns < -tg.entry_pct THEN
                (pm.price_1h_later - pm.close) / pm.close  -- LONG P&L
            ELSE NULL
        END as trade_return
    FROM threshold_grid tg
    CROSS JOIN price_moves pm
    WHERE pm.price_1h_later IS NOT NULL
      AND pm.returns IS NOT NULL
)
SELECT
    entry_pct,
    exit_pct,
    COUNT(*) as total_trades,
    SUM(CASE WHEN trade_return > 0 THEN 1 ELSE 0 END) as winning_trades,
    ROUND(SUM(CASE WHEN trade_return > 0 THEN 1 ELSE 0 END)::NUMERIC /
          NULLIF(COUNT(*), 0), 4) as win_rate,
    ROUND(AVG(trade_return) * 100, 4) as avg_return_pct,
    ROUND(STDDEV(trade_return), 6) as return_stddev,
    ROUND(AVG(trade_return) / NULLIF(STDDEV(trade_return), 0), 4) as sharpe_approx,
    ROUND(SUM(CASE WHEN trade_return > 0 THEN trade_return ELSE 0 END) /
          NULLIF(-SUM(CASE WHEN trade_return < 0 THEN trade_return ELSE 0 END), 0), 4) as profit_factor
FROM backtest
WHERE signal_direction IS NOT NULL
GROUP BY entry_pct, exit_pct
HAVING COUNT(*) >= 30  -- Minimum trades for statistical significance
ORDER BY sharpe_approx DESC, win_rate DESC
LIMIT 20;
```

### 4.3 Signal Event Detection Query

```sql
-- Detect and log signal events based on configured thresholds
INSERT INTO analysis_signal_events (
    symbol, event_time, source_table,
    delta_t_prev, bucket_index, relative_position,
    event_count_last_n, event_density_last_n, same_pattern_streak,
    value_diff_abs, value_diff_pct, rolling_range_n,
    value_change_exceeds_x, event_frequency_exceeds_n,
    consecutive_events_ge_n, pattern_reappeared_within_t,
    threshold_x, threshold_n, threshold_streak, threshold_t_seconds,
    price_at_signal, bid_price, ask_price, spread_pct
)
WITH params AS (
    -- Configurable thresholds (from SignalFrameConfig)
    SELECT
        0.01 as threshold_x,        -- 1% price change
        20 as threshold_n,          -- 20 events in window
        3 as threshold_streak,      -- 3 consecutive same direction
        60.0 as threshold_t,        -- 60 second pattern window
        20 as window_n              -- 20-bar sliding window
),
windowed_data AS (
    SELECT
        t.symbol,
        t.event_time,
        'scalp_ticks' as source_table,
        EXTRACT(EPOCH FROM (t.event_time - LAG(t.event_time) OVER w)) as delta_t_prev,
        ROW_NUMBER() OVER w as bucket_index,
        t.last_price,
        t.bid_price,
        t.ask_price,
        LAG(t.last_price) OVER w as prev_price,
        COUNT(*) OVER (PARTITION BY t.symbol ORDER BY t.event_time
                       ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as event_count_last_n,
        MAX(t.last_price) OVER (PARTITION BY t.symbol ORDER BY t.event_time
                                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) -
        MIN(t.last_price) OVER (PARTITION BY t.symbol ORDER BY t.event_time
                                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as rolling_range_n,
        -- Direction tracking for streak
        SIGN(t.last_price - LAG(t.last_price) OVER w) as direction
    FROM scalp_ticks t
    WHERE t.event_time >= NOW() - INTERVAL '1 hour'
      AND t.quality_flag = 'normal'
    WINDOW w AS (PARTITION BY t.symbol ORDER BY t.event_time)
)
SELECT
    wd.symbol,
    wd.event_time,
    wd.source_table,
    wd.delta_t_prev,
    wd.bucket_index,
    wd.bucket_index::FLOAT / NULLIF(p.window_n, 0) as relative_position,
    wd.event_count_last_n,
    CASE WHEN wd.delta_t_prev > 0
         THEN wd.event_count_last_n / (wd.delta_t_prev * p.window_n)
         ELSE NULL END as event_density_last_n,
    1 as same_pattern_streak,  -- Simplified; full implementation in Python
    ABS(wd.last_price - wd.prev_price) as value_diff_abs,
    (wd.last_price - wd.prev_price) / NULLIF(wd.prev_price, 0) as value_diff_pct,
    wd.rolling_range_n,
    -- Condition evaluations
    ABS((wd.last_price - wd.prev_price) / NULLIF(wd.prev_price, 0)) >= p.threshold_x as value_change_exceeds_x,
    wd.event_count_last_n >= p.threshold_n as event_frequency_exceeds_n,
    FALSE as consecutive_events_ge_n,  -- Requires full streak calculation
    FALSE as pattern_reappeared_within_t,  -- Requires pattern matching
    -- Thresholds used
    p.threshold_x,
    p.threshold_n,
    p.threshold_streak,
    p.threshold_t,
    -- Price context
    wd.last_price as price_at_signal,
    wd.bid_price,
    wd.ask_price,
    (wd.ask_price - wd.bid_price) / NULLIF((wd.bid_price + wd.ask_price) / 2, 0) as spread_pct
FROM windowed_data wd
CROSS JOIN params p
WHERE wd.prev_price IS NOT NULL
  AND (
      -- At least one condition must be met to log as signal event
      ABS((wd.last_price - wd.prev_price) / NULLIF(wd.prev_price, 0)) >= p.threshold_x
      OR wd.event_count_last_n >= p.threshold_n
  );
```

### 4.4 Consecutive Pattern Detection

```sql
-- Find consecutive price movements (for consecutive_events_ge_n condition)
WITH price_directions AS (
    SELECT
        symbol,
        bar_time,
        close,
        CASE
            WHEN close > LAG(close) OVER (PARTITION BY symbol ORDER BY bar_time) THEN 1
            WHEN close < LAG(close) OVER (PARTITION BY symbol ORDER BY bar_time) THEN -1
            ELSE 0
        END as direction,
        ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY bar_time) as rn
    FROM swing_bars_10m
    WHERE bar_time >= NOW() - INTERVAL '7 days'
      AND quality_flag = 'normal'
),
streak_groups AS (
    SELECT
        symbol,
        bar_time,
        close,
        direction,
        rn,
        rn - ROW_NUMBER() OVER (PARTITION BY symbol, direction ORDER BY bar_time) as grp
    FROM price_directions
    WHERE direction != 0
),
streaks AS (
    SELECT
        symbol,
        direction,
        MIN(bar_time) as streak_start,
        MAX(bar_time) as streak_end,
        COUNT(*) as streak_length,
        MIN(close) as streak_low,
        MAX(close) as streak_high
    FROM streak_groups
    GROUP BY symbol, grp, direction
    HAVING COUNT(*) >= 3  -- consecutive_events_ge_n threshold
)
SELECT
    symbol,
    CASE direction WHEN 1 THEN 'UP' WHEN -1 THEN 'DOWN' END as direction,
    streak_start,
    streak_end,
    streak_length,
    ROUND((streak_high - streak_low) / streak_low * 100, 2) as move_pct
FROM streaks
ORDER BY streak_length DESC, symbol
LIMIT 100;
```

---

## 5️⃣ Performance Optimization

### 5.1 PostgreSQL Configuration (1GB Container)

```ini
# postgresql.conf optimizations for Observer workload

# Memory (256MB total for PG buffers)
shared_buffers = 128MB              # 12.5% of 1GB container
effective_cache_size = 512MB        # 50% of total memory
work_mem = 8MB                      # Per-sort operation
maintenance_work_mem = 64MB         # For VACUUM, CREATE INDEX

# Write-Ahead Log (high-frequency tick writes)
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 256MB
min_wal_size = 64MB

# Connection handling
max_connections = 50                # Pool max (10) * 3 + overhead

# Query planning
random_page_cost = 1.1              # SSD storage assumed
effective_io_concurrency = 200      # SSD parallelism

# Autovacuum (tune for write-heavy scalp_ticks)
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_scale_factor = 0.05
autovacuum_naptime = 30s
```

### 5.2 Connection Pool Configuration

```python
# Enhanced pool configuration for mixed workloads
POOL_CONFIG = {
    # Write-heavy pool (Track B scalp data)
    "writer_pool": {
        "min_size": 2,
        "max_size": 5,
        "max_queries": 50000,
        "max_inactive_connection_lifetime": 300.0,  # 5 minutes
        "command_timeout": 30.0,
    },
    # Read-heavy pool (Analysis queries)
    "reader_pool": {
        "min_size": 1,
        "max_size": 3,
        "max_queries": 10000,
        "max_inactive_connection_lifetime": 600.0,  # 10 minutes
        "command_timeout": 120.0,  # Longer timeout for analytics
    }
}
```

### 5.3 Batched Write Implementation

```python
class BatchedRealtimeDBWriter:
    """
    High-performance batched writer for scalp tick data.
    Uses asyncpg COPY protocol for 10x faster inserts.
    """

    def __init__(
        self,
        pool: asyncpg.Pool,
        batch_size: int = 100,
        flush_interval_ms: float = 500.0
    ):
        self._pool = pool
        self._batch: List[Tuple] = []
        self._batch_size = batch_size
        self._flush_interval_ms = flush_interval_ms
        self._last_flush = time.monotonic()
        self._lock = asyncio.Lock()
        self._columns = [
            'symbol', 'event_time', 'bid_price', 'ask_price',
            'bid_size', 'ask_size', 'last_price', 'volume',
            'session_id', 'mitigation_level', 'quality_flag'
        ]

    async def save_scalp_tick(self, data: Dict[str, Any], session_id: str) -> bool:
        """Add tick to batch, auto-flush when batch full or time elapsed."""
        record = (
            data.get('symbol'),
            data.get('event_time'),
            data.get('bid_price'),
            data.get('ask_price'),
            data.get('bid_size'),
            data.get('ask_size'),
            data.get('last_price'),
            data.get('volume'),
            session_id,
            data.get('mitigation_level', 0),
            data.get('quality_flag', 'normal')
        )

        async with self._lock:
            self._batch.append(record)

            should_flush = (
                len(self._batch) >= self._batch_size or
                (time.monotonic() - self._last_flush) * 1000 >= self._flush_interval_ms
            )

            if should_flush:
                return await self._flush_batch()
        return True

    async def _flush_batch(self) -> bool:
        """Execute batched INSERT using COPY protocol."""
        if not self._batch:
            return True

        batch_to_flush = self._batch.copy()
        self._batch.clear()
        self._last_flush = time.monotonic()

        try:
            async with self._pool.acquire() as conn:
                await conn.copy_records_to_table(
                    'scalp_ticks',
                    records=batch_to_flush,
                    columns=self._columns
                )
            return True
        except Exception as e:
            logger.error(f"Batch flush failed ({len(batch_to_flush)} records): {e}")
            # Re-queue failed records for retry
            self._batch = batch_to_flush + self._batch
            return False

    async def flush(self) -> bool:
        """Force flush remaining batch (call on shutdown)."""
        async with self._lock:
            return await self._flush_batch()
```

---

## 6️⃣ Verification Plan

### 6.1 Schema Verification

```sql
-- Verify all tables exist with correct structure
SELECT
    table_name,
    COUNT(*) as column_count
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN (
      'scalp_ticks', 'scalp_1m_bars', 'scalp_gaps',
      'swing_bars_10m',
      'portfolio_policy', 'target_weights', 'portfolio_snapshot',
      'portfolio_positions', 'rebalance_plan', 'rebalance_orders', 'rebalance_execution',
      'migration_log',
      'analysis_rolling_stats', 'analysis_threshold_candidates', 'analysis_signal_events'
  )
GROUP BY table_name
ORDER BY table_name;

-- Expected: 15 tables (12 existing + 3 new analysis tables)

-- Verify index count
SELECT
    tablename,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY index_count DESC;

-- Expected: 25+ indexes
```

### 6.2 Data Integrity Verification

```sql
-- Check for time-series gaps in swing data
SELECT
    symbol,
    bar_time,
    LAG(bar_time) OVER (PARTITION BY symbol ORDER BY bar_time) as prev_bar_time,
    EXTRACT(EPOCH FROM (bar_time - LAG(bar_time) OVER (PARTITION BY symbol ORDER BY bar_time))) / 60 as gap_minutes
FROM swing_bars_10m
WHERE quality_flag = 'normal'
  AND bar_time >= NOW() - INTERVAL '7 days'
HAVING EXTRACT(EPOCH FROM (bar_time - LAG(bar_time) OVER (PARTITION BY symbol ORDER BY bar_time))) / 60 > 15
ORDER BY gap_minutes DESC
LIMIT 20;

-- Check quality flag distribution
SELECT
    DATE_TRUNC('day', bar_time) as day,
    quality_flag,
    COUNT(*) as record_count,
    COUNT(DISTINCT symbol) as symbol_count
FROM swing_bars_10m
WHERE bar_time >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('day', bar_time), quality_flag
ORDER BY day DESC, quality_flag;

-- Check coverage ratio distribution for scalp_1m_bars
SELECT
    CASE
        WHEN coverage_ratio >= 0.9 THEN 'A (90-100%)'
        WHEN coverage_ratio >= 0.75 THEN 'B (75-90%)'
        WHEN coverage_ratio >= 0.5 THEN 'C (50-75%)'
        ELSE 'D (<50%)'
    END as quality_grade,
    COUNT(*) as bar_count,
    ROUND(AVG(coverage_ratio), 3) as avg_coverage
FROM scalp_1m_bars
WHERE bar_time >= NOW() - INTERVAL '7 days'
GROUP BY quality_grade
ORDER BY quality_grade;
```

### 6.3 Performance Verification

```sql
-- Verify index usage for common queries
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT symbol, bar_time, close, returns_pct
FROM swing_bars_10m
WHERE symbol = '005930'
  AND bar_time >= NOW() - INTERVAL '30 days'
  AND quality_flag = 'normal'
ORDER BY bar_time DESC
LIMIT 100;

-- Expected: Index Scan using idx_swing_10m_covering or idx_swing_10m_quality
-- Actual rows should be < 10% of total table rows

-- Verify analysis query performance (target: < 5 seconds)
EXPLAIN (ANALYZE, TIMING)
SELECT
    symbol,
    STDDEV((close - LAG(close) OVER w) / NULLIF(LAG(close) OVER w, 0)) as return_vol
FROM swing_bars_10m
WHERE bar_time >= NOW() - INTERVAL '30 days'
  AND quality_flag = 'normal'
WINDOW w AS (PARTITION BY symbol ORDER BY bar_time)
GROUP BY symbol;
```

### 6.4 Integration Test Checklist

| Test | Query/Action | Expected Result |
|------|--------------|-----------------|
| Rolling stats populated | `SELECT COUNT(*) FROM analysis_rolling_stats` | > 0 after first refresh |
| Threshold optimization | Run grid search query | Returns ranked candidates with valid metrics |
| Signal events logged | `SELECT COUNT(*) FROM analysis_signal_events WHERE event_time >= NOW() - '1 hour'` | > 0 during market hours |
| Batch write performance | Insert 1000 ticks via BatchedWriter | < 200ms total |
| Materialized view refresh | `REFRESH MATERIALIZED VIEW CONCURRENTLY mv_rolling_stats_hourly` | Completes < 30 seconds |

---

## 7️⃣ Implementation Checklist

### Phase 14.1: Schema Enhancement
- [ ] Create `004_create_analysis_tables.sql`
- [ ] Add `spread` and `spread_pct` columns to `scalp_ticks`
- [ ] Add `returns_pct` column and trigger to `swing_bars_10m`
- [ ] Create new composite indexes
- [ ] Run migrations

### Phase 14.2: Partitioning Setup
- [ ] Create `scalp_ticks_partitioned` table
- [ ] Implement `create_monthly_partition()` function
- [ ] Set up partition management table
- [ ] Create initial partitions (current + next month)
- [ ] Plan data migration from `scalp_ticks` to partitioned table

### Phase 14.3: Query Layer
- [ ] Create `mv_rolling_stats_hourly` materialized view
- [ ] Implement threshold optimization stored procedure
- [ ] Create signal event detection query/procedure
- [ ] Set up refresh schedule (pg_cron or external)

### Phase 14.4: Writer Optimization
- [ ] Implement `BatchedRealtimeDBWriter` class
- [ ] Add reader/writer pool separation
- [ ] Update `realtime_writer.py` with batching
- [ ] Configure PostgreSQL parameters

### Phase 14.5: Verification
- [ ] Run schema verification queries
- [ ] Execute data integrity checks
- [ ] Performance test analysis queries (< 5s target)
- [ ] End-to-end integration test

---

## 📚 Appendix

### A. File References

| File | Purpose |
|------|---------|
| `app/observer/src/db/schema/004_create_analysis_tables.sql` | New analysis schema |
| `infra/_shared/migrations/004_create_analysis_tables.sql` | Docker init migration |
| `app/observer/src/db/realtime_writer.py` | Batched writer implementation |
| `app/observer/src/db/models.py` | Pydantic models for analysis tables |
| `app/observer/src/observer/analysis/signal_frame/pipeline.py` | Signal frame integration point |

### B. Related Documents

- [[DB_MIGRATION_INTEGRATION_GUIDE.md]] - Phase 13 schema foundation
- [[observer_architecture_v2.md]] - Overall system architecture
- [[data_pipeline_architecture_observer_v1.0.md]] - Data pipeline design
- [[kis_api_specification_v1.0.md]] - Kiwoom API reference

### C. Glossary

| Term | Definition |
|------|------------|
| ATR | Average True Range - volatility indicator |
| Coverage Ratio | Data completeness metric (0.0-1.0) |
| Hot Zone | Recent data (0-7 days) with optimized access |
| Cold Zone | Historical data (7-90 days) with space-efficient storage |
| Profit Factor | Gross profit / Gross loss ratio |
| Sharpe Ratio | Risk-adjusted return metric |
| Signal Frame | Pipeline for extracting trading signals from raw data |

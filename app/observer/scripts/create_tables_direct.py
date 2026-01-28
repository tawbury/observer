"""
Create all DB tables using SQL statements directly in Python
This approach avoids parsing issues with SQL files
"""
import asyncio
import asyncpg
import sys


async def create_all_tables():
    """Create all tables directly using SQL"""
    
    # Database connection parameters
    db_config = {
        'host': 'localhost',  # Will be 'postgres' in Docker
        'port': 5432,
        'user': 'postgres',
        'password': 'observer_db_pwd',
        'database': 'observer'
    }
    
    # Get host from environment or use 'postgres' for Docker
    import os
    if os.getenv('DB_HOST'):
        db_config['host'] = os.getenv('DB_HOST')
    
    # SQL statements to create all tables
    create_tables_sql = """
    -- Drop existing tables for idempotency
    DROP TABLE IF EXISTS rebalance_orders CASCADE;
    DROP TABLE IF EXISTS rebalance_execution CASCADE;
    DROP TABLE IF EXISTS rebalance_plan CASCADE;
    DROP TABLE IF EXISTS portfolio_positions CASCADE;
    DROP TABLE IF EXISTS portfolio_snapshot CASCADE;
    DROP TABLE IF EXISTS target_weights CASCADE;
    DROP TABLE IF EXISTS portfolio_policy CASCADE;
    DROP TABLE IF EXISTS migration_log CASCADE;
    DROP TABLE IF EXISTS scalp_gaps CASCADE;
    DROP TABLE IF EXISTS scalp_1m_bars CASCADE;
    DROP TABLE IF EXISTS scalp_ticks CASCADE;
    DROP TABLE IF EXISTS swing_bars_10m CASCADE;
    
    -- ======================================================================
    -- Scalp Tables
    -- ======================================================================
    CREATE TABLE scalp_ticks (
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
    
    CREATE INDEX idx_scalp_ticks_symbol ON scalp_ticks(symbol);
    CREATE INDEX idx_scalp_ticks_event_time ON scalp_ticks(event_time DESC);
    CREATE INDEX idx_scalp_ticks_session ON scalp_ticks(session_id);
    
    CREATE TABLE scalp_1m_bars (
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
    
    CREATE INDEX idx_scalp_1m_bars_symbol ON scalp_1m_bars(symbol);
    CREATE INDEX idx_scalp_1m_bars_time ON scalp_1m_bars(bar_time DESC);
    CREATE INDEX idx_scalp_1m_bars_session ON scalp_1m_bars(session_id);
    
    CREATE TABLE scalp_gaps (
        id              SERIAL PRIMARY KEY,
        gap_start_ts    TIMESTAMPTZ NOT NULL,
        gap_end_ts      TIMESTAMPTZ NOT NULL,
        gap_seconds     INT NOT NULL,
        scope           VARCHAR(20),
        reason          VARCHAR(100),
        session_id      VARCHAR(50) NOT NULL
    );
    
    CREATE INDEX idx_scalp_gaps_session ON scalp_gaps(session_id);
    CREATE INDEX idx_scalp_gaps_time ON scalp_gaps(gap_start_ts DESC);
    
    -- ======================================================================
    -- Swing Tables
    -- ======================================================================
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
    
    CREATE INDEX idx_swing_10m_symbol ON swing_bars_10m(symbol);
    CREATE INDEX idx_swing_10m_time ON swing_bars_10m(bar_time DESC);
    CREATE INDEX idx_swing_10m_session ON swing_bars_10m(session_id);
    CREATE INDEX idx_swing_10m_bid_ask ON swing_bars_10m(symbol, bar_time, bid_price, ask_price);
    
    -- ======================================================================
    -- Portfolio Tables
    -- ======================================================================
    CREATE TABLE portfolio_policy (
        policy_id           VARCHAR(50) PRIMARY KEY,
        policy_name         VARCHAR(100) NOT NULL,
        created_at          TIMESTAMPTZ DEFAULT NOW(),
        rebalance_threshold FLOAT DEFAULT 0.05,
        rebalance_frequency VARCHAR(20) DEFAULT 'monthly',
        is_active           BOOLEAN DEFAULT TRUE
    );
    
    CREATE TABLE target_weights (
        policy_id           VARCHAR(50) NOT NULL,
        symbol              VARCHAR(20) NOT NULL,
        target_weight       FLOAT NOT NULL,
        updated_at          TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (policy_id, symbol),
        FOREIGN KEY (policy_id) REFERENCES portfolio_policy(policy_id)
    );
    
    CREATE INDEX idx_target_weights_policy ON target_weights(policy_id);
    
    CREATE TABLE portfolio_snapshot (
        snapshot_id         BIGSERIAL PRIMARY KEY,
        policy_id           VARCHAR(50) NOT NULL,
        snapshot_time       TIMESTAMPTZ NOT NULL,
        total_value         NUMERIC(20,4),
        cash                NUMERIC(20,4),
        created_at          TIMESTAMPTZ DEFAULT NOW(),
        FOREIGN KEY (policy_id) REFERENCES portfolio_policy(policy_id)
    );
    
    CREATE INDEX idx_portfolio_snapshot_policy ON portfolio_snapshot(policy_id);
    CREATE INDEX idx_portfolio_snapshot_time ON portfolio_snapshot(snapshot_time DESC);
    
    CREATE TABLE portfolio_positions (
        position_id         BIGSERIAL PRIMARY KEY,
        snapshot_id         BIGINT NOT NULL,
        symbol              VARCHAR(20) NOT NULL,
        quantity            BIGINT,
        market_price        NUMERIC(15,4),
        market_value        NUMERIC(20,4),
        current_weight      FLOAT,
        target_weight       FLOAT,
        weight_diff         FLOAT,
        FOREIGN KEY (snapshot_id) REFERENCES portfolio_snapshot(snapshot_id)
    );
    
    CREATE INDEX idx_portfolio_positions_snapshot ON portfolio_positions(snapshot_id);
    CREATE INDEX idx_portfolio_positions_symbol ON portfolio_positions(symbol);
    
    CREATE TABLE rebalance_plan (
        plan_id             BIGSERIAL PRIMARY KEY,
        policy_id           VARCHAR(50) NOT NULL,
        snapshot_id         BIGINT NOT NULL,
        status              VARCHAR(20) DEFAULT 'pending',
        reason              TEXT,
        created_at          TIMESTAMPTZ DEFAULT NOW(),
        completed_at        TIMESTAMPTZ,
        FOREIGN KEY (policy_id) REFERENCES portfolio_policy(policy_id),
        FOREIGN KEY (snapshot_id) REFERENCES portfolio_snapshot(snapshot_id)
    );
    
    CREATE INDEX idx_rebalance_plan_policy ON rebalance_plan(policy_id);
    CREATE INDEX idx_rebalance_plan_status ON rebalance_plan(status);
    
    CREATE TABLE rebalance_orders (
        order_id            BIGSERIAL PRIMARY KEY,
        plan_id             BIGINT NOT NULL,
        symbol              VARCHAR(20) NOT NULL,
        side                VARCHAR(10) NOT NULL,
        target_qty          BIGINT,
        order_type          VARCHAR(20) DEFAULT 'MARKET',
        status              VARCHAR(20) DEFAULT 'pending',
        created_at          TIMESTAMPTZ DEFAULT NOW(),
        FOREIGN KEY (plan_id) REFERENCES rebalance_plan(plan_id)
    );
    
    CREATE INDEX idx_rebalance_orders_plan ON rebalance_orders(plan_id);
    CREATE INDEX idx_rebalance_orders_symbol ON rebalance_orders(symbol);
    
    CREATE TABLE rebalance_execution (
        exec_id             BIGSERIAL PRIMARY KEY,
        order_id            BIGINT NOT NULL,
        filled_qty          BIGINT,
        filled_price        NUMERIC(15,4),
        exec_time           TIMESTAMPTZ,
        commission          NUMERIC(20,4),
        slippage            NUMERIC(20,4),
        status              VARCHAR(20),
        error_msg           TEXT,
        created_at          TIMESTAMPTZ DEFAULT NOW(),
        FOREIGN KEY (order_id) REFERENCES rebalance_orders(order_id)
    );
    
    CREATE INDEX idx_rebalance_execution_order ON rebalance_execution(order_id);
    
    -- ======================================================================
    -- Migration Log
    -- ======================================================================
    CREATE TABLE migration_log (
        id              SERIAL PRIMARY KEY,
        migration_name  VARCHAR(100) NOT NULL,
        executed_at     TIMESTAMPTZ DEFAULT NOW(),
        status          VARCHAR(20) DEFAULT 'success',
        details         TEXT
    );
    
    INSERT INTO migration_log (migration_name, status)
    VALUES ('full_schema_creation', 'success');
    """
    
    try:
        # Connect to database
        conn = await asyncpg.connect(**db_config)
        print(f"✓ PostgreSQL 연결 성공: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        # Set timezone to Asia/Seoul (KST)
        await conn.execute("SET TIME ZONE 'Asia/Seoul'")
        print("✓ 시간대 설정: Asia/Seoul (KST)")
        
        # Split and execute statements
        statements = [stmt.strip() for stmt in create_tables_sql.split(';') if stmt.strip()]
        
        for i, stmt in enumerate(statements, 1):
            try:
                await conn.execute(stmt)
            except Exception as e:
                print(f"⚠ Statement {i} 처리 중 오류: {e}")
        
        print("✓ 모든 테이블 생성 완료")
        
        # Verify table creation
        tables = await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )
        print(f"\n생성된 테이블 ({len(tables)}개):")
        for table in sorted(tables, key=lambda x: x['table_name']):
            print(f"  ✓ {table['table_name']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"✗ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(create_all_tables())

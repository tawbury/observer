"""Pytest conftest: add app/observer and app/observer/src to path for test discovery."""
import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
import asyncpg

_root = Path(__file__).resolve().parents[1]
_src = _root / "app" / "observer" / "src"
_observer = _root / "app" / "observer"
for p in (_src, _observer):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


# =====================================================
# Database Test Fixtures
# =====================================================

@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 설정"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """테스트용 PostgreSQL 데이터베이스 연결"""
    
    # DB 연결 정보 (환경 변수 또는 기본값)
    db_host = os.getenv('TEST_DB_HOST', 'localhost')
    db_user = os.getenv('TEST_DB_USER', 'postgres')
    db_password = os.getenv('TEST_DB_PASSWORD', 'observer_db_pwd')
    db_name = os.getenv('TEST_DB_NAME', 'observer_test')
    db_port = int(os.getenv('TEST_DB_PORT', 5432))
    
    conn = None
    try:
        # 테스트 DB 연결
        conn = await asyncpg.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port
        )
        
        yield conn
        
    except asyncpg.InvalidCatalogNameError:
        # 테스트 DB가 없으면 생성
        postgres_conn = await asyncpg.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database='postgres',
            port=db_port
        )
        
        try:
            await postgres_conn.execute(f'CREATE DATABASE "{db_name}"')
            await postgres_conn.close()
            
            # 새로 생성된 DB에 연결
            conn = await asyncpg.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name,
                port=db_port
            )
            
            yield conn
            
        except Exception as e:
            await postgres_conn.close()
            raise e
    
    except Exception as e:
        pytest.skip(f"PostgreSQL 연결 실패: {e}")
    
    finally:
        if conn:
            await conn.close()


@pytest.fixture(scope="function") 
async def db_session(db_connection: asyncpg.Connection) -> AsyncGenerator[asyncpg.Connection, None]:
    """각 테스트마다 트랜잭션 rollback하는 DB 세션"""
    
    # 트랜잭션 시작
    tx = db_connection.transaction()
    await tx.start()
    
    try:
        yield db_connection
    finally:
        # 트랜잭션 롤백 (테스트 데이터 정리)
        await tx.rollback()


@pytest.fixture(scope="session")
async def db_schema_initialized(db_connection: asyncpg.Connection) -> bool:
    """테스트 DB에 스키마가 초기화되어 있는지 확인하고 필요시 초기화"""
    
    # 스키마 SQL 파일 경로
    schema_dir = _root / "app" / "observer" / "src" / "db" / "schema"
    
    if not schema_dir.exists():
        pytest.skip(f"스키마 디렉토리 없음: {schema_dir}")
    
    # 테이블이 이미 존재하는지 확인
    tables_exist = await db_connection.fetchval(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'scalp_ticks'
        )
        """
    )
    
    if not tables_exist:
        # 스키마 초기화
        sql_files = sorted(schema_dir.glob("*.sql"))
        for sql_file in sql_files:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # SQL 실행 (세미콜론으로 분리)
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            for stmt in statements:
                if stmt.upper().startswith(('CREATE', 'INSERT')):
                    await db_connection.execute(stmt)
    
    return True


# =====================================================
# Mock Data Fixtures
# =====================================================

@pytest.fixture
def sample_scalp_tick():
    """샘플 scalp tick 데이터"""
    return {
        "symbol": "005930",
        "event_time": "2026-01-28T09:00:00.000Z",
        "bid_price": 73000.0,
        "ask_price": 73100.0,
        "bid_size": 100,
        "ask_size": 200,
        "last_price": 73050.0,
        "volume": 1000,
        "session_id": "test_session_001",
        "mitigation_level": 0,
        "quality_flag": "normal"
    }


@pytest.fixture
def sample_swing_bar():
    """샘플 swing 10분 봉 데이터"""
    return {
        "symbol": "005930",
        "bar_time": "2026-01-28T09:00:00.000Z",
        "open": 73000.0,
        "high": 73200.0,
        "low": 72800.0,
        "close": 73100.0,
        "volume": 50000,
        "bid_price": 73000.0,
        "ask_price": 73100.0,
        "session_id": "test_session_001",
        "schema_version": "1.0",
        "mitigation_level": 0,
        "quality_flag": "normal"
    }

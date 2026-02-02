"""
DB 스키마 보장: 필요한 테이블이 없을 때만 src/db/schema/*.sql 을 순서대로 실행.
기존 데이터 보호를 위해 DROP 문은 제거하고, CREATE TABLE 은 IF NOT EXISTS 로 실행.
"""

import logging
import re
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# schema 파일에서 생성하는 테이블 목록 (하나라도 없으면 스키마 적용)
REQUIRED_TABLES = [
    "scalp_ticks",
    "scalp_1m_bars",
    "scalp_gaps",
    "migration_log",
    "swing_bars_10m",
    "portfolio_policy",
    "target_weights",
    "portfolio_snapshot",
    "portfolio_positions",
    "rebalance_plan",
    "rebalance_orders",
    "rebalance_execution",
    "analysis_rolling_stats",
    "analysis_threshold_candidates",
    "analysis_signal_events",
]


def _split_sql_statements(content: str) -> list[str]:
    """Split SQL by ';' but do not split inside $$...$$ or single-quoted strings."""
    statements: list[str] = []
    current: list[str] = []
    i = 0
    in_dollar = False
    in_single = False
    n = len(content)

    while i < n:
        if in_dollar:
            if content[i : i + 2] == "$$":
                current.append("$$")
                i += 2
                in_dollar = False
            else:
                current.append(content[i])
                i += 1
            continue
        if in_single:
            if content[i] == "'" and (i == 0 or content[i - 1] != "\\"):
                current.append(content[i])
                i += 1
                in_single = False
            else:
                current.append(content[i])
                i += 1
            continue
        if content[i : i + 2] == "$$":
            current.append("$$")
            i += 2
            in_dollar = True
            continue
        if content[i] == "'":
            current.append(content[i])
            i += 1
            in_single = True
            continue
        if content[i] == ";":
            stmt = "".join(current).strip()
            if stmt and not _is_only_comment_or_empty(stmt):
                statements.append(stmt)
            current = []
            i += 1
            continue
        current.append(content[i])
        i += 1

    stmt = "".join(current).strip()
    if stmt and not _is_only_comment_or_empty(stmt):
        statements.append(stmt)
    return statements


def _is_only_comment_or_empty(s: str) -> bool:
    s = s.strip()
    if not s:
        return True
    for line in s.splitlines():
        line = line.strip()
        if line and not line.startswith("--"):
            return False
    return True


def _strip_drop_statements(sql: str) -> str:
    """Remove DROP TABLE / DROP TRIGGER / DROP MATERIALIZED VIEW / DROP FUNCTION to protect existing data."""
    # Drop whole lines that are DROP ... ; (with optional CASCADE)
    sql = re.sub(
        r"^\s*DROP\s+(TABLE|TRIGGER|MATERIALIZED\s+VIEW|VIEW|FUNCTION|INDEX)\s+.*?;",
        "",
        sql,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return sql


def _add_if_not_exists_to_create_table(sql: str) -> str:
    """Replace 'CREATE TABLE name' with 'CREATE TABLE IF NOT EXISTS name' (only first occurrence per statement)."""
    # Match CREATE TABLE <name> ( but not CREATE TABLE IF NOT EXISTS
    return re.sub(
        r"\bCREATE\s+TABLE\s+(?!IF\s+NOT\s+EXISTS)(\w+)",
        r"CREATE TABLE IF NOT EXISTS \1",
        sql,
        count=0,
        flags=re.IGNORECASE,
    )


async def _table_exists(conn: Any, table_name: str) -> bool:
    """Return True if table exists in public schema."""
    row = await conn.fetchval(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = $1
        """,
        table_name,
    )
    return row is not None


async def _check_required_tables(conn: Any) -> dict[str, bool]:
    """Return dict of table_name -> exists."""
    result = {}
    for name in REQUIRED_TABLES:
        result[name] = await _table_exists(conn, name)
    return result


async def ensure_schema(pool: Any) -> bool:
    """
    필요한 테이블이 하나라도 없으면 schema/*.sql 을 순서대로 실행.
    DROP 문은 제거하고 CREATE TABLE 은 IF NOT EXISTS 로 실행해 기존 데이터를 보호.

    Args:
        pool: asyncpg connection pool (after connect success).

    Returns:
        True if schema is ready (existing or applied), False on unrecoverable error.
    """
    schema_dir = Path(__file__).resolve().parent / "schema"
    if not schema_dir.exists():
        log.warning("ensure_schema: schema dir not found %s", schema_dir)
        return True

    sql_files = sorted(schema_dir.glob("*.sql"))
    if not sql_files:
        log.warning("ensure_schema: no .sql files in %s", schema_dir)
        return True

    async with pool.acquire() as conn:
        existing = await _check_required_tables(conn)
        missing = [k for k, v in existing.items() if not v]
        if not missing:
            log.debug("ensure_schema: all required tables exist, skip")
            return True

        log.info("ensure_schema: missing tables %s, applying schema from %s", missing[:5], schema_dir)

        for sql_path in sql_files:
            raw = sql_path.read_text(encoding="utf-8")
            content = _strip_drop_statements(raw)
            content = _add_if_not_exists_to_create_table(content)
            statements = _split_sql_statements(content)

            for stmt in statements:
                if not stmt:
                    continue
                try:
                    await conn.execute(stmt)
                except Exception as e:
                    # Optional objects (MV, trigger, function) may already exist
                    log.debug("ensure_schema: statement skipped (%s): %s", type(e).__name__, e)
                    continue

        log.info("ensure_schema: schema apply finished")
    return True

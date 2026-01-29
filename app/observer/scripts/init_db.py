"""
Database Initialization Script
생성일: 2026-01-28
설명: PostgreSQL 데이터베이스 스키마 초기화 스크립트
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

import asyncpg

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DBInitializer:
    """PostgreSQL 데이터베이스 초기화 클래스"""
    
    def __init__(self, db_host: str, db_user: str, db_password: str, db_name: str, db_port: int = 5432):
        self.db_host = db_host
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.db_port = db_port
        self.conn = None
        
        # SQL 스키마 파일 경로
        self.schema_dir = Path(__file__).parent.parent / 'src' / 'db' / 'schema'
    
    async def connect(self):
        """데이터베이스 연결"""
        try:
            self.conn = await asyncpg.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                port=self.db_port
            )
            logger.info(f"✓ PostgreSQL 연결 성공: {self.db_host}:{self.db_port}/{self.db_name}")
        except Exception as e:
            logger.error(f"✗ DB 연결 실패: {e}")
            raise
    
    async def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.conn:
            await self.conn.close()
            logger.info("✓ DB 연결 해제")
    
    async def check_database_exists(self) -> bool:
        """데이터베이스 존재 여부 확인"""
        try:
            # postgres DB에 연결하여 target DB 존재 확인
            postgres_conn = await asyncpg.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                database='postgres',
                port=self.db_port
            )
            
            exists = await postgres_conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", self.db_name
            )
            await postgres_conn.close()
            
            return exists is not None
        except Exception as e:
            logger.error(f"✗ DB 존재 확인 실패: {e}")
            return False
    
    async def create_database(self):
        """데이터베이스 생성"""
        try:
            # postgres DB에 연결하여 target DB 생성
            postgres_conn = await asyncpg.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                database='postgres',
                port=self.db_port
            )
            
            await postgres_conn.execute(f'CREATE DATABASE "{self.db_name}"')
            await postgres_conn.close()
            logger.info(f"✓ 데이터베이스 '{self.db_name}' 생성 완료")
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"✓ 데이터베이스 '{self.db_name}' 이미 존재")
            else:
                logger.error(f"✗ 데이터베이스 생성 실패: {e}")
                raise
    
    async def execute_sql_file(self, sql_file: Path) -> bool:
        """SQL 파일 실행"""
        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # PostgreSQL에서는 executescript 대신 여러 statement를 한 번에 실행할 수 있음
            # 주석을 제거하고 명령문을 분리
            lines = []
            for line in sql_content.split('\n'):
                # 주석 제거
                if '--' in line:
                    line = line.split('--')[0]
                line = line.strip()
                if line:
                    lines.append(line)
            
            # 세미콜론으로 분리하여 각 statement 실행
            full_sql = ' '.join(lines)
            statements = [stmt.strip() for stmt in full_sql.split(';') if stmt.strip()]
            
            for stmt in statements:
                try:
                    await self.conn.execute(stmt)
                except Exception as e:
                    # DROP TABLE 실패는 무시 (이미 존재하지 않을 수 있음)
                    if "does not exist" in str(e) and ("DROP" in stmt or "TRUNCATE" in stmt):
                        logger.debug(f"    ℹ {stmt.split()[0:3]} 스킵됨 (테이블 없음)")
                    else:
                        raise
            
            logger.info(f"✓ {sql_file.name} 실행 완료")
            return True
        except Exception as e:
            logger.error(f"✗ {sql_file.name} 실행 실패: {e}")
            return False
    
    async def initialize_schema(self) -> Dict[str, bool]:
        """스키마 초기화 (모든 SQL 파일 실행)"""
        if not self.schema_dir.exists():
            logger.error(f"✗ 스키마 디렉토리 없음: {self.schema_dir}")
            return {}
        
        sql_files = sorted(self.schema_dir.glob("*.sql"))
        if not sql_files:
            logger.warning(f"⚠ SQL 파일이 없음: {self.schema_dir}")
            return {}
        
        results = {}
        for sql_file in sql_files:
            logger.info(f"  실행 중: {sql_file.name}")
            results[sql_file.name] = await self.execute_sql_file(sql_file)
        
        return results
    
    async def check_tables_exist(self) -> Dict[str, bool]:
        """테이블 존재 여부 확인"""
        expected_tables = [
            'scalp_ticks',
            'scalp_1m_bars', 
            'scalp_gaps',
            'swing_bars_10m',
            'portfolio_policy',
            'target_weights',
            'portfolio_snapshot',
            'portfolio_positions',
            'rebalance_plan',
            'rebalance_orders',
            'rebalance_execution',
            'migration_log'
        ]
        
        results = {}
        for table in expected_tables:
            try:
                exists = await self.conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = $1
                    )
                    """,
                    table
                )
                results[table] = exists
            except Exception as e:
                logger.error(f"✗ {table} 테이블 확인 실패: {e}")
                results[table] = False
        
        return results
    
    async def get_table_counts(self) -> Dict[str, int]:
        """테이블별 레코드 수 조회"""
        table_exists = await self.check_tables_exist()
        counts = {}
        
        for table, exists in table_exists.items():
            if exists:
                try:
                    count = await self.conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    counts[table] = count if count else 0
                except Exception as e:
                    logger.debug(f"테이블 {table} 카운트 조회 실패: {e}")
                    counts[table] = 0
            else:
                counts[table] = -1  # 테이블 존재하지 않음
        
        return counts


async def main():
    """메인 DB 초기화 프로세스"""
    
    # DB 연결 정보 (환경 변수 또는 기본값)
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'observer_db_pwd')
    db_name = os.getenv('DB_NAME', 'observer')
    db_port = int(os.getenv('DB_PORT', 5432))
    
    logger.info("=" * 70)
    logger.info("PostgreSQL Database Initialization")
    logger.info("=" * 70)
    logger.info(f"DB Host: {db_host}:{db_port}")
    logger.info(f"DB Name: {db_name}")
    
    initializer = DBInitializer(db_host, db_user, db_password, db_name, db_port)
    
    try:
        # Step 1: 데이터베이스 존재 확인 및 생성
        logger.info("\n[Step 1] 데이터베이스 확인 및 생성")
        db_exists = await initializer.check_database_exists()
        if not db_exists:
            await initializer.create_database()
        else:
            logger.info(f"✓ 데이터베이스 '{db_name}' 이미 존재")
        
        # Step 2: DB 연결
        logger.info("\n[Step 2] 데이터베이스 연결")
        await initializer.connect()
        
        # Step 3: 스키마 초기화
        logger.info("\n[Step 3] 스키마 초기화")
        schema_results = await initializer.initialize_schema()
        
        success_count = sum(1 for success in schema_results.values() if success)
        total_count = len(schema_results)
        
        logger.info(f"✓ 스키마 초기화 완료: {success_count}/{total_count} 파일 성공")
        
        if success_count < total_count:
            logger.warning("⚠ 일부 SQL 파일 실행 실패")
            for file_name, success in schema_results.items():
                if not success:
                    logger.warning(f"  ✗ {file_name}")
        
        # Step 4: 테이블 확인
        logger.info("\n[Step 4] 테이블 확인")
        table_exists = await initializer.check_tables_exist()
        existing_tables = [table for table, exists in table_exists.items() if exists]
        missing_tables = [table for table, exists in table_exists.items() if not exists]
        
        logger.info(f"✓ 생성된 테이블: {len(existing_tables)}개")
        for table in existing_tables:
            logger.info(f"  ✓ {table}")
        
        if missing_tables:
            logger.warning(f"⚠ 누락된 테이블: {len(missing_tables)}개")
            for table in missing_tables:
                logger.warning(f"  ✗ {table}")
        
        # Step 5: 테이블 상태 요약
        logger.info("\n[Step 5] 테이블 상태 요약")
        counts = await initializer.get_table_counts()
        
        logger.info("\n" + "=" * 70)
        logger.info("데이터베이스 초기화 완료!")
        logger.info("=" * 70)
        logger.info(f"데이터베이스: {db_name}")
        logger.info(f"테이블 수: {len(existing_tables)}/{len(table_exists)}")
        logger.info("\n테이블별 상태:")
        for table, count in sorted(counts.items()):
            if count == -1:
                logger.info(f"  ✗ {table:30s}: 테이블 없음")
            else:
                logger.info(f"  ✓ {table:30s}: {count:10,d} 행")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"✗ 초기화 실패: {e}")
        sys.exit(1)
    finally:
        await initializer.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
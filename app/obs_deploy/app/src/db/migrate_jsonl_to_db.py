"""
Phase 13: JSONL to Database Migration Script
변환 대상: JSONL 파일 → PostgreSQL DB
작성일: 2026-01-22
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

import asyncpg

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JSONLToDBMigrator:
    """JSONL 파일을 PostgreSQL DB로 마이그레이션하는 클래스"""
    
    def __init__(self, db_host: str, db_user: str, db_password: str, db_name: str, db_port: int = 5432):
        self.db_host = db_host
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.db_port = db_port
        self.conn = None
        self.batch_size = 1000  # 배치 크기
    
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
            sys.exit(1)
    
    async def disconnect(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            await self.conn.close()
    
    async def migrate_swing_bars_10m(self, jsonl_dir: Path) -> int:
        """Swing 10분 봉 데이터 (JSONL) → swing_bars_10m 테이블"""
        jsonl_files = sorted(jsonl_dir.glob("*.jsonl"))
        if not jsonl_files:
            logger.warning(f"⚠ Swing JSONL 파일 없음: {jsonl_dir}")
            return 0
        
        total_rows = 0
        for jsonl_file in jsonl_files:
            logger.info(f"  처리 중: {jsonl_file.name}")
            try:
                batch = []
                line_count = 0
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if not line.strip():
                            continue
                        
                        try:
                            data = json.loads(line)
                            # Swing JSONL 구조에서 필드 추출
                            price = data.get('price', {})
                            
                            # ISO8601 타임스탬프를 datetime으로 변환
                            ts_str = data.get('ts', '')
                            bar_time = datetime.fromisoformat(ts_str.replace('Z', '+00:00')) if ts_str else None
                            
                            batch.append((
                                data.get('symbol'),
                                bar_time,
                                float(price.get('open', 0)),
                                float(price.get('high', 0)),
                                float(price.get('low', 0)),
                                float(price.get('close', 0)),
                                int(data.get('volume', 0)),
                                float(data['bid_price']) if data.get('bid_price') is not None else None,
                                float(data['ask_price']) if data.get('ask_price') is not None else None,
                                data.get('session', 'track_a_session'),
                                data.get('quality_flag', 'normal')
                            ))
                            line_count += 1
                            
                            # 배치 단위로 삽입
                            if len(batch) >= self.batch_size:
                                await self.conn.executemany(
                                    """
                                    INSERT INTO swing_bars_10m 
                                    (symbol, bar_time, open, high, low, close, volume,
                                     bid_price, ask_price, session_id, quality_flag)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                                    ON CONFLICT (symbol, bar_time) DO UPDATE
                                    SET open = EXCLUDED.open,
                                        high = EXCLUDED.high,
                                        low = EXCLUDED.low,
                                        close = EXCLUDED.close,
                                        volume = EXCLUDED.volume,
                                        bid_price = COALESCE(swing_bars_10m.bid_price, EXCLUDED.bid_price),
                                        ask_price = COALESCE(swing_bars_10m.ask_price, EXCLUDED.ask_price)
                                    """,
                                    batch
                                )
                                total_rows += len(batch)
                                batch = []
                        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
                            logger.debug(f"    라인 {line_num} 파싱 오류: {str(e)}")
                            continue
                
                # 남은 배치 처리
                if batch:
                    await self.conn.executemany(
                        """
                        INSERT INTO swing_bars_10m 
                        (symbol, bar_time, open, high, low, close, volume,
                         bid_price, ask_price, session_id, quality_flag)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (symbol, bar_time) DO UPDATE
                        SET open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume
                        """,
                        batch
                    )
                
                logger.info(f"✓ {jsonl_file.name} 완료: {total_rows} 행 저장")
            except Exception as e:
                logger.error(f"✗ {jsonl_file.name} 처리 실패: {e}")
        
        return total_rows
    
    async def get_statistics(self) -> Dict[str, int]:
        """DB 내 데이터 통계 조회"""
        stats = {}
        tables = ['scalp_ticks', 'scalp_1m_bars', 'scalp_gaps', 'swing_bars_10m', 'portfolio_snapshot']
        
        try:
            for table in tables:
                try:
                    count = await self.conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = count if count else 0
                except:
                    stats[table] = 0
        except Exception as e:
            logger.error(f"✗ 통계 조회 실패: {e}")
        
        return stats


async def main():
    """메인 마이그레이션 프로세스"""
    
    # DB 연결 정보 (환경 변수 또는 기본값)
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'observer_db_pwd')
    db_name = os.getenv('DB_NAME', 'observer')
    db_port = int(os.getenv('DB_PORT', 5432))
    
    # 데이터 소스 경로
    project_root = Path(__file__).parent.parent.parent.parent.parent.parent
    swing_data_dir = project_root / 'app' / 'obs_deploy' / 'app' / 'config' / 'observer' / 'swing'
    
    logger.info("=" * 70)
    logger.info("Phase 13 Task 13.2: JSONL → PostgreSQL 마이그레이션")
    logger.info("=" * 70)
    logger.info(f"DB Host: {db_host}:{db_port}/{db_name}")
    
    migrator = JSONLToDBMigrator(db_host, db_user, db_password, db_name, db_port)
    
    try:
        await migrator.connect()
        
        # Swing 10분 봉 데이터 마이그레이션
        logger.info("\n[Step 1] Swing 10분 봉 데이터 마이그레이션")
        if swing_data_dir.exists():
            swing_bars_count = await migrator.migrate_swing_bars_10m(swing_data_dir)
            logger.info(f"✓ Swing 10분 봉: {swing_bars_count} 행 저장")
        else:
            logger.warning(f"⚠ Swing 데이터 디렉토리 없음: {swing_data_dir}")
            swing_bars_count = 0
        
        # 최종 통계
        logger.info("\n[Step 2] 최종 데이터 통계")
        stats = await migrator.get_statistics()
        logger.info("\n" + "=" * 70)
        logger.info("마이그레이션 완료! 최종 통계:")
        logger.info("=" * 70)
        for table, count in sorted(stats.items()):
            if count > 0:
                logger.info(f"  ✓ {table:30s}: {count:10,d} 행")
            else:
                logger.info(f"    {table:30s}: {count:10,d} 행")
        logger.info("=" * 70)
        
    finally:
        await migrator.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

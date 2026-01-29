"""
Docker 컨테이너에서 실행될 마이그레이션 테스트 스크립트
JSONL 파일을 PostgreSQL로 마이그레이션하고 결과를 출력
"""
import asyncio
import sys
from pathlib import Path

# Set up Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'app' / 'observer' / 'src'))

from db.migrate_jsonl_to_db import JSONLToDBMigrator


async def main():
    """Main migration test function"""
    # 경로 설정
    scalp_source_dir = project_root / 'app' / 'observer' / 'config' / 'observer' / 'scalp'
    swing_source_dir = project_root / 'app' / 'observer' / 'config' / 'observer' / 'swing'
    test_data_dir = project_root / 'tests' / 'test_data'
    
    # Docker 환경인지 로컬인지 판단
    db_host = 'postgres' if 'DOCKER_ENV' in sys.argv else 'localhost'
    
    migrator = JSONLToDBMigrator(
        db_host=db_host,
        db_user='postgres',
        db_password='observer_db_pwd',
        db_name='observer',
        db_port=5432
    )
    
    try:
        print("\n" + "="*80)
        print("DB 마이그레이션 테스트 시작")
        print("="*80)
        
        # Connect to database
        await migrator.connect()
        print("✓ PostgreSQL 연결 성공")
        
        # Get initial statistics
        print("\n[마이그레이션 전]")
        stats = await migrator.get_statistics()
        for table, count in sorted(stats.items()):
            print(f"  {table:35s}: {count:10,d} rows")
        
        # Run migrations
        print("\n[마이그레이션 시작]")
        
        # Migrate scalp_ticks from config dir
        if scalp_source_dir.exists():
            print(f"  > {scalp_source_dir.name} 폴더에서 scalp_ticks 마이그레이션 중...", end="", flush=True)
            scalp_ticks_result = await migrator.migrate_scalp_ticks(scalp_source_dir)
            print(f" {scalp_ticks_result} rows")
        
        # Migrate scalp_1m_bars from config dir
        if scalp_source_dir.exists():
            print(f"  > {scalp_source_dir.name} 폴더에서 scalp_1m_bars 마이그레이션 중...", end="", flush=True)
            scalp_1m_bars_result = await migrator.migrate_scalp_1m_bars(scalp_source_dir)
            print(f" {scalp_1m_bars_result} rows")
        
        # Migrate swing_bars_10m from config dir
        if swing_source_dir.exists():
            print(f"  > {swing_source_dir.name} 폴더에서 swing_bars_10m 마이그레이션 중...", end="", flush=True)
            swing_bars_result = await migrator.migrate_swing_bars_10m(swing_source_dir)
            print(f" {swing_bars_result} rows")
        
        # Migrate test data if available
        if test_data_dir.exists():
            print(f"\n  > test_data 폴더에서 추가 데이터 마이그레이션 중...")
            scalp_ticks_test = await migrator.migrate_scalp_ticks(test_data_dir)
            if scalp_ticks_test > 0:
                print(f"    scalp_ticks (test): {scalp_ticks_test} rows")
            scalp_1m_test = await migrator.migrate_scalp_1m_bars(test_data_dir)
            if scalp_1m_test > 0:
                print(f"    scalp_1m_bars (test): {scalp_1m_test} rows")
            swing_test = await migrator.migrate_swing_bars_10m(test_data_dir)
            if swing_test > 0:
                print(f"    swing_bars_10m (test): {swing_test} rows")
        
        # Get final statistics
        print("\n[마이그레이션 후]")
        stats = await migrator.get_statistics()
        total_rows = 0
        for table, count in sorted(stats.items()):
            print(f"  {table:35s}: {count:10,d} rows")
            total_rows += count
        
        print("\n" + "="*80)
        print(f"✓ 마이그레이션 완료 - 총 {total_rows:,d} rows 적재")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await migrator.disconnect()
        print("✓ 데이터베이스 연결 종료")


if __name__ == '__main__':
    asyncio.run(main())

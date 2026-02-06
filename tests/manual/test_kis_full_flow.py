
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 경로 추가 (d:\development\prj_obs)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "src")) # [Fix] Add src to path for 'observer' module import

# ✅ RUN_MODE 설정 (load_env_by_run_mode가 호출되기 전에 설정)
os.environ["RUN_MODE"] = "local"

# ✅ paths.py의 load_env_by_run_mode() 사용
# 이 함수가 자동으로 .env.local, .env.shared, config/.env를 순서대로 로드
from src.observer.paths import load_env_by_run_mode
env_result = load_env_by_run_mode()

print(f"✅ Environment loaded: RUN_MODE={env_result['run_mode']}")
print(f"📁 Files loaded: {env_result['files_loaded']}")
print(f"⚠️  Files skipped: {env_result['files_skipped']}")

# 경로 확인
print(f"📂 OBSERVER_DATA_DIR: {os.environ.get('OBSERVER_DATA_DIR')}")
print(f"📂 OBSERVER_SNAPSHOT_DIR: {os.environ.get('OBSERVER_SNAPSHOT_DIR')}")
print(f"📂 KIS_TOKEN_CACHE_DIR: {os.environ.get('KIS_TOKEN_CACHE_DIR')}")

# 이제 src 모듈 임포트 가능
from src.provider.kis.kis_auth import KISAuth
from src.provider.kis.kis_rest_provider import KISRestProvider
from src.universe.symbol_generator import SymbolGenerator
from src.universe.universe_manager import UniverseManager
from src.observer.paths import observer_data_dir, snapshot_dir, kis_token_cache_dir

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

# 파일 로깅 추가
log_file = PROJECT_ROOT / "logs" / "full_flow_debug.log"
log_file.parent.mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w')
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
logging.getLogger().addHandler(file_handler)

logger = logging.getLogger("TestKISFlow")

# 개별 모듈 로깅 레벨 조정
logging.getLogger("SymbolGenerator").setLevel(logging.INFO)
logging.getLogger("UniverseManager").setLevel(logging.INFO)
logging.getLogger("KISAuth").setLevel(logging.INFO)

async def main():
    logger.info("🚀 Starting Manual KIS Flow Test")
    logger.info(f"📂 Project Root: {PROJECT_ROOT}")
    logger.info(f"📂 Data Dir: {os.environ.get('OBSERVER_DATA_DIR')}")
    logger.info(f"📂 Snapshot Dir: {os.environ.get('OBSERVER_SNAPSHOT_DIR')}")
    logger.info(f"📂 Token Cache Dir: {os.environ.get('KIS_TOKEN_CACHE_DIR')}")

    # 1. 환경 변수 확인
    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    
    if not app_key or not app_secret:
        logger.error("❌ KIS_APP_KEY or KIS_APP_SECRET is missing!")
        logger.error(f"   KIS_APP_KEY: {'SET' if app_key else 'NOT SET'}")
        logger.error(f"   KIS_APP_SECRET: {'SET' if app_secret else 'NOT SET'}")
        return
    else:
        logger.info("✅ KIS Credentials found.")
        logger.info(f"   KIS_APP_KEY: {app_key[:10]}...")


    # 2. 인증 및 프로바이더 초기화
    try:
        auth = await KISAuth.get_instance()
        provider = KISRestProvider(auth)
        
        # 토큰 확인
        token = await auth.ensure_token()
        logger.info(f"✅ Token secured. Cached at {kis_token_cache_dir()}")

        # 3. Symbol Generator 테스트 (강제 실행)
        logger.info("➡️ Execute: SymbolGenerator (Force=True)")
        generator = SymbolGenerator(provider_engine=provider)
        
        # execute()는 기존에 파일이 있으면 스킵할 수 있으나 force=True로 강제함
        symbol_file = await generator.execute(force=True)
        
        if symbol_file and Path(symbol_file).exists():
            logger.info(f"✅ Symbol Generation Success: {symbol_file}")
        else:
            logger.error("❌ Symbol Generation Failed")
            return

        # 4. Universe Manager 테스트 (스냅샷 생성)
        logger.info("➡️ Execute: UniverseManager (Snapshot Creation)")
        
        # UniverseManager는 내부적으로 SymbolGenerator를 다시 만들지만, 
        # API 엔진을 공유하므로 효율적임.
        # min_count를 낮춰서 테스트 용이성 확보 (100 -> 10)
        manager = UniverseManager(
            provider_engine=provider, 
            min_count=10, 
            min_price=1000 # 테스트를 위해 가격 제한 완화
        )
        
        # 오늘 날짜로 생성
        snapshot_path = await manager.create_daily_snapshot(datetime.today())
        
        if snapshot_path and Path(snapshot_path).exists():
            logger.info(f"✅ Universe Snapshot Success: {snapshot_path}")
            
            # 내용 검증
            import json
            with open(snapshot_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                symbols = data.get("symbols", [])
                logger.info(f"📊 Final Universe Size: {len(symbols)}")
                
                if len(symbols) > 0:
                    logger.info(f"🔍 Sample Symbols: {symbols[:5]}...")
        else:
            logger.error("❌ Universe Snapshot Failed")

    except Exception as e:
        logger.exception(f"❌ Test Aborted due to Error: {e}")
    finally:
        await provider.close()
        logger.info("👋 Test cleanup complete.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

"""시간 확인 스크립트"""
import asyncio
import asyncpg

async def check_time():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='observer_db_pwd',
        database='observer'
    )
    
    # 시간대 설정
    await conn.execute("SET TIME ZONE 'Asia/Seoul'")
    
    # migration_log 확인
    result = await conn.fetchrow(
        'SELECT migration_name, executed_at FROM migration_log ORDER BY id DESC LIMIT 1'
    )
    print(f"마지막 마이그레이션: {result['migration_name']}")
    print(f"실행 시간 (KST): {result['executed_at']}")
    
    # 최근 데이터 확인
    tick = await conn.fetchrow(
        'SELECT symbol, event_time FROM scalp_ticks ORDER BY id DESC LIMIT 1'
    )
    if tick:
        print(f"\n최근 scalp_tick:")
        print(f"  종목: {tick['symbol']}")
        print(f"  시간: {tick['event_time']}")
    
    bar = await conn.fetchrow(
        'SELECT symbol, bar_time FROM scalp_1m_bars ORDER BY bar_time DESC LIMIT 1'
    )
    if bar:
        print(f"\n최근 scalp_1m_bar:")
        print(f"  종목: {bar['symbol']}")
        print(f"  시간: {bar['bar_time']}")
    
    await conn.close()

asyncio.run(check_time())

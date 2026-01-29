"""
DB Models Test
생성일: 2026-01-28
설명: Pydantic 모델 검증 테스트 (PostgreSQL 연결 없이)
"""

import pytest
from datetime import datetime
from decimal import Decimal

from db.models import (
    ScalpTick, Scalp1mBar, ScalpGap, SwingBar10m,
    PortfolioPolicy, TargetWeight, PortfolioSnapshot,
    PortfolioPosition, RebalancePlan, RebalanceOrder,
    MigrationLog
)


def test_scalp_tick_model():
    """ScalpTick 모델 검증"""
    data = {
        "symbol": "005930",
        "event_time": datetime.now(),
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
    
    tick = ScalpTick(**data)
    assert tick.symbol == "005930"
    assert tick.bid_price == 73000.0
    assert tick.ask_price == 73100.0
    assert tick.session_id == "test_session_001"
    assert tick.quality_flag == "normal"


def test_scalp_1m_bar_model():
    """Scalp1mBar 모델 검증"""
    data = {
        "symbol": "005930",
        "bar_time": datetime.now(),
        "open": 73000.0,
        "high": 73200.0,
        "low": 72800.0,
        "close": 73100.0,
        "volume": 50000,
        "coverage_ratio": 0.95,
        "session_id": "test_session_001",
        "quality_flag": "normal"
    }
    
    bar = Scalp1mBar(**data)
    assert bar.symbol == "005930"
    assert bar.open == 73000.0
    assert bar.high == 73200.0
    assert bar.low == 72800.0
    assert bar.close == 73100.0
    assert bar.coverage_ratio == 0.95


def test_swing_bar_10m_model():
    """SwingBar10m 모델 검증"""
    data = {
        "symbol": "005930",
        "bar_time": datetime.now(),
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
    
    bar = SwingBar10m(**data)
    assert bar.symbol == "005930"
    assert bar.bid_price == 73000.0
    assert bar.ask_price == 73100.0
    assert bar.schema_version == "1.0"


def test_portfolio_policy_model():
    """PortfolioPolicy 모델 검증"""
    data = {
        "policy_id": "policy_001",
        "policy_name": "Conservative Portfolio",
        "rebalance_threshold": 0.05,
        "rebalance_frequency": "monthly",
        "is_active": True
    }
    
    policy = PortfolioPolicy(**data)
    assert policy.policy_id == "policy_001"
    assert policy.policy_name == "Conservative Portfolio"
    assert policy.rebalance_threshold == 0.05
    assert policy.is_active == True


def test_target_weight_model():
    """TargetWeight 모델 검증"""
    data = {
        "policy_id": "policy_001",
        "symbol": "005930",
        "target_weight": 0.3
    }
    
    weight = TargetWeight(**data)
    assert weight.policy_id == "policy_001"
    assert weight.symbol == "005930"
    assert weight.target_weight == 0.3


def test_migration_log_model():
    """MigrationLog 모델 검증"""
    data = {
        "migration_name": "001_create_scalp_tables",
        "executed_at": datetime.now(),
        "status": "success",
        "details": "Successfully created scalp tables"
    }
    
    log = MigrationLog(**data)
    assert log.migration_name == "001_create_scalp_tables"
    assert log.status == "success"
    assert log.details == "Successfully created scalp tables"


def test_model_json_serialization():
    """모델 JSON 직렬화 테스트"""
    data = {
        "symbol": "005930",
        "event_time": datetime.now(),
        "bid_price": 73000.0,
        "ask_price": 73100.0,
        "session_id": "test_session_001"
    }
    
    tick = ScalpTick(**data)
    json_str = tick.model_dump_json()
    
    assert "005930" in json_str
    assert "test_session_001" in json_str
    assert "73000.0" in json_str


def test_model_validation_errors():
    """모델 유효성 검증 오류 테스트"""
    # 필수 필드 누락
    with pytest.raises(ValueError):
        ScalpTick()  # symbol, event_time, bid_price, ask_price, session_id 필수
    
    # 음수 가격
    with pytest.raises(ValueError):
        ScalpTick(
            symbol="005930",
            event_time=datetime.now(),
            bid_price=-1000.0,  # 음수 불가
            ask_price=73100.0,
            session_id="test"
        )
    
    # 잘못된 coverage_ratio (0.0 ~ 1.0 범위 초과)
    with pytest.raises(ValueError):
        Scalp1mBar(
            symbol="005930",
            bar_time=datetime.now(),
            coverage_ratio=1.5,  # 1.0 초과 불가
            session_id="test"
        )
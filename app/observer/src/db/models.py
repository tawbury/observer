"""
Database Models for Observer Project
생성일: 2026-01-28
설명: PostgreSQL 테이블에 대응하는 Pydantic 모델들
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# =====================================================
# Scalp Tables (Track B - WebSocket 실시간 데이터)
# =====================================================

class ScalpTick(BaseModel):
    """scalp_ticks 테이블 모델"""
    id: Optional[int] = None
    symbol: str = Field(..., max_length=20)
    event_time: datetime
    bid_price: float = Field(..., ge=0)
    ask_price: float = Field(..., ge=0)
    bid_size: Optional[int] = Field(None, ge=0)
    ask_size: Optional[int] = Field(None, ge=0)
    last_price: Optional[float] = Field(None, ge=0)
    volume: Optional[int] = Field(None, ge=0)
    session_id: str = Field(..., max_length=50)
    mitigation_level: int = Field(default=0)
    quality_flag: str = Field(default='normal', max_length=20)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Scalp1mBar(BaseModel):
    """scalp_1m_bars 테이블 모델"""
    symbol: str = Field(..., max_length=20)
    bar_time: datetime
    open: Optional[float] = Field(None, ge=0)
    high: Optional[float] = Field(None, ge=0)
    low: Optional[float] = Field(None, ge=0)
    close: Optional[float] = Field(None, ge=0)
    volume: Optional[int] = Field(None, ge=0)
    coverage_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    session_id: str = Field(..., max_length=50)
    quality_flag: str = Field(default='normal', max_length=20)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScalpGap(BaseModel):
    """scalp_gaps 테이블 모델"""
    id: Optional[int] = None
    gap_start_ts: datetime
    gap_end_ts: datetime
    gap_seconds: int = Field(..., ge=0)
    scope: Optional[str] = Field(None, max_length=20)
    reason: Optional[str] = Field(None, max_length=100)
    session_id: str = Field(..., max_length=50)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# =====================================================
# Swing Tables (Track A - REST API 10분 봉 데이터)
# =====================================================

class SwingBar10m(BaseModel):
    """swing_bars_10m 테이블 모델"""
    symbol: str = Field(..., max_length=20)
    bar_time: datetime
    open: Optional[float] = Field(None, ge=0)
    high: Optional[float] = Field(None, ge=0)
    low: Optional[float] = Field(None, ge=0)
    close: Optional[float] = Field(None, ge=0)
    volume: Optional[int] = Field(None, ge=0)
    bid_price: Optional[float] = Field(None, ge=0)
    ask_price: Optional[float] = Field(None, ge=0)
    session_id: str = Field(..., max_length=50)
    schema_version: str = Field(default='1.0', max_length=10)
    mitigation_level: int = Field(default=0)
    quality_flag: str = Field(default='normal', max_length=20)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# =====================================================
# Portfolio Tables (포트폴리오 관리)
# =====================================================

class PortfolioPolicy(BaseModel):
    """portfolio_policy 테이블 모델"""
    policy_id: str = Field(..., max_length=50)
    policy_name: str = Field(..., max_length=100)
    created_at: Optional[datetime] = None
    rebalance_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    rebalance_frequency: str = Field(default='monthly', max_length=20)
    is_active: bool = Field(default=True)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TargetWeight(BaseModel):
    """target_weights 테이블 모델"""
    policy_id: str = Field(..., max_length=50)
    symbol: str = Field(..., max_length=20)
    target_weight: float = Field(..., ge=0.0, le=1.0)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PortfolioSnapshot(BaseModel):
    """portfolio_snapshot 테이블 모델"""
    snapshot_id: Optional[int] = None
    policy_id: str = Field(..., max_length=50)
    snapshot_time: datetime
    total_value: Optional[float] = Field(None, ge=0)
    cash: Optional[float] = Field(None, ge=0)
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PortfolioPosition(BaseModel):
    """portfolio_positions 테이블 모델"""
    position_id: Optional[int] = None
    snapshot_id: int
    symbol: str = Field(..., max_length=20)
    quantity: Optional[int] = Field(None, ge=0)
    market_price: Optional[float] = Field(None, ge=0)
    market_value: Optional[float] = Field(None, ge=0)
    current_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    target_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_diff: Optional[float] = Field(None, ge=-1.0, le=1.0)
    
    class Config:
        from_attributes = True


class RebalancePlan(BaseModel):
    """rebalance_plan 테이블 모델"""
    plan_id: Optional[int] = None
    policy_id: str = Field(..., max_length=50)
    snapshot_id: int
    status: str = Field(default='pending', max_length=20)
    reason: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RebalanceOrder(BaseModel):
    """rebalance_orders 테이블 모델"""
    order_id: Optional[int] = None
    plan_id: int
    symbol: str = Field(..., max_length=20)
    side: str = Field(..., max_length=10)  # 'BUY' or 'SELL'
    target_qty: Optional[int] = Field(None, ge=0)
    order_type: str = Field(default='MARKET', max_length=20)
    status: str = Field(default='pending', max_length=20)
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RebalanceExecution(BaseModel):
    """rebalance_execution 테이블 모델"""
    execution_id: Optional[int] = None
    order_id: int
    executed_qty: Optional[int] = Field(None, ge=0)
    executed_price: Optional[float] = Field(None, ge=0)
    executed_at: Optional[datetime] = None
    fees: Optional[float] = Field(None, ge=0)
    status: str = Field(default='pending', max_length=20)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# =====================================================
# Migration Log (메타데이터)
# =====================================================

class MigrationLog(BaseModel):
    """migration_log 테이블 모델"""
    id: Optional[int] = None
    migration_name: str = Field(..., max_length=100)
    executed_at: Optional[datetime] = None
    status: str = Field(default='success', max_length=20)
    details: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# =====================================================
# Analysis Tables (Phase 14 - Strategy Validation & Parameter Optimization)
# =====================================================

class AnalysisRollingStats(BaseModel):
    """analysis_rolling_stats 테이블 모델

    Pre-computed rolling statistics for parameter derivation.
    Stores volatility, ATR, and return distributions.
    """
    symbol: str = Field(..., max_length=20)
    stat_time: datetime
    window_minutes: int = Field(..., ge=1)  # 5, 10, 30, 60, 240
    source_table: str = Field(..., max_length=20)  # 'scalp_1m_bars' or 'swing_bars_10m'

    # Price Statistics
    price_mean: Optional[float] = None
    price_stddev: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None

    # Return Statistics
    return_mean: Optional[float] = None
    return_stddev: Optional[float] = None
    return_skew: Optional[float] = None
    return_kurtosis: Optional[float] = None

    # Volatility Metrics
    atr_n: Optional[float] = None  # Average True Range
    volatility_pct: Optional[float] = None  # Annualized volatility
    high_low_range: Optional[float] = None  # max(high) - min(low)

    # Volume Statistics
    volume_mean: Optional[int] = None
    volume_stddev: Optional[float] = None
    vwap: Optional[float] = None  # Volume-Weighted Average Price

    # Data Quality
    bar_count: Optional[int] = None
    coverage_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Metadata
    computed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisThresholdCandidate(BaseModel):
    """analysis_threshold_candidates 테이블 모델

    Stores evaluated entry/exit threshold combinations with backtest metrics.
    Used for parameter optimization.
    """
    candidate_id: Optional[int] = None

    # Target
    symbol: str = Field(..., max_length=20)
    strategy_type: str = Field(..., max_length=20)  # 'scalp', 'swing', 'portfolio'
    analysis_time: Optional[datetime] = None

    # Threshold Parameters
    entry_threshold_pct: float = Field(...)
    exit_threshold_pct: float = Field(...)
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    holding_period_minutes: Optional[int] = None

    # Backtest Period
    backtest_start: datetime
    backtest_end: datetime

    # Performance Metrics
    total_trades: Optional[int] = Field(None, ge=0)
    winning_trades: Optional[int] = Field(None, ge=0)
    losing_trades: Optional[int] = Field(None, ge=0)
    win_rate: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Return Metrics
    total_return_pct: Optional[float] = None
    avg_return_pct: Optional[float] = None
    max_return_pct: Optional[float] = None
    min_return_pct: Optional[float] = None

    # Risk Metrics
    profit_factor: Optional[float] = Field(None, ge=0)
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    avg_drawdown_pct: Optional[float] = None

    # Statistical Significance
    t_statistic: Optional[float] = None
    p_value: Optional[float] = None

    # Configuration
    config_hash: Optional[str] = Field(None, max_length=64)
    session_id: Optional[str] = Field(None, max_length=50)

    # Ranking
    rank_score: Optional[float] = None
    is_optimal: bool = Field(default=False)

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisSignalEvent(BaseModel):
    """analysis_signal_events 테이블 모델

    Captures signal frame events when conditions are met.
    Used for pattern analysis and outcome tracking.
    """
    event_id: Optional[int] = None

    # Event Identification
    symbol: str = Field(..., max_length=20)
    event_time: datetime
    source_table: str = Field(..., max_length=20)

    # Time Features
    delta_t_prev: Optional[float] = None  # Seconds since previous event
    bucket_index: Optional[int] = None
    relative_position: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Frequency Features
    event_count_last_n: Optional[int] = None
    event_density_last_n: Optional[float] = None  # Events per second
    same_pattern_streak: Optional[int] = None

    # Volatility Features
    value_diff_abs: Optional[float] = None
    value_diff_pct: Optional[float] = None
    rolling_range_n: Optional[float] = None

    # Condition Flags
    value_change_exceeds_x: Optional[bool] = None
    event_frequency_exceeds_n: Optional[bool] = None
    consecutive_events_ge_n: Optional[bool] = None
    pattern_reappeared_within_t: Optional[bool] = None

    # Condition Parameters Used
    threshold_x: Optional[float] = None  # value_change threshold
    threshold_n: Optional[int] = None  # frequency threshold
    threshold_streak: Optional[int] = None  # consecutive threshold
    threshold_t_seconds: Optional[float] = None  # pattern window

    # Price Context
    price_at_signal: Optional[float] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    spread_pct: Optional[float] = None

    # Outcome Tracking (filled after signal)
    price_after_1m: Optional[float] = None
    price_after_5m: Optional[float] = None
    price_after_10m: Optional[float] = None
    return_1m_pct: Optional[float] = None
    return_5m_pct: Optional[float] = None
    return_10m_pct: Optional[float] = None

    # Metadata
    config_version: str = Field(default='1.0', max_length=20)
    session_id: Optional[str] = Field(None, max_length=50)
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# =====================================================
# 모델 그룹핑 (편의성)
# =====================================================

# Scalp 모델들
SCALP_MODELS = [ScalpTick, Scalp1mBar, ScalpGap]

# Swing 모델들
SWING_MODELS = [SwingBar10m]

# Portfolio 모델들
PORTFOLIO_MODELS = [
    PortfolioPolicy,
    TargetWeight,
    PortfolioSnapshot,
    PortfolioPosition,
    RebalancePlan,
    RebalanceOrder,
    RebalanceExecution
]

# Analysis 모델들 (Phase 14)
ANALYSIS_MODELS = [
    AnalysisRollingStats,
    AnalysisThresholdCandidate,
    AnalysisSignalEvent
]

# 모든 모델
ALL_MODELS = SCALP_MODELS + SWING_MODELS + PORTFOLIO_MODELS + ANALYSIS_MODELS + [MigrationLog]
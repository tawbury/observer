import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.provider.kis.kis_rest_provider import KISRestProvider, RateLimiter

@pytest.fixture
def mock_auth():
    auth = MagicMock()
    auth.base_url = "https://mock.api.com"
    auth.ensure_token = AsyncMock()
    auth.get_headers = MagicMock(return_value={"Authorization": "Bearer token"})
    auth.get_session = AsyncMock()
    auth.emergency_refresh = AsyncMock()
    return auth

@pytest.fixture
def provider(mock_auth):
    rate_limiter = RateLimiter(requests_per_second=1000, requests_per_minute=10000)
    p = KISRestProvider(auth=mock_auth, rate_limiter=rate_limiter)
    p.max_retries = 3
    return p

@pytest.mark.asyncio
async def test_fetch_stock_list_merging(provider, mock_auth):
    """KOSPI와 KOSDAQ 리스트가 정상적으로 병합되는지 확인"""
    
    # Mock responses for KOSPI and KOSDAQ
    kospi_data = {
        "rt_cd": "0",
        "msg1": "정상",
        "output": [{"pdno": "005930"}, {"pdno": "000660"}]
    }
    kosdaq_data = {
        "rt_cd": "0",
        "msg1": "정상",
        "output": [{"pdno": "068270"}, {"pdno": "091990"}]
    }
    
    mock_session = AsyncMock()
    mock_auth.get_session.return_value = mock_session
    
    # Setup session.get to return kospi then kosdaq
    mock_response_kospi = MagicMock()
    mock_response_kospi.status = 200
    mock_response_kospi.json = AsyncMock(return_value=kospi_data)
    mock_response_kospi.headers = {"tr_cont": "F"}
    
    mock_response_kosdaq = MagicMock()
    mock_response_kosdaq.status = 200
    mock_response_kosdaq.json = AsyncMock(return_value=kosdaq_data)
    mock_response_kosdaq.headers = {"tr_cont": "D"}
    
    mock_session.get.side_effect = [
        MagicMock(__aenter__=AsyncMock(return_value=mock_response_kospi)),
        MagicMock(__aenter__=AsyncMock(return_value=mock_response_kosdaq))
    ]
    
    symbols = await provider.fetch_stock_list(market="ALL")
    
    assert len(symbols) == 4
    assert "005930" in symbols
    assert "091990" in symbols
    assert symbols == sorted(symbols)

@pytest.mark.asyncio
async def test_fetch_stock_list_pagination(provider, mock_auth):
    """페이지네이션(tr_cont)이 정상적으로 동작하는지 확인"""
    
    page1_data = {
        "rt_cd": "0",
        "output": [{"pdno": "111111"}]
    }
    page2_data = {
        "rt_cd": "0",
        "output": [{"pdno": "222222"}]
    }
    
    mock_session = AsyncMock()
    mock_auth.get_session.return_value = mock_session
    
    mock_res1 = MagicMock()
    mock_res1.status = 200
    mock_res1.json = AsyncMock(return_value=page1_data)
    mock_res1.headers = {"tr_cont": "M"}
    
    mock_res2 = MagicMock()
    mock_res2.status = 200
    mock_res2.json = AsyncMock(return_value=page2_data)
    mock_res2.headers = {"tr_cont": "F"}
    
    mock_session.get.side_effect = [
        MagicMock(__aenter__=AsyncMock(return_value=mock_res1)),
        MagicMock(__aenter__=AsyncMock(return_value=mock_res2))
    ]
    
    symbols = await provider.fetch_stock_list(market="KOSPI")
    
    assert len(symbols) == 2
    assert "111111" in symbols
    assert "222222" in symbols
    assert mock_session.get.call_count == 2

@pytest.mark.asyncio
async def test_fetch_stock_list_retry_mechanism(provider, mock_auth):
    """API 실패 시 재시도 로직이 동작하는지 확인"""
    
    error_data = {"rt_cd": "1", "msg1": "API Error"}
    success_data = {"rt_cd": "0", "output": [{"pdno": "333333"}]}
    
    mock_session = AsyncMock()
    mock_auth.get_session.return_value = mock_session
    
    mock_res_err = MagicMock()
    mock_res_err.status = 200
    mock_res_err.json = AsyncMock(return_value=error_data)
    mock_res_err.headers = {}
    
    mock_res_succ = MagicMock()
    mock_res_succ.status = 200
    mock_res_succ.json = AsyncMock(return_value=success_data)
    mock_res_succ.headers = {}
    
    mock_session.get.side_effect = [
        MagicMock(__aenter__=AsyncMock(return_value=mock_res_err)),
        MagicMock(__aenter__=AsyncMock(return_value=mock_res_err)),
        MagicMock(__aenter__=AsyncMock(return_value=mock_res_succ))
    ]
    
    with patch("asyncio.sleep", AsyncMock()):
        symbols = await provider.fetch_stock_list(market="KOSPI")
    
    assert len(symbols) == 1
    assert "333333" in symbols
    assert mock_session.get.call_count == 3

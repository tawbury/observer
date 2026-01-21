# Meta
- Document Name: KIS API Skeleton for Observer System
- File Name: kis_api_skeleton_observer.md
- Document ID: API-KIS-001
- Status: Draft
- Created Date: 2026-01-20
- Last Updated: 2026-01-20
- Author: Developer Agent
- Parent Document: .ai/workflows/stock_trading_system.workflow.md
- Related Reference: https://github.com/koreainvestment/open-trading-api
- Version: 1.0.0

---

# KIS API Skeleton for Observer System

## Purpose
Comprehensive API skeleton document for Korea Investment & Securities (KIS) Open API integration with the Observer trading system, covering authentication, data collection, trading operations, and real-time monitoring.

## API Overview
KIS Open API provides RESTful endpoints and WebSocket connections for:
- **Market Data**: Domestic/overseas stock prices, indices, fundamental data
- **Trading Operations**: Order placement, cancellation, balance inquiry
- **Account Management**: Portfolio information, transaction history
- **Real-time Data**: WebSocket streaming for live price updates

## Authentication System

### API Credentials Structure
```yaml
# kis_devlp.yaml - Configuration File
# 실전투자 (Production)
my_app: "실전투자 앱키"
my_sec: "실전투자 앱시크릿"

# 모의투자 (Simulation)
paper_app: "모의투자 앱키"
paper_sec: "모의투자 앱시크릿"

# Account Information
my_htsid: "HTS ID (KIS Developers 고객 ID)"
my_acct_stock: "증권계좌 8자리"
my_acct_future: "선물옵션계좌 8자리"
my_paper_stock: "모의투자 증권계좌 8자리"

# Environment Configuration
base_url_real: "https://openapi.koreainvestment.com:9443"
base_url_virtual: "https://openapivts.koreainvestment.com:29443"
```

### Authentication Flow
```python
# kis_auth.py - Core Authentication Module
import yaml
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional

class KISAuth:
    def __init__(self, config_path: str = "kis_devlp.yaml", is_virtual: bool = True):
        self.config = self._load_config(config_path)
        self.is_virtual = is_virtual
        self.base_url = self.config['base_url_virtual'] if is_virtual else self.config['base_url_real']
        self.access_token = None
        self.token_expires = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Load KIS API configuration"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    async def ensure_token(self) -> str:
        """Ensure valid access token"""
        if not self.access_token or self._is_token_expired():
            await self._refresh_token()
        return self.access_token
    
    async def _refresh_token(self) -> None:
        """Refresh access token"""
        app_key = self.config['paper_app'] if self.is_virtual else self.config['my_app']
        app_secret = self.config['paper_sec'] if self.is_virtual else self.config['my_sec']
        
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "appkey": app_key,
            "appsecret": app_secret
        }
        
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        
        if result.get("error_description"):
            raise RuntimeError(f"Token refresh failed: {result['error_description']}")
        
        self.access_token = result["access_token"]
        self.token_expires = datetime.now() + timedelta(seconds=3600)  # 1 hour
    
    def _is_token_expired(self) -> bool:
        """Check if token is expired"""
        return not self.token_expires or datetime.now() >= self.token_expires
    
    def get_headers(self, tr_id: str, cust_type: str = "P") -> Dict[str, str]:
        """Get standard API headers"""
        app_key = self.config['paper_app'] if self.is_virtual else self.config['my_app']
        app_secret = self.config['paper_sec'] if self.is_virtual else self.config['my_sec']
        
        return {
            "authorization": f"Bearer {self.access_token}",
            "appkey": app_key,
            "appsecret": app_secret,
            "tr_id": tr_id,
            "custtype": cust_type
        }
```

## Domestic Stock APIs

### Market Data APIs

#### 1. Daily OHLCV Data
```python
# /uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice
async def fetch_daily_ohlcv(
    self, 
    stock_code: str, 
    days: int = 200,
    start_date: str = "",
    end_date: str = ""
) -> pd.DataFrame:
    """
    국내 주식 일봉 데이터 조회
    
    Args:
        stock_code: 6자리 종목코드 (예: "005930" - 삼성전자)
        days: 조회할 일수 (최대 200일)
        start_date: 시작일 (YYYYMMDD, 빈 값이면 오늘부터)
        end_date: 종료일 (YYYYMMDD, 빈 값이면 오늘까지)
    
    Returns:
        DataFrame with columns: date, open, high, low, close, volume, value
    """
    await self.ensure_token()
    
    url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    headers = self.get_headers("FHKST03010100")
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",  # J: 전체(코스피+코스닥)
        "FID_INPUT_ISCD": stock_code,
        "FID_INPUT_DATE_1": start_date,
        "FID_INPUT_DATE_2": end_date,
        "FID_PERIOD_DIV_CODE": "D",  # D: 일봉
    }
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if data["rt_cd"] != "0":
        raise RuntimeError(f"API 오류: {data['msg1']}")
    
    # 데이터 변환
    output = data["output2"]
    df = pd.DataFrame(output)
    df.columns = ["date", "open", "high", "low", "close", "volume", "value"]
    
    # 데이터 타입 변환
    df["date"] = pd.to_datetime(df["date"])
    for col in ["open", "high", "low", "close", "volume", "value"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df.sort_values("date").reset_index(drop=True).tail(days)
```

#### 2. Current Price Information
```python
# /uapi/domestic-stock/v1/quotations/inquire-price
async def fetch_current_price(self, stock_code: str) -> Dict[str, any]:
    """
    국내 주식 현재가 조회
    
    Args:
        stock_code: 6자리 종목코드
    
    Returns:
        Dict containing current price information
    """
    await self.ensure_token()
    
    url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = self.get_headers("FHKST01010100")
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
    }
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if data["rt_cd"] != "0":
        raise RuntimeError(f"API 오류: {data['msg1']}")
    
    output = data["output"]
    return {
        "stock_code": stock_code,
        "timestamp": pd.Timestamp.now(),
        "current_price": float(output["stck_prpr"]),
        "open": float(output["stck_oprc"]),
        "high": float(output["stck_hgpr"]),
        "low": float(output["stck_lwpr"]),
        "volume": float(output["acml_vol"]),
        "trading_value": float(output["acml_tr_pbmn"]),
        "market_cap": float(output.get("hts_avls", 0)),
        "per": float(output.get("per", 0)),
        "pbr": float(output.get("pbr", 0)),
        "eps": float(output.get("eps", 0)),
        "week_52_high": float(output.get("w52_hgpr", 0)),
        "week_52_low": float(output.get("w52_lwpr", 0)),
        "listed_shares": int(output.get("lstn_stcn", 0)),
    }
```

#### 3. Order Book (Hoga) Information
```python
# /uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn
async def fetch_order_book(self, stock_code: str) -> Dict[str, any]:
    """
    호가창 정보 조회
    
    Args:
        stock_code: 6자리 종목코드
    
    Returns:
        Dict containing order book data
    """
    await self.ensure_token()
    
    url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"
    headers = self.get_headers("FHKST01010200")
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
    }
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if data["rt_cd"] != "0":
        raise RuntimeError(f"API 오류: {data['msg1']}")
    
    output = data["output"]
    
    # 호가 데이터 구조화
    order_book = {
        "stock_code": stock_code,
        "timestamp": pd.Timestamp.now(),
        "total_ask_price": float(output["total_askp_rsqn"]),
        "total_bid_price": float(output["total_bidl_rsqn"]),
        "asks": [],  # 매도 호가
        "bids": [],  # 매수 호가
    }
    
    # 매도 호가 (1~10호가)
    for i in range(1, 11):
        ask_price = output.get(f"askp{i}", 0)
        ask_qty = output.get(f"askp{i}_rsqn", 0)
        if ask_price and ask_qty:
            order_book["asks"].append({
                "price": float(ask_price),
                "quantity": int(ask_qty),
                "order": i
            })
    
    # 매수 호가 (1~10호가)
    for i in range(1, 11):
        bid_price = output.get(f"bidp{i}", 0)
        bid_qty = output.get(f"bidp{i}_rsqn", 0)
        if bid_price and bid_qty:
            order_book["bids"].append({
                "price": float(bid_price),
                "quantity": int(bid_qty),
                "order": i
            })
    
    return order_book
```

### Trading APIs

#### 1. Account Balance Inquiry
```python
# /uapi/domestic-stock/v1/trading/inquire-balance
async def fetch_account_balance(self) -> Dict[str, any]:
    """
    계좌 잔고 조회
    
    Returns:
        Dict containing account balance information
    """
    await self.ensure_token()
    
    account_no = self.config['my_paper_stock'] if self.is_virtual else self.config['my_acct_stock']
    
    url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
    headers = self.get_headers("TTTC8434R")
    params = {
        "CANO": account_no[:8],  # 종합계좌번호 8자리
        "ACNT_PRDT_CD": "01",    # 계좌상품코드 (01: 증권계좌)
        "AFHR_FLPR_YN": "N",     # 섹터플러스 사용여부
        "FNCG_AMT_AUTO_RDPT_YN": "N",  # 자동이체금액 여부
        "INQR_DVSN": "01",       # 조회구분 (01: 순매수도가능수량)
        "UNPR_DVSN": "01",       # 단가구분 (01: 평균단가)
        "CTX_AREA_FK100": "",    # 연속조회키
        "CTX_AREA_NK100": ""     # 연속조회키
    }
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if data["rt_cd"] != "0":
        raise RuntimeError(f"API 오류: {data['msg1']}")
    
    output1 = data.get("output1", [{}])[0]  # 계좌정보
    output2 = data.get("output2", [])       # 종목별 잔고정보
    
    return {
        "account_no": account_no,
        "timestamp": pd.Timestamp.now(),
        "total_deposit": float(output1.get("dnca_tot_amt", 0)),      # 총예수금
        "withdrawal_amount": float(output1.get("withdrawable_amt", 0)), # 출금가능금액
        "orderable_amount": float(output1.get("ord_psbl_amt", 0)),   # 주문가능금액
        "total_evaluation": float(output1.get("tot_evlu_amt", 0)),   # 총평가금액
        "total_profit_loss": float(output1.get("tot_pfls_amt", 0)),  # 총손익금액
        "total_profit_loss_rate": float(output1.get("tot_pfls_rt", 0)), # 총손익수익률
        "positions": [
            {
                "stock_code": pos.get("pdno", ""),
                "stock_name": pos.get("dtl", ""),
                "quantity": int(pos.get("hldg_qty", 0)),
                "avg_price": float(pos.get("pchs_avg_prc", 0)),
                "current_price": float(pos.get("prpr", 0)),
                "evaluation": float(pos.get("evlu_amt", 0)),
                "profit_loss": float(pos.get("pfls_amt", 0)),
                "profit_loss_rate": float(pos.get("pfls_rt", 0)),
            } for pos in output2
        ]
    }
```

#### 2. Order Placement
```python
# /uapi/domestic-stock/v1/trading/order-cash
async def place_order(
    self,
    stock_code: str,
    order_type: str,  # "buy" or "sell"
    quantity: int,
    price: int = 0,  # 0이면 시장가
    order_condition: str = "00"  # 00: 일반, 01: IOC, 02: FOK
) -> Dict[str, any]:
    """
    주식 주문
    
    Args:
        stock_code: 6자리 종목코드
        order_type: "buy" 또는 "sell"
        quantity: 주문수량
        price: 주문가격 (0이면 시장가)
        order_condition: 주문조건
    
    Returns:
        Dict containing order result
    """
    await self.ensure_token()
    
    account_no = self.config['my_paper_stock'] if self.is_virtual else self.config['my_acct_stock']
    
    url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
    
    # 매수/매도에 따른 tr_id 결정
    if order_type.lower() == "buy":
        tr_id = "TTTC0802U" if self.is_virtual else "TTTC0802U"
        buy_sell_code = "2"  # 매수
    else:
        tr_id = "TTTC0801U" if self.is_virtual else "TTTC0801U"
        buy_sell_code = "1"  # 매도
    
    headers = self.get_headers(tr_id)
    params = {
        "CANO": account_no[:8],
        "ACNT_PRDT_CD": "01",
        "PDNO": stock_code,
        "ORD_DVSN": "01" if price > 0 else "02",  # 01: 지정가, 02: 시장가
        "ORD_QTY": str(quantity),
        "ORD_UNPR": str(price) if price > 0 else "0",
        "NOOE_UND": "0",  # 주문통화코드
        "ORD_WAY": buy_sell_code,
        "BRNC_ABRG": "0",  # 지점코드
        "CTAC_ABRG": "0",  # 계좌코드
        "SLL_BUY_DVSN_CD": buy_sell_code,
        "ORD_SVC_DVSN_CD": "0",  # 주문서비스구분코드
        "ALGO_NO": "",  # 알고리즘번호
        "ORD_GNO_CNSC_CD": "0",  # 주문그룹종속코드
        "RMNS_ATFL_APLY_YN": "N",  # 잔량연장적용여부
        "ORD_ABNR_RMSN_YN": "N",  # 주문이상해지여부
        "ORD_MNS_YN": "N",  # 주문만기여부
        "ORD_CNCS_DVSN_CD": "0",  # 주문체결구분코드
        "ORD_MNNO_DVSN_CD": "0",  # 주문번호구분코드
        "ORD_DYNT_TYPE_CD": "0",  # 주문동시구분코드
        "ORD_PTT_CD": order_condition,  # 주문조건구분코드
        "ORD_DVSN_DVCD": "0",  # 주문구분상세코드
        "ORD_TMD_DVCD": "0",  # 주문시간구분코드
    }
    
    response = requests.post(url, headers=headers, data=params)
    data = response.json()
    
    if data["rt_cd"] != "0":
        raise RuntimeError(f"주문 실패: {data['msg1']}")
    
    output = data["output"]
    return {
        "order_no": output.get("ODNO", ""),
        "order_time": output.get("ORD_TMD", ""),
        "stock_code": stock_code,
        "order_type": order_type,
        "quantity": quantity,
        "price": price,
        "status": "ordered"
    }
```

## Overseas Stock APIs

### Market Data
```python
# /uapi/overseas-price/v1/quotations/price/{market}/{symbol}
async def fetch_overseas_price(
    self, 
    market: str,  # NASD, NYSE, AMEX 등
    symbol: str   # AAPL, TSLA 등
) -> Dict[str, any]:
    """
    해외주식 현재가 조회
    
    Args:
        market: 시장코드 (NASD, NYSE, AMEX)
        symbol: 종목심볼
    
    Returns:
        Dict containing overseas stock price information
    """
    await self.ensure_token()
    
    url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price/{market}/{symbol}"
    headers = self.get_headers("HHDFS76240000")
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    if data["rt_cd"] != "0":
        raise RuntimeError(f"API 오류: {data['msg1']}")
    
    output = data["output"]
    return {
        "symbol": symbol,
        "market": market,
        "timestamp": pd.Timestamp.now(),
        "current_price": float(output["last"]),
        "open": float(output["open"]),
        "high": float(output["high"]),
        "low": float(output["low"]),
        "volume": int(output["volum"]),
        "previous_close": float(output["clpr"]),
        "change": float(output["vs"]),
        "change_rate": float(output["vs_rate"]),
        "market_cap": float(output.get("mrktTotAmt", 0)),
        "exchange_rate": float(output.get("exrt", 0)),
    }
```

## WebSocket Real-time Data

### WebSocket Connection Manager
```python
# kis_websocket.py - WebSocket Real-time Data Manager
import asyncio
import json
import websockets
from typing import Callable, Dict, List

class KISWebSocketManager:
    def __init__(self, auth: KISAuth):
        self.auth = auth
        self.websocket = None
        self.subscriptions: Dict[str, Callable] = {}
        self.is_connected = False
        
    async def connect(self) -> None:
        """WebSocket 연결"""
        approval_key = self.auth.config.get("approval_key", "")
        
        # WebSocket URL (모의투자/실전투자 구분)
        if self.auth.is_virtual:
            ws_url = "ws://ops.koreainvestment.com:21000"
        else:
            ws_url = "ws://ops.koreainvestment.com:31000"
        
        headers = {
            "Authorization": f"Bearer {self.auth.access_token}",
            "AppKey": self.auth.config['paper_app'] if self.auth.is_virtual else self.auth.config['my_app'],
            "AppSecret": self.auth.config['paper_sec'] if self.auth.is_virtual else self.auth.config['my_sec'],
            "Approval-Key": approval_key,
        }
        
        self.websocket = await websockets.connect(ws_url, extra_headers=headers)
        self.is_connected = True
        
        # 메시지 수신 루프
        asyncio.create_task(self._message_loop())
    
    async def subscribe_domestic_stock(self, stock_code: str, callback: Callable) -> None:
        """국내주식 실시간 시세 구독"""
        tr_id = "H0STCNT0"  # 실시간 체결가
        subscription_key = f"{tr_id}_{stock_code}"
        
        self.subscriptions[subscription_key] = callback
        
        subscription_data = {
            "header": {
                "tr_id": tr_id,
                "tr_key": stock_code
            },
            "body": {}
        }
        
        await self.websocket.send(json.dumps(subscription_data))
    
    async def _message_loop(self) -> None:
        """WebSocket 메시지 수신 처리"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            self.is_connected = False
            # 재연결 로직
            await self._reconnect()
    
    async def _handle_message(self, data: Dict) -> None:
        """수신 메시지 처리"""
        tr_id = data.get("header", {}).get("tr_id", "")
        tr_key = data.get("header", {}).get("tr_key", "")
        subscription_key = f"{tr_id}_{tr_key}"
        
        if subscription_key in self.subscriptions:
            callback = self.subscriptions[subscription_key]
            await callback(data.get("body", {}))
    
    async def disconnect(self) -> None:
        """WebSocket 연결 종료"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
```

## Error Handling & Rate Limiting

### Error Handler
```python
class KISAPIError(Exception):
    """KIS API 커스텀 에러"""
    def __init__(self, error_code: str, message: str, tr_id: str = ""):
        self.error_code = error_code
        self.message = message
        self.tr_id = tr_id
        super().__init__(f"[{error_code}] {message}")

class KISRateLimitError(KISAPIError):
    """API Rate Limit 에러"""
    pass

class KISTokenError(KISAPIError):
    """토큰 관련 에러"""
    pass

def handle_api_error(response_data: Dict, tr_id: str = "") -> None:
    """API 응답 에러 처리"""
    if response_data.get("rt_cd") != "0":
        error_code = response_data.get("msg_cd", "")
        error_message = response_data.get("msg1", "")
        
        if error_code.startswith("EGW"):  # Rate Limit
            raise KISRateLimitError(error_code, error_message, tr_id)
        elif error_code in ["EGW00223", "EGW00224"]:  # Token Error
            raise KISTokenError(error_code, error_message, tr_id)
        else:
            raise KISAPIError(error_code, error_message, tr_id)
```

## Data Structures & Models

### Market Data Models
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class StockPrice:
    stock_code: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    trading_value: Optional[int] = None
    market_cap: Optional[float] = None
    per: Optional[float] = None
    pbr: Optional[float] = None

@dataclass
class OrderBook:
    stock_code: str
    timestamp: datetime
    asks: List[Dict[str, any]]
    bids: List[Dict[str, any]]
    total_ask_price: float
    total_bid_price: float

@dataclass
class AccountPosition:
    stock_code: str
    stock_name: str
    quantity: int
    avg_price: float
    current_price: float
    evaluation: float
    profit_loss: float
    profit_loss_rate: float

@dataclass
class OrderResult:
    order_no: str
    order_time: str
    stock_code: str
    order_type: str
    quantity: int
    price: int
    status: str
```

## Configuration & Environment Setup

### Environment Variables
```python
# .env file example
KIS_APP_KEY_REAL=your_real_app_key
KIS_APP_SECRET_REAL=your_real_app_secret
KIS_APP_KEY_VIRTUAL=your_virtual_app_key
KIS_APP_SECRET_VIRTUAL=your_virtual_app_secret
KIS_ACCOUNT_NUMBER=your_account_number
KIS_VIRTUAL_ACCOUNT=your_virtual_account
KIS_HTS_ID=your_hts_id
KIS_APPROVAL_KEY=your_approval_key
```

### Usage Examples
```python
# Basic Usage Example
async def main():
    # Initialize KIS API
    kis = KISAuth(config_path="kis_devlp.yaml", is_virtual=True)
    
    # Fetch daily OHLCV data
    daily_data = await kis.fetch_daily_ohlcv("005930", days=30)
    print(daily_data.head())
    
    # Fetch current price
    current_price = await kis.fetch_current_price("005930")
    print(f"Current Price: {current_price['current_price']}")
    
    # Get account balance
    balance = await kis.fetch_account_balance()
    print(f"Total Deposit: {balance['total_deposit']}")
    
    # Place order
    order_result = await kis.place_order(
        stock_code="005930",
        order_type="buy",
        quantity=10,
        price=85000
    )
    print(f"Order No: {order_result['order_no']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Integration Points for Observer System

### Data Pipeline Integration
1. **Scheduled Data Collection**: Daily OHLCV data for strategy backtesting
2. **Real-time Monitoring**: WebSocket streaming for live trading signals
3. **Portfolio Tracking**: Regular balance inquiries for risk management
4. **Order Execution**: Automated order placement based on trading signals

### Risk Management Integration
1. **Position Limits**: Pre-trade validation against risk parameters
2. **Loss Monitoring**: Real-time P&L tracking and stop-loss triggers
3. **Circuit Breakers**: Automatic trading suspension on excessive losses
4. **Compliance Logging**: All trading operations audit trail

### Performance Optimization
1. **Batch Processing**: Multiple stock data requests in parallel
2. **Caching Strategy**: Frequently accessed data caching
3. **Rate Limiting**: API call throttling and retry logic
4. **Error Recovery**: Robust error handling and automatic reconnection

---

## Next Steps for Implementation

1. **Complete API Coverage**: Add remaining API endpoints (futures, options, bonds)
2. **Testing Suite**: Comprehensive unit and integration tests
3. **Documentation**: API reference documentation with examples
4. **Monitoring**: API usage monitoring and alerting
5. **Security**: Enhanced security measures for credential management

---

*This skeleton provides the foundation for integrating KIS Open API with the Observer trading system, covering essential functionality for data collection, trading operations, and real-time monitoring.*

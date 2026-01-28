# Track B WebSocket Implementation - KIS API Compliance Review

**Review Date**: 2025-01-25  
**Focus**: Track B code compliance against KIS official API specifications  
**Status**: 🔴 CRITICAL GAPS IDENTIFIED - Requires immediate fixes before market hours testing

---

## 📋 Executive Summary

Track B WebSocket implementation has **3 critical gaps** and **5 warnings** that violate KIS official API specifications. These must be fixed before production testing during market hours.

| Category | Count | Severity |
|----------|-------|----------|
| Critical API Violations | 3 | 🔴 MUST FIX |
| Warnings/Best Practices | 5 | 🟡 SHOULD FIX |
| Missing Fields | 4+ | 🟠 IMPACT |

---

## 🔴 CRITICAL GAPS

### 1. **Approval Key NOT Used in WebSocket Authentication** ⛔ CRITICAL

**Issue**: KIS official samples REQUIRE `approval_key` in WebSocket header, but your code is missing it.

**KIS Official Spec** (from legacy/websocket/python/ws_domestic_stock.py):
```python
# Official: Uses approval_key
_h = {
    "approval_key": app_key,  # ← REQUIRED for WebSocket
    "custtype": 'P',
    "tr_type": tr_type,
    "content-type": "utf-8"
}
```

**Your Code** (kis_websocket_provider.py line ~310):
```python
subscription_msg = {
    "header": {
        "appkey": self.auth.app_key,        # ← WRONG FIELD NAME
        "appsecret": self.auth.app_secret,  # ← WRONG (WebSocket doesn't use this)
        "custtype": "P",
        "tr_type": "1",
        "content-type": "utf-8",
    },
    "body": { ... }
}
```

**Fix Required**:
```python
# Correct header format per KIS docs
subscription_msg = {
    "header": {
        "approval_key": approval_key,  # ← Get from KISAuth.get_approval_key()
        "custtype": "P",
        "tr_type": "1",
        "content-type": "utf-8",
    },
    "body": { ... }
}
```

**Impact**: 
- ❌ Subscription requests will FAIL
- ❌ Server may return error or ignore subscription
- 💀 No real-time data will be received

**KIS Reference**:
- `legacy/Sample01/kis_domstk_ws.py` line 274-303
- `legacy/websocket/python/ws_domestic_stock.py` line 165-183

---

### 2. **TR_TYPE "1" is WRONG for Unsubscribe** ⛔ CRITICAL

**Issue**: Unsubscribe uses `tr_type: "1"` (subscribe), should be `"0"` or `"2"`.

**KIS Official Spec**:
- `tr_type: "1"` = Subscribe
- `tr_type: "0"` or `"2"` = Unsubscribe

**Your Code** (kis_websocket_provider.py line ~333):
```python
async def _send_unsubscription_request(self, symbol: str) -> None:
    unsubscription_msg = {
        "header": {
            ...
            "tr_type": "1",  # ← WRONG: This means subscribe, not unsubscribe
            ...
        },
        "body": {
            "input": {
                "tr_id": self.MSG_UNSUBSCRIBE,  # ← H0STCNT9 is correct
                "tr_key": symbol,
            }
        }
    }
```

**Correct Implementation**:
```python
async def _send_unsubscription_request(self, symbol: str) -> None:
    unsubscription_msg = {
        "header": {
            "approval_key": approval_key,
            "custtype": "P",
            "tr_type": "0",  # ← CORRECT: 0 or 2 for unsubscribe
            "content-type": "utf-8",
        },
        "body": {
            "input": {
                "tr_id": "H0STCNT0",  # Note: Still H0STCNT0, not H0STCNT9
                "tr_key": symbol,
            }
        }
    }
```

**Impact**:
- ❌ Symbol unsubscription will fail
- ❌ Slot replacement will not free up slots
- 💀 All 41 slots will be exhausted after ~41 replacements

**KIS Reference**:
- `legacy/websocket/python/ws_domestic_stock.py` line 171-174: Shows tr_type='2' for unsubscribe
- `legacy/websocket/python/ws_domestic_stock.py` line 233: Shows tr_type values

---

### 3. **WebSocket URL is WRONG Endpoint** ⛔ CRITICAL

**Issue**: Code tries `wss://openapi.koreainvestment.com:9443/websocket`, but KIS official uses different port/endpoint.

**Your Code** (kis_websocket_provider.py line ~79):
```python
WEBSOCKET_URL = "wss://openapi.koreainvestment.com:9443/websocket"
```

**KIS Official Specs**:
```python
# Real: ws://ops.koreainvestment.com:21000  (or :31000 for virtual)
# Virtual: ws://ops.koreainvestment.com:31000
url = 'ws://ops.koreainvestment.com:21000'  # Real
url = 'ws://ops.koreainvestment.com:31000'  # Virtual
```

From `legacy/websocket/python/ws_domestic_stock.py` line 145:
```python
# url = 'ws://ops.koreainvestment.com:31000' # 모의투자계좌
url = 'ws://ops.koreainvestment.com:21000'  # 실전투자계좌
```

**Your Code Fallback** (kis_websocket_provider.py line ~107):
```python
default_candidates = (
    [
        "ws://ops.koreainvestment.com:21000",  # ← Actually correct here!
        self.WEBSOCKET_URL,  # ← But uses wrong wss:// endpoint as fallback
    ]
    if is_virtual
    else [
        "ws://ops.koreainvestment.com:31000",
        self.WEBSOCKET_URL,
    ]
)
```

**Issue**: Virtual/Real endpoints are SWAPPED!
- Virtual should use `:31000`
- Real should use `:21000`

**Correct Endpoint Setup**:
```python
# Fix: Correct endpoint selection
if is_virtual:
    self.websocket_candidates = [
        "ws://ops.koreainvestment.com:31000",  # Virtual
        "wss://openapi.koreainvestment.com:9443/websocket"  # Fallback
    ]
else:
    self.websocket_candidates = [
        "ws://ops.koreainvestment.com:21000",  # Real (production)
        "wss://openapi.koreainvestment.com:9443/websocket"  # Fallback
    ]
```

**Impact**:
- ❌ May connect to wrong server environment
- ❌ May connect to SSL endpoint when plain ws expected
- 💀 Connection may fail or connect to unintended environment

**KIS Reference**:
- `legacy/websocket/python/ws_domestic_stock.py` line 145-146
- `legacy/websocket/python/ws_domestic_future.py` line 150-151
- `legacy/websocket/python/ws_domestic_overseas_all.py` line 1075-1076

---

## 🟡 WARNINGS - Should Fix

### 4. **Missing EUC-KR Decoding for Real Data** ⚠️ WARNING

**Issue**: Code attempts EUC-KR decoding (line 397), but KIS real-time data format may be pipe-delimited (not JSON).

**Your Code** (kis_websocket_provider.py line ~397):
```python
async def _process_message(self, raw_message: bytes | str) -> None:
    if isinstance(raw_message, bytes):
        message_str = raw_message.decode('euc-kr')
    else:
        message_str = raw_message
    
    message_data = json.loads(message_str)  # ← Assumes JSON
```

**KIS Official Format** (from legacy/websocket/python/ws_domestic_stock.py line ~211):
```python
if data[0] == '0' or data[0] == '1':  # Real data
    recvstr = data.split('|')  # ← PIPE-DELIMITED, not JSON!
    trid0 = recvstr[1]
    
    if trid0 == "H0STCNT0":  # Execution data
        data_cnt = int(recvstr[2])  # Data count
        stockspurchase_domestic(data_cnt, recvstr[3])  # Parse pipe-delimited payload
```

**The Problem**:
- Subscription response: JSON ✓ (handled correctly)
- Real-time data: **Pipe-delimited string** ❌ (NOT JSON)

**Expected Format for H0STCNT0** (from official docs):
```
0|H0STCNT0|체결데이터개수|data_payload^data_payload^...
```

Example:
```
0|H0STCNT0|2|005930^123000^50000^...|051910^156000^30000^...
```

**Missing Parsing Logic**:
Your code will FAIL on real tick data because:
1. ✅ First JSON message (subscription response) OK
2. ❌ Second message (actual tick data) = `0|H0STCNT0|...` → JSON parse fails
3. ❌ `on_price_update` callback never fires

**Correct Implementation**:
```python
async def _process_message(self, raw_message: bytes | str) -> None:
    try:
        # Decode if bytes
        if isinstance(raw_message, bytes):
            message_str = raw_message.decode('euc-kr')
        else:
            message_str = raw_message
        
        # Check message type
        if message_str.startswith('0') or message_str.startswith('1'):
            # Real-time data: pipe-delimited format
            await self._process_realtime_data(message_str)
        else:
            # System message: JSON format
            message_data = json.loads(message_str)
            await self._process_json_message(message_data)
    
    except Exception as e:
        logger.error(f"❌ Error processing message: {e}")
```

**Add Method**:
```python
async def _process_realtime_data(self, data_str: str) -> None:
    """Process pipe-delimited real-time data (H0STCNT0)"""
    try:
        parts = data_str.split('|')
        if len(parts) < 4:
            logger.warning(f"Invalid data format: {data_str[:50]}")
            return
        
        msg_type = parts[0]      # '0' for real-time
        tr_id = parts[1]         # 'H0STCNT0'
        data_cnt = int(parts[2]) # Number of records
        payload = parts[3]       # '^'-delimited records
        
        if tr_id != "H0STCNT0":
            logger.debug(f"Ignoring non-execution data: {tr_id}")
            return
        
        # Parse records
        records = payload.split('^')
        for i, record in enumerate(records):
            if i >= data_cnt:
                break
            
            # Parse individual fields (specific to H0STCNT0)
            fields = record.split('|')
            if len(fields) >= 10:
                price_data = self._parse_execution_record(fields)
                if price_data and self.on_price_update:
                    self.on_price_update(price_data)
    
    except Exception as e:
        logger.error(f"❌ Error processing real-time data: {e}")
```

**Impact**:
- ❌ Current: No tick data logged, scalp log remains empty
- ✅ After fix: Real tick data will populate scalp logs

**KIS Reference**:
- `legacy/websocket/python/ws_domestic_stock.py` line 211-227
- `legacy/Sample01/kis_domstk_ws.py` line 267-306

---

### 5. **Missing Price Field Mapping** ⚠️ WARNING

**Issue**: `_normalize_price_data()` uses field names that may not match KIS response format.

**Your Code** (kis_websocket_provider.py line ~433):
```python
price_data = {
    "symbol": body.get("tr_key", ""),
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "price": {
        "close": int(body.get("stck_prpr", 0)),    # Current price
        "open": int(body.get("stck_oprc", 0)),     # Open price
        "high": int(body.get("stck_hgpr", 0)),     # High price
        "low": int(body.get("stck_lwpr", 0)),      # Low price
    },
    "volume": int(body.get("acml_vol", 0)),        # Accumulated volume
    "bid_price": int(body.get("askp", 0)),         # Ask price
    "ask_price": int(body.get("bidp", 0)),         # Bid price
    "trade_count": int(body.get("acml_tr_pbut", 0)),  # Trade count
}
```

**Problems**:
1. Field names may not match JSON response format
2. Bid/Ask field names are swapped (askp = ask, bidp = bid)
3. `acml_tr_pbut` field name looks incorrect

**KIS Official Field Names for H0STCNT0**:
From examples_user/domestic_stock/domestic_stock_functions_ws.py:
```python
# Real-time execution data columns:
"MKSC_SHRN_ISCD",      # Market + Symbol
"STCK_CNTG_HOUR",      # Execution time (HHMMSS)
"STCK_PRPR",           # ✓ Current price (correct in your code)
"PRDY_VRSS_SIGN",      # Price change sign
"PRDY_VRSS",           # Price change amount
"PRDY_CTRT",           # Price change rate
"WDAY_DSUQ_NAME",      # Day of week
"OPRC_HOUR",           # Open time
"OPRC_PRPR",           # ✓ Open price (correct)
"HIGH_HOUR",           # High time
"HGPR",                # ✓ High price (yours uses stck_hgpr)
"LOW_HOUR",            # Low time
"LWPR",                # ✓ Low price (yours uses stck_lwpr)
"ACML_VOL",            # ✓ Accumulated volume (yours is correct)
"ACML_TR_PBUT",        # Accumulated trade value
...
```

**Better Field Mapping**:
```python
def _parse_execution_record(self, fields: list[str]) -> Optional[Dict[str, Any]]:
    """
    Parse H0STCNT0 pipe-delimited fields
    
    Fields (H0STCNT0 execution data):
    0: 시장구분 (market)
    1: 종목코드 (symbol) ← Use this
    2: 체결시간 (execution time HHMMSS)
    3: 현재가 (current price)
    4: 전일대비부호 (sign)
    5: 전일대비 (change amount)
    6: 등락율 (change rate)
    7: 시가 (open)
    8: 고가 (high)
    9: 저가 (low)
    10: 누적체결량 (accumulated volume)
    ...
    """
    try:
        if len(fields) < 11:
            return None
        
        return {
            "symbol": fields[1],  # Symbol
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "price": {
                "close": int(fields[3] or 0),     # Current price
                "open": int(fields[7] or 0),      # Open
                "high": int(fields[8] or 0),      # High
                "low": int(fields[9] or 0),       # Low
            },
            "volume": {
                "accumulated": int(fields[10] or 0),  # Accumulated volume
            },
            "source": "kis_websocket"
        }
    except Exception as e:
        logger.error(f"Error parsing execution record: {e}")
        return None
```

**Impact**:
- ⚠️ Current: Wrong field values → wrong trigger detection
- ✅ After fix: Correct price/volume data for accuracy

**KIS Reference**:
- `examples_user/domestic_stock/domestic_stock_functions_ws.py` line 348-371 (ccnl_krx columns)
- `legacy/websocket/python/multi_processing_sample_ws.py` line 385-407

---

### 6. **Missing PINGPONG Handler** ⚠️ WARNING

**Issue**: KIS WebSocket requires PINGPONG response to keep connection alive.

**Your Code**: No PINGPONG handling.

**KIS Official** (legacy/Sample01/kis_domstk_ws.py line ~440):
```python
def on_message(ws, data):
    if data[0] in ('0', '1'):
        _dparse(data)  # Real data
    else:
        rsp = _get_sys_resp(data)
        if rsp.isPingPong:
            ws.send(data, websocket.ABNF.OPCODE_PING)  # ← ECHO PING BACK
```

**Correct Implementation**:
```python
async def _process_message(self, raw_message: bytes | str) -> None:
    try:
        if isinstance(raw_message, bytes):
            message_str = raw_message.decode('euc-kr')
        else:
            message_str = raw_message
        
        # Handle PINGPONG (keep-alive)
        if message_str == "PINGPONG":
            logger.debug("📍 Ping received, sending pong...")
            await self._send_message("PINGPONG")
            return
        
        # Handle real data or JSON
        if message_str.startswith('0') or message_str.startswith('1'):
            await self._process_realtime_data(message_str)
        else:
            message_data = json.loads(message_str)
            # Handle JSON response
    
    except Exception as e:
        logger.error(f"Error processing message: {e}")
```

**Impact**:
- ⚠️ Without PINGPONG: Connection may timeout after 30-60 seconds
- ✅ With PINGPONG: Connection stays alive

**KIS Reference**:
- `legacy/websocket/python/ws_domestic_stock.py` line 211-236
- `legacy/Sample01/kis_domstk_ws.py` line 440-445

---

### 7. **Track B Callback Not Receiving Updates** ⚠️ WARNING

**Issue**: `_register_websocket_callback()` is called before WebSocket connects. If WebSocket connection happens asynchronously, callback registration may race.

**Your Code** (track_b_collector.py line ~114):
```python
async def start(self) -> None:
    self._running = True
    
    # Register WebSocket price update callback
    self._register_websocket_callback()  # ← Called BEFORE connect
    
    # Start WebSocket provider
    await self._start_websocket()  # ← Async connect here
```

**Problem**: 
- Callback registered on engine
- WebSocket starts connecting
- But if first subscription happens before connection completes, data is lost

**Better Pattern**:
```python
async def start(self) -> None:
    self._running = True
    
    # Start WebSocket provider FIRST
    await self._start_websocket()
    
    # Register callback AFTER connection
    self._register_websocket_callback()
```

Or verify callback is properly set:
```python
def _register_websocket_callback(self) -> None:
    def on_price_update(data: Dict[str, Any]) -> None:
        log.debug(f"Price update callback fired for {data.get('symbol')}")
        try:
            self._log_scalp_data(data)
        except Exception as e:
            log.error(f"Error handling price update: {e}", exc_info=True)
    
    # Set on provider engine (verify this is called AFTER engine.start_stream())
    self.engine.on_price_update = on_price_update
    log.info(f"✅ Price update callback registered")  # ← ADD THIS
```

**Impact**:
- ⚠️ Current: First few updates might be missed
- ✅ After fix: All updates properly logged

---

### 8. **No Error Handling for Subscription Failures** ⚠️ WARNING

**Issue**: Code doesn't check subscription response for errors.

**KIS sends JSON response** (from examples):
```json
{
  "header": {
    "tr_id": "H0STCNT0",
    "rt_cd": "1"  // "1" = Error, "0" = Success
  },
  "body": {
    "msg1": "SUBSCRIBE SUCCESS"  // or error message
  }
}
```

**Your Code** (kis_websocket_provider.py line ~313):
```python
async def _send_subscription_request(self, symbol: str) -> None:
    subscription_msg = { ... }
    await self._send_message(json.dumps(subscription_msg))
    logger.debug(f"📤 Subscription request sent for {symbol}")
    # ← No error checking!
```

**Better Implementation**:
```python
async def _send_subscription_request(self, symbol: str) -> None:
    subscription_msg = {
        "header": {
            "approval_key": approval_key,
            "custtype": "P",
            "tr_type": "1",
            "content-type": "utf-8",
        },
        "body": {
            "input": {
                "tr_id": "H0STCNT0",
                "tr_key": symbol,
            }
        }
    }
    
    await self._send_message(json.dumps(subscription_msg))
    logger.debug(f"📤 Subscription request sent for {symbol}")
    
    # TODO: Wait for response and check rt_cd field
    # This requires tracking pending subscriptions and response handling
```

**Impact**:
- ⚠️ Silent subscription failures
- ✅ Better with error detection

---

## 🟠 MISSING FIELDS & DATA

### 9. **Scalp Log Missing Critical Fields** ⚠️ WARNING

**Your Record** (track_b_collector.py line ~340):
```python
record = {
    "timestamp": now.isoformat(),
    "symbol": data.get("symbol", ""),
    "price": data.get("price", {}),
    "volume": data.get("volume", {}),
    "source": "websocket",
    "session_id": self.cfg.session_id
}
```

**Missing Fields for Scalp Strategy**:
- ❌ `execution_time` (HHMMSS from WebSocket)
- ❌ `bid_price` / `ask_price` (for scalp execution)
- ❌ `cumulative_volume` (order book depth)
- ❌ `price_change_rate` (volatility indicator)
- ❌ `trade_count` (velocity indicator)

**Better Scalp Record**:
```python
record = {
    "timestamp": now.isoformat(),
    "symbol": data.get("symbol", ""),
    "execution_time": data.get("execution_time"),  # HHMMSS
    "price": {
        "current": data.get("price", {}).get("close", 0),
        "bid": data.get("bid_price", 0),
        "ask": data.get("ask_price", 0),
        "change_rate": data.get("price_change_rate", 0),
    },
    "volume": {
        "accumulated": data.get("volume", {}).get("accumulated", 0),
        "trade_count": data.get("trade_count", 0),
    },
    "source": "websocket",
    "session_id": self.cfg.session_id
}
```

**Impact**:
- ⚠️ Current: Insufficient data for scalp strategy decisions
- ✅ After fix: Complete tick data for analysis

---

## 🛠️ REMEDIATION PRIORITY

### Phase 1: CRITICAL (Must Fix Now) 🔴
1. ✅ Fix approval_key header field (Gap #1)
2. ✅ Fix tr_type "0" for unsubscribe (Gap #2)
3. ✅ Fix WebSocket endpoint selection (Gap #3)
4. ✅ Add pipe-delimited message parsing (Gap #4)
5. ✅ Add PINGPONG handler (Gap #6)

### Phase 2: IMPORTANT (Should Fix Before Testing) 🟡
6. ✅ Add proper field mapping (Gap #5)
7. ✅ Fix callback registration timing (Gap #7)
8. ✅ Add subscription error handling (Gap #8)

### Phase 3: NICE-TO-HAVE (Can Fix Later) 🟢
9. ✅ Enhance scalp log fields (Gap #9)

---

## 📝 Quick Reference: H0STCNT0 Format

### Subscription Request (JSON):
```json
{
  "header": {
    "approval_key": "YOUR_APPROVAL_KEY",
    "custtype": "P",
    "tr_type": "1",
    "content-type": "utf-8"
  },
  "body": {
    "input": {
      "tr_id": "H0STCNT0",
      "tr_key": "005930"  // symbol
    }
  }
}
```

### Subscription Response (JSON):
```json
{
  "header": {
    "tr_id": "H0STCNT0",
    "rt_cd": "0"  // "0"=Success, "1"=Error
  },
  "body": {
    "msg1": "SUBSCRIBE SUCCESS"
  }
}
```

### Real-time Execution Data (Pipe-delimited):
```
0|H0STCNT0|2|005930|161000|50000|...|51910|156000|30000|...|
^--^-----^-^----^-----^-----^
  |  TR_ID | cnt symbol price vol ...
  |
  message_type (0=realtime, 1=notification)
```

---

## ✅ Verification Checklist

Before market hours testing:
- [ ] Approval key is fetched and included in headers
- [ ] Unsubscribe uses tr_type "0" or "2"
- [ ] WebSocket connects to ws://ops.koreainvestment.com:21000 (real) or :31000 (virtual)
- [ ] Message parser handles both JSON and pipe-delimited formats
- [ ] PINGPONG messages trigger echo response
- [ ] Field mapping matches official documentation
- [ ] Scalp log contains complete tick records
- [ ] Subscription responses are error-checked
- [ ] on_price_update callback fires during market hours

---

## 📚 KIS Official Resources Used

1. **GitHub Official Samples**:
   - `legacy/Sample01/kis_domstk_ws.py` - Complete reference implementation
   - `legacy/websocket/python/ws_domestic_stock.py` - WebSocket handling
   - `examples_user/domestic_stock/domestic_stock_functions_ws.py` - Latest API

2. **API Portal**:
   - https://apiportal.koreainvestment.com/

3. **WikiDocs**:
   - https://wikidocs.net/book/7847 - Detailed API documentation

---

## Next Steps

1. **Apply Phase 1 fixes** (3 critical issues) immediately
2. **Test with logs** to verify message format is correct
3. **Re-run with market data** once market hours begin
4. **Monitor scalp logs** for tick data population
5. **Measure latency** (WebSocket -> callback -> log write)

**Expected Outcome After Fixes**:
- ✅ Track B WebSocket successfully subscribes to 41 symbols
- ✅ Real-time 2Hz tick data flows into scalp logs
- ✅ Trigger detection works with accurate volume/volatility data
- ✅ Slot management properly allocates and replaces symbols


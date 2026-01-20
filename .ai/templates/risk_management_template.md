# Meta
- Document Name: [Project/Strategy Name] Risk Management Rules
- File Name: risk_management_[project]_[version].md
- Document ID: RISK-[UNIQUE_ID]
- Status: [Draft | Under Review | Approved | Active | Deprecated]
- Created Date: YYYY-MM-DD
- Last Updated: YYYY-MM-DD
- Author: [Author Name/Agent]
- Reviewer: [Reviewer Name/Agent]
- Version: [Major].[Minor].[Patch]
- Related Documents: [Trading Strategy, Architecture, etc.]

---

# Risk Management Rules: [Project/Strategy Name]

## Executive Summary

### Risk Management Philosophy
[Describe the overall approach to risk management for this trading system]

**Core Principles:**
1. [Principle 1: e.g., Capital preservation is paramount]
2. [Principle 2: e.g., Never risk more than you can afford to lose]
3. [Principle 3: e.g., Diversification across uncorrelated strategies]

### Risk Tolerance Profile
- **Overall Risk Appetite**: [Conservative | Moderate | Aggressive]
- **Maximum Acceptable Annual Loss**: [X% of capital]
- **Target Return**: [X% annually]
- **Risk-Adjusted Return Goal**: [Sharpe Ratio target]

---

## 1. Capital Allocation & Account Limits

### Initial Capital
- **Total Trading Capital**: $[Amount] or [₩ Amount]
- **Minimum Operating Capital**: $[Amount]
- **Reserve Capital (Emergency Fund)**: [X% of total] = $[Amount]

### Capital Allocation by Strategy
| Strategy | Allocation % | Amount | Risk Level |
|----------|--------------|--------|------------|
| [Strategy A] | [30%] | $[Amount] | [Low | Medium | High] |
| [Strategy B] | [25%] | $[Amount] | [Low | Medium | High] |
| [Cash Reserve] | [20%] | $[Amount] | [None] |
| **Total** | **100%** | **$[Total]** | |

### Account-Level Limits
- **Maximum Leverage**: [X:1 or No Leverage]
- **Maximum Margin Usage**: [X% of account value]
- **Minimum Cash Balance**: [X% of account value]
- **Maximum Portfolio Concentration**: [X% in single position]

---

## 2. Per-Trade Risk Limits

### Position Size Limits
**Maximum Position Size:**
- Per trade: [X% of total capital]
- Per asset: [$X or X shares/contracts]
- Per sector: [X% of total capital]

**Position Size Calculation:**
```
Position Size = (Total Capital × Risk Per Trade %) / (Entry Price - Stop Loss Price)

Example:
Total Capital: $100,000
Risk Per Trade: 1%
Entry Price: $50
Stop Loss: $48
Position Size = ($100,000 × 1%) / ($50 - $48) = $1,000 / $2 = 500 shares
```

### Risk Per Trade
- **Maximum Risk Per Trade**: [1-2% of total capital]
- **Maximum Loss Per Trade**: $[Amount]
- **Stop Loss Mandatory**: Yes
- **Stop Loss Placement**: [ATR-based | Fixed % | Technical level]

### Trade Entry Risk Checks
**Pre-Trade Validation (Must Pass All):**
- [ ] Position size within limits
- [ ] Risk per trade within limits
- [ ] Stop loss defined and validated
- [ ] Account has sufficient margin/cash
- [ ] Total exposure limits not exceeded
- [ ] Correlation check passed
- [ ] Sector exposure within limits

---

## 3. Daily Risk Limits

### Daily Loss Limits
**Hard Limits (Automatic Trading Halt):**
- **Maximum Daily Loss**: $[X] or [X% of capital]
  - **Action**: Stop all trading for the day
  - **Notification**: Immediate alert to operator

- **Daily Loss Warning Threshold**: $[X] or [X% of capital]
  - **Action**: Reduce position sizes by [50%]
  - **Notification**: Warning alert to operator

### Daily Trade Limits
- **Maximum Number of Trades**: [X trades per day]
- **Maximum Turnover**: [X% of capital per day]
- **Consecutive Loss Limit**: [X consecutive losing trades]
  - **Action**: Halt trading, review strategy

### Daily Profit Management
- **Daily Profit Lock-In**: [X% profit]
  - **Action**: Close all positions, stop trading for the day (optional)
- **Daily Profit Target**: [X% profit]
  - **Action**: Reduce position sizes, increase caution

---

## 4. Weekly & Monthly Risk Limits

### Weekly Limits
- **Maximum Weekly Loss**: $[X] or [X% of capital]
  - **Action**: Stop trading for remainder of week
- **Maximum Weekly Drawdown**: [X%]
  - **Action**: Reduce position sizes by [50%]

### Monthly Limits
- **Maximum Monthly Loss**: $[X] or [X% of capital]
  - **Action**: Stop trading for remainder of month, conduct full review
- **Maximum Monthly Drawdown**: [X%]
  - **Action**: Strategy review and potential parameter adjustment

### Recovery Procedures
**After hitting weekly/monthly limits:**
1. Conduct thorough post-mortem analysis
2. Review all losing trades
3. Identify systematic issues
4. Adjust parameters if needed
5. Obtain approval before resuming trading
6. Start with reduced position sizes ([50%] for [X days])

---

## 5. Portfolio-Level Risk Limits

### Exposure Limits
- **Maximum Total Exposure**: [X% of capital]
- **Maximum Long Exposure**: [X% of capital]
- **Maximum Short Exposure**: [X% of capital]
- **Net Exposure Range**: [X% to Y%]

### Diversification Requirements
**Position Count:**
- **Minimum Number of Positions**: [X positions] (to avoid over-concentration)
- **Maximum Number of Positions**: [Y positions] (to maintain focus)

**Sector Diversification:**
- **Maximum Per Sector**: [X% of capital]
- **Minimum Number of Sectors**: [X sectors]

**Correlation Limits:**
- **Maximum Correlation Between Positions**: [0.7]
- **Correlation Check**: Performed [daily | weekly]

### Concentration Risk
- **Single Stock Limit**: [X% of portfolio]
- **Top 5 Holdings**: [≤ X% of portfolio]
- **Single Sector Limit**: [X% of portfolio]

---

## 6. Stop Loss Rules

### Stop Loss Requirements
**Mandatory Stop Loss:**
- Every trade MUST have a stop loss defined before entry
- Stop loss must be programmatically enforced
- Manual override prohibited during trading hours

### Stop Loss Types & Parameters

#### 1. Fixed Percentage Stop Loss
- **Default**: [X% below entry for long, X% above entry for short]
- **Application**: [All trades | Specific conditions]

#### 2. ATR-Based Stop Loss
- **Formula**: Entry Price ± (ATR × [Multiplier])
- **ATR Period**: [14 days]
- **Multiplier**: [2.0]

#### 3. Technical Stop Loss
- **Support/Resistance**: [Previous day low/high]
- **Moving Average**: [X-day MA]
- **Volatility Bands**: [Bollinger Bands, Keltner Channels]

#### 4. Trailing Stop Loss
- **Activation**: After [X%] profit
- **Trail Amount**: [X%] or [X × ATR]
- **Update Frequency**: [Every tick | Every X minutes]

### Stop Loss Execution
- **Order Type**: [Stop Market | Stop Limit]
- **Slippage Tolerance**: [X%] (for stop limit orders)
- **Guaranteed Stops**: [Yes | No - platform dependent]

---

## 7. Profit Target & Take Profit Rules

### Profit Target Strategy
- **Primary Target**: [X% profit]
- **Secondary Target**: [Y% profit]
- **Maximum Hold Period**: [X days/hours]

### Partial Profit Taking
**Scaling Out:**
- At [X%] profit: Close [Y%] of position
- At [X%] profit: Close [Y%] of position
- At [X%] profit: Close remaining position

### Trailing Stop for Profit Protection
- **Activation Level**: [X% profit]
- **Trailing Distance**: [Y%] or [Y × ATR]
- **Ratcheting**: [Move stop to breakeven after X% profit]

---

## 8. Circuit Breakers & Emergency Stops

### Automatic Circuit Breakers

#### Circuit Breaker Level 1 (Warning)
**Trigger Conditions:**
- Daily loss reaches [X%] of capital
- [X] consecutive losing trades
- Sharpe ratio drops below [X] (rolling X days)
- Drawdown exceeds [X%]

**Actions:**
- Reduce position sizes to [50%] of normal
- Send warning alert to operator
- Log event for review

#### Circuit Breaker Level 2 (Halt)
**Trigger Conditions:**
- Daily loss reaches [Y%] of capital (harder limit)
- Weekly loss reaches [Y%] of capital
- System detects [X] failed trades in [Y] minutes
- Market volatility exceeds [X] standard deviations

**Actions:**
- **STOP ALL TRADING immediately**
- Close all open positions (optional, based on configuration)
- Send emergency alert to operator
- Require manual approval to resume

#### Circuit Breaker Level 3 (Emergency)
**Trigger Conditions:**
- Account equity drops below [X%] of initial capital
- Data feed failure detected
- Order execution failures exceed threshold
- Connectivity to broker lost
- Unexpected system behavior detected

**Actions:**
- **EMERGENCY STOP: Close ALL positions immediately**
- Halt all trading
- Send critical alert (SMS, email, app notification)
- Require senior approval and full system check before resume

### Manual Emergency Stop
- **Operator can manually trigger emergency stop at any time**
- **No override allowed during emergency stop**
- **Requires documented reason for activation**

---

## 9. Risk Monitoring & Alerts

### Real-Time Risk Monitoring
**Continuous Monitoring (Every [X] seconds/minutes):**
- [ ] Current drawdown vs. limit
- [ ] Daily P&L vs. daily limit
- [ ] Open position sizes vs. limits
- [ ] Total exposure vs. limit
- [ ] Margin usage vs. limit
- [ ] Stop loss orders active and valid

### Alert Thresholds & Actions

| Risk Metric | Warning Level | Critical Level | Action |
|-------------|---------------|----------------|--------|
| Daily Loss | [X%] | [Y%] | [Reduce positions | Halt trading] |
| Drawdown | [X%] | [Y%] | [Review | Emergency stop] |
| Position Size | [X%] | [Y%] | [Alert | Reject order] |
| Exposure | [X%] | [Y%] | [Alert | Reduce exposure] |
| Consecutive Losses | [X trades] | [Y trades] | [Warning | Halt] |

### Alert Delivery Methods
- **Email**: [email@example.com]
- **SMS**: [+XX-XXXX-XXXX]
- **Telegram/Discord**: [Channel/Username]
- **Dashboard**: Real-time risk dashboard
- **Log File**: Persistent alert logging

---

## 10. Position & Exposure Management

### Position Entry Rules
**Before Opening Position:**
1. Verify account has sufficient capital
2. Check daily loss limit not reached
3. Verify position size within limits
4. Check sector/correlation limits
5. Define stop loss
6. Define profit target
7. Log trade rationale

### Position Monitoring
**During Position (Continuous):**
- Monitor unrealized P&L vs. stop loss
- Monitor time in trade vs. max hold period
- Monitor market conditions for exit signals
- Update trailing stops (if applicable)

### Position Exit Rules
**Mandatory Exit Conditions:**
- Stop loss triggered
- Profit target reached
- Max hold period exceeded
- Daily loss limit about to be breached
- Circuit breaker activated
- End of trading day (for day trading strategies)

### Position Reconciliation
**Daily Reconciliation:**
- Verify open positions match system records
- Check stop loss orders are active
- Verify margin/cash balance
- Review any discrepancies immediately

---

## 11. Drawdown Management

### Drawdown Definitions
- **Peak-to-Trough Drawdown**: [Formula]
- **Maximum Acceptable Drawdown**: [X%]
- **Drawdown Recovery Plan Trigger**: [Y%]

### Drawdown Levels & Actions

#### Level 1: [5%] Drawdown
**Actions:**
- Continue normal trading
- Increased monitoring
- Daily review of losing trades

#### Level 2: [10%] Drawdown
**Actions:**
- Reduce position sizes by [25%]
- Review strategy parameters
- Weekly performance review
- Document causes of drawdown

#### Level 3: [15%] Drawdown (Critical)
**Actions:**
- Reduce position sizes by [50%]
- Halt trading (optional)
- Full strategy review
- Consider parameter re-optimization
- Senior management approval required to continue

#### Level 4: [20%] Drawdown (Maximum Acceptable)
**Actions:**
- **STOP ALL TRADING**
- Comprehensive post-mortem analysis
- Strategy re-evaluation
- External review (if applicable)
- Require approval from all stakeholders to resume

### Drawdown Recovery Strategy
**After Drawdown:**
1. Identify root causes
2. Implement corrective measures
3. Conduct simulated trading (paper trading)
4. Gradual capital re-deployment ([X%] increments)
5. Resume normal trading only after [X consecutive] profitable periods

---

## 12. Data & System Risk Management

### Data Quality Checks
**Pre-Trading Data Validation:**
- [ ] Data feed connection active
- [ ] Price data within reasonable range (no outliers)
- [ ] Volume data available and reasonable
- [ ] No missing data (gaps)
- [ ] Timestamp consistency verified

**Data Anomaly Detection:**
- Sudden price jumps > [X%] in [Y seconds]
- Volume spikes > [X] standard deviations
- Missing or delayed data > [X seconds]
- **Action**: Halt trading, investigate before resuming

### System Failure Protocols
**Connectivity Loss:**
- Detect within [X seconds]
- Attempt automatic reconnection [Y times]
- If fails: Trigger circuit breaker Level 3

**Order Execution Failures:**
- Retry [X times]
- If fails: Alert operator, halt strategy
- Manual intervention required

**System Crash:**
- Automatic restart (if configured)
- Position reconciliation upon restart
- Operator notification
- Manual review before resuming

---

## 13. Compliance & Regulatory Risk

### Regulatory Compliance
**Trading Rules:**
- Comply with [Exchange Name] trading rules
- Adhere to [Regulatory Body] regulations
- Pattern Day Trading rules (if applicable in US)
- Short selling regulations
- Market manipulation prevention

**Reporting Requirements:**
- Daily trading log
- Monthly performance report
- Annual compliance audit
- Tax reporting

### Audit Trail
**Record Keeping:**
- All trades (entry, exit, P&L)
- All risk events and alerts
- All circuit breaker activations
- All manual interventions
- All system errors and failures

**Retention Period:** [X years]

---

## 14. Contingency & Disaster Recovery

### Backup Systems
- **Backup Trading System**: [Location, activation procedure]
- **Backup Data Feed**: [Provider, failover time]
- **Backup Broker Connection**: [If applicable]

### Disaster Recovery Plan
**Scenarios:**
1. **Primary System Failure**: [Recovery steps]
2. **Data Feed Failure**: [Switch to backup feed]
3. **Broker API Failure**: [Manual trading procedure]
4. **Complete Connectivity Loss**: [Liquidation plan]

**Recovery Time Objective (RTO):** [X minutes]

### Manual Override Procedures
**When to Use:**
- System malfunction preventing automatic risk management
- Extreme market conditions requiring manual intervention
- Emergency liquidation needed

**Authorization Required:**
- Manual override requires [Operator | Senior Manager] approval
- Document reason for override
- Review override decisions post-event

---

## 15. Risk Reporting & Review

### Daily Risk Report
**Contents:**
- Daily P&L (gross, net, by strategy)
- Open positions and exposure
- Risk limits status (used vs. available)
- Alerts and circuit breaker events
- Any manual interventions

**Distribution:** [Operator, Risk Manager, etc.]

### Weekly Risk Review
**Contents:**
- Weekly performance summary
- Risk metrics (Sharpe, max DD, etc.)
- Limit breaches and near-misses
- Strategy performance comparison
- Risk trend analysis

**Review Meeting:** [Day and time]

### Monthly Risk Review
**Contents:**
- Monthly performance analysis
- Risk-adjusted returns
- Drawdown analysis
- Compliance check
- Strategy effectiveness review
- Parameter optimization review

**Formal Report:** Generated by [Date] each month

### Quarterly Strategy Review
**Contents:**
- Comprehensive performance review
- Market condition analysis
- Strategy adaptation recommendations
- Risk management effectiveness
- Capital allocation review

**Senior Management Review:** Required

---

## 16. Approval & Governance

### Risk Management Approval
- **Strategy Developer**: _________________________ Date: _________
- **Risk Manager Approval**: _________________________ Date: _________
- **Compliance Officer Approval**: _________________________ Date: _________
- **Final Authority Approval**: _________________________ Date: _________

### Review & Update Schedule
- **Next Review Date**: YYYY-MM-DD
- **Review Frequency**: [Monthly | Quarterly]
- **Trigger for Unscheduled Review**: [Major loss event, strategy change, market regime change]

### Change Management
**Any changes to risk limits require:**
1. Written justification
2. Risk Manager approval
3. Testing in simulated environment
4. Documentation update
5. Operator notification

---

## Appendix

### Appendix A: Risk Calculation Formulas
[Detailed formulas for risk metrics, position sizing, etc.]

### Appendix B: Alert Contact List
| Role | Name | Email | Phone | Escalation Level |
|------|------|-------|-------|------------------|
| Operator | [Name] | [Email] | [Phone] | Level 1 |
| Risk Manager | [Name] | [Email] | [Phone] | Level 2 |
| Senior Manager | [Name] | [Email] | [Phone] | Level 3 |

### Appendix C: Historical Risk Events
[Log of past risk events and lessons learned]

### Appendix D: Risk Limit Justification
[Rationale for each risk limit parameter]

---

## Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | YYYY-MM-DD | Initial version | [Name] |
| | | | |

---

*These risk management rules are designed to protect capital, ensure sustainable trading operations, and maintain compliance with all regulatory requirements. All limits are mandatory and enforceable through automated systems.*

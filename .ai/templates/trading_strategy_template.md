# Meta
- Document Name: [Trading Strategy Name]
- File Name: trading_strategy_[strategy_name]_[version].md
- Document ID: STRATEGY-[UNIQUE_ID]
- Status: [Draft | Under Review | Approved | Active | Deprecated]
- Created Date: YYYY-MM-DD
- Last Updated: YYYY-MM-DD
- Author: [Author Name/Agent]
- Reviewer: [Reviewer Name/Agent]
- Version: [Major].[Minor].[Patch]
- Related Documents: [List related documents]

---

# [Trading Strategy Name]

## Strategy Overview

### Strategy Type
- [ ] Trend Following
- [ ] Mean Reversion
- [ ] Breakout
- [ ] Momentum
- [ ] Statistical Arbitrage
- [ ] Market Making
- [ ] Multi-Strategy
- [ ] Other: _______________

### Market & Asset Class
- **Target Market**: [e.g., Korean Stock Market, US Stock Market]
- **Asset Class**: [e.g., Equities, Futures, Options, Forex]
- **Instruments**: [Specific securities or instruments]
- **Trading Session**: [e.g., Regular Hours, Extended Hours, 24/7]

### Strategy Description
[Provide a comprehensive description of the trading strategy, including the core hypothesis and market conditions where it performs best]

**Core Hypothesis:**
[Explain the fundamental assumption or market inefficiency this strategy exploits]

**Market Conditions:**
- **Optimal**: [Conditions where strategy performs best]
- **Acceptable**: [Conditions where strategy is viable]
- **Unfavorable**: [Conditions to avoid or reduce exposure]

### Time Horizon
- **Holding Period**: [Minutes, Hours, Days, Weeks, Months]
- **Trading Frequency**: [Intraday, Daily, Weekly, Monthly]
- **Expected Trades per Day/Week/Month**: [Estimate]

---

## Entry Conditions

### Technical Indicators
[List all technical indicators used for entry signals]

**Primary Indicators:**
1. **[Indicator Name]**: [Parameters, e.g., SMA(20), RSI(14)]
   - Signal: [Condition for entry, e.g., Price > SMA(20)]
   - Weight/Priority: [High | Medium | Low]

2. **[Indicator Name]**: [Parameters]
   - Signal: [Condition]
   - Weight/Priority: [High | Medium | Low]

**Confirmation Indicators:**
1. **[Indicator Name]**: [Parameters]
   - Signal: [Condition]
   - Purpose: [Confirmation/Filter]

### Entry Rules (Long Position)
**Primary Entry Signal:**
```
IF [Condition 1] AND [Condition 2] AND [Condition 3]
THEN open long position
```

**Entry Criteria Checklist:**
- [ ] [Condition 1]: [Description]
- [ ] [Condition 2]: [Description]
- [ ] [Condition 3]: [Description]
- [ ] [Risk Check]: Position size within limits
- [ ] [Time Filter]: Trading window appropriate
- [ ] [Market Filter]: Market conditions acceptable

### Entry Rules (Short Position)
**Primary Entry Signal:**
```
IF [Condition 1] AND [Condition 2] AND [Condition 3]
THEN open short position
```

**Entry Criteria Checklist:**
- [ ] [Condition 1]: [Description]
- [ ] [Condition 2]: [Description]
- [ ] [Condition 3]: [Description]
- [ ] [Risk Check]: Position size within limits
- [ ] [Time Filter]: Trading window appropriate
- [ ] [Market Filter]: Market conditions acceptable

### Entry Filters
**Time-Based Filters:**
- Avoid first [X] minutes of market open
- Avoid last [X] minutes before market close
- Specific time windows: [e.g., 10:00-14:30]

**Market Condition Filters:**
- Minimum liquidity: [Volume threshold]
- Volatility range: [Min/Max acceptable volatility]
- Spread constraint: [Max bid-ask spread]
- News/Event filter: [Avoid earnings, major announcements]

**Risk Filters:**
- Maximum concurrent positions: [Number]
- Maximum sector exposure: [Percentage]
- Maximum correlation: [Threshold]

---

## Exit Conditions

### Profit Target (Take Profit)
**Target Methods:**
- [ ] Fixed percentage: [X%]
- [ ] Fixed dollar amount: [$ per share]
- [ ] Technical level: [Resistance, Fibonacci, etc.]
- [ ] Trailing stop: [Type and parameters]
- [ ] Time-based: [Hold for X days/hours]

**Profit Taking Rules:**
```
IF position profit >= [X%] OR [Technical Condition]
THEN close position
```

**Partial Profit Taking:**
- Scale out at [X%]: Close [Y%] of position
- Scale out at [X%]: Close [Y%] of position
- Final exit at: [Condition]

### Stop Loss
**Stop Loss Methods:**
- [ ] Fixed percentage: [X%]
- [ ] Fixed dollar amount: [$ per share]
- [ ] Technical level: [Support, ATR, etc.]
- [ ] Trailing stop: [Type and parameters]
- [ ] Time-based: [Max holding period]

**Stop Loss Rules:**
```
IF position loss >= [X%] OR [Technical Condition]
THEN close position immediately
```

**Emergency Exit:**
```
IF unexpected event OR system error OR connectivity loss
THEN close all positions immediately
```

### Normal Exit (Signal Reversal)
**Exit Signals:**
- Entry signal reversal: [Description]
- Technical indicator reversal: [Conditions]
- Time-based exit: [End of day, end of week]

---

## Position Sizing Rules

### Base Position Size
**Calculation Method:**
- [ ] Fixed dollar amount: [$X per trade]
- [ ] Fixed percentage of capital: [X% of total capital]
- [ ] Risk-based (Kelly Criterion): [Formula]
- [ ] Volatility-adjusted: [ATR-based, etc.]
- [ ] Other: [Description]

**Base Position Size Formula:**
```
Position Size = [Formula]

Example:
Position Size = (Account Size × Risk Per Trade) / (Entry Price - Stop Loss Price)
```

### Position Sizing Adjustments
**Win Streak Adjustment:**
- After [X] consecutive wins: [Increase/Decrease by Y%]

**Loss Streak Adjustment:**
- After [X] consecutive losses: [Decrease by Y%]

**Volatility Adjustment:**
- High volatility (>X): [Reduce position by Y%]
- Low volatility (<X): [Maintain or increase by Y%]

**Confidence Adjustment:**
- High confidence signals: [Increase by up to X%]
- Low confidence signals: [Reduce by X%]

### Maximum Position Limits
- **Per Position**: [X% of total capital]
- **Per Asset**: [X shares or contracts]
- **Per Sector**: [X% of total capital]
- **Total Exposure**: [X% of total capital]
- **Leverage Limit**: [X:1 or none]

---

## Risk Management Rules

### Per-Trade Risk Limits
- **Maximum Risk Per Trade**: [X% of capital]
- **Maximum Loss Per Trade**: [$X or X%]
- **Stop Loss Mandatory**: [Yes | No]

### Daily Risk Limits
- **Maximum Daily Loss**: [$X or X% of capital]
- **Daily Loss Threshold for Trading Halt**: [$X or X%]
- **Maximum Daily Trades**: [Number]
- **Daily Profit Lock**: [Lock in profits after X% gain]

### Weekly/Monthly Risk Limits
- **Maximum Weekly Loss**: [$X or X% of capital]
- **Maximum Monthly Loss**: [$X or X% of capital]
- **Weekly/Monthly Profit Target**: [$X or X%]

### Circuit Breakers & Emergency Stops
**Automatic Trading Halt Conditions:**
1. Daily loss exceeds [X%]
2. Consecutive losses: [X trades]
3. System error or data feed failure
4. Unusual market conditions (flash crash, halt, etc.)
5. Risk limit breach

**Manual Override:**
- Trading can be manually stopped at any time
- Manual approval required to resume after circuit breaker

### Exposure Limits
- **Maximum Number of Open Positions**: [Number]
- **Maximum Sector Concentration**: [X% per sector]
- **Maximum Correlation Between Positions**: [X]
- **Cash Reserve Requirement**: [X% of capital]

---

## Strategy Parameters

### Core Parameters
| Parameter | Default Value | Range | Description |
|-----------|---------------|-------|-------------|
| [Indicator Period] | [20] | [10-50] | [Moving average period] |
| [Threshold] | [0.5] | [0.1-1.0] | [Entry signal threshold] |
| [Stop Loss %] | [2%] | [1%-5%] | [Stop loss percentage] |
| [Profit Target %] | [4%] | [2%-10%] | [Profit target percentage] |
| [Position Size %] | [10%] | [5%-20%] | [Position size as % of capital] |

### Parameter Optimization
- **Backtesting Period for Optimization**: [Date range]
- **Walk-Forward Analysis**: [Yes | No]
- **Out-of-Sample Testing**: [X% of data]
- **Optimization Metric**: [Sharpe Ratio | Max Drawdown | Win Rate | etc.]

### Parameter Review Schedule
- Review frequency: [Weekly | Monthly | Quarterly]
- Adjustment criteria: [Performance degradation threshold]
- Re-optimization trigger: [Conditions]

---

## Backtesting Requirements

### Historical Data Requirements
- **Data Period**: [Start Date] to [End Date]
- **Minimum Data Length**: [X years/months]
- **Data Frequency**: [Tick | 1-min | 5-min | Daily | etc.]
- **Data Sources**: [List providers]
- **Data Quality**: [Requirements for completeness, accuracy]

### Backtesting Methodology
- **Platform/Tool**: [Name of backtesting software]
- **Slippage Assumption**: [X ticks or X%]
- **Commission/Fees**: [$X per trade or X%]
- **Market Impact**: [Model or assumption]
- **Realistic Order Fill**: [Limit orders, market orders]

### Performance Targets (Minimum Acceptable)
| Metric | Target | Description |
|--------|--------|-------------|
| **Sharpe Ratio** | [≥ 1.5] | Risk-adjusted return |
| **Maximum Drawdown** | [≤ 15%] | Worst peak-to-trough decline |
| **Win Rate** | [≥ 55%] | Percentage of winning trades |
| **Profit Factor** | [≥ 1.5] | Gross profit / Gross loss |
| **CAGR** | [≥ X%] | Compound annual growth rate |
| **Calmar Ratio** | [≥ X] | CAGR / Max Drawdown |
| **Total Trades** | [≥ X] | Sufficient sample size |
| **Average Trade Duration** | [X hours/days] | Consistent with strategy hypothesis |

### Backtesting Validation
- [ ] Strategy profitable in backtesting period
- [ ] Performance metrics meet or exceed targets
- [ ] Consistent performance across different market conditions
- [ ] Robustness test (parameter sensitivity)
- [ ] Walk-forward analysis passed
- [ ] Out-of-sample test passed
- [ ] Transaction costs realistically modeled

---

## Performance Metrics & Monitoring

### Real-Time Tracking Metrics
**Daily Metrics:**
- Total P&L (daily, cumulative)
- Number of trades (wins, losses)
- Win rate
- Average win/loss ratio
- Maximum drawdown (daily, cumulative)
- Sharpe ratio (rolling)

**Weekly/Monthly Metrics:**
- Cumulative return
- Sharpe ratio
- Sortino ratio
- Maximum drawdown
- Profit factor
- Win/loss streaks

### Performance Benchmarks
- **Benchmark Index**: [e.g., KOSPI, S&P 500]
- **Alpha Target**: [X% above benchmark]
- **Beta Target**: [Target correlation with benchmark]

### Alerts & Notifications
**Performance Alerts:**
- Daily loss exceeds [X%]
- Weekly loss exceeds [X%]
- Sharpe ratio drops below [X]
- Drawdown exceeds [X%]
- Win rate falls below [X%]

**System Alerts:**
- Trade execution failure
- Data feed interruption
- Order rejection
- Position limit breach

---

## Strategy Implementation Notes

### Technical Requirements
**Data Requirements:**
- Real-time market data feed
- Historical data for backtesting
- News/events feed (if applicable)

**Infrastructure:**
- Trading platform/API
- Execution speed requirements
- Server/hosting requirements
- Backup systems

**Software/Tools:**
- Programming language: [Python, C++, etc.]
- Libraries/frameworks: [pandas, numpy, backtrader, etc.]
- Database: [PostgreSQL, MongoDB, etc.]

### Operational Procedures
**Daily Checklist:**
- [ ] Pre-market: System health check
- [ ] Pre-market: Data feed verification
- [ ] Pre-market: Position reconciliation
- [ ] Market hours: Real-time monitoring
- [ ] Post-market: P&L review
- [ ] Post-market: Trade log review

**Weekly Review:**
- Performance analysis
- Parameter adjustment (if needed)
- Strategy refinement
- Risk exposure review

---

## Known Limitations & Risks

### Strategy Limitations
- **Market Conditions**: [Conditions where strategy underperforms]
- **Liquidity Constraints**: [Minimum volume/liquidity required]
- **Capacity Limits**: [Maximum capital before strategy degradation]
- **Model Risk**: [Assumptions that may not hold]

### Risk Factors
- **Market Risk**: [Systemic market movements]
- **Execution Risk**: [Slippage, partial fills]
- **Model Risk**: [Strategy assumptions break down]
- **Operational Risk**: [System failures, connectivity]
- **Regulatory Risk**: [Compliance issues]

### Contingency Plans
- **Strategy Underperformance**: [Action plan if targets not met]
- **Market Crisis**: [Risk-off procedures]
- **System Failure**: [Backup systems, manual procedures]
- **Regulatory Changes**: [Adaptation plan]

---

## Approval & Review

### Initial Approval
- **Strategy Developer**: _________________________ Date: _________
- **Risk Manager Review**: _________________________ Date: _________
- **Final Approval**: _________________________ Date: _________

### Review Schedule
- **Next Review Date**: YYYY-MM-DD
- **Review Frequency**: [Monthly | Quarterly | Semi-Annual]
- **Review Triggers**: [Performance degradation, market regime change]

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | YYYY-MM-DD | Initial version | [Name] |
| | | | |

---

## Appendix

### Appendix A: Detailed Technical Indicator Calculations
[Provide formulas and calculation methods for all indicators used]

### Appendix B: Sample Trade Examples
[Provide annotated examples of successful and unsuccessful trades]

### Appendix C: Backtest Results Summary
[Include charts, equity curves, drawdown graphs]

### Appendix D: Code Snippets
[Include key algorithm pseudocode or actual code]

---

*This trading strategy template ensures comprehensive documentation of all aspects of the trading approach, from entry/exit rules to risk management and performance monitoring.*

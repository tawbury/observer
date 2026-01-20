# Meta
- Document Name: [Strategy Name] Backtesting Report
- File Name: backtesting_report_[strategy]_[version]_[date].md
- Document ID: BACKTEST-[UNIQUE_ID]
- Status: [Draft | Under Review | Approved | Final]
- Created Date: YYYY-MM-DD
- Last Updated: YYYY-MM-DD
- Author: [Author Name/Agent]
- Reviewer: [Reviewer Name/Agent]
- Version: [Major].[Minor].[Patch]
- Related Documents: [Trading Strategy, Risk Management, etc.]

---

# Backtesting Report: [Strategy Name]

## Executive Summary

### Test Overview
- **Strategy Name**: [Name]
- **Test Date**: YYYY-MM-DD
- **Backtest Period**: [Start Date] to [End Date]
- **Total Duration**: [X years/months]
- **Data Frequency**: [Tick | 1-min | 5-min | Daily]
- **Market/Asset Class**: [e.g., Korean Equities, US Stocks]

### Key Results Summary
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Total Return** | [X%] | [Y%] | [✓ Pass | ✗ Fail] |
| **CAGR** | [X%] | [Y%] | [✓ Pass | ✗ Fail] |
| **Sharpe Ratio** | [X] | [≥ Y] | [✓ Pass | ✗ Fail] |
| **Maximum Drawdown** | [X%] | [≤ Y%] | [✓ Pass | ✗ Fail] |
| **Win Rate** | [X%] | [≥ Y%] | [✓ Pass | ✗ Fail] |
| **Profit Factor** | [X] | [≥ Y] | [✓ Pass | ✗ Fail] |

### Overall Assessment
**Result**: [✓ PASS | ✗ FAIL | ⚠ CONDITIONAL PASS]

**Recommendation**:
- [ ] Proceed to paper trading
- [ ] Proceed to limited live trading
- [ ] Requires parameter optimization
- [ ] Requires strategy modification
- [ ] Reject strategy

**Summary Statement:**
[1-2 paragraph summary of key findings and overall assessment]

---

## 1. Test Configuration

### Strategy Parameters
| Parameter | Value | Optimization Range | Notes |
|-----------|-------|-------------------|-------|
| [Entry Indicator Period] | [20] | [10-50] | [Optimized/Fixed] |
| [Stop Loss %] | [2%] | [1%-5%] | [Optimized/Fixed] |
| [Profit Target %] | [4%] | [2%-10%] | [Optimized/Fixed] |
| [Position Size %] | [10%] | [5%-20%] | [Optimized/Fixed] |

### Backtesting Platform
- **Software/Tool**: [Name and version]
- **Programming Language**: [Python, C++, etc.]
- **Libraries Used**: [pandas, backtrader, etc.]

### Data Specifications
- **Data Provider**: [Name]
- **Data Quality**: [% completeness]
- **Missing Data Handling**: [Forward fill | Drop | Interpolate]
- **Corporate Actions**: [Adjusted | Unadjusted]
- **Survivorship Bias**: [Considered | Not considered]

### Transaction Cost Assumptions
- **Commission**: [$X per trade or X%]
- **Slippage**: [X ticks or X%]
- **Market Impact**: [Modeled | Not modeled]
- **Spread**: [Bid-ask spread considered: Yes/No]

### Initial Conditions
- **Starting Capital**: $[Amount]
- **Leverage**: [X:1 or None]
- **Compounding**: [Yes | No]
- **Reinvestment of Profits**: [Yes | No]

---

## 2. Performance Metrics

### Return Metrics
| Metric | Value | Benchmark | Notes |
|--------|-------|-----------|-------|
| **Total Return** | [X%] | [Y%] | [Absolute return over test period] |
| **CAGR (Compound Annual Growth Rate)** | [X%] | [Y%] | [Annualized return] |
| **Average Annual Return** | [X%] | - | [Arithmetic mean] |
| **Best Year** | [X%] | - | [YYYY] |
| **Worst Year** | [X%] | - | [YYYY] |
| **Annualized Volatility** | [X%] | - | [Standard deviation of returns] |

### Risk-Adjusted Returns
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Sharpe Ratio** | [X] | [≥ 1.5] | [✓ | ✗] |
| **Sortino Ratio** | [X] | [≥ 2.0] | [✓ | ✗] |
| **Calmar Ratio** | [X] | [≥ 1.0] | [✓ | ✗] |
| **Information Ratio** | [X] | - | - |
| **Omega Ratio** | [X] | [≥ 1.5] | [✓ | ✗] |

**Formulas:**
- Sharpe Ratio = (Mean Return - Risk-Free Rate) / Std Dev of Returns
- Sortino Ratio = (Mean Return - Risk-Free Rate) / Downside Deviation
- Calmar Ratio = CAGR / Maximum Drawdown

### Drawdown Analysis
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Maximum Drawdown** | [X%] | [≤ 15%] | [✓ | ✗] |
| **Average Drawdown** | [X%] | - | - |
| **Drawdown Duration** | [X days] | - | [Longest drawdown period] |
| **Recovery Factor** | [X] | [≥ 2.0] | [Net Profit / Max DD] |
| **Ulcer Index** | [X] | - | [Drawdown severity measure] |

**Drawdown Periods:**
| Period | Start Date | End Date | Duration | Depth |
|--------|------------|----------|----------|-------|
| Drawdown 1 | [YYYY-MM-DD] | [YYYY-MM-DD] | [X days] | [-X%] |
| Drawdown 2 | [YYYY-MM-DD] | [YYYY-MM-DD] | [X days] | [-X%] |
| Drawdown 3 | [YYYY-MM-DD] | [YYYY-MM-DD] | [X days] | [-X%] |

---

## 3. Trade Statistics

### Trade Count & Frequency
| Metric | Value | Notes |
|--------|-------|-------|
| **Total Trades** | [X] | [Long + Short] |
| **Long Trades** | [X] | |
| **Short Trades** | [X] | |
| **Average Trades per Day** | [X] | |
| **Average Trades per Month** | [X] | |
| **Average Holding Period** | [X hours/days] | |

### Win/Loss Statistics
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Win Rate** | [X%] | [≥ 55%] | [✓ | ✗] |
| **Winning Trades** | [X] | - | |
| **Losing Trades** | [X] | - | |
| **Break-even Trades** | [X] | - | |
| **Largest Win** | $[X] or [X%] | - | |
| **Largest Loss** | $[X] or [X%] | - | |
| **Average Win** | $[X] or [X%] | - | |
| **Average Loss** | $[X] or [X%] | - | |
| **Win/Loss Ratio** | [X:1] | [≥ 1.5:1] | [Average Win / Average Loss] |

### Profit Factor & Expectancy
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Profit Factor** | [X] | [≥ 1.5] | [✓ | ✗] |
| **Expectancy** | $[X] | [> 0] | [✓ | ✗] |
| **Expectancy %** | [X%] | [> 0] | [✓ | ✗] |

**Formulas:**
- Profit Factor = Gross Profit / Gross Loss
- Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)

### Streak Analysis
| Metric | Value | Notes |
|--------|-------|-------|
| **Longest Winning Streak** | [X] trades | |
| **Longest Losing Streak** | [X] trades | |
| **Average Winning Streak** | [X] trades | |
| **Average Losing Streak** | [X] trades | |

---

## 4. Detailed Trade Analysis

### Trade Distribution by Result
| Result Range | Count | % of Total | Cumulative P&L |
|--------------|-------|------------|----------------|
| > +10% | [X] | [X%] | $[Amount] |
| +5% to +10% | [X] | [X%] | $[Amount] |
| +0% to +5% | [X] | [X%] | $[Amount] |
| 0% to -5% | [X] | [X%] | $[Amount] |
| -5% to -10% | [X] | [X%] | $[Amount] |
| < -10% | [X] | [X%] | $[Amount] |

### Trade Duration Analysis
| Duration | Count | Avg P&L | Win Rate |
|----------|-------|---------|----------|
| < 1 hour | [X] | $[X] | [X%] |
| 1-4 hours | [X] | $[X] | [X%] |
| 4-24 hours | [X] | $[X] | [X%] |
| 1-7 days | [X] | $[X] | [X%] |
| > 7 days | [X] | $[X] | [X%] |

### Entry/Exit Effectiveness
| Metric | Value | Notes |
|--------|-------|-------|
| **Average Favorable Excursion (AFE)** | [X%] | [Max profit before exit] |
| **Average Maximum Adverse Excursion (MAE)** | [X%] | [Max loss before exit] |
| **Exit Efficiency** | [X%] | [Captured profit / AFE] |

---

## 5. Market Condition Analysis

### Performance by Market Regime
| Market Condition | Trades | Win Rate | Total Return | Sharpe Ratio |
|-----------------|--------|----------|--------------|--------------|
| Bull Market | [X] | [X%] | [X%] | [X] |
| Bear Market | [X] | [X%] | [X%] | [X] |
| Sideways/Range | [X] | [X%] | [X%] | [X] |
| High Volatility | [X] | [X%] | [X%] | [X] |
| Low Volatility | [X] | [X%] | [X%] | [X] |

### Performance by Time Period
| Period | Trades | Win Rate | Total Return | Max DD |
|--------|--------|----------|--------------|--------|
| [Year 1] | [X] | [X%] | [X%] | [X%] |
| [Year 2] | [X] | [X%] | [X%] | [X%] |
| [Year 3] | [X] | [X%] | [X%] | [X%] |

### Monthly Returns Distribution
| Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | Year |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|------|
| [X%] | [X%] | [X%] | [X%] | [X%] | [X%] | [X%] | [X%] | [X%] | [X%] | [X%] | [X%] | [X%] |

**Observations:**
- Best performing months: [Months]
- Worst performing months: [Months]
- Seasonality patterns: [Description]

---

## 6. Benchmark Comparison

### Benchmark Performance
- **Benchmark Index**: [e.g., KOSPI, S&P 500]
- **Benchmark Total Return**: [X%]
- **Benchmark CAGR**: [X%]
- **Benchmark Max Drawdown**: [X%]
- **Benchmark Sharpe Ratio**: [X]

### Strategy vs. Benchmark
| Metric | Strategy | Benchmark | Difference |
|--------|----------|-----------|------------|
| Total Return | [X%] | [Y%] | [+/- Z%] |
| CAGR | [X%] | [Y%] | [+/- Z%] |
| Volatility | [X%] | [Y%] | [+/- Z%] |
| Sharpe Ratio | [X] | [Y] | [+/- Z] |
| Max Drawdown | [X%] | [Y%] | [+/- Z%] |

### Alpha & Beta
- **Alpha**: [X%] (excess return over benchmark)
- **Beta**: [X] (correlation to benchmark)
- **Correlation**: [X] (to benchmark)
- **Tracking Error**: [X%]

---

## 7. Robustness Testing

### Parameter Sensitivity Analysis
**Tested Parameter:** [Entry Indicator Period]

| Parameter Value | Total Return | Sharpe Ratio | Max DD |
|----------------|--------------|--------------|--------|
| [10] | [X%] | [X] | [X%] |
| [15] | [X%] | [X] | [X%] |
| [20] (Optimal) | [X%] | [X] | [X%] |
| [25] | [X%] | [X] | [X%] |
| [30] | [X%] | [X] | [X%] |

**Observations:**
- Strategy performance [stable | sensitive] to parameter changes
- Optimal parameter range: [X to Y]
- Risk of overfitting: [Low | Medium | High]

### Walk-Forward Analysis
| Period | In-Sample Sharpe | Out-of-Sample Sharpe | Degradation |
|--------|-----------------|---------------------|-------------|
| Period 1 | [X] | [Y] | [Z%] |
| Period 2 | [X] | [Y] | [Z%] |
| Period 3 | [X] | [Y] | [Z%] |

**Result:** [✓ Pass | ✗ Fail]
- Average degradation: [X%]
- Acceptable if < [20%]

### Monte Carlo Simulation
- **Simulations Run**: [1000+]
- **Confidence Interval (95%)**: [X% to Y%] CAGR
- **Probability of Positive Return**: [X%]
- **Probability of Exceeding Max DD**: [X%]
- **Value at Risk (VaR 95%)**: [X%]
- **Conditional Value at Risk (CVaR 95%)**: [X%]

---

## 8. Risk Analysis

### Risk Metrics Summary
| Risk Metric | Value | Acceptable Range | Status |
|-------------|-------|-----------------|--------|
| **Value at Risk (VaR 95%)** | [X%] | [< Y%] | [✓ | ✗] |
| **Conditional VaR (CVaR)** | [X%] | [< Y%] | [✓ | ✗] |
| **Downside Deviation** | [X%] | [< Y%] | [✓ | ✗] |
| **Skewness** | [X] | [> 0 preferred] | [Positive/Negative] |
| **Kurtosis** | [X] | [~3] | [Fat tails: Yes/No] |

### Risk-Adjusted Performance
- **Return per Unit of Risk**: [X% return per 1% risk]
- **Risk of Ruin**: [X%] (probability of losing Y% of capital)
- **Expected Shortfall**: [X%] (average loss in worst Z% of cases)

### Concentration Risk
- **Maximum Single Position**: [X% of capital]
- **Average Number of Concurrent Positions**: [X]
- **Maximum Sector Exposure**: [X%]

---

## 9. Notable Trades & Events

### Top 10 Winning Trades
| # | Date | Asset | Entry | Exit | Return | Duration | Notes |
|---|------|-------|-------|------|--------|----------|-------|
| 1 | [YYYY-MM-DD] | [Symbol] | $[X] | $[Y] | [+Z%] | [X days] | [Reason for success] |
| 2 | | | | | | | |
| ... | | | | | | | |

### Top 10 Losing Trades
| # | Date | Asset | Entry | Exit | Return | Duration | Notes |
|---|------|-------|-------|------|--------|----------|-------|
| 1 | [YYYY-MM-DD] | [Symbol] | $[X] | $[Y] | [-Z%] | [X days] | [Reason for loss] |
| 2 | | | | | | | |
| ... | | | | | | | |

### Trades During Market Crises
[Analysis of strategy performance during known market events: 2008 crisis, COVID-19, etc.]

---

## 10. Validation & Limitations

### Validation Checklist
- [ ] **Sufficient Sample Size**: [X trades] (minimum [100] required)
- [ ] **Statistical Significance**: [t-test p-value < 0.05]
- [ ] **Out-of-Sample Testing**: Passed
- [ ] **Walk-Forward Analysis**: Passed
- [ ] **Parameter Robustness**: Passed
- [ ] **Transaction Costs**: Realistically modeled
- [ ] **Slippage Assumptions**: Conservative
- [ ] **Survivorship Bias**: Addressed
- [ ] **Look-Ahead Bias**: Avoided

### Known Limitations
**Data Limitations:**
- [Limitation 1: e.g., Limited historical data for certain assets]
- [Limitation 2: e.g., Data quality issues for specific periods]

**Model Limitations:**
- [Limitation 1: e.g., Assumes constant volatility]
- [Limitation 2: e.g., Does not account for extreme tail events]

**Execution Assumptions:**
- [Assumption 1: e.g., All orders filled at limit price]
- [Assumption 2: e.g., No broker rejection or partial fills]

### Risks to Live Trading
- **Market Impact**: [Strategy may move prices in live trading]
- **Capacity**: [Maximum capital before performance degradation]
- **Liquidity**: [Requires minimum daily volume of $X]
- **Execution Slippage**: [May be higher than backtested assumption]

---

## 11. Recommendations

### Next Steps
**Recommended Actions:**
1. **[ ]** Proceed to paper trading for [X weeks/months]
2. **[ ]** Implement real-time monitoring dashboard
3. **[ ]** Set up risk management controls
4. **[ ]** Start with limited capital ($[X] or [Y%] of total)
5. **[ ]** Monitor live performance against backtest assumptions

### Parameter Recommendations
- **Optimal Parameters**: [List final recommended parameters]
- **Safe Ranges**: [Conservative parameter ranges for live trading]
- **Do Not Exceed**: [Hard limits for parameters]

### Risk Management Recommendations
- **Initial Position Size**: [X% of capital per trade]
- **Maximum Daily Loss**: [$X or Y% of capital]
- **Maximum Drawdown Before Review**: [X%]
- **Circuit Breaker Levels**: [Define levels]

### Monitoring & Maintenance
**Required Monitoring:**
- Daily: [Metrics to check daily]
- Weekly: [Metrics to review weekly]
- Monthly: [Full performance review]

**Re-Optimization Triggers:**
- Sharpe ratio drops below [X] for [Y consecutive] periods
- Win rate drops below [X%] for [Y consecutive] periods
- Drawdown exceeds [X%]

---

## 12. Conclusion

### Overall Assessment
[Provide a comprehensive assessment of the backtesting results]

**Strengths:**
1. [Strength 1]
2. [Strength 2]
3. [Strength 3]

**Weaknesses:**
1. [Weakness 1]
2. [Weakness 2]
3. [Weakness 3]

**Opportunities:**
1. [Opportunity 1: e.g., Parameter optimization potential]
2. [Opportunity 2: e.g., Additional markets to test]

**Threats:**
1. [Threat 1: e.g., Strategy crowding]
2. [Threat 2: e.g., Market regime change]

### Final Recommendation
**Decision**: [✓ APPROVE | ✗ REJECT | ⚠ CONDITIONAL APPROVAL]

**Rationale:**
[Provide clear justification for the decision]

**Conditions (if Conditional Approval):**
1. [Condition 1]
2. [Condition 2]

**Sign-Off:**
- **Backtesting Analyst**: _________________________ Date: _________
- **Risk Manager**: _________________________ Date: _________
- **Final Approval**: _________________________ Date: _________

---

## Appendices

### Appendix A: Equity Curve
[Insert equity curve chart showing strategy growth over time]

### Appendix B: Drawdown Chart
[Insert drawdown chart showing peak-to-trough declines]

### Appendix C: Monthly Returns Heatmap
[Insert heatmap of monthly returns]

### Appendix D: Trade Distribution Histogram
[Insert histogram of trade returns distribution]

### Appendix E: Complete Trade Log
[Link to or attach complete trade-by-trade log]

### Appendix F: Code & Configuration
[Include backtesting code or configuration files]

---

*This backtesting report provides a comprehensive analysis of the trading strategy's historical performance and serves as the foundation for deciding whether to proceed with live trading.*

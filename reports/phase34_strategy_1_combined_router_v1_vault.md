# Phase 34 Strategy #1 Vault - Combined Router v1

## A. Strategy Identity

- Strategy name: Combined Router v1
- Strategy number: Strategy #1
- Asset: BTCUSDT Perpetual / Binance USD-M
- Timeframe: 1h primary
- Execution model: market entry at next open after signal close
- Status: VALID_EXECUTABLE_BASELINE, BACKTEST_VERIFIED_NOT_SHADOWED, NOT_REAL_CAPITAL_READY

## B. Exact Components

Combined Router v1 is a union router over two sleeves:

1. Floor strategy component: PF1.2-derived floor/reversal family from `build_p10_1_strategy()`.
2. CAND_0190 component: `UniversalStrategyTemplate` with Bollinger expansion breakout parameters.
3. Router: `PortfolioStrategy([floor_strat, best_strat], conflict_rule="cancel", fusion_mode="union")`.
4. Engine: `MultiPositionBacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005, max_positions=1, cooldown_candles=5)`.

Conflict rule: if both sleeves fire on the same candle or conflict by direction, cancel the trade. Max concurrent positions is 1. Cooldown is 5 candles after exit. Funding, fees, slippage, TP, SL, same-candle SL-first priority, and time stop are handled by the backtest engine and serialized rulebook.

## C. Full Entry Rules

### Floor Long
- Closed 1h candle close below lower Bollinger Band.
- RSI(14) below oversold threshold, default 30.
- Funding is not deeply negative; skip if below -0.05% per 8h.
- No open position and cooldown satisfied.

### Floor Short
- Closed 1h candle close above upper Bollinger Band.
- RSI(14) above overbought threshold, default 70.
- Funding is not deeply positive; skip if above +0.05% per 8h.
- No open position and cooldown satisfied.

### CAND_0190 Long
- Close breaks above upper Bollinger Band.
- RSI(14) < 70.
- ADX(14) > 15.
- No open position and cooldown satisfied.

### CAND_0190 Short
- Close breaks below lower Bollinger Band.
- RSI(14) > 20.
- ADX(14) > 15.
- No open position and cooldown satisfied.

CAND_0190 exact parameters: `{"template_type":"bollinger_expansion_breakout","trend_filter":null,"regime_filter_mode":"no_filter","tp_atr_mult":2.0,"sl_atr_mult":1.8,"rsi_overbought":70,"rsi_oversold":20,"adx_thresh":15,"timeframe":"1h"}`

## D. Full Exit Rules

- Stop loss: ATR(14) times `sl_atr_mult` from entry. CAND_0190 uses 1.8 ATR; floor is approximately 1.5 ATR.
- Take profit: ATR(14) times `tp_atr_mult` from entry. CAND_0190 uses 2.0 ATR; floor approximately 2.0 ATR.
- Time stop: max hold 240 candles.
- Breakeven: move SL to entry after +0.5R per serialized rulebook.
- Same-candle SL/TP: conservative SL-first priority.
- Exit order type: reduce-only expectation for live automation; backtest uses touch-fill path.
- Fees/slippage/funding: taker fee 0.05%, slippage 0.05%, funding every 8 hours.

## E. Full Router Logic

Signals are collected from floor and CAND_0190 after the current 1h candle closes. If exactly one sleeve emits a valid signal and no position is open, the router accepts it. If both sleeves emit same-candle signals, the router cancels. If an existing position is open, new signals are ignored. After exit, the router waits 5 candles before considering a new signal.

This is a combined router, not a single strategy, because final trades come from a union of floor/reversal and Bollinger expansion sleeves.

## F. Exact Code Preservation

Reproduction command: `python scripts/phase31_runner.py`

Key code paths and hashes:

| File | SHA-256 | Bytes |
|---|---|---:|
| scripts/phase31_runner.py | 38387934ffe4cc7bb94984622b843f235e66bd851f8ff2ca6963f90f5255fe06 | 28005 |
| src/backtest/engine.py | 81c806bc7a1782d4a1bdc1d1d14a312de17555676de5698ab2e530ea66b62d70 | 61717 |
| src/strategies/candidates.py | 77b2d8a7d1606b7963cab1402a16e8d2d4cca5f67b2dd0ce918d45bfdb4986ab | 98168 |
| src/strategies/portfolio.py | 3ec48f7acea65a4df7949c65e1ee48babdc872b44634326d93fe9a5156dd06d8 | 14685 |
| src/features/indicators.py | beaac2312da63a222a75fe9a0bc77ef5db2545f0f3b0f6b6616a156afa6df60f | 8215 |
| data/processed/BTCUSDT_1h_processed.csv | 0d9f63bc016b203ea5774a97bdf6ef974d13e2cff9af3d81a9fa02532514b26a | 10726176 |
| data/processed/BTCUSDT_5m_processed.csv | 2baf36eeb9165dc874f8d0b004d31415171528745f6e1c4ec58f1176115526bf | 124600689 |
| reports/phase31_best_router_trade_log.csv | 8c66a4957480fb3f1aca9cfff3a57ef2c25f833c2b46b80805722657ac37daf6 | 232668 |
| reports/phase33_1_baseline_recovery_trade_log.csv | e1262d4b8cb305994ddfb166bedc8723bef2a3cb3b4df75a8766ae17349ff922 | 239888 |

Core functions/classes:
- `scripts/phase31_runner.py::compile_best_router`
- `src.research.phase12_runner::build_p10_1_strategy`
- `src.strategies.candidates::UniversalStrategyTemplate`
- `src.strategies.portfolio::PortfolioStrategy`
- `src.backtest.engine::MultiPositionBacktestEngine`
- `src.features.indicators::add_indicators`

## G. Exact Metrics

| Metric | Value |
|---|---:|
| Net PnL | 11205.2 |
| Gross Profit | 55640.85 |
| Gross Loss | 44435.66 |
| Profit Factor | 1.2522 |
| Max Drawdown % | 16.2186 |
| Win Rate | 0.5404 |
| Winning Trades | 301 |
| Losing Trades | 256 |
| Average Win | 184.85 |
| Average Loss | -173.58 |
| Expectancy | 20.12 |
| Largest Win | 332.06 |
| Largest Loss | -274.42 |
| Max Consecutive Wins | 9 |
| Max Consecutive Losses | 8 |
| Positive / Negative / Zero Months | 52 / 25 / 0 |
| Best / Worst Month | 1317.97 / -718.58 |
| Trades per Month | 7.23 |

## H. Trade Log Preservation

- Full trade log path: `reports/phase34_strategy_1_trade_log_copy.csv`
- Source trade log: `reports/phase33_1_baseline_recovery_trade_log.csv`
- Trade log hash: `e1262d4b8cb305994ddfb166bedc8723bef2a3cb3b4df75a8766ae17349ff922`
- Row count: 557
- Required columns: `strategy, entry_time, entry_datetime, exit_time, exit_datetime, side, entry_price, exit_price, raw_exit_price, stop_loss, take_profit, size, gross_pnl, fees, entry_slippage, exit_slippage, slippage, funding, net_pnl, capital_after, reason, R, hold_candles, is_limit, is_fallback_market, is_partial_fill, is_adverse_selection, exit_datetime_parsed, month, same_candle, session, expected_R, total_friction_cost, cost_to_risk, projected_net_R, source_sleeve`

### First 10 Rows

```csv
strategy,entry_time,entry_datetime,exit_time,exit_datetime,side,entry_price,exit_price,raw_exit_price,stop_loss,take_profit,size,gross_pnl,fees,entry_slippage,exit_slippage,slippage,funding,net_pnl,capital_after,reason,R,hold_candles,is_limit,is_fallback_market,is_partial_fill,is_adverse_selection,exit_datetime_parsed,month,same_candle,session,expected_R,total_friction_cost,cost_to_risk,projected_net_R,source_sleeve
Low-Activity Filler Long,1578646800000,2020-01-10 09:00:00+00:00,1578664800000,2020-01-10 14:00:00+00:00,Long,7709.7,7947.399518116238,7951.375205719097,7565.549882446231,7951.375205719097,0.713,169.4797564168779,5.581755978208438,2.745049999999611,2.834665260838232,5.579715260837842,0.0,163.89800043866947,10163.89800043867,TP Hit,1.64897207265596,5,False,False,False,False,2020-01-10 14:00:00,2020-01,False,LONDON,1.6765522624631293,11.16147123904628,0.07742949800150524,1.5679554910725189,Low-Activity Filler Long
BB Expansion Long,1578974400000,2020-01-14 04:00:00+00:00,1579010400000,2020-01-14 14:00:00+00:00,Long,8473.8,8637.074842104905,8641.395539874842,8346.320011290114,8641.395539874842,0.823,134.3751950523372,7.041124997526167,3.5059799999986825,3.555934264658477,7.06191426465716,1.81502119715,125.51904885766103,10289.417049296331,TP Hit,1.2807880182393256,10,False,False,False,False,2020-01-14 14:00:00,2020-01,False,OFF_HOURS,1.3146811634589277,15.918060459333326,0.12486713107230599,1.1629592545010832,BB Expansion Long
Funding Reversal Short,1579050000000,2020-01-15 01:00:00+00:00,1579240800000,2020-01-17 06:00:00+00:00,Short,8779.3,9005.452019343827,9000.951543572042,9000.951543572042,8561.148456427956,0.468,-105.8391450529116,4.161631972526457,2.059200000000681,2.106222661195476,4.165422661196157,-4.977731863026,-105.02304516241206,10184.394004133916,SL Hit,-1.020304283467904,53,False,False,False,False,2020-01-17 06:00:00,2020-01,False,OFF_HOURS,0.9842094490135486,13.304786496748616,0.060025688440216905,0.8559494309788971,Funding Reversal Short
Funding Reversal Short,1579302000000,2020-01-17 23:00:00+00:00,1579395600000,2020-01-19 01:00:00+00:00,Short,8939.6,9112.880602001442,9108.32643878205,9108.32643878205,8779.67356121795,0.62,-107.43397324089364,5.596268986620448,2.79,2.8235811960223147,5.613581196022315,-6.568042950812,-106.4621992767021,10077.931804857217,SL Hit,-1.026991402487156,26,False,False,False,False,2020-01-19 01:00:00,2020-01,False,OFF_HOURS,0.9478445698046972,17.77789313345476,0.1053651891297193,0.7779007163696661,Funding Reversal Short
Funding Reversal Short,1579424400000,2020-01-19 09:00:00+00:00,1579431600000,2020-01-19 11:00:00+00:00,Short,9108.7,8995.132147037159,8990.636828622848,9238.243171377151,8990.636828622848,0.814,92.44423231175352,7.368259683844124,3.711839999999585,3.6591891892487727,7.371029189248357,0.0,85.07597262790938,10163.007777485129,TP Hit,0.8766795791358271,2,False,False,False,False,2020-01-19 11:00:00,2020-01,False,LONDON,0.9113808942767426,14.73928887309248,0.11377897203227094,0.7716032873574908,Funding Reversal Short
BB Expansion Short,1579438800000,2020-01-19 13:00:00+00:00,1579780800000,2020-01-23 12:00:00+00:00,Short,8641.4,8404.925338484236,8400.724975996238,8822.16801728271,8400.724975996238,0.576,136.2094050330799,4.909341697483459,2.505600000000209,2.4194087930868844,4.925008793087094,-11.7822602750976,143.08232361069403,10306.090101095822,TP Hit,1.308166483598327,95,False,False,False,False,2020-01-23 12:00:00,2020-01,False,NEW_YORK,1.331402687386683,21.616610765668156,0.11958205378698808,1.1237949551176065,BB Expansion Short
Funding Reversal Short,1579881600000,2020-01-24 16:00:00+00:00,1579910400000,2020-01-25 00:00:00+00:00,Short,8505.0,8379.074021095446,8374.886577806543,8643.533422193455,8374.886577806543,0.767,96.58522581979264,6.475042387090104,3.2290699999993304,3.2117690025890027,6.4408390025883335,-3.3968141428468,93.50699757554932,10399.597098671373,TP Hit,0.9089934898793154,8,False,False,False,False,2020-01-25 00:00:00,2020-01,False,NEW_YORK,0.9392204432209859,16.31269553252524,0.11775277961260011,0.7856966106100339,Funding Reversal Short
BB Expansion Long,1580173200000,2020-01-28 01:00:00+00:00,1580230800000,2020-01-28 17:00:00+00:00,Long,9081.0,8935.066298255231,8939.536066288374,8939.536066288374,9228.61881523514,0.759,-110.76367962427948,6.837097160187861,3.453449999999448,3.392553937155406,6.846003937154854,8.4452204472702,-126.04599723173756,10273.551101439634,SL Hit,-1.0315965201579538,16,False,False,False,False,2020-01-28 17:00:00,2020-01,False,OFF_HOURS,1.0435084856049694,22.128321544612916,0.15642376798118363,0.8374165646811439,BB Expansion Long
Funding Reversal Short,1580245200000,2020-01-28 21:00:00+00:00,1580252400000,2020-01-28 23:00:00+00:00,Short,9066.5,9243.190703724276,9238.57141801527,9238.57141801527,8903.42858198473,0.613,-108.3114013829814,5.611920200691491,2.7585,2.8316221396209,5.5901221396209,0.0,-113.92332158367287,10159.62777985596,SL Hit,-1.026845165584655,2,False,False,False,False,2020-01-28 23:00:00,2020-01,False,NEW_YORK,0.9476961362682481,11.20204234031239,0.06510112178722383,0.8414952850655991,Funding Reversal Short
Funding Reversal Short,1580274000000,2020-01-29 05:00:00+00:00,1580407200000,2020-01-30 18:00:00+00:00,Short,9340.0,9537.422837432205,9532.656509177616,9532.656509177616,9155.963490822383,0.539,-106.41090937595834,5.08746545468798,2.5009599999996865,2.569050929223524,5.07001092922321,-15.093935239128902,-96.40443959151742,10063.223340264443,SL Hit,-1.024740032272644,37,False,False,False,False,2020-01-30 18:00:00,2020-01,False,OFF_HOURS,0.9552571567044643,25.25141162304009,0.13106960014395405,0.7120853568084456,Funding Reversal Short

```

### Last 10 Rows

```csv
strategy,entry_time,entry_datetime,exit_time,exit_datetime,side,entry_price,exit_price,raw_exit_price,stop_loss,take_profit,size,gross_pnl,fees,entry_slippage,exit_slippage,slippage,funding,net_pnl,capital_after,reason,R,hold_candles,is_limit,is_fallback_market,is_partial_fill,is_adverse_selection,exit_datetime_parsed,month,same_candle,session,expected_R,total_friction_cost,cost_to_risk,projected_net_R,source_sleeve
BB Expansion Long,1776121200000,2026-04-13 23:00:00+00:00,1776236400000,2026-04-15 07:00:00+00:00,Long,74637.3,73522.07999612382,73558.85942583674,73558.85942583674,76045.78968633786,0.202,-225.2744407829884,14.964097379608509,7.534600000000588,7.429444802008803,14.96404480200939,-2.672609263456,-237.5659288991409,20767.351638838696,SL Hit,-1.0341042711059447,32,False,False,False,False,2026-04-15 07:00:00,2026-04,False,OFF_HOURS,1.3060429290975666,32.600751445073904,0.030229529772994677,1.156391791607494,BB Expansion Long
Low-Activity Filler Long,1776538800000,2026-04-18 19:00:00+00:00,1776618000000,2026-04-19 17:00:00+00:00,Long,75641.5,74753.59270591132,74790.98820001131,74790.98820001131,77025.94564998019,0.256,-227.304267286703,19.25057186635665,9.676800000000746,9.573246489599349,19.25004648960009,-3.905423269376,-242.64941588368364,20524.702222955017,SL Hit,-1.043968224897638,22,False,False,False,False,2026-04-19 17:00:00,2026-04,False,NEW_YORK,1.627779473487147,42.40604162533275,0.04985943948796107,1.433016037987299,Low-Activity Filler Long
ATR Expansion Short,1777896000000,2026-05-04 12:00:00+00:00,1777903200000,2026-05-04 14:00:00+00:00,Short,78714.1,79803.72642878264,79763.84450652938,79763.84450652938,77237.98324020594,0.203,-221.1941650428748,16.08955938252144,7.998199999998819,8.09603021741219,16.09423021741101,0.0,-237.2837244253962,20287.41849852962,SL Hit,-1.0379920275888066,2,False,False,False,False,2026-05-04 14:00:00,2026-05,False,LONDON,1.4061676442340718,32.18378959993245,0.030658688280577287,1.2551396231474843,ATR Expansion Short
ATR Expansion Long,1777906800000,2026-05-04 15:00:00+00:00,1778058000000,2026-05-06 09:00:00+00:00,Long,80205.3,81950.47016401491,81991.46589696339,78939.1894020244,81991.46589696339,0.166,289.6982472264753,13.45892892361324,6.656600000000966,6.805291669446859,13.461891669447828,-3.1741382974700003,279.41345660033204,20566.83195512995,TP Hit,1.378371026042505,42,False,False,False,False,2026-05-06 09:00:00,2026-05,False,NEW_YORK,1.4107502929201565,30.094958890531068,0.023769612969554457,1.2675598533445274,ATR Expansion Long
ATR Expansion Short,1779807600000,2026-05-26 15:00:00+00:00,1779854400000,2026-05-27 04:00:00+00:00,Short,76835.2,75551.15283167119,75513.39613360439,77780.40257759708,75513.39613360439,0.227,291.4787072106388,17.29585104639468,8.716800000001982,8.570770461164793,17.287570461166773,-2.725802568864,276.9086587331081,20843.740613863058,TP Hit,1.3584888560007324,13,False,False,False,False,2026-05-27 04:00:00,2026-05,False,NEW_YORK,1.398434470794538,37.30922407642545,0.03947219882882023,1.2245481323415854,ATR Expansion Short
ATR Expansion Short,1780081200000,2026-05-29 19:00:00+00:00,1780318800000,2026-06-01 13:00:00+00:00,Short,73306.2,71890.69737133078,71854.76998633762,74335.15334244158,71854.76998633762,0.21,297.2555520205352,15.245674223989733,7.706999999999389,7.54475084856429,15.251750848563676,-6.271753213529999,288.2816310100755,21132.02224487314,TP Hit,1.3756723169880505,66,False,False,False,False,2026-06-01 13:00:00,2026-06,False,NEW_YORK,1.4105887544116482,36.76917828608341,0.035734543802379275,1.240424260114604,ATR Expansion Short
BB Expansion Short,1780416000000,2026-06-02 16:00:00+00:00,1780455600000,2026-06-03 03:00:00+00:00,Short,67240.4,65898.51794353315,65865.58515095768,68288.05869131048,65865.58515095768,0.208,279.11146774510314,13.846447466127447,6.98880000000121,6.8500208556992,13.83882085570041,-2.32598956616,267.59100984513566,21399.61325471828,TP Hit,1.2808389484063014,11,False,False,False,False,2026-06-03 03:00:00,2026-06,False,NEW_YORK,1.312273606323645,30.011257887987856,0.028646025787699717,1.1745523284981656,BB Expansion Short
BB Expansion Short,1780534800000,2026-06-04 01:00:00+00:00,1780538400000,2026-06-04 02:00:00+00:00,Short,63282.8,61452.56888838719,61421.85795940749,64677.03026922661,61421.85795940749,0.157,287.3462845232113,9.791726457738395,4.976899999999543,4.821615849813032,9.798515849812574,0.0,277.554558065473,21677.16781278375,TP Hit,1.3127179577216144,1,False,False,False,False,2026-06-04 02:00:00,2026-06,False,OFF_HOURS,1.334745114682377,19.59024230755097,0.014050937452690532,1.245248697786259,BB Expansion Short
BB Expansion Short,1780675200000,2026-06-05 16:00:00+00:00,1780808400000,2026-06-07 05:00:00+00:00,Short,60370.6,62138.77836204551,62107.724499795615,62107.724499795615,58030.07152806166,0.127,-224.55865197977977,7.779345525989891,3.8354000000005546,3.9438405057364654,7.77924050573702,0.077172344639,-232.41516985040863,21444.75264293334,SL Hit,-1.0178765898780124,37,False,False,False,False,2026-06-07 05:00:00,2026-06,False,NEW_YORK,1.347357931002481,15.63575837636591,0.009000942867483335,1.2764843651167854,BB Expansion Short
BB Expansion Short,1782324000000,2026-06-24 18:00:00+00:00,1782331200000,2026-06-24 20:00:00+00:00,Short,59333.9,60425.73622041314,60395.53845118755,60395.53845118755,57930.59104001729,0.208,-227.10193384593327,12.455002166922966,6.177599999999394,6.2811359989226325,12.458735998922029,0.0,-239.55693601285623,21205.195706920484,SL Hit,-1.0284444946316802,2,False,False,False,False,2026-06-24 20:00:00,2026-06,False,NEW_YORK,1.3218332082951307,24.913738165844997,0.023467253035133036,1.2090098763954527,BB Expansion Short

```

### Exit Reason Summary

```csv
reason,count,sum
SL Hit,256,-44435.65767958936
TP Hit,301,55640.853386509836

```

### Sleeve Summary

```csv
source_sleeve,count,sum
ATR Expansion Long,47,1195.997215645912
ATR Expansion Short,56,1583.7790678763945
BB Expansion Long,149,4900.853648129897
BB Expansion Short,159,1748.3467619541473
Funding Reversal Long,6,724.9332539285017
Funding Reversal Short,110,927.921131277915
Low-Activity Filler Long,16,-812.1480064182554
Low-Activity Filler Short,14,935.5126345259619

```

### Session Summary

```csv
session,count,sum
LONDON,90,287.5278562901158
NEW_YORK,264,9755.207147391833
OFF_HOURS,203,1162.4607032385256

```

### Monthly Summary

```csv
month,net_pnl,trades,winners,losers,status
2020-01,155.57,11,6,5,positive
2020-02,-258.88,4,1,3,negative
2020-03,929.98,12,10,2,positive
2020-04,769.03,10,8,2,positive
2020-05,-126.85,6,2,4,negative
2020-06,-308.53,3,0,3,negative
2020-07,134.94,5,3,2,positive
2020-08,-338.35,3,0,3,negative
2020-09,110.23,4,3,1,positive
2020-10,39.96,4,2,2,positive
2020-11,145.97,11,6,5,positive
2020-12,-339.74,7,2,5,negative
2021-01,922.91,36,22,14,positive
2021-02,-350.29,3,0,3,negative
2021-03,670.88,26,16,10,positive
2021-04,1317.97,14,12,2,positive
2021-05,608.93,25,14,11,positive
2021-06,-380.51,8,3,5,negative
2021-07,648.88,5,4,1,positive
2021-08,-108.41,10,5,5,negative
2021-09,43.04,8,4,4,positive
2021-10,998.56,14,10,4,positive
2021-11,516.38,16,10,6,positive
2021-12,34.16,8,4,4,positive
2022-01,338.89,7,4,3,positive
2022-02,334.84,11,6,5,positive
2022-03,76.31,6,3,3,positive
2022-04,-543.74,3,0,3,negative
2022-05,644.58,7,5,2,positive
2022-06,287.05,13,7,6,positive
2022-07,168.58,8,4,4,positive
2022-08,236.24,5,3,2,positive
2022-09,161.11,8,4,4,positive
2022-10,324.17,3,2,1,positive
2022-11,325.45,5,3,2,positive
2022-12,567.16,2,2,0,positive
2023-01,139.31,6,3,3,positive
2023-02,91.84,4,2,2,positive
2023-03,329.89,11,6,5,positive
2023-04,355.19,5,3,2,positive
2023-05,594.41,2,2,0,positive
2023-06,89.75,6,3,3,positive
2023-08,666.94,4,3,1,positive
2023-09,555.76,2,2,0,positive
2023-10,44.67,2,1,1,positive
2023-11,-188.59,3,1,2,negative
2023-12,-175.38,8,4,4,negative
2024-01,-653.06,6,1,5,negative
2024-02,-251.43,11,5,6,negative
2024-03,-612.37,19,9,10,negative
2024-04,277.57,6,4,2,positive
2024-05,61.33,4,2,2,positive
2024-06,-416.2,4,1,3,negative
2024-07,-534.39,3,0,3,negative
2024-08,236.98,7,4,3,positive
2024-09,-648.08,3,0,3,negative
2024-10,-437.73,2,0,2,negative
2024-11,647.35,10,6,4,positive
2024-12,413.1,7,4,3,positive
2025-01,-76.17,7,3,4,negative
2025-02,167.38,6,3,3,positive
2025-03,552.65,9,5,4,positive
2025-04,398.11,7,4,3,positive
2025-05,-678.18,3,0,3,negative
2025-06,152.81,2,1,1,positive
2025-07,725.4,4,3,1,positive
2025-08,606.16,2,2,0,positive
2025-09,-675.46,4,1,3,negative
2025-10,-225.63,3,1,2,negative
2025-11,-188.1,3,1,2,negative
2025-12,-502.99,7,2,5,negative
2026-01,264.33,7,4,3,positive
2026-02,429.87,9,5,4,positive
2026-03,949.8,7,5,2,positive
2026-04,-718.58,3,0,3,negative
2026-05,319.04,3,2,1,positive
2026-06,361.46,5,3,2,positive

```

## I. Live Automation Integration Notes

An automation engineer must implement: candle-close listener, closed-candle indicator calculation, sleeve signal evaluation, router conflict/cooldown state, market entry after signal close, immediate reduce-only TP/SL placement, funding accounting, tick/step/min-notional rounding, position state recovery, emergency stop, daily loss guard, monitoring, and 30+ day Binance Testnet shadow validation.

Missing before real capital: exchange connector, websocket recovery, order lifecycle proof, testnet fills, partial fill handling, kill switch, daily loss guard, live monitoring, and documented shadow profitability.

## J. Known Weaknesses

- Max DD is 16.2186%.
- Negative months: 25.
- Stress result is only 7/15 PASS.
- Combined adverse PnL is -$39,138.38.
- High cost/slippage/delay sensitivity.
- Same-candle ambiguity exists and is conservatively classified.
- NOT_REAL_CAPITAL_READY.

## K. Reproduction Commands

```powershell
python scripts/phase31_runner.py
python scripts/research_lab.py status
python scripts/research_lab.py audit
pytest tests/test_project_memory_protocol.py -v
pytest -q
```

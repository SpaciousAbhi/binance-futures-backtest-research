# Phase 36 Strategy #1 Edge Map

## Core Finding

Strategy #1 edge is concentrated in BB Expansion Long, ATR Expansion sleeves, and selected New York activity. The weakest named bucket is Low-Activity Filler Long, and the main open problem remains stress fragility from friction/delay.

## Sleeve Contribution

source_sleeve,count,sum,mean
BB Expansion Long,149,4900.853648129897,32.8916352223483
BB Expansion Short,159,1748.3467619541477,10.995891584617281
ATR Expansion Short,56,1583.7790678763945,28.28176906922133
ATR Expansion Long,47,1195.997215645912,25.44674926906196
Low-Activity Filler Short,14,935.5126345259619,66.8223310375687
Funding Reversal Short,110,927.9211312779149,8.435646647981045
Funding Reversal Long,6,724.9332539285017,120.82220898808362
Low-Activity Filler Long,16,-812.1480064182554,-50.75925040114096


## Session Contribution

session,count,sum,mean
NEW_YORK,264,9755.207147391831,36.95154222496906
OFF_HOURS,203,1162.4607032385259,5.726407405115891
LONDON,90,287.52785629011595,3.1947539587790663


## Worst Months

month,net_pnl,trades,winners,losers,status
2026-04,-718.58,3,0,3,negative
2025-05,-678.18,3,0,3,negative
2025-09,-675.46,4,1,3,negative
2024-01,-653.06,6,1,5,negative
2024-09,-648.08,3,0,3,negative
2024-03,-612.37,19,9,10,negative
2022-04,-543.74,3,0,3,negative
2024-10,-543.18,3,0,3,negative
2024-07,-534.39,3,0,3,negative
2025-12,-502.99,7,2,5,negative


## Max Drawdown Context

entry_datetime,source_sleeve,session,net_pnl,R
2024-07-05 05:00:00+00:00,BB Expansion Short,OFF_HOURS,-105.34868051688689,-1.0173934143301109
2024-07-08 15:00:00+00:00,ATR Expansion Short,NEW_YORK,-207.60012084391917,-1.0173990503715837
2024-07-19 19:00:00+00:00,BB Expansion Long,NEW_YORK,-221.43905144203265,-1.0332992019725766
2024-08-01 23:00:00+00:00,ATR Expansion Long,OFF_HOURS,-211.79591672662417,-1.0240472812142605
2024-08-02 15:00:00+00:00,ATR Expansion Short,NEW_YORK,268.89897316054515,1.4257432082408914
2024-08-05 01:00:00+00:00,BB Expansion Short,OFF_HOURS,126.78105607382501,1.3245304367827042
2024-08-08 16:00:00+00:00,BB Expansion Long,NEW_YORK,252.66504352199044,1.3223803789149482
2024-08-23 21:00:00+00:00,BB Expansion Long,NEW_YORK,247.36044395171035,1.2851017026815648
2024-08-27 12:00:00+00:00,Low-Activity Filler Long,LONDON,-230.65456066715365,-1.0393019466194824
2024-08-28 00:00:00+00:00,BB Expansion Short,OFF_HOURS,-216.27851082661485,-1.0250209018479979
2024-09-06 18:00:00+00:00,BB Expansion Short,NEW_YORK,-213.22603851255744,-1.0224086318279493
2024-09-09 22:00:00+00:00,BB Expansion Long,OFF_HOURS,-213.423346310733,-1.0283374743693479
2024-09-16 04:00:00+00:00,Low-Activity Filler Long,OFF_HOURS,-221.42777946792296,-1.0398672463346965
2024-10-11 14:00:00+00:00,Low-Activity Filler Short,NEW_YORK,-218.77473229269748,-1.0411425605239644
2024-10-21 16:00:00+00:00,Low-Activity Filler Long,NEW_YORK,-218.954267166981,-1.040291391372383
2024-10-31 19:00:00+00:00,Low-Activity Filler Long,NEW_YORK,-105.4519537306666,-1.034088425208675


## Repair Implications

- Suppress or harden Low-Activity Filler Long.
- Test off-hours and cost-to-risk filters, but do not promote trade-log-only gates.
- Favor New York/London activity when trade count remains viable.
- Stress fragility is broad, so any upgrade must improve combined adverse and not just normal PnL.

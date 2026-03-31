# Bandwidth Figureas and Tables

| `h` | Precision | Recall | F1 | Mean GT Duration | Mean Pred Duration | Mean Duration Diff |
| --- | --- | --- | --- | --- | --- | --- |
| 1.0 | 0.9443 | 0.1155 | 0.2034 | 21.37 | 13.18 | 8.19 |
| 3.2 | 0.9132 | 0.2256 | 0.3578 | 21.37 | 20.14 | 1.80 |
| 5.0 | 0.8848 | 0.2557 | 0.3913 | 21.37 | 23.39 | 3.11 |
| 7.0 | 0.8606 | 0.2627 | 0.3983 | 21.37 | 26.23 | 4.85 |
| 10.0 | 0.8484 | 0.2442 | 0.3764 | 21.37 | 26.54 | 5.17 |
| 15.0 | 0.8227 | 0.1574 | 0.2613 | 21.37 | 32.28 | 10.91 |
| 20.0 | 0.8641 | 0.1231 | 0.2080 | 21.37 | 31.60 | 10.23 |

*Mean GT Duration denotes the average duration of the aligned ground-truth highlight intervals across the evaluated matches.*

**Figure 1. Mean precision, recall, and F1 across KDE bandwidths.**
![KDE bandwidth precision-recall-F1 curve](./kde_ablation/kde_bandwidth_time_f1_curve.png)

**Figure 2. Mean GT duration, predicted duration, and duration difference across KDE bandwidths.**
![KDE bandwidth duration alignment curve](./kde_ablation/kde_bandwidth_duration_diff_curve.png)

**Figure 3. Multi-bandwidth qualitative comparison against GT highlights, example 1.**
![KDE multi-h GT comparison 1](./kde_ablation/2024_LCK_spring_multi_kde_rect_comparison.png)

**Figure 4. Multi-bandwidth qualitative comparison against GT highlights, example 2.**
![KDE multi-h GT comparison 2](./kde_ablation/2024_LCK_summer_multi_kde_rect_comparison.png)

**Figure 5. Multi-bandwidth qualitative comparison against GT highlights, example 3.**
![KDE multi-h GT comparison 3](./kde_ablation/2023_LCK_summer_multi_kde_rect_comparison.png)

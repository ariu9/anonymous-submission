# KDE Bandwidth vs GT Metrics

- GT source: `hle_kt_match42.txt`
- Matches used: `3`
- Best mean F1: `h=7.0` (0.3983)
- Smallest mean duration diff: `h=3.2` (1.80s)
- Best combined score: `h=3.2` (0.6387)
- Combined score uses `0.5 * time_f1 + 0.5 * duration_score`, where `duration_score = max(0, 1 - duration_diff / gt_mean_duration)`.

![KDE bandwidth precision recall F1 sweep](kde_bandwidth_time_f1_curve.png)

![KDE bandwidth duration sweep](kde_bandwidth_duration_diff_curve.png)

![KDE bandwidth combined score sweep](kde_bandwidth_combined_curve.png)

## Mean Metrics

| h | Matches | Mean Precision | Mean Recall | Mean F1 | Mean GT Dur | Mean Pred Dur | Mean Dur Diff | Mean Dur Score | Mean Combined | Std Precision | Std Recall | Std F1 | Std Dur Diff | Std Combined |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.0 | 3 | 0.9443 | 0.1155 | 0.2034 | 21.37 | 13.18 | 8.19 | 0.6295 | 0.4165 | 0.0367 | 0.0438 | 0.0696 | 2.87 | 0.0778 |
| 3.2 | 3 | 0.9132 | 0.2256 | 0.3578 | 21.37 | 20.14 | 1.80 | 0.9196 | 0.6387 | 0.0246 | 0.0610 | 0.0821 | 1.77 | 0.0746 |
| 5.0 | 3 | 0.8848 | 0.2557 | 0.3913 | 21.37 | 23.39 | 3.11 | 0.8427 | 0.6170 | 0.0103 | 0.0728 | 0.0924 | 1.15 | 0.0231 |
| 7.0 | 3 | 0.8606 | 0.2627 | 0.3983 | 21.37 | 26.23 | 4.85 | 0.7637 | 0.5810 | 0.0227 | 0.0679 | 0.0847 | 2.53 | 0.0214 |
| 10.0 | 3 | 0.8484 | 0.2442 | 0.3764 | 21.37 | 26.54 | 5.17 | 0.7598 | 0.5681 | 0.0274 | 0.0567 | 0.0727 | 3.56 | 0.0579 |
| 15.0 | 3 | 0.8227 | 0.1574 | 0.2613 | 21.37 | 32.28 | 10.91 | 0.4931 | 0.3772 | 0.0623 | 0.0444 | 0.0609 | 6.74 | 0.1097 |
| 20.0 | 3 | 0.8641 | 0.1231 | 0.2080 | 21.37 | 31.60 | 10.23 | 0.5498 | 0.3789 | 0.0848 | 0.0639 | 0.0952 | 5.87 | 0.0687 |

## GT Dataset

| Match | Sync | # Highlights | GT Sec |
| --- | --- | --- | --- |
| GEN vs DRX - KT vs DK  2023 LCK 서머 스플릿_3 | 02:31 | 21 | 352.00 |
| NS vs DK - BRO vs T1  2024 LCK 서머 스플릿_4 | 05:21 | 21 | 504.00 |
| T1 vs NS - HLE vs KT  2024 LCK 스프링 스플릿_4 | 05:20 | 28 | 654.00 |

## Per-Match Metrics

| Match | h | Precision | Recall | F1 | GT Mean Dur | Pred Mean Dur | Dur Diff | # Segments |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GEN vs DRX - KT vs DK  2023 LCK 서머 스플릿_3 | 1.0 | 0.9822 | 0.1738 | 0.2954 | 16.76 | 12.46 | 4.30 | 5 |
| GEN vs DRX - KT vs DK  2023 LCK 서머 스플릿_3 | 3.2 | 0.9467 | 0.2843 | 0.4373 | 16.76 | 17.62 | 0.86 | 6 |
| GEN vs DRX - KT vs DK  2023 LCK 서머 스플릿_3 | 5.0 | 0.8927 | 0.3226 | 0.4739 | 16.76 | 21.20 | 4.44 | 6 |
| GEN vs DRX - KT vs DK  2023 LCK 서머 스플릿_3 | 7.0 | 0.8702 | 0.3256 | 0.4739 | 16.76 | 21.95 | 5.19 | 6 |
| GEN vs DRX - KT vs DK  2023 LCK 서머 스플릿_3 | 10.0 | 0.8691 | 0.3001 | 0.4461 | 16.76 | 20.26 | 3.50 | 6 |
| GEN vs DRX - KT vs DK  2023 LCK 서머 스플릿_3 | 15.0 | 0.8984 | 0.1236 | 0.2173 | 16.76 | 24.21 | 7.45 | 2 |
| GEN vs DRX - KT vs DK  2023 LCK 서머 스플릿_3 | 20.0 | 0.9784 | 0.0547 | 0.1037 | 16.76 | 19.69 | 2.93 | 1 |
| NS vs DK - BRO vs T1  2024 LCK 서머 스플릿_4 | 1.0 | 0.8946 | 0.0684 | 0.1271 | 24.00 | 12.85 | 11.15 | 3 |
| NS vs DK - BRO vs T1  2024 LCK 서머 스플릿_4 | 3.2 | 0.9048 | 0.1416 | 0.2448 | 24.00 | 19.72 | 4.28 | 4 |
| NS vs DK - BRO vs T1  2024 LCK 서머 스플릿_4 | 5.0 | 0.8702 | 0.1545 | 0.2624 | 24.00 | 22.36 | 1.64 | 4 |
| NS vs DK - BRO vs T1  2024 LCK 서머 스플릿_4 | 7.0 | 0.8292 | 0.1685 | 0.2801 | 24.00 | 25.60 | 1.60 | 4 |
| NS vs DK - BRO vs T1  2024 LCK 서머 스플릿_4 | 10.0 | 0.8097 | 0.1664 | 0.2761 | 24.00 | 25.90 | 1.90 | 4 |
| NS vs DK - BRO vs T1  2024 LCK 서머 스플릿_4 | 15.0 | 0.7458 | 0.1285 | 0.2192 | 24.00 | 28.94 | 4.94 | 3 |
| NS vs DK - BRO vs T1  2024 LCK 서머 스플릿_4 | 20.0 | 0.7757 | 0.1060 | 0.1865 | 24.00 | 34.43 | 10.43 | 2 |
| T1 vs NS - HLE vs KT  2024 LCK 스프링 스플릿_4 | 1.0 | 0.9561 | 0.1041 | 0.1878 | 23.36 | 14.24 | 9.11 | 5 |
| T1 vs NS - HLE vs KT  2024 LCK 스프링 스플릿_4 | 3.2 | 0.8881 | 0.2508 | 0.3912 | 23.36 | 23.09 | 0.27 | 8 |
| T1 vs NS - HLE vs KT  2024 LCK 스프링 스플릿_4 | 5.0 | 0.8915 | 0.2901 | 0.4378 | 23.36 | 26.60 | 3.25 | 8 |
| T1 vs NS - HLE vs KT  2024 LCK 스프링 스플릿_4 | 7.0 | 0.8823 | 0.2939 | 0.4410 | 23.36 | 31.13 | 7.77 | 7 |
| T1 vs NS - HLE vs KT  2024 LCK 스프링 스플릿_4 | 10.0 | 0.8663 | 0.2660 | 0.4070 | 23.36 | 33.47 | 10.11 | 6 |
| T1 vs NS - HLE vs KT  2024 LCK 스프링 스플릿_4 | 15.0 | 0.8238 | 0.2201 | 0.3474 | 23.36 | 43.69 | 20.33 | 4 |
| T1 vs NS - HLE vs KT  2024 LCK 스프링 스플릿_4 | 20.0 | 0.8381 | 0.2085 | 0.3339 | 23.36 | 40.67 | 17.31 | 4 |
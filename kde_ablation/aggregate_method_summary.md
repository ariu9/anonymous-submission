# Aggregate Multi-Method Summary

- GT source: `hle_kt_match42.txt`
- Number of GT matches: `3`

## Mean Metrics Across GT Matches

| Method | # GTs | Mean Precision | Mean Recall | Mean F1 | Std Precision | Std Recall | Std F1 | Mean # Segments |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DBSCAN | 3 | 1.0000 | 0.0476 | 0.0903 | 0.0000 | 0.0173 | 0.0313 | 2.33 |
| Sliding Window | 3 | 0.9848 | 0.1504 | 0.2565 | 0.0216 | 0.0548 | 0.0795 | 4.67 |
| KDE h=3.2 | 3 | 0.9480 | 0.2123 | 0.3433 | 0.0194 | 0.0521 | 0.0711 | 6.00 |

## Per-GT Metrics

| Method | GT Match | Precision | Recall | F1 | # Segments |
| --- | --- | --- | --- | --- | --- |
| DBSCAN | GEN vs DRX - KT vs DK  2023 LCK 서머 스플릿_3 | 1.0000 | 0.0343 | 0.0663 | 1 |
| DBSCAN | NS vs DK - BRO vs T1  2024 LCK 서머 스플릿_4 | 1.0000 | 0.0363 | 0.0701 | 2 |
| DBSCAN | T1 vs NS - HLE vs KT  2024 LCK 스프링 스플릿_4 | 1.0000 | 0.0721 | 0.1344 | 4 |
| Sliding Window | GEN vs DRX - KT vs DK  2023 LCK 서머 스플릿_3 | 0.9543 | 0.2260 | 0.3654 | 6 |
| Sliding Window | NS vs DK - BRO vs T1  2024 LCK 서머 스플릿_4 | 1.0000 | 0.0977 | 0.1781 | 3 |
| Sliding Window | T1 vs NS - HLE vs KT  2024 LCK 스프링 스플릿_4 | 1.0000 | 0.1274 | 0.2260 | 5 |
| KDE h=3.2 | GEN vs DRX - KT vs DK  2023 LCK 서머 스플릿_3 | 0.9490 | 0.2546 | 0.4015 | 6 |
| KDE h=3.2 | NS vs DK - BRO vs T1  2024 LCK 서머 스플릿_4 | 0.9713 | 0.1390 | 0.2432 | 4 |
| KDE h=3.2 | T1 vs NS - HLE vs KT  2024 LCK 스프링 스플릿_4 | 0.9238 | 0.2434 | 0.3853 | 8 |

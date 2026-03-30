

**Reg. comparison with alternative segment selection strategies**

We additionally compare KDE-based segment extraction against DBSCAN and Sliding Window using manually aligned ground-truth highlight intervals from the same matches. Visuals: https://anonymous.4open.science/r/anonymous-submission-27793/mm.md. The aggregate results are:

| Method | Precision | Recall | F1 | Mean # Segments |
|:------:|:---------:|:------:|:--:|:---------------:|
| DBSCAN | 1.0000 | 0.0476 | 0.0903 | 2.33 |
| Sliding Window | 0.9848 | 0.1504 | 0.2565 | 4.67 |
| KDE h=3.2 | 0.9480 | 0.2123 | 0.3433 | 6.00 |

These results show that DBSCAN is highly precise but too sparse, while Sliding Window improves coverage but remains less adaptive. KDE (`h=3.2`) achieves the highest recall and F1 while maintaining high precision, indicating a better overall balance for key interaction segment selection. The same pattern appears in the qualitative GT comparisons (Figs. 1-3).

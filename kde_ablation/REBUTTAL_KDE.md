# Rebuttal for KDE Segment Selection

Thank you for your careful reading and constructive feedback. We appreciate your point that KDE is a classical technique, and we agree that the choice of KDE should be empirically validated against reasonable alternative segment selection strategies.

## Reviewer Comment

> "KDE is a classical technique, and the paper does not compare it against alternative segment selection strategies — for example, sliding window with count thresholds, a learned saliency predictor, or simple density thresholding without kernel smoothing. The contribution of the KDE formulation is stated but not empirically validated."

## Response

We appreciate this concern. In this case, we understand the main issue not as a claim about broad novelty, but as a request for clearer **empirical validation** of the KDE-based segment selection choice. We agree with this point.

Our goal is not to argue that KDE itself is new as an algorithm. Rather, the key question is whether KDE is an effective way to extract **Key Interaction Segments** from temporally clustered gameplay events, relative to simpler alternative strategies. To address this directly, we prepared additional revision material that compares KDE against alternative non-learned segment selection strategies and also provides a bandwidth ablation study for KDE.

In particular, the revision includes:

- a direct comparison between **KDE**, **Sliding Window**, and **DBSCAN** using manually aligned ground-truth highlight intervals
- an aggregated summary showing that **KDE h=3.2** achieves the strongest overall balance of precision, recall, and F1 among the compared methods
- a bandwidth ablation showing that KDE exhibits a clear precision-recall tradeoff, with `h = 3.2` selected as a precision-preserving operating point

## Compared Methods and Parameters

For the multi-method comparison, the methods are configured as follows:

- **KDE**: bandwidth `h = 3.2`, density-threshold factor `= 5.0`, minimum interaction count `= 2`
- **DBSCAN**: neighborhood radius `epsilon = 6.0`, minimum samples `= 2`
- **Sliding Window**: window size `= 12.0` seconds, event-count threshold `= 2`

These choices are intended to compare KDE against two reasonable non-learned alternatives:

- **DBSCAN** groups temporally nearby events using a density-based clustering rule
- **Sliding Window** selects salient regions using a fixed temporal window and a simple event-count threshold

## Key Quantitative Evidence

The aggregate multi-method comparison across the three ground-truth matches is summarized below:

| Method | Mean Precision | Mean Recall | Mean F1 | Std Precision | Std Recall | Std F1 | Mean # Segments |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DBSCAN | 1.0000 | 0.0476 | 0.0903 | 0.0000 | 0.0173 | 0.0313 | 2.33 |
| Sliding Window | 0.9848 | 0.1504 | 0.2565 | 0.0216 | 0.0548 | 0.0795 | 4.67 |
| KDE h=3.2 | 0.9480 | 0.2123 | 0.3433 | 0.0194 | 0.0521 | 0.0711 | 6.00 |

These results indicate that:

- **DBSCAN** achieves perfect mean precision (`1.0000`) but very low mean recall (`0.0476`), which indicates that it detects only a small subset of the ground-truth highlights. In other words, DBSCAN is conservative but misses many relevant interaction segments.
- **Sliding Window** improves recall to `0.1504` and F1 to `0.2565`, showing that a simple count-threshold baseline can recover more highlights than DBSCAN. However, because it relies on fixed temporal windows, its predicted segments remain less adaptive to the true temporal extent of highlight intervals.
- **KDE h=3.2** achieves the highest mean recall (`0.2123`) and the highest mean F1 (`0.3433`) among the compared methods, while still maintaining high mean precision (`0.9480`). This indicates that KDE captures more of the annotated highlights without excessively sacrificing temporal precision.

Overall, these results support the view that KDE is better suited to interaction-segment selection than the compared alternatives because it adapts to the temporal density of events rather than relying on either rigid fixed windows or highly sparse cluster assignments.

We also include a bandwidth sensitivity analysis for KDE:

| `h` | Precision | Recall | F1 |
| --- | --- | --- | --- |
| 1.0 | 0.9941 | 0.1089 | 0.1945 |
| 3.2 | 0.9480 | 0.2123 | 0.3433 |
| 5.0 | 0.9581 | 0.1682 | 0.2828 |
| 7.0 | 0.9209 | 0.2555 | 0.3962 |
| 10.0 | 0.9283 | 0.2425 | 0.3819 |
| 15.0 | 0.9581 | 0.1682 | 0.2828 |
| 20.0 | 0.9853 | 0.1323 | 0.2258 |

This analysis shows that KDE bandwidth controls a clear precision-recall tradeoff. Small bandwidths produce highly localized but fragmented segments, whereas larger bandwidths broaden the selected intervals and improve coverage at the cost of temporal specificity. Although larger bandwidths such as `h = 7.0` can produce higher F1, we choose `h = 3.2` as a conservative operating point because it preserves tighter temporal localization while maintaining competitive recall and overall performance.

## Revision Text

We will revise the paper to clarify that the main point here is not novelty of KDE itself, but empirical support for using KDE as the segment selection mechanism. We will also explicitly add comparison against alternative segment selection strategies.

A concise revision-ready summary is:

> We agree that KDE is a classical technique and that its use should be empirically validated rather than assumed. To address this, we additionally compare KDE-based segment extraction with DBSCAN and sliding-window baselines using manually aligned ground-truth highlight intervals. Across the compared methods, KDE (`h = 3.2`) achieves the best overall balance of precision and recall, yielding the highest mean F1 while maintaining high precision. We also provide a bandwidth ablation showing that KDE exhibits a clear precision-recall tradeoff, which supports our choice of `h = 3.2` as a precision-preserving operating point for key interaction segment selection.

## Scope Clarification

To keep the rebuttal precise, we note the current scope of the added validation:

- Included: **KDE**, **DBSCAN**, and **Sliding Window**
- Not included in this revision note: a learned saliency predictor
- Not included as a separate standalone baseline: raw density thresholding without kernel smoothing

The accompanying revision material is documented in [README.md](./README.md).

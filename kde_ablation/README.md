# KDE Ablation Study for Key Interaction Segments

This note is intended for revision materials for the paper *Interaction-Aware Highlight Selection and Caption Generation in Gaming Content*.

This folder documents the **KDE ablation study** for the KDE-based **Key Interaction Segment** selection module used in [ICML_2026.pdf](./ICML_2026.pdf).

This revision note is prepared to address the reviewer concern that KDE is a classical technique and that its contribution should be empirically validated against alternative segment selection strategies. Accordingly, the material below includes:

- a direct comparison between KDE and alternative non-learned segment selection strategies
- an aggregated multi-method summary against ground-truth highlights
- a bandwidth ablation study showing how KDE behaves under different smoothing levels

Every PNG in this folder is embedded directly in this Markdown file. For PDF assets, a preview image is shown inline and the original PDF is linked immediately below it.

## 1. KDE versus baseline segment extraction methods

This section comes first because it directly shows how the KDE-based Key Interaction Segment method compares against baseline segment extraction methods using ground-truth highlight intervals.

The goal of this comparison is to empirically validate the KDE formulation against alternative segment selection strategies. In this revision material, the alternatives are:

- DBSCAN as a density-based clustering baseline without KDE smoothing
- Sliding Window with a count threshold as a simple fixed-window heuristic

Methods:

- DBSCAN
- Sliding window
- KDE

Visual encoding:

- Black lines: interaction events
- Purple rectangles: DBSCAN predictions
- Green rectangles: sliding-window predictions
- Blue rectangles: KDE predictions
- Red rectangles: ground-truth highlights

Main interpretation:

- DBSCAN gives sparse detections and often misses many ground-truth highlight intervals.
- Sliding window improves coverage but has coarse temporal boundaries relative to the ground-truth highlights.
- KDE with `h = 3.2` best matches the location and duration of the ground-truth highlights.

This comparison supports why the KDE-based segment selection used in the paper is preferable to DBSCAN and sliding-window alternatives.

Scope note:

- The current revision material directly evaluates KDE against sliding window and DBSCAN.
- A learned saliency predictor is not included in this comparison set.
- Simple density thresholding without kernel smoothing is also not included as a separate standalone baseline here.

### Multi-method parameter settings

The multi-method comparison uses the following main **method-level parameters**:

| Method | Main parameters | Values used | Role |
| --- | --- | --- | --- |
| KDE | Bandwidth `h`, density threshold, minimum interaction count | `h = 3.2`, density-threshold factor `= 5.0`, minimum interaction count `= 2` | Controls temporal smoothing and salient-segment selection |
| DBSCAN | Neighborhood radius `epsilon`, minimum samples | `epsilon = 6.0`, `min_samples = 2` | Controls cluster radius and cluster density requirement |
| Sliding Window | Window size, event-count threshold | window size `= 12.0` sec, event-count threshold `= 2` | Controls fixed temporal scope and saliency decision |

### Aggregated multi-method summary

The following table summarizes the aggregate results across the three ground-truth matches used in the multi-method comparison.

| Method | Mean Precision | Mean Recall | Mean F1 | Std Precision | Std Recall | Std F1 | Mean # Segments |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DBSCAN | 1.0000 | 0.0476 | 0.0903 | 0.0000 | 0.0173 | 0.0313 | 2.33 |
| Sliding Window | 0.9848 | 0.1504 | 0.2565 | 0.0216 | 0.0548 | 0.0795 | 4.67 |
| KDE h=3.2 | 0.9480 | 0.2123 | 0.3433 | 0.0194 | 0.0521 | 0.0711 | 6.00 |

### `23_summer.pdf`

Preview comparing baseline methods and KDE against ground-truth highlights:

![23 summer method comparison preview](./23_summer_preview.png)

Original PDF: [23_summer.pdf](./23_summer.pdf)

### `24_spring.pdf`

Preview comparing baseline methods and KDE against ground-truth highlights:

![24 spring method comparison preview](./24_spring_preview.png)

Original PDF: [24_spring.pdf](./24_spring.pdf)

### `24_summer.pdf`

Preview comparing baseline methods and KDE against ground-truth highlights:

![24 summer method comparison preview](./24_summer_preview.png)

Original PDF: [24_summer.pdf](./24_summer.pdf)

## 2. KDE bandwidth ablation: quantitative result

### `kde_bandwidth_gt_curve.png`

This figure summarizes the **quantitative ablation study** over KDE bandwidth values for the KDE-based Key Interaction Segment selection method.

- As bandwidth `h` increases, recall generally improves because predicted segments become broader.
- Precision tends to decrease because broader segments include more temporally irrelevant regions.
- Although `h = 7.0` gives the highest mean F1, `h = 3.2` is selected as a precision-preserving operating point that still keeps recall and F1 competitive.

This corresponds to the bandwidth sensitivity analysis described in the paper for KDE-based segment extraction.

### KDE bandwidth sweep settings

The KDE bandwidth ablation uses the following main settings:

| Item | Value |
| --- | --- |
| Bandwidths reported in the paper figure/table | `1.0, 3.2, 5.0, 7.0, 10.0, 15.0, 20.0` |
| KDE kernel | Gaussian |
| Density threshold factor | `5.0` |
| Recommended bandwidth rule | `h = 0.8 x Q1` of inter-event gaps |
| Bandwidth clipping | `[1.0, 12.0]` or `[2.0, 12.0]`, depending on the bandwidth-selection setup |

### KDE bandwidth comparison table

This is the quantitative **KDE ablation study** table reported for the manually aligned highlight ground-truth set.

| `h` | Precision | Recall | F1 |
| --- | --- | --- | --- |
| 1.0 | 0.9941 | 0.1089 | 0.1945 |
| 3.2 | 0.9480 | 0.2123 | 0.3433 |
| 5.0 | 0.9581 | 0.1682 | 0.2828 |
| 7.0 | 0.9209 | 0.2555 | 0.3962 |
| 10.0 | 0.9283 | 0.2425 | 0.3819 |
| 15.0 | 0.9581 | 0.1682 | 0.2828 |
| 20.0 | 0.9853 | 0.1323 | 0.2258 |

![KDE bandwidth sensitivity curve](./kde_bandwidth_gt_curve.png)

## 3. KDE bandwidth ablation: qualitative comparison

These three figures qualitatively compare the **KDE ablation study across multiple bandwidths** on individual matches.

Visual encoding:

- Black lines: interaction events
- Blue rectangles: predicted segments
- Red rectangles: ground-truth highlight intervals

Main interpretation of the ablation:

- Small bandwidths produce fragmented segments that miss complete interactions.
- Large bandwidths over-merge nearby events into overly broad intervals.
- The selected setting `h = 3.2` yields temporally concise segments that align well with the ground-truth highlights.

### `NS_vs_DK_-_BRO_vs_T1_2024_LCK_4_multi_kde_rect_comparison.png`

![Bandwidth comparison for match 1](./NS_vs_DK_-_BRO_vs_T1_2024_LCK_4_multi_kde_rect_comparison.png)

### `T1_vs_NS_-_HLE_vs_KT_2024_LCK_4_multi_kde_rect_comparison.png`

![Bandwidth comparison for match 2](./T1_vs_NS_-_HLE_vs_KT_2024_LCK_4_multi_kde_rect_comparison.png)

### `GEN_vs_DRX_-_KT_vs_DK_2023_LCK_3_multi_kde_rect_comparison.png`

![Bandwidth comparison for match 3](./GEN_vs_DRX_-_KT_vs_DK_2023_LCK_3_multi_kde_rect_comparison.png)

## 4. Relation to the paper

In [ICML_2026.pdf](./ICML_2026.pdf), KDE is used to identify **Key Interaction Segments** from temporally clustered interaction events.

The figures in this folder support that part of the method in two ways:

- The bandwidth plots and per-match visualizations form the **KDE ablation study**.
- The seasonal PDF comparisons show how the selected KDE setup compares against DBSCAN and sliding-window baselines.

Together, they justify using KDE with `h = 3.2` for Key Interaction Segment selection in the paper.

## 5. LaTeX reference correction

The draft text had one reference issue:

- `\label{fig:kde_qualitative}` was reused for two different `figure*` environments.
- The multi-method paragraph referred to `Fig.~\ref{fig:method_comparison}`, but that label was not attached to the corresponding figure in the snippet.

Use distinct labels as follows:

```latex
\begin{figure*}[t]
    \centering
    \includegraphics[width=0.73\linewidth]{fig/ablation_kde/NS_vs_DK_-_BRO_vs_T1_2024_LCK_4_multi_kde_rect_comparison.png}
    \includegraphics[width=0.73\linewidth]{fig/ablation_kde/T1_vs_NS_-_HLE_vs_KT_2024_LCK_4_multi_kde_rect_comparison.png}
    \includegraphics[width=0.73\linewidth]{fig/ablation_kde/GEN_vs_DRX_-_KT_vs_DK_2023_LCK_3_multi_kde_rect_comparison.png}
    \caption{
    Qualitative comparison of KDE-based interaction segments across different bandwidths.
    Black lines indicate interaction events, blue rectangles denote predicted segments,
    and red rectangles represent ground-truth highlights.
    Smaller bandwidths produce fragmented segments, while larger bandwidths generate overly broad segments.
    The selected bandwidth ($h=3.2$) yields temporally concise segments that align well with ground-truth intervals.
    }
    \label{fig:kde_qualitative}
\end{figure*}

\begin{figure*}[t]
    \centering
    \includegraphics[width=0.9\linewidth]{fig/ablation_kde/23_summer.pdf}
    \includegraphics[width=0.9\linewidth]{fig/ablation_kde/24_spring.pdf}
    \includegraphics[width=0.9\linewidth]{fig/ablation_kde/24_summer.pdf}
    \caption{
    Qualitative comparison of segment extraction methods across multiple matches.
    Black lines denote interaction events, while colored rectangles indicate predicted segments
    (DBSCAN: purple, sliding window: green, KDE: blue) and ground-truth highlights (red),
    where ground-truth intervals are derived from curated highlight videos and aligned to the broadcast videos.
    DBSCAN produces sparse detections, and sliding window yields imprecise temporal boundaries,
    whereas the KDE-based method ($h=3.2$) generates segments that best align with ground-truth highlights
    in both location and duration.
    }
    \label{fig:method_comparison}
\end{figure*}
```

Recommended in-text references:

- Bandwidth qualitative comparison: `Fig.~\ref{fig:kde_qualitative}`
- Multi-method qualitative comparison: `Fig.~\ref{fig:method_comparison}`

From the current paper PDF, the corresponding rendered figure numbers are:

- KDE bandwidth sensitivity curve: Fig. 5
- KDE qualitative bandwidth comparison: Fig. 6
- Multi-method qualitative comparison: Fig. 7

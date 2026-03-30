## Reviewer Question 1

**Reg. generalizability of the Salient Interaction Module**

> “How could the Salient Interaction Module adapt ... pixel-level character behavior?”


The current **Salient Interaction Module** is designed for **HUD-rich broadcast gameplay videos**, where cues such as **event logs** and **minimap icons** are explicitly available on screen. We chose this setting intentionally because, unlike general videos, gameplay videos often expose structured state information that directly reflects player and object interactions. This design also enables **temporally precise event detection directly from the video itself**, without relying on external APIs or game metadata.

Detecting interaction units solely from **pixel-level character behavior** is certainly an important direction. However, in fast-paced game environments with frequent motion, camera shifts, overlapping visual effects, and multiple agents acting simultaneously, purely pixel-based interaction detection remains considerably more challenging. We therefore use visible HUD cues as reliable anchors for accurate interaction timing in the current work.

Our design is also motivated by robustness under realistic broadcast and streaming conditions. Since our goal is to support short-form generation not only for professional broadcasts but also for user-recorded gameplay, we formulate event recognition as an **object-detection** problem, as gameplay HUD elements are small, partially overlapping, and easily confused with the background.

Extending the module to gameplay videos where explicit event logs or minimaps are not available, through direct visual behavior modeling, is an important direction for future work. We will clarify this scope more explicitly in the revision.


# KDE Bandwidth Sensitivity for Key Interaction Segment Selection

Thank you for the question regarding bandwidth selection. This note summarizes the additional analysis addressing how sensitive highlight detection is to the KDE bandwidth `h`.

## Question Addressed

> Appendix B mentions selecting the bandwidth `h` using a global statistic. How sensitive is highlight detection and caption quality to variations in this bandwidth?

## Ground-Truth Highlights

The bandwidth sensitivity evaluation uses manually aligned ground-truth highlight intervals constructed from curated YouTube highlight videos of the same matches. These intervals are aligned to the corresponding full broadcast videos using a synchronization point between game time and video time, and are used to evaluate temporal overlap-based precision, recall, and F1 across different bandwidth settings.

## KDE Parameters

The KDE-based segment selection uses the following main parameters:

- Gaussian kernel
- bandwidth `h`
- density-threshold factor `= 5.0`
- minimum interaction count `= 2`

The selected bandwidth is computed from a robust global statistic of inter-event intervals:

- `Q1 = 4.0` seconds
- `h = 0.8 x Q1 = 3.2` seconds

## Quantitative Bandwidth Comparison

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

## Quantitative Interpretation

The results show that highlight detection is **meaningfully sensitive** to the bandwidth choice.

- At very small bandwidths such as `h = 1.0`, precision is extremely high (`0.9941`), but recall is very low (`0.1089`). This means the predicted segments are temporally sharp but too fragmented to cover many complete highlights.
- As bandwidth increases, recall generally improves because nearby events are merged more readily into broader interaction segments.
- Larger bandwidths such as `h = 7.0` and `h = 10.0` achieve the highest recall and F1, showing that broader smoothing can improve overlap with the ground-truth intervals.
- However, larger bandwidths also lead to less temporally concise segments, which is undesirable when the goal is precise highlight localization.

For this reason, we select **`h = 3.2`** as a conservative operating point. Although it does not maximize F1, it preserves high precision (`0.9480`) while still improving recall substantially over very small bandwidths. In other words, `h = 3.2` provides a better balance when the goal is not only to cover highlights, but also to keep interaction segments temporally tight.

## Qualitative Bandwidth Comparison

The following examples compare KDE predictions across multiple bandwidth values against ground-truth highlights.

Because OpenReview space is limited, the full qualitative visualizations can be referred to through the GitHub supplementary materials if needed. The explanation is retained here so that the qualitative behavior across bandwidth values remains clear even when the figures are referenced externally.

Visual encoding:

- Black lines: interaction events
- Blue rectangles: predicted KDE segments
- Red rectangles: ground-truth highlights

### `NS_vs_DK_-_BRO_vs_T1_2024_LCK_4_multi_kde_rect_comparison.png`

![Bandwidth comparison for match 1](./NS_vs_DK_-_BRO_vs_T1_2024_LCK_4_multi_kde_rect_comparison.png)

### `T1_vs_NS_-_HLE_vs_KT_2024_LCK_4_multi_kde_rect_comparison.png`

![Bandwidth comparison for match 2](./T1_vs_NS_-_HLE_vs_KT_2024_LCK_4_multi_kde_rect_comparison.png)

### `GEN_vs_DRX_-_KT_vs_DK_2023_LCK_3_multi_kde_rect_comparison.png`

![Bandwidth comparison for match 3](./GEN_vs_DRX_-_KT_vs_DK_2023_LCK_3_multi_kde_rect_comparison.png)

## Qualitative Interpretation

The qualitative examples support the same pattern seen in the quantitative results.

- Small bandwidths produce fragmented segments that often fail to capture complete interactions.
- Large bandwidths merge temporally nearby events into overly broad intervals that can extend beyond the annotated highlight regions.
- The selected setting `h = 3.2` produces segments that remain temporally concise while still aligning well with the ground-truth highlight intervals.


**Reg. comparison with broader baselines**

> “While domain-specific baselines ... Video-LLaVA or Gemini Pro Vision.”

To address it, we expanded the comparison not only to a general-purpose video-language model (Video-LLaVA) in a zero-shot setting, but also to broader dense video captioning baselines (Vid2Seq and CM²), in addition to the game-specific baseline LoL-V2T.

| Model | BLEU-3 | BLEU-4 | METEOR | ROUGE-L | CIDEr | CLIP-S | BERT-S |
|:------|:------:|:------:|:------:|:-------:|:-----:|:------:|:------:|
| Video-LLaVA | 0.13 | 0.00 | 3.14 | 6.84 | 0.01 | 26.49 | 7.89 |
| Vid2Seq | 0.01 | 0.01 | 3.18 | 2.13 | 0.01 | 21.99 | 0.00 |
| CM² | 0.09 | 0.00 | 8.33 | 10.56 | 0.01 | 24.08 | 14.75 |
| LoL-V2T | 2.17 | 1.25 | 12.26 | 12.66 | 8.34 | 28.95 | 17.86 |
| Ours | 3.17 | 1.54 | 16.05 | 15.31 | 7.14 | 28.06 | 24.64 |

*Video-LLaVA is evaluated in a zero-shot setting without task-specific training. Vid2Seq, CM2, and LoL-V2T are trained on our dataset for comparison, and our method is trained on the same dataset.*

As shown above, these broader baselines underperform our method on this task, suggesting that interaction-heavy gameplay commentary requires stronger domain-specific grounding than generic transfer alone can provide.
**Rebuttal:**

We thank Reviewer SEnx for the detailed and helpful feedback. We respond to the concerns as follows:

**Reg. interaction-aware conditioning**

To isolate the effect of interaction-aware conditioning, we fixed the best-performing configuration from Table 5 (ViT-B/16 + RelPos + LSTM) and compared two settings: one trained on single events only, and the other with full interaction-level conditioning.

| Setting | BLEU-3 | BLEU-4 | METEOR | ROUGE-L | CIDEr |
|:------------|:------:|:------:|:------:|:-------:|:-----:|
| Event-level | 2.59 | 1.12 | 14.74 | 13.57 | 5.64 |
| Interaction-level | 3.17 | 1.54 | 16.05 | 15.31 | 7.14 |

Under the same encoder-decoder configuration, the interaction-level version performs better across all metrics. We attribute this gain to the use of caption targets from temporally dense interaction segments, which better reflect meaningful gameplay moments than single events.

**Reg. broader baseline comparison and CIDEr**

**Comparison baselines**: We expanded the comparison to include a zero-shot video-language model (Video-LLaVA), recent dense video captioning baselines (Vid2Seq and CM2), and the game-specific baseline LoL-V2T. In the updated results, our method achieves the best performance on BLEU-3, BLEU-4, METEOR, ROUGE-L, and BERTScore (BERT-S).

| Model | BLEU-3 | BLEU-4 | METEOR | ROUGE-L | CIDEr | CLIP-S | BERT-S |
|:------|:------:|:------:|:------:|:-------:|:-----:|:------:|:------:|
| Video-LLaVA | 0.13 | 0.00 | 3.14 | 6.84 | 0.01 | 26.49 | 7.89 |
| Vid2Seq | 0.01 | 0.01 | 3.18 | 2.13 | 0.01 | 21.99 | 18.70 |
| CM² | 0.09 | 0.00 | 8.33 | 10.56 | 0.01 | 24.08 | 14.75 |
| LoL-V2T | 2.17 | 1.25 | 12.26 | 12.66 | 8.34 | 28.95 | 17.86 |
| Ours | 3.17 | 1.54 | 16.05 | 15.31 | 7.14 | 28.06 | 24.64 |

*Video-LLaVA is evaluated in a zero-shot setting without task-specific training. Vid2Seq, CM², and LoL-V2T are trained on our dataset for comparison, and our method is trained on the same dataset.*

**CIDEr analysis** : Regarding CIDEr, we agree that this metric is important and that the gap with LoL-V2T deserves clarification. We believe this difference arises because CIDEr is more sensitive to lexical consensus with the reference captions. In gameplay commentary, a given interaction can admit multiple valid descriptions depending on which events or contextual details are emphasized. Recent work likewise suggests that traditional overlap-based metrics may not fully reflect semantic quality in detailed caption evaluation [1]. 

We therefore additionally report BERT-S, a semantic similarity metric, under which our method performs substantially better (24.64 vs. 17.86). This suggests that the interaction-level formulation improves semantic quality even when it does not maximize reference-level n-gram consensus.

*[1] Chai, Wenhao, et al. "AuroraCap: Efficient, Performant Video Detailed Captioning and a New Benchmark." International Conference on Learning Representations (2025).*

**Reg. segment selection comparison**

We additionally compare KDE-based segment extraction against DBSCAN and Sliding Window using manually aligned ground-truth highlight intervals from the same matches. Visuals: https://anonymous.4open.science/r/anonymous-submission-27793/mm.md. The aggregate results are:

| Method | Precision | Recall | F1 | Mean # Segments |
|:------:|:---------:|:------:|:--:|:---------------:|
| DBSCAN | 1.0000 | 0.0476 | 0.0903 | 2.33 |
| Sliding Window | 0.9848 | 0.1504 | 0.2565 | 4.67 |
| KDE h=3.2 | 0.9480 | 0.2123 | 0.3433 | 6.00 |

These results show that DBSCAN is highly precise but too sparse, while Sliding Window improves coverage but remains less adaptive. KDE (`h=3.2`) achieves the highest recall and F1 while maintaining high precision, indicating a better overall balance for key interaction segment selection. The same pattern appears in the qualitative GT comparisons (Figs. 1-3).

**Reg. user study and generalization**
- **Evaluation scope:**  The user study is not caption-only. It evaluates end-to-end short-form quality (highlight selection + captions) on user-recorded gameplay. We also provide the demo video used in the study: https://anonymous.4open.science/r/anonymous-submission-27793/README.md

- **Component disentanglement:**  We do not separate highlight selection and caption generation because our goal is to assess overall short-form quality. Caption-level quality is complemented by automatic metrics, including BERT-S.

- **Exhibition setting:**  The public exhibition matches our target application, as participants are real game players who can judge contextual appropriateness.

- **Generalization:**  We report quantitative metrics on broadcast data because reliable ground-truth captions are available there, while such annotations are difficult to obtain at scale for user-recorded gameplay. User satisfaction on more diverse and noisy user videos therefore provides practical evidence of generalization. We will clarify this in the revision.
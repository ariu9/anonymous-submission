**Rebuttal:**

Thank you for your detailed and encouraging feedback. We appreciate that you found the problem practically motivated and the interaction-aware framing sensible for gameplay videos, where highlights naturally arise from sequences of related actions rather than isolated events.

**Reg. technical novelty beyond standard components**

> “the underlying components ... are relatively standard techniques in the field”

We appreciate this concern. At the component level, object detection, KDE-based temporal grouping, and autoregressive decoders may indeed appear standard when considered individually. However, we see the contribution somewhat differently. We would like to highlight that the novelty of our work lies in organizing these components around an **interaction-level caption unit**, rather than a conventional event-level unit. In gameplay videos, highlight semantics often emerge from temporally dense and causally related event sequences, rather than from isolated atomic events alone. We therefore view the main contribution as an **interaction-aware reformulation of gameplay highlight captioning**, rather than component-level novelty.

To further clarify this point, we additionally compared an event-level caption unit with our interaction-level caption unit under the same training and evaluation setting. As shown below, the interaction-level formulation consistently performs better than the event-level variant, including improvements in BLEU-4 (1.12 → 1.54), METEOR (14.74 → 16.05), and CIDEr (5.64 → 7.14). These results support our view that the main gain does not come merely from combining standard components. Rather, it comes from redefining the caption unit from isolated events to interaction-level segments, which distinguishes our method from conventional event-level dense video captioning. We will include this comparison in the revision to make this point clearer.

| Caption unit | BLEU-3 | BLEU-4 | METEOR | ROUGE-L | CIDEr |
|:------------|:------:|:------:|:------:|:-------:|:-----:|
| Event-level | 2.59 | 1.12 | 14.74 | 13.57 | 5.64 |
| Interaction-level | 3.17 | 1.54 | 16.05 | 15.31 | 7.14 |

**Reg. evaluation beyond n-gram metrics**

> “The caption generation evaluation focuses heavily on n-gram metrics ...”

We agree that gameplay commentary is more open-ended than standard captioning, and that BLEU / METEOR / ROUGE alone cannot fully capture factual consistency or strategic understanding.

To address this concern, we additionally report two complementary semantic metrics: CLIPScore (CLIP-S) for reference-free visual-semantic alignment, and BERTScore (BERT-S) for text-level semantic similarity beyond n-gram overlap. We also expanded the comparison to include a general-purpose video-language model (Video-LLaVA ) evaluated in a zero-shot setting, as well as dense video captioning baselines (Vid2Seq and CM2), in addition to the game-specific baseline LoL-V2T.

| Model | BLEU-3 | BLEU-4 | METEOR | ROUGE-L | CIDEr | CLIP-S | BERT-S |
|:------|:------:|:------:|:------:|:-------:|:-----:|:------:|:------:|
| Video-LLaVA | 0.13 | 0.00 | 3.14 | 6.84 | 0.01 | 26.49 | 7.89 |
| Vid2Seq | 0.01 | 0.01 | 3.18 | 2.13 | 0.01 | 21.99 | 18.70 |
| CM2 | 0.09 | 0.00 | 8.33 | 10.56 | 0.01 | 24.08 | 14.75 |
| LoL-V2T | 2.17 | 1.25 | 12.26 | 12.66 | 8.34 | 28.95 | 17.86 |
| Ours | 3.17 | 1.54 | 16.05 | 15.31 | 7.14 | 28.06 | 24.64 |

*Video-LLaVA is evaluated in a zero-shot setting without task-specific training. Vid2Seq, CM2, and LoL-V2T are trained on our dataset for comparison, and our method is trained on the same dataset.*

- **CLIP-S** provides a reference-free measure of visual-semantic alignment, but shows limited discriminability in our setting. This is likely because CLIP is trained on general image-text pairs rather than gameplay-specific content, making it less sensitive to the strategic and interaction-level semantics of gameplay commentary. As a result, the strongest models receive very similar scores.

- **BERT-S** is more informative in this setting because it better captures text-level semantic similarity. Under this metric, our method achieves the best result (24.64).

Our user study was also not text-only: participants evaluated the complete pipeline output, i.e., extracted highlight segments together with their corresponding narrative captions in video context. While the current protocol focuses more on overall viewing experience and contextual naturalness than on explicitly separated ratings of factual consistency or strategic understanding, it still reflects the practical usability of the full system in a realistic setting. 

We also provide a video demo as supplementary material so that the reviewer can directly inspect representative outputs. In future work, we plan to extend the evaluation protocol with more explicit criteria for factual consistency and strategic understanding.

Video demo: https://anonymous.4open.science/r/anonymous-submission-27793/README.md

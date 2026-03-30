**Rebuttal:**

We thank Reviewer rurB for taking the time to review our paper and provide valuable feedback. We respond to the concerns as follows:

**Reg. generalizability of the Salient Interaction Module**

The current Salient Interaction Module is designed for HUD-rich broadcast gameplay videos, where cues such as event logs and minimap icons are explicitly visible. We chose this setting intentionally because such on-screen state information directly reflects player and object interactions and enables temporally precise event detection from video itself, without relying on external APIs or game metadata (Sections 2 and 5.4).

Detecting interaction units solely from pixel-level character behavior remains more challenging in fast-paced gameplay with frequent motion, camera shifts, overlapping effects, and simultaneous multi-agent actions. We therefore use visible HUD cues as reliable anchors for accurate interaction timing, while recognizing direct visual behavior modeling for low-UI gameplay as an important future direction.

**Reg. comparison with broader baselines**

To address it, we expanded the comparison not only to a general-purpose video-language model (Video-LLaVA) in a zero-shot setting, but also to broader dense video captioning baselines (Vid2Seq and CM²), in addition to the game-specific baseline LoL-V2T.

| Model | BLEU-3 | BLEU-4 | METEOR | ROUGE-L | CIDEr | CLIP-S | BERT-S |
|:------|:------:|:------:|:------:|:-------:|:-----:|:------:|:------:|
| Video-LLaVA | 0.13 | 0.00 | 3.14 | 6.84 | 0.01 | 26.49 | 7.89 |
| Vid2Seq | 0.01 | 0.01 | 3.18 | 2.13 | 0.01 | 21.99 | 18.70 |
| CM² | 0.09 | 0.00 | 8.33 | 10.56 | 0.01 | 24.08 | 14.75 |
| LoL-V2T | 2.17 | 1.25 | 12.26 | 12.66 | 8.34 | 28.95 | 17.86 |
| Ours | 3.17 | 1.54 | 16.05 | 15.31 | 7.14 | 28.06 | 24.64 |

*Video-LLaVA is evaluated in a zero-shot setting without task-specific training. Vid2Seq, CM2, and LoL-V2T are trained on our dataset for comparison, and our method is trained on the same dataset.*

As shown above, these broader baselines underperform our method on this task, suggesting that interaction-heavy gameplay commentary requires stronger domain-specific grounding than generic transfer alone can provide.

**Reg. caster bias in broadcast commentary**

Our target is broadcast-style gameplay narration, not strictly neutral captioning. 

In gameplay commentary, there is often no single correct description for a given scene: different casters may describe the same interaction with different wording, emphasis, or degree of hype, while still referring to the same underlying event. 
Our goal is therefore not to reproduce commentator-specific phrasing itself, but to generate narration that remains grounded in the interaction content within the style space of broadcast commentary. 

During dataset construction, we anonymized team, player, and champion names and refined the commentary so that the model follows the narrative style of broadcasts while remaining closer to objective interaction content. We will clarify this dataset characteristic more explicitly in a newer version.

**Reg. interaction awareness in caption generation**

As described in Section 4.3, each interaction segment is represented as a set of event embeddings, and each event embedding is extracted from a pre-event temporal window using temporal attention pooling.

Thus, the model is not conditioned on an event token alone, but on multiple temporally related events within the interaction segment. While event order is not modeled by a separate sequential module, the interaction-level input itself provides richer temporal context.


**Reg. video demo**

We include a video demo of the full pipeline, i.e., highlight extraction from full gameplay videos and the corresponding generated captions.

Video demo: https://anonymous.4open.science/r/anonymous-submission-27793/README.md
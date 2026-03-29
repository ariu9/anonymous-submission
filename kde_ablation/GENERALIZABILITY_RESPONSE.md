# Generalizability of the Salient Interaction Module

Thank you for raising the question of generalizability beyond UI-rich gameplay videos. We agree that this is an important limitation to clarify.

## Reviewer Comments

> "The approach relies heavily on visible HUD elements (minimap, event logs), limiting applicability to games with minimal UI or cinematic-style recordings."

> "Generalizability: How could the Salient Interaction Module adapt to games without explicit event logs or minimaps? Is it feasible to detect interactions solely from pixel-level character behavior?"

## Our View

We think these comments are best understood as a **scope and generalizability** question rather than a weakness of the KDE formulation itself.

In the current paper, the Salient Interaction Module is designed for gameplay videos where interaction cues are externally observable through broadcast-style UI signals such as event logs and the minimap. This design choice is intentional: in MOBA gameplay videos, these cues provide structured evidence about interactions, objectives, and temporal context that would otherwise be difficult to infer reliably from pixels alone.

So our current position is:

- the present method is most appropriate for **UI-rich broadcast or recorded gameplay videos**
- the method is **not yet claimed** to generalize directly to cinematic-style recordings or games with minimal visible HUD information
- this should be stated more clearly as a limitation in the paper

## Response

We agree that the current formulation relies on visible UI-derived cues such as event logs and minimap information, and therefore is best suited to games and recordings where such interaction signals are available. We will clarify this scope more explicitly in the revision.

At the same time, we believe the broader **interaction-aware formulation** is not inherently limited to explicit event logs. In principle, the Salient Interaction Module could be adapted to low-UI or no-UI games by replacing UI-derived events with interaction cues inferred from visual observations, such as:

- character trajectories and proximity patterns
- combat engagement dynamics
- camera motion patterns associated with salient events
- object-state changes and multi-agent coordination signals

Under such a setting, the interaction signal would need to be estimated from pixel-level behavior rather than read from structured on-screen logs. In that case, KDE or a similar temporal grouping mechanism could still be applied after obtaining event-like interaction candidates from vision models.

## Feasibility of Pixel-Level Interaction Detection

We believe this is feasible in principle, but it would require a substantially different front-end than the one used in the current paper.

- In the current work, event logs provide a strong and reliable source of interaction evidence.
- In a pixel-only setting, the system would first need to detect or infer interaction events from character motion, combat patterns, and scene dynamics.
- Once such event candidates are available, the temporal grouping stage could still operate in a similar way to identify salient interaction segments.

So the main challenge is not the temporal grouping stage itself, but the **upstream extraction of interaction cues** from raw visual content.

## Revision Text

We will revise the paper to clarify that the current method is designed for UI-rich gameplay videos and does not yet directly target cinematic-style or low-UI game recordings. We will also add a brief discussion that, although the current implementation relies on event logs and minimap cues, the broader interaction-segment formulation could in principle be extended to pixel-level interaction detection by replacing the current event extraction stage with vision-based interaction estimators.

A concise revision-ready summary is:

> We agree that the current Salient Interaction Module relies on visible UI-derived cues such as event logs and minimap information, and is therefore best suited to UI-rich gameplay videos. We will clarify this scope more explicitly in the revision. More broadly, we do not view the interaction-aware formulation as inherently limited to explicit logs: in principle, the same segment-selection framework could be extended to low-UI settings by first inferring event-like interaction cues from pixel-level character behavior, such as motion, proximity, combat dynamics, and multi-agent coordination patterns. In that case, the main additional challenge lies in extracting reliable interaction candidates from raw visual observations rather than in the temporal grouping stage itself.

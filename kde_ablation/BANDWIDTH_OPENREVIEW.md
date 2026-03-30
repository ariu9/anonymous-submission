# Bandwidth Sensitivity

Thank you for the question on KDE bandwidth sensitivity. We evaluated highlight detection across multiple bandwidths using manually aligned ground-truth highlight intervals from the same matches. The results show a clear tradeoff: larger `h` improves recall and F1, but also broadens segments; smaller `h` keeps segments tighter but fragments interactions. We therefore report both overlap quality and duration alignment.

| `h` | Precision | Recall | F1 | Dur. Diff |
| --- | --- | --- | --- | --- |
| 1.0 | 0.9443 | 0.1155 | 0.2034 | 8.19 |
| 3.2 | 0.9132 | 0.2256 | 0.3578 | 1.80 |
| 5.0 | 0.8848 | 0.2557 | 0.3913 | 3.11 |
| 7.0 | 0.8606 | 0.2627 | 0.3983 | 4.85 |

Although `h=7.0` gives the highest mean F1, `h=3.2` gives the smallest mean duration difference and the best balance between coverage and temporal tightness. We therefore keep `h=3.2` as a conservative operating point for concise highlight localization. Qualitative bandwidth examples are provided in the GitHub supplementary materials: [BANDWIDTH_SENSITIVITY.md](./BANDWIDTH_SENSITIVITY.md).

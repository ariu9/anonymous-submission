import argparse
import csv
import json
from pathlib import Path

import numpy as np

try:
    import matplotlib
    matplotlib.use("agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

import compare_highlights_md as ch


def parse_bandwidths(raw: str):
    vals = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        vals.append(chunk)
    if not vals:
        raise ValueError("At least one bandwidth must be provided.")
    return vals


def load_gt_blocks(gt_file: str | None, gt_dir: str | None):
    if gt_file:
        gt_path = Path(gt_file)
        return gt_path.name, ch.parse_gt_blocks(gt_path)

    if not gt_dir:
        raise ValueError("Either --gt_file or --gt_dir must be provided.")

    gt_root = Path(gt_dir)
    all_blocks = []
    seen_titles = set()
    for path in sorted(gt_root.glob("*.txt")):
        for block in ch.parse_gt_blocks(path):
            title_key = ch.normalize_text(block["title"])
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            all_blocks.append(block)
    if not all_blocks:
        raise ValueError(f"No GT blocks found in {gt_root}")
    return gt_root.name, all_blocks


def gt_dataset_rows(blocks):
    rows = []
    for block in blocks:
        intervals = block["highlight_intervals"]
        total_gt_sec = sum(iv["video_end_sec"] - iv["video_start_sec"] for iv in intervals)
        rows.append({
            "match": block["title"],
            "sync_mmss": ch.seconds_to_mmss(block["sync_point"]),
            "num_highlights": len(intervals),
            "total_gt_sec": float(total_gt_sec),
        })
    return rows


def metric_row_for_bandwidth(block, title, bandwidth_label, root: Path):
    seg_path, payload = ch.find_matching_segment_json(root / "segments", title)
    _ = seg_path
    pred_intervals = [
        {"start": float(seg["start"]), "end": float(seg["end"])}
        for seg in payload.get("segments", [])
    ]
    gt_intervals = [
        {"start": float(iv["video_start_sec"]), "end": float(iv["video_end_sec"])}
        for iv in block["highlight_intervals"]
    ]
    metrics = ch.compute_time_metrics(pred_intervals=pred_intervals, gt_intervals=gt_intervals)
    return {
        "match": title,
        "bandwidth_label": bandwidth_label,
        "bandwidth_sec": float(bandwidth_label),
        "num_segments": len(pred_intervals),
        "pred_total_sec": float(metrics["pred_total_sec"]),
        "gt_total_sec": float(metrics["gt_total_sec"]),
        "overlap_sec": float(metrics["overlap_sec"]),
        "time_precision": float(metrics["time_precision"]),
        "time_recall": float(metrics["time_recall"]),
        "time_f1": float(metrics["time_f1"]),
        "pred_mean_duration_sec": float(metrics["pred_mean_duration_sec"]),
        "gt_mean_duration_sec": float(metrics["gt_mean_duration_sec"]),
        "duration_diff_sec": float(metrics["duration_diff_sec"]),
    }


def build_summary_rows(per_match_rows):
    grouped = {}
    for row in per_match_rows:
        grouped.setdefault(row["bandwidth_label"], []).append(row)

    summary_rows = []
    for bandwidth_label, rows in sorted(grouped.items(), key=lambda item: float(item[0])):
        precision = np.array([r["time_precision"] for r in rows], dtype=float)
        recall = np.array([r["time_recall"] for r in rows], dtype=float)
        f1 = np.array([r["time_f1"] for r in rows], dtype=float)
        pred_sec = np.array([r["pred_total_sec"] for r in rows], dtype=float)
        overlap_sec = np.array([r["overlap_sec"] for r in rows], dtype=float)
        pred_mean_duration_sec = np.array([r["pred_mean_duration_sec"] for r in rows], dtype=float)
        gt_mean_duration_sec = np.array([r["gt_mean_duration_sec"] for r in rows], dtype=float)
        duration_diff_sec = np.array([r["duration_diff_sec"] for r in rows], dtype=float)
        duration_score = np.maximum(0.0, 1.0 - (duration_diff_sec / np.maximum(gt_mean_duration_sec, 1e-9)))
        combined_score = 0.5 * f1 + 0.5 * duration_score
        summary_rows.append({
            "bandwidth_label": bandwidth_label,
            "bandwidth_sec": float(bandwidth_label),
            "n_matches": len(rows),
            "mean_precision": float(precision.mean()),
            "mean_recall": float(recall.mean()),
            "mean_f1": float(f1.mean()),
            "std_precision": float(precision.std(ddof=0)),
            "std_recall": float(recall.std(ddof=0)),
            "std_f1": float(f1.std(ddof=0)),
            "mean_pred_total_sec": float(pred_sec.mean()),
            "mean_overlap_sec": float(overlap_sec.mean()),
            "mean_pred_mean_duration_sec": float(pred_mean_duration_sec.mean()),
            "mean_gt_mean_duration_sec": float(gt_mean_duration_sec.mean()),
            "mean_duration_diff_sec": float(duration_diff_sec.mean()),
            "std_duration_diff_sec": float(duration_diff_sec.std(ddof=0)),
            "mean_duration_score": float(duration_score.mean()),
            "mean_combined_score": float(combined_score.mean()),
            "std_combined_score": float(combined_score.std(ddof=0)),
        })
    return summary_rows


def write_csv(path: Path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def plot_time_f1_curve(summary_rows, out_path: Path, title: str):
    if plt is None:
        return None

    x = np.array([row["bandwidth_sec"] for row in summary_rows], dtype=float)
    precision = np.array([row["mean_precision"] for row in summary_rows], dtype=float)
    recall = np.array([row["mean_recall"] for row in summary_rows], dtype=float)
    f1 = np.array([row["mean_f1"] for row in summary_rows], dtype=float)

    plt.figure(figsize=(10, 6))
    plt.plot(x, precision, marker="o", linewidth=2.0, color="#1d3557", label="Mean Precision")
    plt.plot(x, recall, marker="o", linewidth=2.0, color="#e76f51", label="Mean Recall")
    plt.plot(x, f1, marker="o", linewidth=2.4, color="#2a9d8f", label="Mean F1")
    plt.xlabel("KDE global_h (seconds)", fontsize=13)
    plt.ylabel("Mean score across GT matches", fontsize=13)
    plt.title(title, fontsize=15)
    plt.ylim(0.0, min(1.0, max(precision.max(), recall.max(), f1.max(), 0.05) + 0.08))
    plt.grid(True, linestyle=":", alpha=0.35)
    plt.legend(loc="best", fontsize=11)
    plt.xticks(x, [f"{v:.1f}" for v in x], fontsize=11)
    plt.yticks(fontsize=11)
    plt.tight_layout()
    plt.savefig(out_path, dpi=140)
    plt.close()
    return out_path


def plot_duration_diff_curve(summary_rows, out_path: Path, title: str):
    if plt is None:
        return None

    x = np.array([row["bandwidth_sec"] for row in summary_rows], dtype=float)
    gt_mean = np.array([row["mean_gt_mean_duration_sec"] for row in summary_rows], dtype=float)
    pred_mean = np.array([row["mean_pred_mean_duration_sec"] for row in summary_rows], dtype=float)
    duration_diff = np.array([row["mean_duration_diff_sec"] for row in summary_rows], dtype=float)

    plt.figure(figsize=(10, 6))
    plt.plot(x, gt_mean, marker="o", linewidth=2.0, color="#6c757d", label="Mean GT Duration")
    plt.plot(x, pred_mean, marker="o", linewidth=2.0, color="#264653", label="Mean Pred Duration")
    plt.plot(x, duration_diff, marker="o", linewidth=2.4, color="#d62828", label="Mean Duration Diff")
    plt.xlabel("KDE global_h (seconds)", fontsize=13)
    plt.ylabel("Seconds", fontsize=13)
    plt.title(title, fontsize=15)
    plt.grid(True, linestyle=":", alpha=0.35)
    plt.legend(loc="best", fontsize=11)
    plt.xticks(x, [f"{v:.1f}" for v in x], fontsize=11)
    plt.yticks(fontsize=11)
    plt.tight_layout()
    plt.savefig(out_path, dpi=140)
    plt.close()
    return out_path


def plot_combined_curve(summary_rows, out_path: Path, title: str):
    if plt is None:
        return None

    x = np.array([row["bandwidth_sec"] for row in summary_rows], dtype=float)
    precision = np.array([row["mean_precision"] for row in summary_rows], dtype=float)
    recall = np.array([row["mean_recall"] for row in summary_rows], dtype=float)
    f1 = np.array([row["mean_f1"] for row in summary_rows], dtype=float)
    duration_score = np.array([row["mean_duration_score"] for row in summary_rows], dtype=float)
    combined = np.array([row["mean_combined_score"] for row in summary_rows], dtype=float)

    plt.figure(figsize=(10, 6))
    plt.plot(x, precision, marker="o", linewidth=1.8, color="#1d3557", alpha=0.75, label="Mean Precision")
    plt.plot(x, recall, marker="o", linewidth=1.8, color="#e76f51", alpha=0.75, label="Mean Recall")
    plt.plot(x, f1, marker="o", linewidth=2.0, color="#2a9d8f", alpha=0.85, label="Mean F1")
    plt.plot(x, duration_score, marker="o", linewidth=2.0, color="#8d99ae", alpha=0.9, label="Mean Duration Diff Score")
    plt.plot(x, combined, marker="o", linewidth=2.8, color="#3a5a40", label="Mean Combined Score")
    plt.xlabel("KDE global_h (seconds)", fontsize=13)
    plt.ylabel("Normalized score", fontsize=13)
    plt.title(title, fontsize=15)
    plt.ylim(0.0, min(1.0, max(combined.max(), precision.max(), recall.max(), f1.max(), duration_score.max(), 0.05) + 0.08))
    plt.grid(True, linestyle=":", alpha=0.35)
    plt.legend(loc="best", fontsize=11)
    plt.xticks(x, [f"{v:.1f}" for v in x], fontsize=11)
    plt.yticks(fontsize=11)
    plt.tight_layout()
    plt.savefig(out_path, dpi=140)
    plt.close()
    return out_path


def write_markdown(path: Path, summary_rows, per_match_rows, time_f1_plot_path: Path | None, duration_diff_plot_path: Path | None, combined_plot_path: Path | None, gt_source_label: str, dataset_rows):
    best = max(summary_rows, key=lambda row: row["mean_f1"])
    best_duration = min(summary_rows, key=lambda row: row["mean_duration_diff_sec"])
    best_combined = max(summary_rows, key=lambda row: row["mean_combined_score"])
    lines = []
    lines.append("# KDE Bandwidth vs GT Metrics")
    lines.append("")
    lines.append(f"- GT source: `{gt_source_label}`")
    lines.append(f"- Matches used: `{len({row['match'] for row in per_match_rows})}`")
    lines.append(f"- Best mean F1: `h={best['bandwidth_sec']:.1f}` ({best['mean_f1']:.4f})")
    lines.append(f"- Smallest mean duration diff: `h={best_duration['bandwidth_sec']:.1f}` ({best_duration['mean_duration_diff_sec']:.2f}s)")
    lines.append(f"- Best combined score: `h={best_combined['bandwidth_sec']:.1f}` ({best_combined['mean_combined_score']:.4f})")
    lines.append("- Combined score uses `0.5 * time_f1 + 0.5 * duration_score`, where `duration_score = max(0, 1 - duration_diff / gt_mean_duration)`.")
    lines.append("")
    if time_f1_plot_path is not None:
        lines.append(f"![KDE bandwidth precision recall F1 sweep]({time_f1_plot_path.name})")
        lines.append("")
    if duration_diff_plot_path is not None:
        lines.append(f"![KDE bandwidth duration sweep]({duration_diff_plot_path.name})")
        lines.append("")
    if combined_plot_path is not None:
        lines.append(f"![KDE bandwidth combined score sweep]({combined_plot_path.name})")
        lines.append("")

    lines.append("## Mean Metrics")
    lines.append("")
    lines.append("| h | Matches | Mean Precision | Mean Recall | Mean F1 | Mean GT Dur | Mean Pred Dur | Mean Dur Diff | Mean Dur Score | Mean Combined | Std Precision | Std Recall | Std F1 | Std Dur Diff | Std Combined |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in summary_rows:
        lines.append(
            f"| {row['bandwidth_sec']:.1f} | {row['n_matches']} | {row['mean_precision']:.4f} | "
            f"{row['mean_recall']:.4f} | {row['mean_f1']:.4f} | "
            f"{row['mean_gt_mean_duration_sec']:.2f} | {row['mean_pred_mean_duration_sec']:.2f} | "
            f"{row['mean_duration_diff_sec']:.2f} | {row['mean_duration_score']:.4f} | "
            f"{row['mean_combined_score']:.4f} | {row['std_precision']:.4f} | "
            f"{row['std_recall']:.4f} | {row['std_f1']:.4f} | {row['std_duration_diff_sec']:.2f} | "
            f"{row['std_combined_score']:.4f} |"
        )
    lines.append("")

    lines.append("## GT Dataset")
    lines.append("")
    lines.append("| Match | Sync | # Highlights | GT Sec |")
    lines.append("| --- | --- | --- | --- |")
    for row in sorted(dataset_rows, key=lambda item: item["match"]):
        lines.append(
            f"| {row['match']} | {row['sync_mmss']} | {row['num_highlights']} | {row['total_gt_sec']:.2f} |"
        )
    lines.append("")

    lines.append("## Per-Match Metrics")
    lines.append("")
    lines.append("| Match | h | Precision | Recall | F1 | GT Mean Dur | Pred Mean Dur | Dur Diff | # Segments |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in sorted(per_match_rows, key=lambda item: (item["match"], item["bandwidth_sec"])):
        lines.append(
            f"| {row['match']} | {row['bandwidth_sec']:.1f} | {row['time_precision']:.4f} | "
            f"{row['time_recall']:.4f} | {row['time_f1']:.4f} | {row['gt_mean_duration_sec']:.2f} | "
            f"{row['pred_mean_duration_sec']:.2f} | {row['duration_diff_sec']:.2f} | {row['num_segments']} |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gt_file", default=None, type=str)
    parser.add_argument("--gt_dir", default=None, type=str)
    parser.add_argument("--kde_bandwidths", required=True, type=str, help="Comma-separated bandwidths like 1.0,2.6,3.2,4.0,5.0")
    parser.add_argument("--kde_roots", default=None, help="Optional comma-separated KDE roots matching the bandwidth order")
    parser.add_argument("--out_dir", default="./kde_gt_bandwidth_curve")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    gt_source_label, blocks = load_gt_blocks(args.gt_file, args.gt_dir)
    dataset_rows = gt_dataset_rows(blocks)
    bandwidths = parse_bandwidths(args.kde_bandwidths)

    if args.kde_roots:
        roots = [Path(item) for item in parse_bandwidths(args.kde_roots)]
        if len(roots) != len(bandwidths):
            raise ValueError("--kde_roots must have the same number of entries as --kde_bandwidths")
    else:
        roots = ch.resolve_kde_roots(None, None, args.kde_bandwidths)

    per_match_rows = []
    for bandwidth_label, root in zip(bandwidths, roots):
        for block in blocks:
            per_match_rows.append(metric_row_for_bandwidth(block, block["title"], bandwidth_label, root))

    summary_rows = build_summary_rows(per_match_rows)

    csv_path = out_dir / "kde_bandwidth_gt_summary.csv"
    per_match_csv_path = out_dir / "kde_bandwidth_gt_per_match.csv"
    json_path = out_dir / "kde_bandwidth_gt_summary.json"
    time_f1_plot_path = out_dir / "kde_bandwidth_time_f1_curve.png"
    duration_diff_plot_path = out_dir / "kde_bandwidth_duration_diff_curve.png"
    combined_plot_path = out_dir / "kde_bandwidth_combined_curve.png"
    md_path = out_dir / "kde_bandwidth_gt_curve.md"

    write_csv(
        csv_path,
        summary_rows,
        [
            "bandwidth_label", "bandwidth_sec", "n_matches",
            "mean_precision", "mean_recall", "mean_f1",
            "std_precision", "std_recall", "std_f1",
            "mean_pred_total_sec", "mean_overlap_sec",
            "mean_gt_mean_duration_sec", "mean_pred_mean_duration_sec",
            "mean_duration_diff_sec", "std_duration_diff_sec",
            "mean_duration_score", "mean_combined_score", "std_combined_score",
        ],
    )
    write_csv(
        per_match_csv_path,
        per_match_rows,
        [
            "match", "bandwidth_label", "bandwidth_sec", "num_segments",
            "pred_total_sec", "gt_total_sec", "overlap_sec",
            "time_precision", "time_recall", "time_f1",
            "gt_mean_duration_sec", "pred_mean_duration_sec", "duration_diff_sec",
        ],
    )
    json_path.write_text(json.dumps({
        "gt_source": gt_source_label,
        "bandwidths": [float(v) for v in bandwidths],
        "gt_dataset": dataset_rows,
        "summary": summary_rows,
        "per_match": per_match_rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    generated_time_f1_plot = plot_time_f1_curve(
        summary_rows,
        time_f1_plot_path,
        title="KDE bandwidth vs mean GT-based precision/recall/F1",
    )
    generated_duration_diff_plot = plot_duration_diff_curve(
        summary_rows,
        duration_diff_plot_path,
        title="KDE bandwidth vs GT mean, predicted mean, and duration diff",
    )
    generated_combined_plot = plot_combined_curve(
        summary_rows,
        combined_plot_path,
        title="KDE bandwidth vs precision/recall/F1, duration diff score, and combined score",
    )
    write_markdown(md_path, summary_rows, per_match_rows, generated_time_f1_plot, generated_duration_diff_plot, generated_combined_plot, gt_source_label, dataset_rows)

    print(f"[OK] wrote {csv_path}")
    print(f"[OK] wrote {per_match_csv_path}")
    print(f"[OK] wrote {json_path}")
    if generated_time_f1_plot is None:
        print("[WARN] matplotlib not available, skipped time F1 PNG plot")
    else:
        print(f"[OK] wrote {generated_time_f1_plot}")
    if generated_duration_diff_plot is None:
        print("[WARN] matplotlib not available, skipped duration diff PNG plot")
    else:
        print(f"[OK] wrote {generated_duration_diff_plot}")
    if generated_combined_plot is None:
        print("[WARN] matplotlib not available, skipped combined PNG plot")
    else:
        print(f"[OK] wrote {generated_combined_plot}")
    print(f"[OK] wrote {md_path}")


if __name__ == "__main__":
    main()

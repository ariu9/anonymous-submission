import argparse
import csv
import glob
import json
from pathlib import Path

import numpy as np
from sklearn.neighbors import KernelDensity


def extract_timestamps(event_dict):
    secs = []
    for key in event_dict.keys():
        head = str(key).split("_")[0]
        try:
            secs.append(float(head))
        except ValueError:
            continue
    return np.array(sorted(secs), dtype=float)


def inter_event_gaps(ts: np.ndarray) -> np.ndarray:
    ts = np.asarray(sorted(set(ts)), dtype=float)
    return np.diff(ts) if ts.size >= 2 else np.array([], dtype=float)


def q1_of_gaps(gaps: np.ndarray):
    gaps = np.sort(gaps)
    if gaps.size == 0:
        return None
    lower = gaps[: gaps.size // 2] if gaps.size > 1 else gaps
    return float(np.median(lower)) if lower.size > 0 else float(gaps[0])


def recommend_h_from_q1(q1, scale=0.8, clip_min=1.0, clip_max=12.0):
    if q1 is None:
        return None
    h = scale * float(q1)
    return float(min(max(h, clip_min), clip_max))


def plot_kde(ts: np.ndarray, bandwidth: float, num_points: int = 1500):
    kde = KernelDensity(kernel="gaussian", bandwidth=bandwidth)
    kde.fit(ts[:, None])
    t_min, t_max = float(ts.min()), float(ts.max())
    grid = np.linspace(max(0.0, t_min - 30.0), t_max + 30.0, num_points)
    dens = np.exp(kde.score_samples(grid[:, None]))
    return grid, dens


def extract_segments_from_density1(ts, x, dens, mean_factor=5.0, min_len=10.0, prepend=5.0, min_events=2):
    thr = float(np.mean(dens)) * mean_factor
    above = dens >= thr

    segs = []
    valid_mask = np.zeros_like(above, dtype=bool)
    start_idx = None

    for i, is_above in enumerate(above):
        if is_above and start_idx is None:
            start_idx = i
        if (not is_above or i == len(above) - 1) and start_idx is not None:
            end_idx = i if not is_above else i
            a = float(x[start_idx]) - prepend
            b = float(x[end_idx])
            if a < 0.0:
                a = 0.0
            if (b - a) >= min_len:
                n_in = int(((ts >= a) & (ts <= b)).sum())
                if n_in >= min_events:
                    segs.append((a, b, n_in))
                    valid_mask[start_idx:end_idx + 1] = True
            start_idx = None

    return segs, thr, valid_mask


def parse_bandwidths(raw: str) -> list[float]:
    vals = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        vals.append(float(chunk))
    if not vals:
        raise ValueError("At least one bandwidth must be provided.")
    return vals


def load_events(event_root: str, min_top_level_entries: int) -> dict[str, dict]:
    json_files = glob.glob(
        str(Path(event_root) / "**" / "*_event_log.json"),
        recursive=True,
    )
    events_by_file = {}
    for file_path in sorted(json_files):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if len(data) < min_top_level_entries:
            continue
        events_by_file[file_path] = data
    return events_by_file


def build_segment_records(segments):
    return [
        {
            "start": float(a),
            "end": float(b),
            "duration": float(b - a),
            "n_events": int(n),
        }
        for a, b, n in segments
    ]


def summarize_segments(records, ts: np.ndarray) -> dict[str, float | int | None]:
    if not records:
        return {
            "num_segments": 0,
            "sum_segment_seconds": 0.0,
            "mean_segment_seconds": 0.0,
            "median_segment_seconds": 0.0,
            "mean_events_per_segment": 0.0,
            "max_segment_seconds": 0.0,
            "event_span_seconds": float(ts[-1] - ts[0]) if ts.size >= 2 else 0.0,
            "segment_coverage_ratio": 0.0,
        }

    durations = np.array([r["duration"] for r in records], dtype=float)
    n_events = np.array([r["n_events"] for r in records], dtype=float)
    sum_segment_seconds = float(durations.sum())
    event_span_seconds = float(ts[-1] - ts[0]) if ts.size >= 2 else 0.0
    coverage_ratio = sum_segment_seconds / event_span_seconds if event_span_seconds > 0 else 0.0
    return {
        "num_segments": int(len(records)),
        "sum_segment_seconds": sum_segment_seconds,
        "mean_segment_seconds": float(durations.mean()),
        "median_segment_seconds": float(np.median(durations)),
        "mean_events_per_segment": float(n_events.mean()),
        "max_segment_seconds": float(durations.max()),
        "event_span_seconds": event_span_seconds,
        "segment_coverage_ratio": float(coverage_ratio),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--event_root", type=str, default="./2023_2024_event_logs")
    ap.add_argument("--out_dir", type=str, default="./kde_h_sweep")
    ap.add_argument(
        "--bandwidths",
        type=str,
        default="2.0,2.6,3.2,4.0,5.0",
        help="Comma-separated bandwidth values to evaluate",
    )
    ap.add_argument("--factor", type=float, default=5.0)
    ap.add_argument("--min_len", type=float, default=10.0)
    ap.add_argument("--prepend", type=float, default=5.0)
    ap.add_argument("--num_points", type=int, default=1500)
    ap.add_argument("--min_events", type=int, default=2)
    ap.add_argument("--min_top_level_entries", type=int, default=10)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    bandwidths = parse_bandwidths(args.bandwidths)
    events_by_file = load_events(args.event_root, args.min_top_level_entries)
    if not events_by_file:
        raise RuntimeError("No event logs found for the sweep.")

    per_file_q1 = []
    for ev in events_by_file.values():
        ts = extract_timestamps(ev)
        q1 = q1_of_gaps(inter_event_gaps(ts))
        if q1 is not None:
            per_file_q1.append(q1)
    if not per_file_q1:
        raise RuntimeError("No valid Q1 values found across event logs.")

    global_q1 = float(np.median(np.array(sorted(per_file_q1), dtype=float)))
    recommended_h = float(recommend_h_from_q1(global_q1, scale=0.8, clip_min=1.0, clip_max=12.0))

    summary_rows = []
    per_file_rows = []

    for bandwidth in bandwidths:
        total_segments = 0
        files_with_segments = 0
        total_segment_seconds = 0.0
        segment_lengths = []
        segment_events = []
        coverage_ratios = []

        for fp, ev in events_by_file.items():
            ts = extract_timestamps(ev)
            if ts.size < 2:
                continue

            x, dens = plot_kde(ts, bandwidth=bandwidth, num_points=args.num_points)
            segs, thr, _ = extract_segments_from_density1(
                ts,
                x,
                dens,
                mean_factor=args.factor,
                min_len=args.min_len,
                prepend=args.prepend,
                min_events=args.min_events,
            )
            records = build_segment_records(segs)
            stats = summarize_segments(records, ts)

            if stats["num_segments"] > 0:
                files_with_segments += 1
                total_segments += int(stats["num_segments"])
                total_segment_seconds += float(stats["sum_segment_seconds"])
                segment_lengths.extend([r["duration"] for r in records])
                segment_events.extend([r["n_events"] for r in records])
                coverage_ratios.append(float(stats["segment_coverage_ratio"]))

            per_file_rows.append({
                "bandwidth_sec": float(bandwidth),
                "file": fp,
                "threshold": float(thr),
                "num_events_total": int(ts.size),
                **stats,
            })

        summary_rows.append({
            "bandwidth_sec": float(bandwidth),
            "files_processed": int(len(events_by_file)),
            "files_with_segments": int(files_with_segments),
            "total_segments": int(total_segments),
            "total_segment_seconds": float(total_segment_seconds),
            "mean_segment_seconds": float(np.mean(segment_lengths)) if segment_lengths else 0.0,
            "median_segment_seconds": float(np.median(segment_lengths)) if segment_lengths else 0.0,
            "mean_events_per_segment": float(np.mean(segment_events)) if segment_events else 0.0,
            "mean_coverage_ratio": float(np.mean(coverage_ratios)) if coverage_ratios else 0.0,
        })

    summary_rows.sort(key=lambda row: row["bandwidth_sec"])
    per_file_rows.sort(key=lambda row: (row["bandwidth_sec"], row["file"]))

    summary_json = {
        "event_root": str(Path(args.event_root).resolve()),
        "recommended_global_h_sec": recommended_h,
        "global_q1_sec": global_q1,
        "factor": float(args.factor),
        "min_len": float(args.min_len),
        "prepend": float(args.prepend),
        "min_events": int(args.min_events),
        "num_points": int(args.num_points),
        "bandwidths": [float(v) for v in bandwidths],
        "summary": summary_rows,
    }

    summary_json_path = out_dir / "bandwidth_sweep_summary.json"
    summary_csv_path = out_dir / "bandwidth_sweep_summary.csv"
    per_file_csv_path = out_dir / "bandwidth_sweep_per_file.csv"
    report_md_path = out_dir / "bandwidth_sweep_report.md"

    summary_json_path.write_text(
        json.dumps(summary_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with open(summary_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    with open(per_file_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(per_file_rows[0].keys()))
        writer.writeheader()
        writer.writerows(per_file_rows)

    report_lines = [
        "# KDE Bandwidth Sweep",
        "",
        f"- Event root: `{Path(args.event_root).resolve()}`",
        f"- Recommended global h from Q1: `{recommended_h:.3f}` sec",
        f"- Global Q1: `{global_q1:.3f}` sec",
        f"- Sweep bandwidths: `{', '.join(f'{v:.2f}' for v in bandwidths)}`",
        f"- Density threshold factor: `{args.factor}`",
        f"- Min segment length: `{args.min_len}` sec",
        f"- Prepend: `{args.prepend}` sec",
        f"- Min events per segment: `{args.min_events}`",
        "",
        "| bandwidth_sec | files_processed | files_with_segments | total_segments | total_segment_seconds | mean_segment_seconds | median_segment_seconds | mean_events_per_segment | mean_coverage_ratio |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in summary_rows:
        report_lines.append(
            "| "
            + " | ".join(
                [
                    f"{row['bandwidth_sec']:.3f}",
                    str(row["files_processed"]),
                    str(row["files_with_segments"]),
                    str(row["total_segments"]),
                    f"{row['total_segment_seconds']:.3f}",
                    f"{row['mean_segment_seconds']:.3f}",
                    f"{row['median_segment_seconds']:.3f}",
                    f"{row['mean_events_per_segment']:.3f}",
                    f"{row['mean_coverage_ratio']:.4f}",
                ]
            )
            + " |"
        )

    report_md_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"[OK] Summary JSON: {summary_json_path}")
    print(f"[OK] Summary CSV:  {summary_csv_path}")
    print(f"[OK] Per-file CSV: {per_file_csv_path}")
    print(f"[OK] Report MD:    {report_md_path}")


if __name__ == "__main__":
    main()

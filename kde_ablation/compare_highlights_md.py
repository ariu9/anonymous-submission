import argparse
import json
import re
import unicodedata
from pathlib import Path
import math

import numpy as np

try:
    import matplotlib
    matplotlib.use("agg")
    import matplotlib.pyplot as plt
except ImportError:
    matplotlib = None
    plt = None


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\uE000-\uF8FF]", "", text)
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def mmss_to_seconds(raw: str) -> int:
    raw = raw.strip()
    if not raw:
        raise ValueError("Empty time string")
    if len(raw) < 4:
        raw = raw.zfill(4)
    minutes = int(raw[:-2])
    seconds = int(raw[-2:])
    return minutes * 60 + seconds


def seconds_to_mmss(total_seconds: float) -> str:
    total_seconds = int(round(total_seconds))
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def slugify_filename(text: str) -> str:
    text = normalize_text(text)
    text = text.replace(" ", "_")
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "match"


def compact_plot_title(text: str) -> str:
    clean = normalize_text(text)
    clean = clean.replace("서머", "Summer").replace("스프링", "Spring")
    year_match = re.search(r"(20\d{2})", clean)
    idx_match = re.search(r"[_\-\s](\d+)\s*$", clean)
    idx_match = False

    if "Summer" in clean:
        season = "Summer"
    elif "Spring" in clean:
        season = "Spring"
    else:
        season = None

    if year_match and season and idx_match:
        return f"{year_match.group(1)} LCK {season} {int(idx_match.group(1))}"
    if year_match and season:
        return f"{year_match.group(1)} LCK {season}"
    return clean


def _parse_block(block_lines):
    lines = [line.strip() for line in block_lines if line.strip()]
    if len(lines) < 4:
        raise ValueError("Each GT block must contain title, sync line, and at least one interval pair.")

    title = lines[0]
    sync_point = mmss_to_seconds(lines[1])
    time_values = [mmss_to_seconds(v) for v in lines[2:]]
    if len(time_values) % 2 != 0:
        raise ValueError(f"Highlight times must come in start/end pairs for block: {title}")

    highlight_intervals = []
    for i in range(0, len(time_values), 2):
        start_game = time_values[i]
        end_game = time_values[i + 1]
        highlight_intervals.append({
            "game_start_sec": start_game,
            "game_end_sec": end_game,
            "video_start_sec": start_game + sync_point,
            "video_end_sec": end_game + sync_point,
        })

    return {
        "title": title,
        "sync_point": sync_point,
        "highlight_intervals": highlight_intervals,
        "slug": slugify_filename(title),
    }


def parse_gt_blocks(path: Path):
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    blocks = []
    i = 0
    n = len(raw_lines)

    while i < n:
        while i < n and not raw_lines[i].strip():
            i += 1
        if i >= n:
            break

        title = raw_lines[i].strip()
        i += 1

        while i < n and not raw_lines[i].strip():
            i += 1
        if i >= n:
            raise ValueError(f"Missing sync line after title: {title}")

        sync = raw_lines[i].strip()
        i += 1

        times = []
        while i < n:
            line = raw_lines[i].strip()
            if not line:
                i += 1
                continue
            if not line.isdigit():
                break
            times.append(line)
            i += 1

        blocks.append(_parse_block([title, sync, *times]))

    if not blocks:
        raise ValueError("GT file does not contain any valid match blocks.")
    return blocks


def find_matching_segment_json(segments_dir: Path, title: str):
    target = normalize_text(title)
    for path in sorted(segments_dir.glob("*_segments.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        source_file = payload.get("file", "")
        source_name = Path(source_file).name.replace("_event_log.json", "")
        if normalize_text(source_name) == target:
            return path, payload
    raise FileNotFoundError(f"No segment JSON matched title: {title}")


def infer_plot_path(report_root: Path, segment_json_path: Path, method_key: str):
    stem = segment_json_path.name.replace("_segments.json", "")
    if method_key.startswith("kde"):
        suffix = "_kde.png"
    else:
        suffix = {
            "dbscan": "_dbscan.png",
            "sliding_window": "_sliding_window.png",
        }[method_key]
    return report_root / "plots" / f"{stem}{suffix}"


def interval_overlap(a_start, a_end, b_start, b_end):
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def total_interval_seconds(intervals):
    return sum(max(0.0, iv["end"] - iv["start"]) for iv in intervals)


def compute_time_metrics(pred_intervals, gt_intervals):
    pred_total = total_interval_seconds(pred_intervals)
    gt_total = total_interval_seconds(gt_intervals)
    overlap_total = 0.0

    for pred in pred_intervals:
        for gt in gt_intervals:
            overlap_total += interval_overlap(pred["start"], pred["end"], gt["start"], gt["end"])

    precision = overlap_total / pred_total if pred_total > 0 else 0.0
    recall = overlap_total / gt_total if gt_total > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "pred_total_sec": pred_total,
        "gt_total_sec": gt_total,
        "overlap_sec": overlap_total,
        "time_precision": precision,
        "time_recall": recall,
        "time_f1": f1,
    }


def format_table(rows, columns):
    headers = [col[1] for col in columns]
    aligns = ["---"] * len(columns)
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(aligns) + " |"]
    for row in rows:
        vals = []
        for key, _label in columns:
            val = row.get(key, "")
            vals.append(str(val))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def build_segment_rows(segments):
    rows = []
    for idx, seg in enumerate(segments, start=1):
        rows.append({
            "id": idx,
            "start_sec": f"{seg['start']:.2f}",
            "end_sec": f"{seg['end']:.2f}",
            "start_mmss": seconds_to_mmss(seg["start"]),
            "end_mmss": seconds_to_mmss(seg["end"]),
            "duration_sec": f"{seg['duration']:.2f}",
            "n_events": seg["n_events"],
        })
    return rows


def extract_timestamps_from_event_file(event_file: Path):
    payload = json.loads(event_file.read_text(encoding="utf-8"))
    times = []
    for key in payload.keys():
        m = re.match(r"^(\d+(?:\.\d+)?)", str(key))
        if m:
            try:
                times.append(float(m.group(1)))
            except ValueError:
                pass
    return np.array(sorted(times), dtype=float)


def extract_segments_from_mask(ts, x, mask, prepend, min_len, min_events):
    segments = []
    valid_mask = np.zeros_like(mask, dtype=bool)
    start_idx = None
    for i, is_valid in enumerate(mask):
        if is_valid and start_idx is None:
            start_idx = i
        if (not is_valid or i == len(mask) - 1) and start_idx is not None:
            end_idx = i if not is_valid else i
            a = max(0.0, float(x[start_idx]) - prepend)
            b = float(x[end_idx])
            if (b - a) >= min_len:
                n_in = int(((ts >= a) & (ts <= b)).sum())
                if n_in >= min_events:
                    segments.append((a, b, n_in))
                    valid_mask[start_idx:end_idx + 1] = True
            start_idx = None
    return segments, valid_mask


def dbscan_1d_clusters(ts: np.ndarray, eps: float, min_samples: int):
    n = len(ts)
    if n == 0:
        return []
    labels = [-1] * n
    visited = [False] * n
    cluster_id = 0

    def region_query(i):
        left = i
        while left > 0 and ts[i] - ts[left - 1] <= eps:
            left -= 1
        right = i
        while right + 1 < n and ts[right + 1] - ts[i] <= eps:
            right += 1
        return list(range(left, right + 1))

    for i in range(n):
        if visited[i]:
            continue
        visited[i] = True
        neighbors = region_query(i)
        if len(neighbors) < min_samples:
            labels[i] = -1
            continue
        labels[i] = cluster_id
        seeds = neighbors[:]
        seed_pos = 0
        while seed_pos < len(seeds):
            j = seeds[seed_pos]
            if not visited[j]:
                visited[j] = True
                j_neighbors = region_query(j)
                if len(j_neighbors) >= min_samples:
                    for idx in j_neighbors:
                        if idx not in seeds:
                            seeds.append(idx)
            if labels[j] < 0:
                labels[j] = cluster_id
            seed_pos += 1
        cluster_id += 1

    clusters = []
    for cid in sorted(set(labels)):
        if cid < 0:
            continue
        idxs = [i for i, lbl in enumerate(labels) if lbl == cid]
        if idxs:
            clusters.append(idxs)
    return clusters


def dbscan_score_curve(ts, eps, min_samples, prepend, min_len, num_points, min_events):
    t_min, t_max = float(ts.min()), float(ts.max())
    x = np.linspace(max(0.0, t_min - 30.0), t_max + 30.0, num_points)
    score = np.array([int(((ts >= xi - eps) & (ts <= xi + eps)).sum()) for xi in x], dtype=float)
    threshold = float(min_samples)
    clusters = dbscan_1d_clusters(ts, eps=eps, min_samples=min_samples)
    mask = np.zeros_like(x, dtype=bool)
    for idxs in clusters:
        a = max(0.0, float(ts[idxs[0]]) - prepend)
        b = float(ts[idxs[-1]])
        if (b - a) < min_len:
            continue
        n_in = int(((ts >= a) & (ts <= b)).sum())
        if n_in < min_events:
            continue
        mask |= ((x >= a) & (x <= b))
    return x, score, threshold, mask


def sliding_window_score_curve(ts, window_sec, count_threshold, prepend, min_len, num_points, min_events):
    t_min, t_max = float(ts.min()), float(ts.max())
    x = np.linspace(max(0.0, t_min - 30.0), t_max + 30.0, num_points)
    half = window_sec / 2.0
    score = np.array([int(((ts >= xi - half) & (ts <= xi + half)).sum()) for xi in x], dtype=float)
    threshold = float(count_threshold)
    mask = score >= threshold
    _segments, valid_mask = extract_segments_from_mask(ts, x, mask, prepend, min_len, min_events)
    return x, score, threshold, valid_mask


def kde_score_curve(ts, bandwidth, factor, prepend, min_len, num_points, min_events):
    from sklearn.neighbors import KernelDensity

    kde = KernelDensity(kernel="gaussian", bandwidth=bandwidth)
    kde.fit(ts[:, None])
    t_min, t_max = float(ts.min()), float(ts.max())
    x = np.linspace(max(0.0, t_min - 30.0), t_max + 30.0, num_points)
    score = np.exp(kde.score_samples(x[:, None]))
    threshold = float(np.mean(score)) * factor
    above = score >= threshold
    _segments, valid_mask = extract_segments_from_mask(ts, x, above, prepend, min_len, min_events)
    return x, score, threshold, valid_mask


def single_kernels_on_grid(ts: np.ndarray, x: np.ndarray, bandwidth: float) -> np.ndarray:
    n = len(ts)
    if n == 0:
        return np.zeros((len(x), 0), dtype=float)
    h = float(bandwidth)
    z = (x[:, None] - ts[None, :]) / h
    phi = np.exp(-0.5 * z**2) / math.sqrt(2.0 * math.pi)
    return phi / (n * h)


def plot_method_result_with_gt(ts, x, score, threshold, valid_mask, method_name, plot_title, gt_intervals, bandwidth=None):
    plt.figure(figsize=(18, 5))
    plt.plot(x, score, color="black", linewidth=1.8, label=f"{method_name} score")
    plt.axhline(threshold, linestyle=":", linewidth=1.5, color="gray", label=f"Threshold ({threshold:g})")
    plt.fill_between(x, score, threshold, where=valid_mask, interpolate=True, alpha=0.25,
                     label="Accepted segments")
    plt.vlines(ts, ymin=0.0, ymax=max(score.max(), threshold) * 0.08 if len(score) else 1.0,
               color="red", alpha=0.45, linewidth=0.8, label="Events")
    if bandwidth is not None:
        kernels = single_kernels_on_grid(ts, x, bandwidth=bandwidth)
        for idx in range(kernels.shape[1]):
            plt.plot(
                x,
                kernels[:, idx],
                linestyle="--",
                color="red",
                alpha=0.6,
                linewidth=1.0,
                label="Single kernel" if idx == 0 else None,
            )
    ymax = max(float(score.max()) if len(score) else 1.0, float(threshold))
    for idx, gt in enumerate(gt_intervals):
        plt.axvspan(
            gt["start"],
            gt["end"],
            ymin=0.0,
            ymax=0.08,
            color="firebrick",
            alpha=0.45,
            label="GT highlights" if idx == 0 else None,
        )
    plt.xlabel("Time (seconds)", fontsize=18)
    plt.ylabel("Score", fontsize=18)
    plt.title(plot_title, fontsize=24)
    plt.legend(loc="upper left", fontsize=12)
    plt.yticks(fontsize=14)
    plt.xticks(fontsize=14)
    plt.ylim(bottom=0.0, top=ymax * 1.08 if ymax > 0 else 1.0)


def draw_rectangle_comparison_plot(out_path: Path, title: str, method_name: str, segments, gt_intervals, event_file_path: Path):
    if plt is None:
        return None
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    all_points = []
    for seg in segments:
        all_points.extend([float(seg["start"]), float(seg["end"])])
    for gt in gt_intervals:
        all_points.extend([float(gt["start"]), float(gt["end"])])
    ts = extract_timestamps_from_event_file(event_file_path)
    if ts.size:
        all_points.extend(ts.tolist())

    if all_points:
        x_min = max(0.0, min(all_points) - 30.0)
        x_max = max(all_points) + 30.0
    else:
        x_min, x_max = 0.0, 60.0

    fig, ax = plt.subplots(figsize=(18, 4.5))

    for gt in gt_intervals:
        ax.axvspan(gt["start"], gt["end"], ymin=0.04, ymax=0.20, color="#d62828", alpha=0.45)

    for seg in segments:
        ax.axvspan(seg["start"], seg["end"], ymin=0.34, ymax=0.56, color="#2d528aff", alpha=0.55)

    if ts.size:
        ax.vlines(ts, ymin=0.76, ymax=0.94, color="black", alpha=0.55, linewidth=0.9)

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(0.0, 1.0)
    ax.set_xlabel("Video Time (seconds)", fontsize=16)
    ax.set_yticks([0.12, 0.45, 0.85])
    ax.set_yticklabels(["GT Highlights", "Pred Segments", "Events"], fontsize=13)
    ax.tick_params(axis="x", labelsize=13)
    ax.grid(axis="x", linestyle=":", alpha=0.35)
    ax.set_title(f"{method_name} vs GT — {compact_plot_title(title)}", fontsize=18)
    legend_handles = [
        Patch(facecolor="#d62828", edgecolor="none", alpha=0.45, label="GT Highlights"),
        Patch(facecolor="#2d528aff", edgecolor="none", alpha=0.55, label="Pred Segments"),
        Line2D([0], [0], color="black", alpha=0.55, linewidth=1.2, label="Events"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="center",
        bbox_to_anchor=(0.14, 0.45),
        fontsize=11,
        frameon=True,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


def draw_multi_kde_rectangle_plot(out_path: Path, title: str, kde_items, gt_intervals, event_file_path: Path):
    if plt is None or not kde_items:
        return None
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    all_points = []
    for item in kde_items:
        for seg in item["segments"]:
            all_points.extend([float(seg["start"]), float(seg["end"])])
    for gt in gt_intervals:
        all_points.extend([float(gt["start"]), float(gt["end"])])
    ts = extract_timestamps_from_event_file(event_file_path)
    if ts.size:
        all_points.extend(ts.tolist())

    if all_points:
        x_min = max(0.0, min(all_points) - 30.0)
        x_max = max(all_points) + 30.0
    else:
        x_min, x_max = 0.0, 60.0

    n_kde = len(kde_items)
    total_rows = n_kde + 2  # GT + KDE rows + Events
    fig_height = max(4.8, 1.15 * total_rows)
    fig, ax = plt.subplots(figsize=(18, fig_height))

    row_labels = ["GT Highlights"] + [item["method_name"] for item in kde_items] + ["Events"]
    row_centers = list(range(total_rows))
    row_half_height = 0.32

    gt_center = row_centers[0]
    for gt in gt_intervals:
        ax.axvspan(
            gt["start"],
            gt["end"],
            ymin=(gt_center - row_half_height + 0.5) / total_rows,
            ymax=(gt_center + row_half_height + 0.5) / total_rows,
            color="#d62828",
            alpha=0.45,
        )

    kde_items_sorted = sorted(
        kde_items,
        key=lambda item: float(re.search(r"([0-9]+(?:\.[0-9]+)?)", item["method_name"]).group(1))
        if re.search(r"([0-9]+(?:\.[0-9]+)?)", item["method_name"]) else float("inf"),
    )
    kde_colors = [
        "#02070D",
        "#0C2E5A",
        "#125AAD",
        "#2b79cc",
        "#609bda",
        "#8bb2db",
        "#b5cce3",
    ]
    for idx, item in enumerate(kde_items_sorted, start=1):
        center = row_centers[idx]
        color = kde_colors[(idx - 1) % len(kde_colors)]
        for seg in item["segments"]:
            ax.axvspan(
                float(seg["start"]),
                float(seg["end"]),
                ymin=(center - row_half_height + 0.5) / total_rows,
                ymax=(center + row_half_height + 0.5) / total_rows,
                color=color,
                alpha=0.80,
            )

    if ts.size:
        event_center = row_centers[-1]
        ax.vlines(
            ts,
            ymin=event_center - row_half_height,
            ymax=event_center + row_half_height,
            color="black",
            alpha=0.60,
            linewidth=0.9,
        )

    for boundary in np.arange(0.5, total_rows - 0.49, 1.0):
        ax.axhline(boundary, color="gray", linestyle=":", linewidth=1.0, alpha=0.5, zorder=0)

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(-0.6, total_rows - 0.4)
    ax.set_xlabel("Video Time (seconds)", fontsize=16)
    ax.set_yticks(row_centers)
    row_labels = ["GT Highlights"] + [item["method_name"] for item in kde_items_sorted] + ["Events"]
    ax.set_yticklabels(row_labels, fontsize=16)
    ax.tick_params(axis="x", labelsize=14)
    ax.grid(axis="x", linestyle=":", alpha=0.35)
    ax.set_title(f"Multi-KDE vs GT — {compact_plot_title(title)}", fontsize=18)
    legend_handles = [
        Line2D([0], [0], color="black", alpha=0.60, linewidth=1.2, label="Events"),
        Patch(facecolor="#0051a7", edgecolor="none", alpha=0.70, label="KDE Segments"),
        Patch(facecolor="#d62828", edgecolor="none", alpha=0.45, label="GT Highlights"),
    ]
    ax.legend(handles=legend_handles, loc="center left", fontsize=14, frameon=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def draw_multi_method_rectangle_plot(out_path: Path, title: str, method_items, gt_intervals, event_file_path: Path):
    if plt is None or not method_items:
        return None
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    order_map = {"dbscan": 0, "sliding_window": 1}

    def method_rank(item):
        key = item["method_key"]
        if key.startswith("kde"):
            return 2
        return order_map.get(key, 99)

    ordered_items = sorted(method_items, key=method_rank)

    all_points = []
    for item in ordered_items:
        for seg in item["segments"]:
            all_points.extend([float(seg["start"]), float(seg["end"])])
    for gt in gt_intervals:
        all_points.extend([float(gt["start"]), float(gt["end"])])
    ts = extract_timestamps_from_event_file(event_file_path)
    if ts.size:
        all_points.extend(ts.tolist())

    if all_points:
        x_min = max(0.0, min(all_points) - 30.0)
        x_max = max(all_points) + 30.0
    else:
        x_min, x_max = 0.0, 60.0

    # Bottom to top in plot coordinates: GT, KDE, Sliding, DBSCAN, Events
    row_items_bottom_to_top = list(reversed(ordered_items))
    row_labels = ["GT Highlights"] + [item["method_name"] for item in row_items_bottom_to_top] + ["Events"]
    total_rows = len(row_labels)
    row_centers = list(range(total_rows))
    row_half_height = 0.32

    fig_height = max(5.2, 1.15 * total_rows)
    fig, ax = plt.subplots(figsize=(18, fig_height))

    gt_center = row_centers[0]
    for gt in gt_intervals:
        ax.axvspan(
            gt["start"],
            gt["end"],
            ymin=(gt_center - row_half_height + 0.5) / total_rows,
            ymax=(gt_center + row_half_height + 0.5) / total_rows,
            color="#d62828",
            alpha=0.45,
        )

    method_colors = {
        "kde": "#205086",
        "sliding_window": "#2a9d8f",
        "dbscan": "#7a3e9d",
    }
    for idx, item in enumerate(row_items_bottom_to_top, start=1):
        center = row_centers[idx]
        key = "kde" if item["method_key"].startswith("kde") else item["method_key"]
        color = method_colors.get(key, "#4e79a7")
        for seg in item["segments"]:
            ax.axvspan(
                float(seg["start"]),
                float(seg["end"]),
                ymin=(center - row_half_height + 0.5) / total_rows,
                ymax=(center + row_half_height + 0.5) / total_rows,
                color=color,
                alpha=0.70,
            )

    if ts.size:
        event_center = row_centers[-1]
        ax.vlines(
            ts,
            ymin=event_center - row_half_height,
            ymax=event_center + row_half_height,
            color="black",
            alpha=0.60,
            linewidth=0.9,
        )

    for boundary in np.arange(0.5, total_rows - 0.49, 1.0):
        ax.axhline(boundary, color="gray", linestyle=":", linewidth=1.0, alpha=0.5, zorder=0)

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(-0.6, total_rows - 0.4)
    ax.set_xlabel("Video Time (seconds)", fontsize=16)
    ax.set_yticks(row_centers)
    ax.set_yticklabels(row_labels, fontsize=16)
    ax.tick_params(axis="x", labelsize=14)
    ax.grid(axis="x", linestyle=":", alpha=0.35)
    ax.set_title(f"Method Comparison vs GT — {compact_plot_title(title)}", fontsize=18)
    legend_handles = [
        Line2D([0], [0], color="black", alpha=0.60, linewidth=1.2, label="Events"),
        Patch(facecolor=method_colors["dbscan"], edgecolor="none", alpha=0.70, label="DBSCAN"),
        Patch(facecolor=method_colors["sliding_window"], edgecolor="none", alpha=0.70, label="Sliding Window"),
        Patch(facecolor=method_colors["kde"], edgecolor="none", alpha=0.70, label="KDE"),
        Patch(facecolor="#d62828", edgecolor="none", alpha=0.45, label="GT Highlights"),
    ]
    ax.legend(handles=legend_handles, loc="center left", fontsize=16, frameon=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def build_plot_for_method(out_path: Path, method_key: str, method_name: str, payload, gt_intervals):
    if plt is None:
        return None
    ts = extract_timestamps_from_event_file(Path(payload["file"]))
    if ts.size < 2:
        return None
    try:
        if method_key == "kde":
            x, score, threshold, valid_mask = kde_score_curve(
                ts,
                bandwidth=float(payload["bandwidth_sec"]),
                factor=float(payload["density_threshold_factor"]),
                prepend=float(payload.get("prepend_sec", 5.0)),
                min_len=float(payload.get("min_segment_len_sec", 10.0)),
                num_points=1500,
                min_events=2,
            )
            plot_method_result_with_gt(
                ts, x, score, threshold, valid_mask, method_name,
                f"{method_name} result", gt_intervals,
                bandwidth=float(payload["bandwidth_sec"]),
            )
        elif method_key == "dbscan":
            params = payload.get("method_params", {})
            x, score, threshold, valid_mask = dbscan_score_curve(
                ts,
                eps=float(params.get("eps", 6.0)),
                min_samples=int(params.get("min_samples", payload.get("min_events", 2))),
                prepend=float(payload.get("prepend_sec", 5.0)),
                min_len=float(payload.get("min_segment_len_sec", 10.0)),
                num_points=1500,
                min_events=int(payload.get("min_events", 2)),
            )
            plot_method_result_with_gt(ts, x, score, threshold, valid_mask, method_name, f"{method_name} result", gt_intervals)
        else:
            params = payload.get("method_params", {})
            x, score, threshold, valid_mask = sliding_window_score_curve(
                ts,
                window_sec=float(params.get("window_sec", 12.0)),
                count_threshold=int(params.get("count_threshold", 2)),
                prepend=float(payload.get("prepend_sec", 5.0)),
                min_len=float(payload.get("min_segment_len_sec", 10.0)),
                num_points=1500,
                min_events=int(payload.get("min_events", 2)),
            )
            plot_method_result_with_gt(ts, x, score, threshold, valid_mask, method_name, f"{method_name} result", gt_intervals)
        plt.tight_layout()
        plt.savefig(out_path, format="png", dpi=130)
        plt.close()
        return out_path
    except Exception:
        try:
            plt.close()
        except Exception:
            pass
        return None


def resolve_report_root(root_arg: str | None, preferred_prefix: str, preferred_suffix: str | None = None):
    if root_arg:
        root = Path(root_arg)
        if not root.exists():
            raise FileNotFoundError(f"Report root does not exist: {root}")
        return root

    candidates = []
    for path in Path(".").iterdir():
        if not path.is_dir():
            continue
        if not path.name.startswith(preferred_prefix):
            continue
        if preferred_suffix is not None and not path.name.endswith(preferred_suffix):
            continue
        if (path / "segments").exists():
            candidates.append(path)

    if not candidates:
        suffix_note = f" ending with '{preferred_suffix}'" if preferred_suffix is not None else ""
        raise FileNotFoundError(f"No report root found for prefix '{preferred_prefix}'{suffix_note}.")

    return sorted(candidates)[0]


def parse_csv_args(raw: str | None):
    if raw is None:
        return []
    return [chunk.strip() for chunk in raw.split(",") if chunk.strip()]


def _matches_bandwidth_dirname(dirname: str, bandwidth: str):
    raw = bandwidth.strip()
    if not raw:
        return False
    m = re.search(r"(?:^|_)h([0-9]+(?:\.[0-9]+)?)$", dirname)
    if not m:
        return False
    token = m.group(1)
    candidates = {raw}
    try:
        candidates.add(f"{float(raw):.1f}")
    except ValueError:
        pass
    if "." in raw:
        candidates.add(raw.replace(".", ""))
    if any("." in candidate for candidate in list(candidates)):
        for candidate in list(candidates):
            if "." in candidate:
                candidates.add(candidate.replace(".", ""))
    return token in candidates


def resolve_kde_roots(kde_root: str | None, kde_roots: str | None, kde_bandwidths: str | None):
    if kde_roots:
        roots = [Path(item) for item in parse_csv_args(kde_roots)]
        if not roots:
            raise ValueError("No valid KDE roots were provided.")
        return roots

    bandwidths = parse_csv_args(kde_bandwidths)
    if bandwidths:
        resolved = []
        cwd = Path.cwd()
        for bandwidth in bandwidths:
            matches = []
            for path in cwd.iterdir():
                if not path.is_dir():
                    continue
                if not path.name.startswith("kde_reports"):
                    continue
                if not _matches_bandwidth_dirname(path.name, bandwidth):
                    continue
                if (path / "segments").exists():
                    matches.append(path)
            if not matches:
                raise FileNotFoundError(f"No KDE report root found ending with '{bandwidth}'.")
            resolved.append(sorted(matches)[0])
        return resolved

    return [resolve_report_root(kde_root, "kde_reports", "3.2")]


def bandwidth_label_from_root(root: Path):
    seg_dir = root / "segments"
    for path in sorted(seg_dir.glob("*_segments.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        bandwidth = payload.get("bandwidth_sec")
        if bandwidth is not None:
            try:
                return f"{float(bandwidth):.1f}"
            except Exception:
                pass
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)$", root.name)
    return m.group(1) if m else root.name


def build_comparison_for_block(block, gt_path: Path, out_dir: Path, method_info):
    title = block["title"]
    sync_point = block["sync_point"]
    highlight_intervals = block["highlight_intervals"]
    gt_for_metrics = [
        {"start": iv["video_start_sec"], "end": iv["video_end_sec"]}
        for iv in highlight_intervals
    ]

    matched = []
    for method_key, method_name, root in method_info:
        seg_path, payload = find_matching_segment_json(root / "segments", title)
        segments = payload.get("segments", [])
        generated_plot = out_dir / f"{block['slug']}_{method_key}_rect_comparison.png"
        plot_path = draw_rectangle_comparison_plot(
            generated_plot,
            title,
            method_name,
            segments,
            gt_for_metrics,
            Path(payload["file"]),
        )
        if plot_path is None:
            plot_path = infer_plot_path(root, seg_path, method_key)
        metrics = compute_time_metrics(
            pred_intervals=[{"start": s["start"], "end": s["end"]} for s in segments],
            gt_intervals=gt_for_metrics,
        )
        matched.append({
            "method_key": method_key,
            "method_name": method_name,
            "root": root,
            "seg_path": seg_path,
            "plot_path": plot_path,
            "segments": segments,
            "metrics": metrics,
            "payload": payload,
        })

    best = max(matched, key=lambda item: item["metrics"]["time_f1"])
    out_path = out_dir / f"{block['slug']}_comparison.md"
    kde_items = [item for item in matched if item["method_key"].startswith("kde")]
    multi_kde_plot_path = None
    if len(kde_items) >= 2:
        multi_kde_plot_path = draw_multi_kde_rectangle_plot(
            out_dir / f"{block['slug']}_multi_kde_rect_comparison.png",
            title,
            kde_items,
            gt_for_metrics,
            Path(kde_items[0]["payload"]["file"]),
        )
    multi_method_plot_path = None
    if len(matched) >= 3 and any(not item["method_key"].startswith("kde") for item in matched):
        multi_method_plot_path = draw_multi_method_rectangle_plot(
            out_dir / f"{block['slug']}_multi_method_rect_comparison.png",
            title,
            matched,
            gt_for_metrics,
            Path(matched[0]["payload"]["file"]),
        )

    lines = []
    lines.append(f"# Highlight Comparison — {title}")
    lines.append("")
    lines.append(f"- Source GT file: `{gt_path.name}`")
    lines.append(f"- Sync point: `{seconds_to_mmss(sync_point)}` video time = game `00:00`")
    lines.append(f"- Ground-truth highlight intervals: `{len(highlight_intervals)}`")
    lines.append(f"- Best by time F1: `{best['method_name']}` ({best['metrics']['time_f1']:.4f})")
    lines.append("")
    if multi_kde_plot_path is not None:
        rel_multi_kde_plot = os.path.relpath(multi_kde_plot_path, out_dir)
        lines.append("## Multi-KDE View")
        lines.append("")
        lines.append(f"![Multi-KDE comparison]({rel_multi_kde_plot})")
        lines.append("")
    if multi_method_plot_path is not None:
        rel_multi_method_plot = os.path.relpath(multi_method_plot_path, out_dir)
        lines.append("## Multi-Method View")
        lines.append("")
        lines.append(f"![Multi-method comparison]({rel_multi_method_plot})")
        lines.append("")
    lines.append("## Metric Summary")
    lines.append("")

    metric_rows = []
    for item in matched:
        metric_rows.append({
            "method": item["method_name"],
            "segments": len(item["segments"]),
            "pred_total_sec": f"{item['metrics']['pred_total_sec']:.2f}",
            "gt_total_sec": f"{item['metrics']['gt_total_sec']:.2f}",
            "overlap_sec": f"{item['metrics']['overlap_sec']:.2f}",
            "precision": f"{item['metrics']['time_precision']:.4f}",
            "recall": f"{item['metrics']['time_recall']:.4f}",
            "f1": f"{item['metrics']['time_f1']:.4f}",
        })
    lines.append(format_table(metric_rows, [
        ("method", "Method"),
        ("segments", "# Segments"),
        ("pred_total_sec", "Pred Sec"),
        ("gt_total_sec", "GT Sec"),
        ("overlap_sec", "Overlap Sec"),
        ("precision", "Time Precision"),
        ("recall", "Time Recall"),
        ("f1", "Time F1"),
    ]))
    lines.append("")

    for item in matched:
        rel_plot = os.path.relpath(item["plot_path"], out_dir)
        rel_json = os.path.relpath(item["seg_path"], out_dir)
        lines.append(f"## {item['method_name']}")
        lines.append("")
        lines.append(f"![{item['method_name']}]({rel_plot})")
        lines.append("")
        lines.append(f"[Full segments JSON]({rel_json})")
        lines.append("")
        lines.append(
            f"Time precision `{item['metrics']['time_precision']:.4f}`, "
            f"time recall `{item['metrics']['time_recall']:.4f}`, "
            f"time F1 `{item['metrics']['time_f1']:.4f}`."
        )
        lines.append("")
        segment_rows = build_segment_rows(item["segments"])
        if segment_rows:
            lines.append(format_table(segment_rows, [
                ("id", "ID"),
                ("start_sec", "Start Sec"),
                ("end_sec", "End Sec"),
                ("start_mmss", "Start MM:SS"),
                ("end_mmss", "End MM:SS"),
                ("duration_sec", "Duration"),
                ("n_events", "# Events"),
            ]))
        else:
            lines.append("_No segments found._")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path, matched


def write_aggregate_method_summary(out_dir: Path, gt_path: Path, block_summaries):
    grouped = {}
    for block_title, matched in block_summaries:
        for item in matched:
            grouped.setdefault(item["method_name"], []).append({
                "match": block_title,
                "time_precision": float(item["metrics"]["time_precision"]),
                "time_recall": float(item["metrics"]["time_recall"]),
                "time_f1": float(item["metrics"]["time_f1"]),
                "num_segments": int(len(item["segments"])),
            })

    if not grouped:
        return None

    summary_rows = []
    per_match_rows = []
    for method_name, rows in grouped.items():
        precisions = np.array([row["time_precision"] for row in rows], dtype=float)
        recalls = np.array([row["time_recall"] for row in rows], dtype=float)
        f1s = np.array([row["time_f1"] for row in rows], dtype=float)
        seg_counts = np.array([row["num_segments"] for row in rows], dtype=float)
        summary_rows.append({
            "method": method_name,
            "matches": len(rows),
            "mean_precision": f"{float(precisions.mean()):.4f}",
            "mean_recall": f"{float(recalls.mean()):.4f}",
            "mean_f1": f"{float(f1s.mean()):.4f}",
            "std_precision": f"{float(precisions.std(ddof=0)):.4f}",
            "std_recall": f"{float(recalls.std(ddof=0)):.4f}",
            "std_f1": f"{float(f1s.std(ddof=0)):.4f}",
            "mean_segments": f"{float(seg_counts.mean()):.2f}",
        })
        for row in rows:
            per_match_rows.append({
                "method": method_name,
                "match": row["match"],
                "precision": f"{row['time_precision']:.4f}",
                "recall": f"{row['time_recall']:.4f}",
                "f1": f"{row['time_f1']:.4f}",
                "segments": row["num_segments"],
            })

    def method_sort_key(row):
        order = {"DBSCAN": 0, "Sliding Window": 1, "KDE": 2}
        name = row["method"]
        if name.startswith("KDE"):
            return (order["KDE"], name)
        return (order.get(name, 99), name)

    summary_rows = sorted(summary_rows, key=method_sort_key)
    per_match_rows = sorted(per_match_rows, key=lambda row: (method_sort_key({"method": row["method"]}), row["match"]))

    out_path = out_dir / "aggregate_method_summary.md"
    lines = []
    lines.append("# Aggregate Multi-Method Summary")
    lines.append("")
    lines.append(f"- GT source: `{gt_path.name}`")
    lines.append(f"- Number of GT matches: `{len(block_summaries)}`")
    lines.append("")
    lines.append("## Mean Metrics Across GT Matches")
    lines.append("")
    lines.append(format_table(summary_rows, [
        ("method", "Method"),
        ("matches", "# GTs"),
        ("mean_precision", "Mean Precision"),
        ("mean_recall", "Mean Recall"),
        ("mean_f1", "Mean F1"),
        ("std_precision", "Std Precision"),
        ("std_recall", "Std Recall"),
        ("std_f1", "Std F1"),
        ("mean_segments", "Mean # Segments"),
    ]))
    lines.append("")
    lines.append("## Per-GT Metrics")
    lines.append("")
    lines.append(format_table(per_match_rows, [
        ("method", "Method"),
        ("match", "GT Match"),
        ("precision", "Precision"),
        ("recall", "Recall"),
        ("f1", "F1"),
        ("segments", "# Segments"),
    ]))
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gt_file", required=True, type=str)
    parser.add_argument("--kde_root", default=None)
    parser.add_argument("--kde_roots", default=None, help="Comma-separated KDE report roots")
    parser.add_argument("--kde_bandwidths", default=None, help="Comma-separated bandwidth suffixes like 2.6,3.2,4.0")
    parser.add_argument("--dbscan_root", default=None)
    parser.add_argument("--sliding_root", default=None)
    parser.add_argument("--out_dir", default="./highlight_compare")
    parser.add_argument("--only_kde", action="store_true", help="Compare only KDE variants")
    args = parser.parse_args()

    gt_path = Path(args.gt_file)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    kde_roots = resolve_kde_roots(args.kde_root, args.kde_roots, args.kde_bandwidths)
    blocks = parse_gt_blocks(gt_path)

    method_info = []
    for root in kde_roots:
        bw_label = bandwidth_label_from_root(root)
        method_info.append((f"kde_h{bw_label}", f"KDE h={bw_label}", root))

    if not args.only_kde:
        dbscan_root = resolve_report_root(args.dbscan_root, "dbscan_reports")
        sliding_root = resolve_report_root(args.sliding_root, "sliding_reports")
        method_info.extend([
            ("dbscan", "DBSCAN", dbscan_root),
            ("sliding_window", "Sliding Window", sliding_root),
        ])

    out_paths = []
    block_summaries = []
    for block in blocks:
        out_path, matched = build_comparison_for_block(block, gt_path, out_dir, method_info)
        out_paths.append(out_path)
        block_summaries.append((block["title"], matched))
        print(f"[OK] wrote {out_path}")

    aggregate_path = None
    if len(block_summaries) >= 2:
        aggregate_path = write_aggregate_method_summary(out_dir, gt_path, block_summaries)
        if aggregate_path is not None:
            print(f"[OK] wrote {aggregate_path}")

    if len(out_paths) > 1:
        print(f"[OK] generated {len(out_paths)} comparison markdown files from {gt_path.name}")


if __name__ == "__main__":
    import os
    main()

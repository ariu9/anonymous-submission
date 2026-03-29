# batch_reports.py
import os, re, io, json, base64, argparse
import numpy as np
import pandas as pd
from pathlib import Path
from statistics import median
from sklearn.neighbors import KernelDensity
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("agg")
import math
# ---- You must provide these from your codebase ----
# events_by_file: dict[str, dict]  # {filepath: event_dict_loaded}
# extract_timestamps(event_dict) -> np.ndarray[float]  # parses your keys to seconds
# segments_to_dataframe(segments, label, ts) -> pd.DataFrame  # optional if you have it
# If you don't have segments_to_dataframe, we'll build a DataFrame directly.

def extract_segments_from_density1(ts, x, dens,
                                  mean_factor=5.0,
                                  min_len=10.0,
                                  prepend=5.0,
                                  min_events=2):
    """
    Returns:
      segs: list of (a, b, n_events) for regions with dens >= thr, length >= min_len,
            and n_events >= min_events
      thr:  threshold used (mean(dens) * mean_factor)
      valid_mask: boolean array over x where regions satisfy *both* density and event-count
    """
    thr = float(np.mean(dens)) * mean_factor
    above = dens >= thr

    segs = []
    valid_mask = np.zeros_like(above, dtype=bool)

    start_idx = None
    for i, is_above in enumerate(above):
        if is_above and start_idx is None:
            start_idx = i
        if (not is_above or i == len(above)-1) and start_idx is not None:
            end_idx = i if not is_above else i  # inclusive index for the above-run

            # region in time
            a = float(x[start_idx]) - prepend
            b = float(x[end_idx])
            if a < 0.0:
                a = 0.0

            if (b - a) >= min_len:
                # how many events fall inside [a, b]?
                n_in = int(((ts >= a) & (ts <= b)).sum())
                if n_in >= min_events:  # strictly "> 2" means min_events=3
                    segs.append((a, b, n_in))
                    # mark this contiguous region as valid for shading
                    valid_mask[start_idx:end_idx+1] = True

            start_idx = None

    return segs, thr, valid_mask

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def inter_event_gaps(ts: np.ndarray) -> np.ndarray:
    ts = np.asarray(sorted(set(ts)), dtype=float)
    return np.diff(ts) if ts.size >= 2 else np.array([], dtype=float)

def single_kernels_on_grid(ts: np.ndarray, x: np.ndarray, bandwidth: float) -> np.ndarray:
    """
    Return matrix K of shape (len(x), len(ts)) where each column is the
    contribution of a single Gaussian kernel centered at ts[j] evaluated on x.
    Scaled as (1/(n*h))*phi((x - t_j)/h) so that sum over j equals KDE density.
    """
    n = len(ts)
    if n == 0:
        return np.zeros((len(x), 0), dtype=float)
    h = float(bandwidth)
    Z = (x[:, None] - ts[None, :]) / h                      # (len(x), n)
    phi = np.exp(-0.5 * Z**2) / math.sqrt(2.0 * math.pi)   # standard normal pdf
    return (phi / (n * h))          

def q1_of_gaps(gaps: np.ndarray):
    g = np.sort(gaps)
    if g.size == 0:
        return None
    n = g.size
    lower = g[: n//2] if n > 1 else g
    return float(np.median(lower)) if lower.size > 0 else float(g[0])

def recommend_h_from_q1(q1, scale=0.8, clip_min=2.0, clip_max=12.0):
    if q1 is None:
        return None
    h = scale * float(q1)
    return float(min(max(h, clip_min), clip_max))

def safe_stem(fp: str, count) -> str:
    return str(count) + "_" + re.sub(r'[^A-Za-z0-9._-]+', '_', Path(fp).stem)

def plot_kde(ts: np.ndarray, bandwidth: float, num_points: int = 1500):
    kde = KernelDensity(kernel='gaussian', bandwidth=bandwidth)
    kde.fit(ts[:, None])
    t_min, t_max = float(ts.min()), float(ts.max())
    grid = np.linspace(max(0.0, t_min - 30.0), t_max + 30.0, num_points)[:, None]
    dens = np.exp(kde.score_samples(grid))
    return grid[:, 0], dens

def fig_to_png_bytes():
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=130)
    plt.close()
    buf.seek(0)
    return buf.read()

def png_bytes_to_base64(png_bytes: bytes) -> str:
    return base64.b64encode(png_bytes).decode('ascii')

def build_segment_df(segments):
    # segments: list[(a,b,n_events)]
    return pd.DataFrame(
        [{"start": float(a), "end": float(b), "duration": float(b - a), "n_events": int(n)} for a,b,n in segments]
    )

def extract_segments_from_density(ts, x, dens, mean_factor=5.0, min_len=10.0, prepend=5.0):
    thr = float(np.mean(dens)) * mean_factor
    above = dens >= thr
    segs = []
    start_idx = None
    for i, is_above in enumerate(above):
        if is_above and start_idx is None:
            start_idx = i
        if (not is_above or i == len(above)-1) and start_idx is not None:
            end_idx = i if not is_above else i
            a = float(x[start_idx]) - prepend
            b = float(x[end_idx])
            if a < 0: a = 0.0
            if (b - a) >= min_len:
                n_in = int(((ts >= a) & (ts <= b)).sum())
                if n_in > 1:  # enforce >1 event
                    segs.append((a, b, n_in))
            start_idx = None
    return segs

def write_markdown_report(path: Path, batch_items, params):
    # batch_items: list of dicts with keys: file, rel_img, seg_df_path, preview_df
    lines = []
    lines.append(f"# KDE Segments Report — batch ({len(batch_items)} files)")
    lines.append("")
    lines.append(f"**Params**: bandwidth={params['bandwidth']:.3f}s, "
                 f"density_threshold_factor={params['factor']}, "
                 f"min_segment_len_sec={params['min_len']}, "
                 f"prepend_sec={params['prepend']}")
    lines.append("")
    for item in batch_items:
        lines.append(f"## {os.path.basename(item['file'])}")
        lines.append("")
        lines.append(f"![KDE]({item['rel_img']})")
        lines.append("")
        lines.append(f"[Full segments JSON]({item['seg_json_rel']})")
        lines.append("")
        # preview first 20 segments as markdown table
        df = item["preview_df"].head(20)
        if len(df):
            lines.append(df.to_markdown(index=False))
            lines.append("")
        else:
            lines.append("_No segments found with current parameters._\n")
        lines.append("<hr/>\n")
    path.write_text("\n".join(lines), encoding="utf-8")

def write_html_report(path: Path, batch_items, params):
    parts = []
    parts.append(f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>KDE Segments Report</title>
<style>
body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 24px; }}
h1,h2 {{ margin: 12px 0; }}
hr {{ margin: 24px 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 8px 0; }}
th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: right; }}
th {{ background: #f5f5f5; text-align: center; }}
.filename {{ font-weight: bold; }}
.params {{ color: #555; margin-bottom: 16px; }}
img {{ max-width: 100%; height: auto; border: 1px solid #ccc; }}
.details {{ font-size: 13px; color: #666; }}
</style></head><body>
<h1>KDE Segments Report — batch ({len(batch_items)} files)</h1>
<div class="params">Params: bandwidth={params['bandwidth']:.3f}s, density_threshold_factor={params['factor']}, min_segment_len_sec={params['min_len']}, prepend_sec={params['prepend']}</div>
""")
    for item in batch_items:
        parts.append(f"""<h2 class="filename">{os.path.basename(item['file'])}</h2>
<img src="data:image/png;base64,{item['img_b64']}" alt="KDE plot"/>
<div class="details"><a href="{item['seg_json_rel']}">Full segments JSON</a></div>
{item['preview_df'].to_html(index=False)}
<hr/>""")
    parts.append("</body></html>")
    path.write_text("\n".join(parts), encoding="utf-8")

def extract_timestamps(event_dict):
    """Return sorted np.array of seconds parsed from dict keys like '751.23_0' or '827.31'."""
    secs = []
    for k in event_dict.keys():
        m = re.match(r'^(\d+(?:\.\d+)?)', str(k))
        if m:
            try:
                secs.append(float(m.group(1)))
            except ValueError:
                pass
    return np.array(sorted(secs), dtype=float)
from collections import OrderedDict

def main():
    import os
    import glob
    import json
    import warnings
    warnings.filterwarnings("ignore", message="Glyph.*missing from font")
    # import matplotlib
    # matplotlib.use("TkAgg")
    import matplotlib.ticker as mticker

    EVENT_GLOB = "./2023_2024_event_logs"  # your directory with JSON files
    # EVENT_GLOB = "./BRO vs DK - HLE vs T1  2023 LCK 서머 스플릿_1_event_log"
    # json_files = glob.glob(os.path.join(EVENT_GLOB, "*.json"))
    json_files = glob.glob(os.path.join(EVENT_GLOB, "**", "*_event_log.json"), recursive=True)
    # json_files = json_files[0]filtered = [
    filtered = [
        f for f in json_files
        if (lambda d: len(d) >= 10)(
            json.load(open(f, "r", encoding="utf-8"))
        )
    ]
    json_files = filtered
    events_by_file = {}
    vid_names = []
    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            temp_json = json.load(f)
        if len(temp_json) < 10 :
            continue
        with open(file_path, 'r', encoding='utf-8') as f:
            events_by_file[file_path] = json.load(f)

        # vid_names = [jf.split("/")[-1].split("_event")[0] + ".mp4" for jf in json_files]
        vid_names.append(file_path.split("/")[-1].split("_event")[0] + ".mp4")

    print(f"Loaded {len(events_by_file)} files.")
    print(list(events_by_file.keys())[:5])
    import json, csv
    with open("./vid_names.json", "w", encoding="utf-8") as f:
        json.dump(vid_names, f)
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", type=str, default="./kde_reports", help="Output root directory")
    ap.add_argument("--batch_size", type=int, default=100)
    ap.add_argument("--format", type=str, choices=["md", "html"], default="md")
    ap.add_argument("--scale", type=float, default=0.8, help="h = scale * Q1")
    ap.add_argument("--clip_min", type=float, default=1.0)
    ap.add_argument("--clip_max", type=float, default=12.0)
    ap.add_argument("--factor", type=float, default=5.0, help="density_threshold_factor")
    ap.add_argument("--min_len", type=float, default=10.0, help="min_segment_len_sec")
    ap.add_argument("--prepend", type=float, default=5.0, help="start shift seconds")
    ap.add_argument("--num_points", type=int, default=1500)
    ap.add_argument("--bandwidth_override", type=float, default=None,
                    help="Use this bandwidth directly instead of the computed global value")
    args = ap.parse_args()

    # out_dir = Path(args.out_dir)
    base_out_dir = args.out_dir

    # ---- compute global bandwidth from per-file Q1 ----
    per_file_q1 = []
    for fp, ev in events_by_file.items():
        ts = extract_timestamps(ev)
        q1 = q1_of_gaps(inter_event_gaps(ts))
        if q1 is not None:
            per_file_q1.append(q1)
    if not per_file_q1:
        raise RuntimeError("No valid Q1 across files.")
    global_Q1 = float(median(sorted(per_file_q1)))
    computed_global_h = recommend_h_from_q1(global_Q1, args.scale, args.clip_min, args.clip_max)
    global_h = float(args.bandwidth_override) if args.bandwidth_override is not None else float(computed_global_h)
    print(f"[GLOBAL] Q1={global_Q1:.3f}s -> bandwidth={global_h:.3f}s")

    in_path = "./event_detection_scores.json"
    if os.path.exists(in_path):
        out_path = f"./per_class_scores_h_{global_h:.1f}.csv"
        with open(in_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["name", "precision", "recall", "f1"])
            for k in sorted(data["per_champion"].keys()):
                v = data["per_champion"][k]
                w.writerow([k, v["precision"], v["recall"], v["f1_score"]])
        print("Wrote:", out_path)
    else:
        print(f"[WARN] skipped per-class CSV because {in_path} was not found")

    # plt.rcParams['font.family'] = 'NanumGothic'
    out_dir = Path(f"{base_out_dir}_h{global_h:.1f}")

    plots_dir = out_dir / "plots"
    segs_dir  = out_dir / "segments"
    ensure_dir(out_dir); ensure_dir(plots_dir); ensure_dir(segs_dir)

    # ---- iterate files & build batches ----
    batch_items = []
    batch_idx = 0
    file_idx = 0
    count = 0
    
    # --- compute the same threshold used by extract_segments_from_density ---
    # thr = float(np.mean(dens)) * args.factor
    # above = dens >= thr
    
    # NEW:

    for fp, ev in events_by_file.items():
        ts = extract_timestamps(ev)
        if ts.size < 2:
            continue
        count += 1
        x, dens = plot_kde(ts, bandwidth=global_h, num_points=args.num_points)
        segs, thr, valid_mask = extract_segments_from_density1(
            ts, x, dens,
            mean_factor=args.factor,
            min_len=args.min_len,
            prepend=args.prepend,
            min_events=2,
        )
        df = build_segment_df(segs)

        # save per-file segments JSON
        stem = safe_stem(fp, count)
        seg_json_path = segs_dir / f"{stem}_segments.json"
        seg_json_path.write_text(json.dumps({
            "file": fp,
            "bandwidth_sec": float(global_h),
            "density_threshold_factor": float(args.factor),
            "min_segment_len_sec": float(args.min_len),
            "prepend_sec": float(args.prepend),
            "segments": df.to_dict(orient="records"),
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        # save PNG plot (for markdown); also prepare base64 (for html)
        plt.figure(figsize=(18, 5))
        # plt.plot(x, dens, label="KDE density", linewidth=1.8, 
        #          color=(14.0/255, 40.0/255, 65.0/255), alpha=.8)
        plt.plot(x, dens, label="KDE density", linewidth=1.8, 
                 color="black", alpha=.8)

        
        # KDE 그래프 그린 후
        starts = [a for a, b, n in segs]
        ends   = [b for a, b, n in segs]

        # # 현재 xticks 가져오기
        # xticks = plt.xticks()[0]

        # # 기존 tick + segment 경계 tick 합치기
        # new_xticks = sorted(set(xticks.tolist() + starts + ends))
        # plt.xticks(new_xticks, fontsize=24, rotation=45)        

        # for (a, b, n) in segs:
        #     plt.axvline(a, color="green", linestyle="--", alpha=0.7)
        #     plt.axvline(b, color="green", linestyle="--", alpha=0.7)
        #     plt.text(a, plt.ylim()[1]*0.6, f"start", rotation=90, va="top", ha="right", fontsize=24, color="green")
        #     plt.text(b, plt.ylim()[1]*0.6, f"end", rotation=90, va="top", ha="left", fontsize=24, color="green")
        
        # for (a, b, n) in segs:
        #     plt.axvspan(a, b, ymin=0, ymax=0.05, color="orange", alpha=0.5)

        # ... plotting code ...
        ax = plt.gca()
        # 표시용 KDE (계산은 h=3.2 유지)
        ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=4))  # y축 눈금 최대 4개

        # h_vis = global_h * 3  # 예: 1.5배
        # kde_vis = KernelDensity(kernel='gaussian', bandwidth=h_vis).fit(ts[:, None])
        # dens_vis = np.exp(kde_vis.score_samples(x[:, None]))
        # ax.plot(x, dens_vis, linewidth=1.5, alpha=0.4, linestyle='-',
        #         label=f"Smoothed KDE (h={h_vis:.1f})")
        
        # 1) 기본 눈금은 Matplotlib이 자동으로 배치
        default_ticks = ax.get_xticks()

        # 2) 구간 start/end 값 추출
        segment_ticks = [a for a, b, n in segs] + [b for a, b, n in segs]

        # 3) 전체 눈금 = 기본 + segment
        all_ticks = sorted(set(default_ticks.tolist() + segment_ticks))

        # 4) tick 위치 설정
        ax.set_xticks(all_ticks)

        # 5) 레이블은 기본 눈금에만, segment는 빈 문자열
        labels = []
        for t in all_ticks:
            if t in default_ticks:   # 기본 tick → 값 표시
                labels.append(str(int(t)))
            else:                    # segment tick → 레이블 없음
                labels.append("")

        ax.set_xticklabels(labels, fontsize=24)

        # threshold line
        ax.axhline(thr, linestyle=":", linewidth=1.5, color="gray",
                label=f"Threshold (μ×{args.factor:g})")

        # shade only regions that satisfy BOTH conditions (density≥thr AND >=3 events)
        ax.fill_between(x, dens, thr, where=valid_mask, interpolate=True, alpha=0.25,
                        label="KIS (density ≥ Threshold & \n # interactions in segment ≥ 2 )")
        
        # ax = plt.gca()
        # # 1) horizontal threshold line
        # ax.axhline(thr, linestyle=":", linewidth=1.5, color="gray",
        #         label=f"Threshold (μ×{args.factor:g})")

        # # 2) shade where density is above threshold
        # ax.fill_between(x, dens, thr, where=above, interpolate=True, alpha=0.25,
        #                 color="tab:orange", label="Above threshold")
        
        # --- add: per-event single kernels (red dashed) ---
        K = single_kernels_on_grid(ts, x, bandwidth=global_h)  # (len(x), n_events)
        if K.shape[1] > 0:
            for j in range(K.shape[1]):
                if j == 0 :
                    plt.plot(x, K[:, j], linestyle="--", color="red", alpha=0.6, linewidth=1.0,
                            label="Single kernel")
                
                plt.plot(x, K[:, j], linestyle="--", color="red", alpha=0.6, linewidth=1.0)
                
        # 1) Remove private-use glyphs (like \uf027)
        s = re.sub(r"[\uE000-\uF8FF]", "", os.path.basename(fp))

        # 2) Extract team matchup (before the year)
        match_part = re.search(r"^(.*?)\s*20\d{2}", os.path.basename(fp)).group(1).strip()
        if "\uf027" in match_part : 
            match_part = match_part.replace("\uf027", "")
        # 3) Extract year + LCK season info
        season_part = re.search(r"(20\d{2}\s*LCK\s*서머\s*스플릿[_\-\s]*\d+)", os.path.basename(fp))
        if season_part:
            season_part = season_part.group(1)
            # Optional: normalize Korean → English
            season_part = (season_part
                        .replace("서머", "Summer")
                        .replace("스플릿", "Split")
                        .replace("_", " ")
                        .strip())
        
        # (선택) 기준선/레이블
        plt.xlabel("Time (seconds)", fontsize=24); plt.ylabel("Estimated density", fontsize=24)
        # plt.title(f"KDE result — {os.path.basename(fp)} (bw={global_h:.2f}s)")
        plt.title(f"KDE result — match {count} (bandwidth={global_h:.2f}s)", fontsize=30)
        plt.legend(loc="upper left", fontsize=15)
        # plt.xticks(fontsize=24)
        plt.yticks(fontsize=24)

        png_bytes = fig_to_png_bytes()
        plot_path = plots_dir / f"{stem}_kde.png"
        plot_path.write_bytes(png_bytes)

        # plt.figure()
        # plt.plot(x, dens)
        # plt.xlabel("Time (seconds)"); plt.ylabel("Estimated density")
        # plt.title(f"KDE — {os.path.basename(fp)} (bw={global_h:.2f}s)")
        # png_bytes = fig_to_png_bytes()
        # plot_path = plots_dir / f"{stem}_kde.png"
        # plot_path.write_bytes(png_bytes)

        item = {
            "file": fp,
            "rel_img": os.path.relpath(plot_path, out_dir),
            "img_b64": png_bytes_to_base64(png_bytes),
            "seg_json_rel": os.path.relpath(seg_json_path, out_dir),
            "preview_df": df
        }
        batch_items.append(item)
        file_idx += 1

        # write a batch report every N processed files
        if len(batch_items) == args.batch_size:
            params = {"bandwidth": global_h, "factor": args.factor, "min_len": args.min_len, "prepend": args.prepend}
            report_name = f"report_batch_{batch_idx:03d}.{args.format}"
            report_path = out_dir / report_name
            if args.format == "md":
                write_markdown_report(report_path, batch_items, params)
            else:
                write_html_report(report_path, batch_items, params)
            print(f"[BATCH] wrote {report_path} with {len(batch_items)} files")
            batch_idx += 1
            batch_items = []

    if batch_items:
        params = {"bandwidth": global_h, "factor": args.factor, "min_len": args.min_len, "prepend": args.prepend}
        report_name = f"report_batch_{batch_idx:03d}.{args.format}"
        report_path = out_dir / report_name
        if args.format == "md":
            write_markdown_report(report_path, batch_items, params)
        else:
            write_html_report(report_path, batch_items, params)
        print(f"[BATCH] wrote {report_path} with {len(batch_items)} files")



    # # ---- 파일별 segment 추출 & 통계 집계 ----
    # per_file_rows = []           # CSV 용
    # all_durations = []           # 전체 평균 계산용
    # all_n_events  = []           # 전체 평균 계산용
    # files_with_segments = 0
    # total_segments = 0

    # for fp, ev in events_by_file.items():
    #     ts = extract_timestamps(ev)
    #     if ts.size < 2:
    #         per_file_rows.append([fp, 0, np.nan, np.nan])
    #         continue

    #     # KDE density 계산 (플롯 X)
    #     x, dens = plot_kde(ts, bandwidth=global_h, num_points=args.num_points)

    #     # segment 추출
    #     segs = extract_segments_from_density(
    #         ts, x, dens,
    #         mean_factor=args.factor,
    #         min_len=args.min_len,
    #         prepend=args.prepend
    #     )
    #     df = build_segment_df(segs)

    #     if len(df) > 0:
    #         files_with_segments += 1
    #         total_segments += len(df)
    #         # 파일별 평균
    #         mean_duration = float(df["duration"].mean())
    #         mean_n_events = float(df["n_events"].mean())
    #         per_file_rows.append([fp, int(len(df)), mean_duration, mean_n_events])

    #         # 전체 평균 계산을 위해 누적
    #         all_durations.extend(df["duration"].tolist())
    #         all_n_events.extend(df["n_events"].tolist())
    #     else:
    #         per_file_rows.append([fp, 0, np.nan, np.nan])

    # # ---- 결과 저장 ----
    # # 파일별 CSV
    # per_file_csv = out_dir / "per_file_segments.csv"
    # pd.DataFrame(per_file_rows, columns=["file", "num_segments", "mean_duration", "mean_n_events"]) \
    #   .to_csv(per_file_csv, index=False, encoding="utf-8")
    # print("Wrote:", per_file_csv)

    # # 전체 요약 JSON
    # if len(all_durations) > 0:
    #     global_mean_duration = float(np.mean(all_durations))
    #     global_mean_n_events = float(np.mean(all_n_events))
    # else:
    #     global_mean_duration = None
    #     global_mean_n_events = None

    # summary = {
    #     "bandwidth_sec": float(global_h),
    #     "density_threshold_factor": float(args.factor),
    #     "min_segment_len_sec": float(args.min_len),
    #     "prepend_sec": float(args.prepend),
    #     "total_segments": int(total_segments),
    #     "num_files_with_segments": int(files_with_segments),
    #     "global_mean_duration": global_mean_duration,   # 전체 segment 기준 평균 길이(초)
    #     "global_mean_n_events": global_mean_n_events    # 전체 segment 기준 평균 이벤트 개수
    # }
    # summary_path = out_dir / "summary.json"
    # summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    # print("Wrote:", summary_path)

if __name__ == "__main__":
    main()


    

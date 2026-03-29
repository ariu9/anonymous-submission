# kde_bandwidth_from_keys.py
import os, json, argparse
from pathlib import Path
from statistics import median
from typing import List, Optional, Tuple

def keys_as_seconds(d) -> List[float]:
    """Assume top-level keys of dict are seconds (int/float or numeric strings)."""
    if not isinstance(d, dict):
        return []
    secs = []
    for k in d.keys():
        try:
            secs.append(float(k))
        except:
            # skip non-numeric keys
            pass
    # unique + sorted + strictly increasing
    secs = sorted(set(secs))
    return secs

def inter_event_gaps(secs: List[float]) -> List[float]:
    gaps = []
    for i in range(1, len(secs)):
        dt = secs[i] - secs[i-1]
        if dt > 0:
            gaps.append(dt)
    return gaps

def q1_q2(vals: List[float]) -> Tuple[Optional[float], Optional[float]]:
    if not vals:
        return None, None
    vals = sorted(vals)
    n = len(vals)
    # Q2 (median)
    Q2 = median(vals)
    # Q1 (median of lower half)
    lower = vals[: n//2] if n > 1 else vals
    Q1 = median(lower) if lower else vals[0]
    return float(Q1), float(Q2)

def recommend_h(q1: Optional[float], scale=0.8, clip_min=2.0, clip_max=12.0) -> Optional[float]:
    if q1 is None:
        return None
    h = scale * q1
    if h < clip_min: h = clip_min
    if h > clip_max: h = clip_max
    return float(h)

def scan_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"file": path, "num_events": 0, "Q1": None, "Q2": None, "h": None, "error": str(e)}

    secs = keys_as_seconds(data)
    gaps = inter_event_gaps(secs)
    Q1, Q2 = q1_q2(gaps)
    h = recommend_h(Q1)
    return {"file": path, "num_events": len(secs), "Q1": Q1, "Q2": Q2, "h": h, "error": None}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, required=True, help="Season folder (scans recursively)")
    ap.add_argument("--pattern", type=str, default="**/*.json", help="Glob pattern (default: **/*.json)")
    ap.add_argument("--save_csv", type=str, default=None, help="Optional CSV path")
    ap.add_argument("--scale", type=float, default=0.8, help="h = scale * Q1 (default 0.8)")
    ap.add_argument("--clip_min", type=float, default=2.0, help="Min clip for h (default 2.0s)")
    ap.add_argument("--clip_max", type=float, default=12.0, help="Max clip for h (default 12.0s)")
    args = ap.parse_args()

    files = []
    for p in Path(args.root).glob(args.pattern):
        if not str(p).endswith("_event_log.json"):
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            if len(data) >= 10:   # only keep if JSON has >10 top-level entries
                files.append(str(p))
        except Exception as e:
            print(f"Skipping {p}: {e}")

    print(f"Kept {len(files)} event log JSONs")
    # files = [str(p) for p in Path(args.root).glob(args.pattern)]
    print(f"# Found {len(files)} JSON files")
    results = []
    q1s = []

    for fp in files:
        r = scan_json(fp)
        # format numbers nicely
        q1 = f"{r['Q1']:.3f}" if r["Q1"] is not None else "None"
        q2 = f"{r['Q2']:.3f}" if r["Q2"] is not None else "None"
        h  = f"{r['h']:.3f}"  if r["h"]  is not None else "None"
        err = "OK" if r["error"] is None else f"ERR: {r['error']}"
        print(f"- {os.path.relpath(fp, args.root)} | events={r['num_events']:4d} | Q1={q1} | Q2={q2} | h={h} | {err}")

        results.append(r)
        if r["Q1"] is not None:
            q1s.append(r["Q1"])

    # Global recommendation (median of per-file Q1)
    if q1s:
        q1s_sorted = sorted(q1s)
        global_Q1 = median(q1s_sorted)
        # allow custom scale/clip on the command line
        global_h = max(args.clip_min, min(args.clip_max, args.scale * global_Q1))
        print("\n# Global summary")
        print(f"  - files with valid Q1: {len(q1s)}")
        print(f"  - global Q1 (median of per-file Q1): {global_Q1:.3f}s")
        print(f"  - global recommended h: {global_h:.3f}s (scale={args.scale}, clip=[{args.clip_min},{args.clip_max}])")
    else:
        print("\n# Global summary: No valid Q1 values found.")

    # Optional CSV
    if args.save_csv:
        import csv
        with open(args.save_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["file", "num_events", "Q1_sec", "Q2_sec", "h_sec", "error"])

            # --- Global row first ---
            if q1s:
                global_Q1 = median(sorted(q1s))
                global_h  = max(args.clip_min, min(args.clip_max, args.scale * global_Q1))
                w.writerow([
                    "GLOBAL",
                    sum(r["num_events"] for r in results),
                    global_Q1,
                    None,         # no single global Q2, you can leave empty or compute differently
                    global_h,
                    None
                ])
            else:
                w.writerow(["GLOBAL", 0, None, None, None, "No valid Q1"])

            # --- Per-file rows ---
            for r in results:
                w.writerow([r["file"], r["num_events"], r["Q1"], r["Q2"], r["h"], r["error"]])

        print(f"\nSaved CSV: {args.save_csv}")
        
if __name__ == "__main__":
    main()

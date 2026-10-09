#!/usr/bin/env python3
"""Lab 9: analyse one recorded run folder (lab9/eval/runs/<run>/, made by record_run.sh). Never moves the robot.

Per pick, from the logs in the run folder:
  brain log (logs/)      target, events, warnings, bin, time per pick
  controller (logs_pi/)  actual flange position: first position after "pump on" = contact
  vision log (logs/)     object of the same colour still within 25 mm of the target 4 s after the drop = not placed
Writes <run>/analysis.md and appends one row per pick to lab9/eval/runs.csv (unless --no-csv).
With --plot also <run>/joints_pump.png (joint angles from the bag, pump-on phases shaded) and <run>/start_end.jpg
(camera snapshots before the first pick and after the last one).

    source ~/rosenv9.sh     # --plot reads the bag with rosbag2_py
    python3 solutions/lab9_real_hardware/lab9_analyse_run.py lab9/eval/runs/2026-10-09_1537_sort_test6 \
        --start 15:37:10 --end 15:40:35 --plot
Times are local (HH:MM:SS) on the day of the run folder. "placed" means "left the plate", not "landed in the bin":
check that by eye (start_end.jpg) and note it in runs.csv.
"""
import argparse, csv, datetime, glob, math, os, re

import yaml

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CONFIG = os.path.join(REPO, "pp_moveit_ws", "src", "lab9_pick_place", "config", "lab9.yaml")
LINE = re.compile(r"\[(\w+)\] \[(\d{10}\.\d+)\] \[([^\]]+)\]: (.*)")
COORD = re.compile(r"Current coordinates: \[([-\d.]+), ([-\d.]+), ([-\d.]+)")
OBJ = re.compile(r"([a-z]+)_(cube|cylinder|unknown)_\d+ \((-?\d+), (-?\d+)\)")
MOVE = re.compile(r"move to \[([-\d.]+), ([-\d.]+), ([-\d.]+), [-\d.]+, ([-\d.]+), ([-\d.]+)\]")
hm = lambda t: datetime.datetime.fromtimestamp(t).strftime("%H:%M:%S")


def epoch(day, hhmmss):
    return datetime.datetime.strptime(f"{day} {hhmmss}", "%Y-%m-%d %H:%M:%S").timestamp()


def events(run, node, folders, t0, t1):
    out = set()
    for f in sum((glob.glob(os.path.join(run, d, "*.log")) for d in folders), []):
        for line in open(f, errors="replace"):
            m = LINE.search(line)
            if m and m.group(3) == node and t0 <= float(m.group(2)) <= t1:
                out.add((float(m.group(2)), m.group(1), m.group(4).strip()))
    return sorted(out)


def analyse(run, t0, t1, hover_m):
    brain = events(run, "mycobot_brain_lab9", ["logs"], t0, t1)
    ctrl = events(run, "controller", ["logs_pi"], t0, t1)
    vis = events(run, "vision_lab9", ["logs"], t0, t1)

    def objects_at(t):
        last = None
        for tt, _, msg in vis:
            if tt <= t and msg.startswith("objects:"):
                last = msg
        return [(c, s, int(x), int(y)) for c, s, x, y in OBJ.findall(last or "")]

    picks, cur = [], None
    for t, lvl, msg in brain:
        if msg.startswith("planning scene:"):
            cur = {"t_start": t, "moves": [], "warn": []}
        elif cur is None:
            continue
        elif msg.startswith("move to ["):
            m = MOVE.search(msg)
            if m:
                cur["moves"].append((t, *map(float, m.groups())))
        elif "pump on" in msg:
            cur["t_pump_on"] = t
        elif msg.endswith(" picked"):
            cur["id"], cur["t_picked"] = msg.split()[0], t
        elif "dropped into bin" in msg:
            cur["bin"], cur["t_drop"] = msg.split()[-1], t
            picks.append(cur); cur = None
        elif "sequence stopped" in msg:
            cur["stopped"], cur["t_drop"] = msg, t
            picks.append(cur); cur = None
        elif lvl in ("WARN", "ERROR"):
            cur["warn"].append(msg)

    rows = []
    for p in picks:
        tp, td = p.get("t_pump_on", p["t_start"]), p["t_drop"]
        coords = [tuple(map(float, COORD.search(m).groups())) for t, _, m in ctrl if tp <= t <= td + 1.5 and COORD.search(m)]
        before = [mv for mv in p["moves"] if mv[0] <= tp]
        hover = before[-1] if before else None
        carry = [mv for mv in p["moves"] if mv[0] > p.get("t_picked", td)]
        tx, ty = (hover[1], hover[2]) if hover else (float("nan"),) * 2
        oid = p.get("id", "?_?")
        color, shape = (oid.split("_") + ["?"])[:2]
        after = objects_at(td + 4.0)
        still = [o for o in after if o[0] == color and math.hypot(o[2] - tx * 1000, o[3] - ty * 1000) < 25]
        rows.append(dict(
            id=oid, color=color, shape=shape, t_start=hm(p["t_start"]), dur=td - p["t_start"],
            tx=tx * 1000, ty=ty * 1000,
            contact=f"({coords[0][0]:.1f}, {coords[0][1]:.1f}, {coords[0][2]:.1f})" if coords else "-",
            contact_z=coords[0][2] if coords else float("nan"),
            dxy=math.hypot(coords[0][0] - tx * 1000, coords[0][1] - ty * 1000) if coords else float("nan"),
            planned_z=(hover[3] - hover_m + 0.040) * 1000 if hover else float("nan"),   # pump_head + 40 mm = flange
            carry=(f"z {carry[-1][3]:.3f}, pitch {carry[-1][4]:.2f}"
                   + (" (TILTED)" if abs(carry[-1][4] - math.pi) > 0.05 else " (vertical)")
                   + (f", after {len(carry) - 1} failed plans" if len(carry) > 1 else "")) if carry else "-",
            bin=p.get("bin", "-"),
            outcome="stopped" if "stopped" in p else ("placed" if not still else "still_on_plate"),
            warn=("; ".join(sorted(set(p["warn"]))) or p.get("stopped", ""))[:140]))
    return rows


def report(run, rows, t0, t1):
    out = [f"# Analysis of {os.path.basename(run)} ({hm(t0)}–{hm(t1)})", "",
           "Sources: brain log (targets, events), Pi controller log (actual flange position), vision log (object still on",
           "the plate 4 s after the drop = not placed). Contact = first controller position after `pump on`.", "",
           "| # | start | object | target (mm) | contact flange (mm) | planned contact z | xy diff | carry above bin | bin | outcome | time (s) | notes |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        out.append(f"| {i} | {r['t_start']} | `{r['id']}` | ({r['tx']:.0f}, {r['ty']:.0f}) | {r['contact']} | "
                   f"{r['planned_z']:.0f} | {r['dxy']:.1f} | {r['carry']} | {r['bin']} | **{r['outcome']}** | "
                   f"{r['dur']:.1f} | {r['warn']} |")
    ok = [r for r in rows if r["outcome"] == "placed"]
    if rows:
        out += ["", f"**Summary:** {len(ok)} of {len(rows)} picks placed; mean time per pick "
                f"{sum(r['dur'] for r in rows) / len(rows):.1f} s; contact z (actual) "
                f"{min(r['contact_z'] for r in rows):.1f}–{max(r['contact_z'] for r in rows):.1f} mm vs planned "
                f"{rows[0]['planned_z']:.0f} mm; xy difference target → actual ≤ {max(r['dxy'] for r in rows):.1f} mm."]
    text = "\n".join(out) + "\n"
    open(os.path.join(run, "analysis.md"), "w").write(text)
    print(text)


def append_csv(run, rows):
    path = os.path.join(REPO, "lab9", "eval", "runs.csv")
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow([r["t_start"], "extended", os.path.basename(run), "2 auto sort", r["id"], f"{r['color']} {r['shape']}",
                        "", "", f"{r['tx']:.0f}", f"{r['ty']:.0f}", r["bin"], r["outcome"], "", f"{r['dur']:.1f}",
                        "runs/" + os.path.basename(run), f"contact flange {r['contact']}; carry {r['carry']}; {r['warn']}"])
    print(f"appended {len(rows)} rows to {path}")


def plot(run, rows, day):
    import cv2, numpy as np, rosbag2_py
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from rclpy.serialization import deserialize_message
    from sensor_msgs.msg import JointState
    from std_msgs.msg import String
    rd = rosbag2_py.SequentialReader()
    rd.open(rosbag2_py.StorageOptions(uri=os.path.join(run, "bag"), storage_id="mcap"), rosbag2_py.ConverterOptions("cdr", "cdr"))
    t_js, q, pump = [], [], []
    while rd.has_next():
        topic, data, t = rd.read_next()
        if topic == "/joint_states":
            t_js.append(t / 1e9); q.append(np.degrees(deserialize_message(data, JointState).position))
        elif topic == "/pump_controller":
            pump.append((t / 1e9, deserialize_message(data, String).data))
    t_js, q = np.array(t_js), np.array(q); T0 = t_js[0]
    fig, ax = plt.subplots(figsize=(11, 4.2))
    for j in range(6):
        ax.plot(t_js - T0, q[:, j], lw=1.2, label=f"J{j + 1}")
    on = None
    for t, s in pump:
        if s == "on":
            on = t
        elif s == "off" and on is not None:
            ax.axvspan(on - T0, t - T0, color="tab:green", alpha=0.15); on = None
    starts = [epoch(day, r["t_start"]) - T0 for r in rows]
    for x0, r in zip(starts, rows):
        ax.axvline(x0, color="k", ls=":", lw=1); ax.text(x0 + 1, 160, r["id"].replace("_1", ""), fontsize=8)
    if rows:
        ax.set_xlim(starts[0] - 10, min(t_js[-1] - T0, starts[-1] + rows[-1]["dur"] + 15))
    ax.set_ylim(-160, 190); ax.grid(alpha=0.3); ax.legend(ncol=6, fontsize=8, loc="lower right")
    ax.set_xlabel(f"time (s) from {hm(T0)}"); ax.set_ylabel("joint angle (deg)")
    ax.set_title(f"{os.path.basename(run)}: joint angles, pump on = green (straight lines = no joint states while executing)")
    fig.tight_layout(); fig.savefig(os.path.join(run, "joints_pump.png"), dpi=130)
    snaps = sorted(glob.glob(os.path.join(run, "snapshots", "*.jpg")))
    if snaps and rows:
        st = lambda f: epoch(day, f"{os.path.basename(f)[0:2]}:{os.path.basename(f)[2:4]}:{os.path.basename(f)[4:6]}")
        near = lambda t: min(snaps, key=lambda f: abs(st(f) - t))
        a = cv2.imread(near(epoch(day, rows[0]["t_start"]) - 2))
        b = cv2.imread(near(epoch(day, rows[-1]["t_start"]) + rows[-1]["dur"] + 5))
        for img, txt in ((a, f"start {rows[0]['t_start']}"), (b, "after the last pick")):
            cv2.putText(img, txt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        cv2.imwrite(os.path.join(run, "start_end.jpg"), np.hstack([a, b]), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"wrote {os.path.join(run, 'joints_pump.png')} and start_end.jpg")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", help="run folder, e.g. lab9/eval/runs/2026-10-09_1537_sort_test6")
    ap.add_argument("--start", required=True, help="HH:MM:SS, local time")
    ap.add_argument("--end", required=True, help="HH:MM:SS, local time")
    ap.add_argument("--hover-m", type=float, help="robot.hover_m used in the run (default: from lab9.yaml)")
    ap.add_argument("--no-csv", action="store_true", help="do not append to lab9/eval/runs.csv")
    ap.add_argument("--plot", action="store_true", help="also joints_pump.png + start_end.jpg (needs the bag)")
    a = ap.parse_args()
    day = os.path.basename(os.path.normpath(a.run))[:10]
    hover_m = a.hover_m if a.hover_m is not None else yaml.safe_load(open(CONFIG))["robot"]["hover_m"]
    t0, t1 = epoch(day, a.start), epoch(day, a.end)
    rows = analyse(a.run, t0, t1, hover_m)
    report(a.run, rows, t0, t1)
    if not a.no_csv:
        append_csv(a.run, rows)
    if a.plot:
        plot(a.run, rows, day)


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# Lab 9 evidence for one run (Lab PC). Never moves the robot: it only records topics and copies log files.
#
#   record_run.sh bag <name>              before a run: record joint states, pump and planning-scene topics
#                                         (small, no images) until Ctrl+C
#   record_run.sh collect <name> [min]    after a run: copy the ROS logs (Lab PC + Pi controller), vision frames and
#                                         vision_*.log of the last <min> minutes (default 30), write timeline.txt
#                                         (events with times + time per pick) and a notes.md template
#
# Everything goes to ~/mycobot-project/lab9/eval/runs/<YYYY-MM-DD_HHMM>_<name>/ ; "collect" reuses the folder of a
# "bag <name>" started in the same window. Then add one line per pick to lab9/eval/runs.csv (run_dir = that folder).
set -euo pipefail

REPO=${LAB9_REPO:-$HOME/mycobot-project}   # LAB9_REPO only for testing
RUNS=$REPO/lab9/eval/runs
FRAMES=$REPO/pp_moveit_ws/src/lab9_pick_place/frames
cmd=${1:-}; name=${2:-}; min=${3:-30}
[[ -z "$cmd" || -z "$name" ]] && { sed -n '2,11p' "$0"; exit 1; }
mkdir -p "$RUNS"

run_dir() {   # newest folder of this name from the last <min> minutes, else a new one
    local d
    d=$(find "$RUNS" -maxdepth 1 -type d -name "*_$name" -mmin -"$min" 2>/dev/null | sort | tail -1)
    [[ -n "$d" ]] && echo "$d" || echo "$RUNS/$(date +%Y-%m-%d_%H%M)_$name"
}

case "$cmd" in
bag)
    dir=$(run_dir); mkdir -p "$dir"
    echo "recording to $dir/bag (Ctrl+C to stop)"
    ros2 bag record -o "$dir/bag" /joint_states /pump_controller /collision_object /attached_collision_object
    ;;

collect)
    dir=$(run_dir); mkdir -p "$dir/logs" "$dir/frames"
    # Lab PC: logs of the Lab 9 and course nodes (vision, brain, camera, MoveIt)
    while IFS= read -r f; do
        if [[ $(basename "$f") == move_group_* ]] || \
           grep -qE '\[(vision_lab9|mycobot_brain_lab9|vision|mycobot_brain|image_publisher)\]' "$f" 2>/dev/null; then
            cp "$f" "$dir/logs/"
        fi
    done < <(find ~/.ros/log -maxdepth 1 -name '*.log' -size +0 -mmin -"$min")
    # Pi: controller logs (course controller or controller_lab9, both log as [controller])
    mkdir -p "$dir/logs_pi"
    ssh -o ConnectTimeout=5 cobot "cd ~/.ros/log && find . -maxdepth 1 -name '*.log' -size +0 -mmin -$min \
        | xargs -r grep -l '\[controller\]' | xargs -r tar cz" 2>/dev/null | tar xz -C "$dir/logs_pi" 2>/dev/null \
        || echo "note: Pi controller logs not copied (Pi not reachable?)"
    # frames saved with key s, and vision logs saved with tee
    find "$FRAMES" -maxdepth 1 -name '*.png' -mmin -"$min" -exec cp {} "$dir/frames/" \; 2>/dev/null || true
    find "$REPO/lab9/eval" -maxdepth 1 -name 'vision_*.log' -mmin -"$min" -exec cp {} "$dir/" \; 2>/dev/null || true

    # timeline: key events with local times; time per pick (brain_lab9: scene refresh -> dropped / placed;
    # course brain: cube coordinates requested for the pick -> "in the bin")
    python3 - "$dir" > "$dir/timeline.txt" <<'PY'
import datetime, glob, os, re, sys
d = sys.argv[1]
KEY = re.compile(r"planning scene|picked|dropped into bin|placed|sequence stopped|MoveIt error|could not reach|"
                 r"cube coordinates:|picked up!|in the bin!|placed on top|not detected|execution failed|Rejoice")
STAMP = re.compile(r"\[(\d{10}\.\d+)\] \[([^\]]+)\]: (.*)")
events = []
for f in glob.glob(os.path.join(d, "logs*", "*.log")):
    for line in open(f, errors="replace"):
        m = STAMP.search(line)
        if m and KEY.search(m.group(3)):
            events.append((float(m.group(1)), m.group(2), m.group(3).strip()))
events.sort()
fmt = lambda t: datetime.datetime.fromtimestamp(t).strftime("%H:%M:%S")
print("# events (local time, node, message)")
for t, node, msg in events:
    print(f"{fmt(t)}  {node:22s} {msg[:150]}")
print("\n# time per pick (s)")
start = None
for t, node, msg in events:
    if "planning scene" in msg or "cube coordinates:" in msg:
        start = start or t
    elif start and ("dropped into bin" in msg or "in the bin!" in msg or "placed" in msg):
        print(f"{fmt(start)} -> {fmt(t)}  {t - start:6.1f} s  {msg[:80]}")
        start = None
    elif "sequence stopped" in msg:
        print(f"{fmt(start or t)} -> {fmt(t)}  stopped: {msg[:80]}")
        start = None
PY
    [[ -f "$dir/notes.md" ]] || cat > "$dir/notes.md" <<EOF
# Run $(basename "$dir")

- System: original (course brain + controller) / extended (lab9_pick_place)
- Scene (objects, colours, shapes, ruler positions in mm):
- Menu selections and bins:
- Outcome per pick (picked / placed / missed / failed) and miss in mm:
- Observations, limitations:
- Photos / video (file names):
EOF
    echo "$(date '+%Y-%m-%d %H:%M') | $name | $(ls "$dir/logs" | wc -l) Lab PC logs, $(ls "$dir/logs_pi" 2>/dev/null | wc -l) Pi logs, $(ls "$dir/frames" | wc -l) frames | runs/$(basename "$dir")/" \
        >> "$REPO/lab9/eval/README.md"
    echo "collected into $dir"; tail -n +1 "$dir/timeline.txt" | sed -n '/# time per pick/,$p'
    ;;

*)  sed -n '2,11p' "$0"; exit 1 ;;
esac

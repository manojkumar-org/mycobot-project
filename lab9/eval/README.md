# Lab 9 evidence (`lab9/eval/`)

Everything recorded in the lab for `pp_moveit_ws/src/lab9_pick_place/LAB9_REPORT.md`. Nothing here moves the robot.

| File / folder | What | Written by | Report section |
|---|---|---|---|
| `queries.csv` | `/get_object` answers: existing / absent / several | `lab9_eval_logger.py query <scene>` | §3.4 |
| `features.csv` | C, fill, vertices per detected object | `lab9_eval_logger.py features <log> --scene <scene>` | §3.2, §3.3 |
| `vision_<scene>.log` | vision output (`objects: … C … fill … v …`) | `ros2 run lab9_pick_place vision_lab9 2>&1 \| tee lab9/eval/vision_<scene>.log` | §3 |
| `ground_truth.csv` | taped spots on the plate, measured with a ruler from the robot base centre (mm) | by hand, once per plate/marker setup | §3.3, §4.3 (true positions) |
| `runs.csv` | **one line per pick**: system (original / extended), scene, mode, selection, true and vision position, bin, outcome, miss, time | by hand after each pick (time from `timeline.txt`) | §2.2, §4.3 |
| `runs/<date_time>_<name>/` | per run: `logs/` (Lab PC nodes), `logs_pi/` (controller), `frames/`, `bag/`, `timeline.txt` (events + time per pick), `notes.md` | `solutions/lab9_real_hardware/record_run.sh` | Appendix A |
| `runs/<run>/analysis.md`, `joints_pump.png`, `start_end.jpg` | per pick: target vs actual contact, carry pose, outcome, time; joint/pump plot; before/after image | `solutions/lab9_real_hardware/lab9_analyse_run.py <run> --start HH:MM:SS --end HH:MM:SS [--plot] [--no-csv]` (also appends `runs.csv`) | §4.3, slides |
| `runs/<run>/snapshots/` | camera frame every 2 s (raw data, gitignored, in the export zip) | `solutions/lab9_real_hardware/lab9_snapshots.py <run>/snapshots 2.0` | slides (time-lapse) |
| frames (`lab9_annotated_*`, `lab9_raw_*`) | annotated / raw images, key `s` in the vision window | `vision_lab9` | §3.3, Appendix A |

The frames stay in `pp_moveit_ws/src/lab9_pick_place/frames/` (next to the report); `record_run.sh collect` copies the
ones of a run into its folder.

## One run, step by step (Lab PC, `deactivate; source ~/rosenv9.sh` in every terminal)

1. Before the run, terminal 3: `solutions/lab9_real_hardware/record_run.sh bag <name>` (e.g. `part0_sort`, `ext_sort`).
2. Run as in `LAB9_RUN_STEPS.txt` (C = Part 0, D = final system). Press `s` in the vision window for each scene.
3. After the run: Ctrl+C the bag, then `solutions/lab9_real_hardware/record_run.sh collect <name>` (same name).
   It prints the time per pick.
4. `lab9_analyse_run.py <run> --start … --end … --plot` writes `analysis.md` + plots and one `runs.csv` row per pick
   (fill the ruler position and miss by hand); fill `notes.md`; take a photo/video of the arm if useful.
5. Raw data (`bag/`, `snapshots/`, `logs*/`, run `frames/`, `lab9_raw_*.png`) is gitignored: copy it into an export zip
   (as `~/lab9_export_2026-10-09.zip`) to keep it.

`runs.csv` columns: `system` = `original` or `extended`; `outcome` = `placed` / `picked_not_placed` / `missed` /
`failed_plan` / `not_detected`; `miss_mm` = distance from the nozzle to the object centre at the pick (ruler), empty if
not measurable; `duration_s` = time per pick from `timeline.txt`.

## Run index (appended by `record_run.sh collect`)

date time | name | contents | folder
---|---|---|---
2026-10-09 15:01 | sort_test | 6 Lab PC logs, 2 Pi logs, 2 frames | runs/2026-10-09_1458_sort_test/
2026-10-09 15:16 | sort_test2 | 4 Lab PC logs, 1 Pi logs, 2 frames | runs/2026-10-09_1514_sort_test2/
2026-10-09 15:22 | sort_test3 | 5 Lab PC logs, 2 Pi logs, 6 frames | runs/2026-10-09_1519_sort_test3/
2026-10-09 15:32 | sort_test4 | 6 Lab PC logs, 2 Pi logs, 8 frames | runs/2026-10-09_1522_sort_test4/
2026-10-09 15:40 | sort_test6 | 5 Lab PC logs, 1 Pi logs, 14 frames | runs/2026-10-09_1537_sort_test6/

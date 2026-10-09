# Analysis of 2026-10-09_1522_sort_test4 (window 15:22:30–15:26:02)

Sources: brain log (targets, events), Pi controller log (actual flange position), vision log (object still on the plate
4 s after the drop = not picked). Contact = first controller position after `pump on` (end of the straight descent).

| # | start | object | target (mm) | contact flange (mm) | planned contact z | xy diff | carry above bin | bin | outcome | time (s) | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 15:24:07 | `red_cube_1` | (220, 35) | (222.1, 40.9, 118.2) | 106 | 6.3 | z 0.166, pitch 3.14 (vertical) | red | **placed** | 19.4 |  |
| 2 | 15:24:39 | `yellow_cube_1` | (151, 10) | (152.7, 15.7, 116.4) | 106 | 5.9 | z 0.166, pitch 2.80 (TILTED), after 6 failed plans | yellow | **placed** | 50.3 | MoveIt error code 99999 |
| 3 | 15:25:38 | `blue_cylinder_1` | (201, -39) | (204.8, -32.7, 116.8) | 106 | 7.4 | z 0.166, pitch 3.14 (vertical) | blue | **placed** | 18.2 | cartesian path only 0 % feasible; straight descent into the bin not feasible: releasing at the carry level |

**Summary:** 3 of 3 picks placed; mean time per pick 29.3 s (placed only: 29.3 s); contact z (actual) 116.4–118.2 mm vs planned 106 mm; xy difference target→actual ≤ 7.4 mm.

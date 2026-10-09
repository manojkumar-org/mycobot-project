# Analysis of 2026-10-09_1537_sort_test6 (15:37:10–15:40:35)

Sources: brain log (targets, events), Pi controller log (actual flange position), vision log (object still on
the plate 4 s after the drop = not placed). Contact = first controller position after `pump on`.

| # | start | object | target (mm) | contact flange (mm) | planned contact z | xy diff | carry above bin | bin | outcome | time (s) | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 15:38:32 | `red_cube_1` | (166, -11) | (168.7, -5.5, 117.0) | 106 | 6.1 | z 0.166, pitch 3.14 (vertical) | red | **placed** | 21.3 |  |
| 2 | 15:39:09 | `yellow_cube_1` | (188, 46) | (188.9, 51.2, 117.6) | 106 | 5.3 | z 0.166, pitch 3.14 (vertical) | yellow | **placed** | 19.4 |  |
| 3 | 15:39:35 | `blue_cylinder_1` | (236, -20) | (239.4, -15.2, 118.3) | 106 | 5.9 | z 0.166, pitch 3.14 (vertical) | blue | **placed** | 24.2 |  |

**Summary:** 3 of 3 picks placed; mean time per pick 21.6 s; contact z (actual) 117.0–118.3 mm vs planned 106 mm; xy difference target → actual ≤ 6.1 mm.

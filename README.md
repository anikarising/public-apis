# FlyWire Qualification Challenge

This repository contains a verified constructive solution for the FlyWire
Qualification Challenge. The submitted circuit is a directed induced out-star
shared by three datasets:

- `FAFB`
- `MAOL`
- `MCNS`

The matched circuit has `N = 1999` neurons. Row 1 is the source neuron in each
dataset, and rows 2-1999 are matched leaves. In each selected dataset, the
source has directed edges to every selected leaf, there are no reverse source
edges, there are no directed edges among selected leaves, and no selected neuron
has a self-loop.

## Main files

- `outputs/flywire_solution.csv` - headerless challenge solution CSV with three
  columns (`FAFB`, `MAOL`, `MCNS`) and 1999 matched neuron rows.
- `outputs/verification.json` - verification result produced from the raw edge
  lists.
- `outputs/matching_summary.json` - construction summary and selected centers.
- `report/research_note.md` - one-page research note.
- `report/figures/identified_out_star_network.svg` - network graph
  visualization of the verified circuit.
- `report/codex_3d_viewer_helper.txt` - Codex 3D Viewer helper link and FAFB
  root ID notes.

## Reproduce

Place the five raw edge-list CSV files in `data/raw/`, keep them in
`/Users/nafiul_khalid/Downloads`, or set `FLYWIRE_DATA_DIR` to their directory.
Expected filenames are listed in `data/README.md`.

Run:

```bash
python3 src/find_star_solution.py --target-n 1999
python3 src/verify_solution.py
python3 src/make_report_assets.py
```

The solver uses only Python standard-library modules.

## Method summary

A directed induced out-star is a valid weakly connected directed induced
subgraph. For a fixed center neuron, candidate leaves are unilateral outgoing
neighbors of the center. A leaf-conflict graph is built where two candidate
leaves conflict if either directed edge exists between them. Any independent set
in that conflict graph gives a valid induced out-star.

The script uses high-yield centers found during exploration in `FAFB`, `MAOL`,
and `MCNS`, applies a seeded minimum-current-degree greedy independent-set
heuristic to choose leaves, then truncates all three stars to the same size. The
verifier independently rescans the raw edge lists and compares the induced
directed edge sets under the CSV row correspondence.

Verification result:

```json
{
  "n": 1999,
  "directed_edge_count": 1998,
  "isomorphic_induced_subgraphs": true,
  "weakly_connected": true,
  "matches_out_star_pattern": true,
  "selected_self_loop_counts": {
    "FAFB": 0,
    "MAOL": 0,
    "MCNS": 0
  }
}
```

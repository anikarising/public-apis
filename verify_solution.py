#!/usr/bin/env python3
"""Verify that a submitted solution CSV defines isomorphic induced subgraphs."""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import deque
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIRS = [
    PROJECT_ROOT / "data" / "raw",
    Path("/Users/nafiul_khalid/Downloads"),
]

DATASET_FILES = {
    "BANC": "banc_626_edge_list.csv",
    "FAFB": "fafb_783_edge_list.csv",
    "MANC": "manc_1.2.1_edge_list.csv",
    "MAOL": "maol_1.1_edge_list.csv",
    "MCNS": "mcns_0.9_edge_list.csv",
}


def resolve_input(filename: str) -> Path:
    env_dir = os.environ.get("FLYWIRE_DATA_DIR")
    search_dirs = ([Path(env_dir)] if env_dir else []) + DEFAULT_DATA_DIRS
    for directory in search_dirs:
        path = directory / filename
        if path.exists():
            return path
    searched = ", ".join(str(d) for d in search_dirs)
    raise FileNotFoundError(f"Could not find {filename}; searched: {searched}")


def read_solution(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    if not rows:
        raise ValueError("Solution CSV is empty")
    if all(value in DATASET_FILES for value in rows[0]):
        headers = rows[0]
        body = rows[1:]
    else:
        headers = ["FAFB", "MAOL", "MCNS"]
        body = rows
    if len(headers) != 3:
        raise ValueError(f"Expected exactly 3 dataset columns, found {len(headers)}")
    if not body:
        raise ValueError("Solution CSV contains no matched neuron rows")
    for line_number, row in enumerate(body, start=2):
        if len(row) != 3:
            raise ValueError(f"Line {line_number}: expected 3 values, found {len(row)}")
    return headers, body


def induced_edges(dataset: str, matched_ids: list[str]) -> tuple[set[tuple[int, int]], int]:
    filename = DATASET_FILES[dataset]
    path = resolve_input(filename)
    index = {neuron_id: i for i, neuron_id in enumerate(matched_ids)}
    if len(index) != len(matched_ids):
        raise ValueError(f"{dataset}: duplicate neuron IDs in solution column")

    edges: set[tuple[int, int]] = set()
    selected_loops = 0
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            source = row["source neuron id"].strip()
            target = row["target neuron id"].strip()
            if source not in index or target not in index:
                continue
            if source == target:
                selected_loops += 1
                continue
            edges.add((index[source], index[target]))

    return edges, selected_loops


def is_weakly_connected(node_count: int, edges: set[tuple[int, int]]) -> bool:
    adjacency = [[] for _ in range(node_count)]
    for source, target in edges:
        adjacency[source].append(target)
        adjacency[target].append(source)

    seen = {0}
    queue: deque[int] = deque([0])
    while queue:
        node = queue.popleft()
        for neighbor in adjacency[node]:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return len(seen) == node_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "solution",
        nargs="?",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "flywire_solution.csv",
        help="Solution CSV to verify.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "verification.json",
        help="Path for a machine-readable verification report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    headers, rows = read_solution(args.solution)
    node_count = len(rows)

    edge_sets: dict[str, set[tuple[int, int]]] = {}
    loop_counts: dict[str, int] = {}
    for column_index, dataset in enumerate(headers):
        if dataset not in DATASET_FILES:
            raise ValueError(f"Unknown dataset column: {dataset}")
        ids = [row[column_index] for row in rows]
        edge_sets[dataset], loop_counts[dataset] = induced_edges(dataset, ids)

    reference_dataset = headers[0]
    reference_edges = edge_sets[reference_dataset]
    isomorphic = all(edge_sets[dataset] == reference_edges for dataset in headers[1:])
    weakly_connected = is_weakly_connected(node_count, reference_edges)
    expected_star_edges = {(0, i) for i in range(1, node_count)}
    is_out_star = reference_edges == expected_star_edges

    report = {
        "solution": str(args.solution),
        "datasets": headers,
        "n": node_count,
        "directed_edge_count": len(reference_edges),
        "isomorphic_induced_subgraphs": isomorphic,
        "weakly_connected": weakly_connected,
        "matches_out_star_pattern": is_out_star,
        "selected_self_loop_counts": loop_counts,
        "edge_counts_by_dataset": {dataset: len(edges) for dataset, edges in edge_sets.items()},
    }

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2) + "\n")

    print(json.dumps(report, indent=2))
    if not (isomorphic and weakly_connected and is_out_star and all(v == 0 for v in loop_counts.values())):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

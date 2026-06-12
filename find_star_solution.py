#!/usr/bin/env python3
"""Construct a certified three-dataset induced out-star solution.

The challenge asks for the largest directed induced subgraph shared across at
least three connectome snapshots. Exact maximum common induced subgraph search
is not tractable at this scale, so this script constructs a large, easy-to-audit
common motif: one source neuron connected to many leaves, with no reverse edges
and no edges among leaves. Any three such stars of equal size are mutually
isomorphic as directed induced subgraphs.
"""

from __future__ import annotations

import argparse
import csv
import heapq
import json
import os
import random
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIRS = [
    PROJECT_ROOT / "data" / "raw",
    Path("/Users/nafiul_khalid/Downloads"),
]

DATASETS = {
    "FAFB": {
        "filename": "fafb_783_edge_list.csv",
        "center": "720575940628908548",
        "orientation": "out",
    },
    "MAOL": {
        "filename": "maol_1.1_edge_list.csv",
        "center": "10046",
        "orientation": "out",
    },
    "MCNS": {
        "filename": "mcns_0.9_edge_list.csv",
        "center": "10157",
        "orientation": "out",
    },
}


def resolve_input(filename: str) -> Path:
    """Find an edge-list file without requiring raw data in the repository."""

    env_dir = os.environ.get("FLYWIRE_DATA_DIR")
    search_dirs = ([Path(env_dir)] if env_dir else []) + DEFAULT_DATA_DIRS
    for directory in search_dirs:
        path = directory / filename
        if path.exists():
            return path
    searched = ", ".join(str(d) for d in search_dirs)
    raise FileNotFoundError(f"Could not find {filename}; searched: {searched}")


def load_graph(
    path: Path,
) -> tuple[DefaultDict[str, set[str]], DefaultDict[str, set[str]], int, set[str]]:
    """Load a directed graph and record nodes with self-loops."""

    out: DefaultDict[str, set[str]] = defaultdict(set)
    incoming: DefaultDict[str, set[str]] = defaultdict(set)
    nodes: set[str] = set()
    loop_nodes: set[str] = set()

    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            source = row["source neuron id"].strip()
            target = row["target neuron id"].strip()
            nodes.add(source)
            nodes.add(target)
            if source == target:
                loop_nodes.add(source)
                continue
            out[source].add(target)
            incoming[target].add(source)

    for node in nodes:
        out.setdefault(node, set())
        incoming.setdefault(node, set())

    return out, incoming, len(nodes), loop_nodes


def build_conflict_graph(candidates: set[str], out: DefaultDict[str, set[str]]) -> dict[str, set[str]]:
    """Conflict graph on leaves.

    Two leaves conflict when either directed edge exists between them in the
    original graph. An independent set in this graph is therefore a valid leaf
    set for an induced star.
    """

    candidate_set = set(candidates)
    conflict = {node: set() for node in candidate_set}
    for source in sorted(candidate_set):
        for target in out.get(source, ()):
            if target in candidate_set and target != source:
                conflict[source].add(target)
                conflict[target].add(source)
    return conflict


def greedy_dynamic_independent_set(conflict: dict[str, set[str]], seed: int) -> list[str]:
    """Minimum-current-degree greedy independent set with seeded tie breaks."""

    rng = random.Random(seed)
    remaining = set(conflict)
    degree = {node: len(neighbors) for node, neighbors in conflict.items()}
    heap = [(degree[node], rng.random(), node) for node in sorted(conflict)]
    heapq.heapify(heap)
    selected: list[str] = []

    while heap:
        heap_degree, _, node = heapq.heappop(heap)
        if node not in remaining:
            continue
        if heap_degree != degree[node]:
            heapq.heappush(heap, (degree[node], rng.random(), node))
            continue

        selected.append(node)
        to_remove = sorted(conflict[node] & remaining)
        to_remove.append(node)

        for removed in to_remove:
            if removed not in remaining:
                continue
            remaining.remove(removed)
            for neighbor in sorted(conflict[removed]):
                if neighbor in remaining:
                    degree[neighbor] -= 1
                    heapq.heappush(heap, (degree[neighbor], rng.random(), neighbor))

    return selected


def find_star(
    dataset_name: str,
    config: dict[str, str],
    target_leaves: int,
    max_seeds: int,
) -> tuple[list[str], dict[str, object]]:
    """Find a large induced out-star/in-star around a fixed center."""

    path = resolve_input(config["filename"])
    out, incoming, node_count, loop_nodes = load_graph(path)

    center = config["center"]
    orientation = config["orientation"]
    if orientation == "out":
        candidates = set(out[center] - incoming[center])
    elif orientation == "in":
        candidates = set(incoming[center] - out[center])
    else:
        raise ValueError(f"Unsupported orientation: {orientation}")
    candidates.discard(center)
    candidates.difference_update(loop_nodes)
    if center in loop_nodes:
        raise RuntimeError(f"{dataset_name} center {center} has a self-loop")

    conflict = build_conflict_graph(candidates, out)
    conflict_edges = sum(len(neighbors) for neighbors in conflict.values()) // 2

    best: list[str] = []
    best_seed: int | None = None
    for seed in range(max_seeds):
        leaves = greedy_dynamic_independent_set(conflict, seed)
        if len(leaves) > len(best):
            best = leaves
            best_seed = seed
        if len(best) >= target_leaves:
            break

    if len(best) < target_leaves:
        raise RuntimeError(
            f"{dataset_name} produced only {len(best)} leaves; need {target_leaves}."
        )

    summary = {
        "dataset": dataset_name,
        "input_file": str(path),
        "node_count": node_count,
        "self_loop_node_count_excluded": len(loop_nodes),
        "center": center,
        "orientation": orientation,
        "candidate_leaf_count": len(candidates),
        "leaf_conflict_edges": conflict_edges,
        "best_leaf_count_found": len(best),
        "best_n_found": len(best) + 1,
        "best_seed": best_seed,
        "selected_leaf_count": target_leaves,
    }

    return best[:target_leaves], summary


def write_solution(
    output_csv: Path,
    selected: dict[str, tuple[str, list[str]]],
    include_header: bool,
) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    headers = list(selected)
    row_count = len(next(iter(selected.values()))[1]) + 1

    with output_csv.open("w", newline="") as handle:
        writer = csv.writer(handle)
        if include_header:
            writer.writerow(headers)
        writer.writerow([selected[name][0] for name in headers])
        for index in range(row_count - 1):
            writer.writerow([selected[name][1][index] for name in headers])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-n",
        type=int,
        default=1999,
        help="Number of matched neurons to write, including the center row.",
    )
    parser.add_argument(
        "--max-seeds",
        type=int,
        default=120,
        help="Maximum greedy tie-break seeds to try per dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "flywire_solution.csv",
        help="Output CSV path. Default is headerless for challenge submission.",
    )
    parser.add_argument(
        "--include-header",
        action="store_true",
        help="Write a dataset-name header row before matched IDs.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "matching_summary.json",
        help="Output JSON summary path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target_leaves = args.target_n - 1
    if target_leaves < 1:
        raise ValueError("--target-n must be at least 2")

    selected: dict[str, tuple[str, list[str]]] = {}
    summaries: list[dict[str, object]] = []

    for dataset_name, config in DATASETS.items():
        leaves, summary = find_star(dataset_name, config, target_leaves, args.max_seeds)
        selected[dataset_name] = (config["center"], leaves)
        summaries.append(summary)
        print(
            f"{dataset_name}: selected {target_leaves} leaves "
            f"(best found {summary['best_leaf_count_found']}, seed {summary['best_seed']})"
        )

    write_solution(args.output, selected, args.include_header)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(
            {
                "target_n": args.target_n,
                "motif": "directed induced out-star",
                "datasets": summaries,
                "notes": [
                    "Neurons with self-loops are excluded from the selected motif.",
                    "Rows after the first row are interchangeable leaves of the star.",
                ],
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Wrote {args.output}")
    print(f"Wrote {args.summary}")


if __name__ == "__main__":
    main()

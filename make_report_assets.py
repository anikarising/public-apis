#!/usr/bin/env python3
"""Create static report assets from the verified solution CSV."""

from __future__ import annotations

import csv
import math
import textwrap
from pathlib import Path
from urllib.parse import quote_plus


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOLUTION = PROJECT_ROOT / "outputs" / "flywire_solution.csv"
FIGURE_DIR = PROJECT_ROOT / "report" / "figures"


def read_solution() -> tuple[list[str], list[list[str]]]:
    with SOLUTION.open(newline="") as handle:
        rows = list(csv.reader(handle))
    if rows[0] == ["FAFB", "MAOL", "MCNS"]:
        return rows[0], rows[1:]
    return ["FAFB", "MAOL", "MCNS"], rows


def make_network_svg(headers: list[str], rows: list[list[str]]) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output = FIGURE_DIR / "identified_out_star_network.svg"
    n = len(rows)
    leaves = n - 1
    size = 980
    center = size / 2
    radius = 405
    leaf_radius = 2.1 if leaves > 1000 else 3.0

    edge_parts: list[str] = []
    node_parts: list[str] = []
    for i in range(1, n):
        angle = 2 * math.pi * (i - 1) / leaves
        x = center + radius * math.cos(angle)
        y = center + radius * math.sin(angle)
        edge_parts.append(
            f'<line x1="{center:.2f}" y1="{center:.2f}" x2="{x:.2f}" y2="{y:.2f}" '
            'stroke="#7d8b99" stroke-width="0.42" stroke-opacity="0.34" />'
        )
        node_parts.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{leaf_radius}" '
            'fill="#2f6f8f" fill-opacity="0.82" />'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" role="img" aria-labelledby="title desc">
  <title id="title">Verified FlyWire shared induced out-star</title>
  <desc id="desc">One source neuron connected to {leaves} leaves; no reverse or leaf-to-leaf edges in FAFB, MAOL, or MCNS.</desc>
  <rect width="{size}" height="{size}" fill="#f8faf9" />
  <circle cx="{center:.2f}" cy="{center:.2f}" r="{radius + 28}" fill="none" stroke="#d4dce1" stroke-width="1.2" />
  {"".join(edge_parts)}
  {"".join(node_parts)}
  <circle cx="{center:.2f}" cy="{center:.2f}" r="15" fill="#b73535" stroke="#ffffff" stroke-width="3" />
  <text x="{center:.2f}" y="{center - 28:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="19" fill="#22313a">N = {n} directed induced out-star</text>
  <text x="{center:.2f}" y="{center + 42:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#3c4b55">center -> {leaves} leaves; no other selected directed edges</text>
  <text x="24" y="{size - 28}" font-family="Arial, sans-serif" font-size="13" fill="#3c4b55">Datasets: {", ".join(headers)}</text>
</svg>
"""
    output.write_text(svg)


def make_codex_helpers(headers: list[str], rows: list[list[str]]) -> None:
    fafb_index = headers.index("FAFB")
    fafb_ids = [row[fafb_index] for row in rows]
    center = fafb_ids[0]
    sample_ids = fafb_ids[:25]
    query = " || ".join(f"root_id == {cell_id}" for cell_id in sample_ids)
    sample_url = "https://codex.flywire.ai/app/view_3d?dataset=fafb&query=" + quote_plus(query)

    all_ids_path = PROJECT_ROOT / "report" / "fafb_matched_neuron_ids.txt"
    all_ids_path.write_text("\n".join(fafb_ids) + "\n")

    helper = f"""FAFB Codex 3D visualization helper

Verified center neuron:
{center}

Sample Codex 3D Viewer URL, center plus first 24 leaves:
{sample_url}

All {len(fafb_ids)} FAFB matched root IDs are in:
report/fafb_matched_neuron_ids.txt

For the full set, open Codex -> 3D Viewer with dataset FAFB and paste/upload the IDs from that file. Codex may ask to sample or confirm before rendering a large query.
"""
    (PROJECT_ROOT / "report" / "codex_3d_viewer_helper.txt").write_text(helper)


def make_report_snippet(headers: list[str], rows: list[list[str]]) -> None:
    snippet = f"""Selected datasets: {", ".join(headers)}
Matched neurons: {len(rows)}
Directed induced edges per dataset: {len(rows) - 1}
Motif: directed out-star. Row 1 is the source neuron; every other row is a leaf.

Verification command:
python3 src/verify_solution.py
"""
    wrapped = "\n".join(textwrap.wrap(snippet, width=88, replace_whitespace=False))
    (PROJECT_ROOT / "report" / "result_summary.txt").write_text(wrapped + "\n")


def main() -> None:
    headers, rows = read_solution()
    make_network_svg(headers, rows)
    make_codex_helpers(headers, rows)
    make_report_snippet(headers, rows)
    print(f"Wrote {FIGURE_DIR / 'identified_out_star_network.svg'}")
    print(f"Wrote {PROJECT_ROOT / 'report' / 'codex_3d_viewer_helper.txt'}")
    print(f"Wrote {PROJECT_ROOT / 'report' / 'fafb_matched_neuron_ids.txt'}")


if __name__ == "__main__":
    main()

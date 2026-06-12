# Research Note: Shared Directed Out-Star Circuit

**Selected datasets.** `FAFB`, `MAOL`, and `MCNS`. The submitted CSV identifies
`N = 1999` matched neurons forming the same directed induced out-star in all
three datasets. In FAFB the source neuron is `720575940628908548`; it has
directed edges to 1998 selected leaves. Within the selected induced subgraph
there are no reverse source edges, no leaf-to-leaf edges, and no selected
self-loops. The same edge pattern is verified in MAOL with source `10046` and in
MCNS with source `10157`.

**Network visualization.** See
`report/figures/identified_out_star_network.svg`. The red center is the source
neuron; blue peripheral nodes are the leaves. The figure intentionally uses the
full 1999-node circuit rather than a sampled subgraph, so the biological detail
comes from the verified topology rather than readable node labels.

**Codex 3D mesh visualization.** I selected FAFB for morphology inspection
because Codex publicly documents FAFB v783 and supports 3D Neuroglancer views for
queried root IDs. A ready-to-open sample link for the source plus 24 leaves is in
`report/codex_3d_viewer_helper.txt`, and the full FAFB root-ID list is in
`report/fafb_matched_neuron_ids.txt`. Codex notes that its 3D Viewer renders
queried cells in Neuroglancer, while full mesh downloads are not served directly
from Codex and should use Meshparty when needed.

**Interpretation.** This solution is best interpreted as a large conserved
topological motif, not as a claimed homologous cell-type circuit. The edge lists
do not include cell type, neurotransmitter, compartment, or synapse-count
metadata, and the optimization explicitly ignores weights. The motif nevertheless
has a biologically meaningful shape: a single high-output neuron broadcasting to
many selected downstream partners that are mutually disconnected at the edge-list
threshold. A plausible hypothesis is that each selected source is a broad
projection or integrator-like neuron whose downstream partners can be sampled as
an approximately independent efferent fan-out. The absence of selected
leaf-to-leaf edges should be treated as a property of this induced subset, not as
evidence that the downstream population is globally independent.

**Limitations.** The construction maximizes a certified lower bound rather than
proving global optimality for the maximum common induced subgraph problem. Exact
search is computationally infeasible at these graph sizes, so I prioritized a
large, exactly verifiable, weakly connected structure. The verifier rescans the
raw edge lists and confirms identical induced directed edge sets across the
three CSV columns.

**References.**

- Codex FAQ: datasets, search attributes, 3D Viewer, graph model, and mesh-download guidance. https://codex.flywire.ai/faq
- Dorkenwald, S., Matsliah, A., Sterling, A. R. et al. "Neuronal wiring diagram of an adult brain." *Nature* 634, 124-138 (2024). https://www.nature.com/articles/s41586-024-07558-y
- Schlegel, P., Yin, Y., Bates, A. S. et al. "Whole-brain annotation and multi-connectome cell typing of Drosophila." *Nature* 634, 139-152 (2024). https://www.nature.com/articles/s41586-024-07686-5

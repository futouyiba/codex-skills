---
name: d2-diagram-harness
description: Build or improve YAML/JSON-source-driven D2 diagram generation harnesses. Use when Codex needs to create maintainable diagram pipelines that generate .d2, render SVG/PNG with the d2 CLI, validate graph structure, iterate on layout readability, or convert hand-drawn/requirements-driven architecture, product, system, or design diagrams into reproducible D2 outputs.
---

# D2 Diagram Harness

Use this skill to build a maintainable D2 diagram pipeline, not a one-off diagram. The default pattern is:

```text
structured source data -> generate .d2 -> render SVG/PNG -> inspect image -> adjust source/generator -> validate
```

## Workflow

1. Preserve source of truth outside the generated D2.
   - Use `diagram-source/*.yaml` or JSON-compatible YAML when dependencies should stay minimal.
   - Keep generated files in `generated/`.
   - Keep scripts in `scripts/`.

2. Separate diagram semantics from rendering.
   - Source files define nodes, edges, layout intent, styles, and metadata.
   - `scripts/generate_d2.py` translates source data into D2.
   - D2 output is generated, not hand-maintained.

3. Choose the right D2 level of detail.
   - Prefer section-level containers plus child labels for overview diagrams.
   - Avoid drawing every child-node dependency in D2; D2 auto-layout often turns dense graphs into long, tangled layouts.
   - Draw only the edges that explain the reading order and key causality.

4. Render and visually inspect.
   - Run `d2 generated/name.d2 generated/name-d2.svg`.
   - Convert SVG to PNG with `sips`, `rsvg-convert`, or another available renderer.
   - Inspect the PNG before declaring success.

5. Iterate with constraints.
   - If the graph becomes too wide, reduce edge count or group nodes into containers.
   - If lines imply the wrong causality, connect from the specific child node, not the parent container.
   - If one group is more important, use heavier stroke/fill and weaken secondary nodes.

6. Add validation.
   - Check required nodes and edges exist.
   - Check forbidden edges are absent.
   - Check generated D2 compiles when `d2` is available.

## Recommended Files

```text
diagram-source/
  overview.nodes.yaml
  overview.edges.yaml
  overview.meta.yaml
scripts/
  generate_d2.py
  validate_diagram.py
generated/
  overview.d2
  overview-d2.svg
  overview-d2.png
```

For source-driven diagrams, copy or adapt `scripts/d2_harness_template.py` from this skill.

## D2 Layout Guidance

For management/product/system overview diagrams, use this shape:

```text
A top intent / stages
  ↓
optional intermediate decomposition layer
  ↓
B anchor / control metrics
  ↓
C/D/E main modules + G cross-cutting modifiers
  ↓
F bottom result / plan / ledger / outcome layer
```

Use containers for major blocks:

```d2
direction: down

A: "Top Layer" {
  direction: right
  A1: "Item 1"
  A2: "Item 2"
}

B: "Anchor Metrics" {
  direction: right
  B1: "Primary"
  B2: "Secondary"
}

A -> B: "drives"
B.B1 -> C: "specific causal link"
```

Use child-specific edges when the requirement says a concrete metric or subnode is the source of causality:

```d2
B.revenue_speed -> Output: "drives output"
B.cost_speed -> Cost: "drives cost"
B.accumulation_time -> Access: "sets pacing"
```

## Styling Rules

- Highlight primary anchors with stronger stroke and warmer fill.
- Weak secondary anchors with pale fill and thinner stroke.
- Use dashed edges for modifiers, constraints, or indirect effects.
- Use dashed boxes for tentative or not-yet-quantified modules.
- Keep labels short; D2 native text wrapping is limited and long labels stretch the diagram.
- Prefer concise Chinese labels over multiline Markdown labels when PNG export uses macOS `sips`; Markdown/block labels can render poorly in non-browser converters.

## Python Environment

Use a virtual environment for Python tools that need third-party packages. Do not install Python packages into system Python or user site-packages unless the user explicitly asks.

Recommended project-local setup:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install PyYAML
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" "${CODEX_HOME:-$HOME/.codex}/skills/d2-diagram-harness"
```

For one-off skill validation, a temporary venv under `/private/tmp` is also acceptable. Keep virtual environments out of the skill folder and do not commit or bundle them as skill resources.

## Rendering Commands

Use local project D2 first when present:

```bash
./.bin/d2 generated/overview.d2 generated/overview-d2.svg
sips -s format png generated/overview-d2.svg --out generated/overview-d2.png
```

Otherwise use system D2:

```bash
d2 generated/overview.d2 generated/overview-d2.svg
```

If `d2` is missing and network is available, install it in the project rather than assuming global availability:

```bash
GOBIN="$PWD/.bin" go install oss.terrastruct.com/d2@v0.7.1
```

If Go proxy access fails, try a configured regional proxy only after user approval if network escalation is required.

## References

- Read `references/d2-overview-patterns.md` for the reusable overview-diagram pattern and common failure modes.

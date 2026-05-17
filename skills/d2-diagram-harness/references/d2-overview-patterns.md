# D2 Overview Diagram Patterns

## Good Fit For D2

- Overview diagrams with 5-10 major blocks.
- Containers with short child labels.
- A small number of causality edges.
- Dashed modifier relationships.
- Generated diagrams where layout may be approximate but reproducible.

## Poor Fit For D2

- Dense dependency graphs with many child-to-child edges.
- Precise 16:9 presentation layouts requiring exact coordinates.
- Long multiline labels rendered through non-browser SVG converters.
- Diagrams where every resource/module pair is connected.

Use draw.io/SVG generation for precise placement, and D2 for discussion/overview variants.

## Recommended Overview Pattern

Use a layered structure:

```text
Top goal/stage layer
Intermediate decomposition layer, optional
Anchor/control metric layer
Main modules and cross-cutting modifiers
Outcome/planning/ledger layer
```

Example D2 skeleton:

```d2
direction: down

A: "阶段 / 等阶目标" {
  direction: right
  A1: "新手期"
  A2: "成长期"
}

AB: "小阶段体验目标" {
  direction: right
  AB1: "新手目标"
  AB2: "成长目标"
}

B: "小阶段锚点指标" {
  direction: right
  B1: "RTP"
  B2: "积累标准时间"
  B3: "收益速度"
  B4: "消耗速度"
}

A -> AB: "拆分小阶段"
AB -> B: "决定锚点指标"
B.B3 -> C: "收益速度驱动"
B.B4 -> D: "消耗速度驱动"
```

## Iteration Checklist

- The title of each major container communicates its role without reading children.
- Key causal edges originate from the specific child node when appropriate.
- Primary anchors are visually stronger than secondary anchors.
- Cross-cutting relationships use dashed edges.
- The bottom layer is an outcome/result layer, not a dumping ground for every resource.
- The generated PNG is visually inspected, not just compiled.

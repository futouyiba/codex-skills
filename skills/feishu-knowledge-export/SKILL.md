---
name: feishu-knowledge-export
description: Use when exporting Feishu/Lark Docs or Wiki pages into an Agent-friendly knowledge package with Markdown text, image/table/diagram assets, resource summaries, a manifest, and ChatGPT Project upload guidance. Also use when the user says 飞书导出, 导出飞书, 飞书知识包, or asks in Chinese to export a Feishu document.
---

# Feishu Knowledge Export

Use this skill when the user wants to turn important Feishu/Lark documents into durable Markdown knowledge packages for Codex, ChatGPT Projects, or other agents.

The goal is not only "Feishu to Markdown". The goal is a package that supports progressive reading:

- `doc.md` contains the readable text plus short resource summaries.
- `assets/` contains images, diagrams, exported tables, and original visual resources.
- Whiteboards/boards are exported as structured resources when permissions allow: metadata Markdown, node JSON, and a Mermaid logic sketch.
- `manifest.json` tells an agent where each resource is, what it is, and when to open it.
- `chatgpt-project-instructions.md` explains how to use the package after uploading files to a ChatGPT Project.

## Default Workflow

1. If the input is a Feishu/Lark URL, try the bundled script in `export` mode. It uses `feishu-docx` when available.
2. If the input is an already-exported Markdown file or directory, use `package` mode.
3. Inspect `doc.md`, `manifest.json`, and the asset count.
4. If image summaries are placeholders, improve the high-value ones by opening the image files and updating `doc.md`/`manifest.json`.
5. For ChatGPT Projects, upload `doc.md`, `manifest.json`, `chatgpt-project-instructions.md`, and only the important assets first.

## Commands

If a separately maintained exporter app exists, point the skill entrypoint at it with:

```bash
export FEISHU_KNOWLEDGE_EXPORTER_SCRIPT="/path/to/FeishuKnowledgeExporterApp/scripts/feishu_knowledge_export.py"
```

Otherwise use the bundled skill-local implementation:

```bash
python3 scripts/feishu_knowledge_export.py export "<FEISHU_OR_LARK_URL>" -o ./exported-doc
python3 scripts/feishu_knowledge_export.py package ./existing-export -o ./knowledge-pack
```

When called through the skill entrypoint, it defaults to `--multimodal-alt --vision-detail high`. Feishu export defaults to `--board-mode all` in the shared exporter, so whiteboard image and node metadata are requested. If `OPENAI_API_KEY` is available, local raster images are sent to the OpenAI vision model for better alt text and resource summaries. If no key is available, or if images are remote/SVG/unavailable, the exporter falls back to context-based summaries.

If running outside the skill directory, call either:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/feishu-knowledge-export/scripts/feishu_knowledge_export.py" export "<URL>" -o ./exported-doc --project-mode
python3 "$FEISHU_KNOWLEDGE_EXPORTER_SCRIPT" export "<URL>" -o ./exported-doc --project-mode
```

Useful options:

- `--title "Name"`: override document title.
- `--source-url "URL"`: preserve the source URL when packaging an existing export.
- `--project-mode`: also optimize guidance for ChatGPT Project upload.

## Output Contract

The exported package must use this shape:

```text
exported-doc/
  doc.md
  manifest.json
  chatgpt-project-instructions.md
  assets/
    fig-001-name.png
    table-001.md
    table-001.csv
```

`manifest.json` resource fields:

- `id`: stable resource id, such as `fig-001` or `table-001`.
- `type`: `image`, `diagram`, `table`, `remote_image`, `attachment`, or `unknown`.
- `path`: local path relative to package root when available.
- `source`: original Markdown URL/path or Feishu source reference.
- `summary`: one-sentence resource digest.
- `open_when`: short list of reasons to inspect the full resource.

## Resource Summary Rules

Keep the main document readable without forcing every visual/table into context.

For images and diagrams:

```markdown
![Short factual alt text](./assets/fig-001-arch.svg)

Resource summary (`fig-001`): One sentence explaining what the resource contributes.
Open when: need exact labels, arrows, numbers, small text, or layout-specific details.
```

For tables:

```markdown
Table summary (`table-001`): 12 rows x 5 columns. Open the attached table when exact row values, column names, or formulas matter.
```

Use concise summaries in `doc.md`; put structured details in `manifest.json`.

## Quality Gate

Before considering the export done, verify:

- `doc.md` exists and is readable.
- Every local Markdown image path points to an existing file.
- `manifest.json` exists and has a resource entry for every copied image and extracted table.
- Feishu whiteboards, when accessible, produce `board-xxx.metadata.md`, `board-xxx.nodes.json`, and `board-xxx.mermaid.md` resources.
- Tables are not replaced by screenshots when Markdown/CSV extraction is possible.
- Mermaid code blocks remain fenced as `mermaid`.
- Complex diagrams retain the original image/SVG even if a Mermaid approximation is added.
- ChatGPT Project guidance explains that relative paths are references, not guaranteed automatic attachment links.

## When ChatGPT Project Is the Target

Do not assume ChatGPT will automatically resolve `./assets/foo.png` from inside `doc.md`.

Package for upload like this:

1. Upload `doc.md`.
2. Upload `manifest.json`.
3. Upload `chatgpt-project-instructions.md`.
4. Upload only important assets first, because project file limits and retrieval behavior vary by plan.
5. If there are many visuals, create a compact PDF or select top assets instead of uploading everything.

Read `references/chatgpt-project.md` when the user asks about Project upload strategy, tradeoffs, or attachment discoverability.

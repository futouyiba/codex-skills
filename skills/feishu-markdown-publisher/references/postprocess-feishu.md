# Feishu Post-Processing Workflow

Use this reference after Markdown has been uploaded/imported into Feishu.

## Operating Principles

- Preserve the local Markdown file as canonical.
- Modify only blocks generated from explicit custom markers.
- Prefer deterministic block replacement over manual visual editing.
- After successful conversion, remove marker syntax from the Feishu document.

## Tool Selection

- Use `lark-doc` for reading, creating, and editing Feishu Docs/Docx content.
- Use `lark-drive` when the task is upload/import, file placement, title changes, or cloud-drive organization.
- Use `lark-whiteboard` only if the user explicitly wants diagrams converted into whiteboards instead of text drawing/Mermaid blocks.

If a Feishu API capability is not available in the existing CLI wrapper, use the closest documented Lark skill workflow first, then explain the remaining manual step precisely.

## Conversion Pass

1. Read the uploaded Feishu document and locate marker blocks.
   - Search for lines beginning with `:::callout`, `:::mermaid`, `:::decision`, `:::risk`, or `:::todo`.
   - Capture all content until the matching closing `:::`.

2. Convert `:::mermaid` blocks.
   - Extract the fenced Mermaid source.
   - Replace the imported marker/code-block region with a Feishu text drawing/Mermaid block when supported.
   - Insert the Mermaid source into the text drawing block as its diagram code.
   - Set the block display mode to chart-only / diagram-only by default so the published document shows the rendered diagram, not the source code.
   - The visible Feishu block title should come from `title`, if present.
   - Do not leave the Mermaid source as a normal code block unless API support is unavailable.
   - If the API exposes a "show code" or "display source" property, disable it unless the user explicitly requests visible code.

3. Convert callout-like blocks.
   - `callout type="info|note"` -> neutral highlight/callout.
   - `callout type="success"` and `decision status="accepted"` -> success/conclusion highlight.
   - `callout type="warning"` and `risk level="medium|high"` -> warning highlight.
   - `callout type="danger"` and `risk level="critical"` -> danger highlight.
   - Preserve the title as the first line or block title, depending on Feishu capabilities.

4. Convert TODO blocks.
   - Prefer a Feishu task/todo block if available and requested.
   - Otherwise convert to a visible callout labelled with owner and due date.

5. Clean up.
   - Remove opening and closing marker lines.
   - Remove redundant Markdown code fences around converted Mermaid diagrams.
   - Re-read the affected sections to verify block order and surrounding headings.

## Verification Checklist

- No raw custom marker lines remain in Feishu unless intentionally left as source text.
- Mermaid diagrams render as text drawings/Mermaid blocks, not plain code blocks.
- Mermaid text drawings are set to chart-only / diagram-only display unless the user requested source code visibility.
- High-signal blocks are rendered as Feishu callouts/highlights.
- Heading order is intact.
- The Markdown source still contains the original semantic markers.
- The final response names the Markdown source path and Feishu document URL/token.

## Failure Handling

If conversion cannot be fully automated:

- Keep the Feishu document readable.
- Report exact sections and marker types that need manual conversion.
- Do not delete source marker content until the rich block replacement exists.
- Recommend improving the post-processing wrapper only for repeated failures, not one-off documents.

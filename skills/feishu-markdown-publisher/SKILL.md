---
name: feishu-markdown-publisher
description: Markdown-first Feishu/Lark document publishing workflow for long design docs, specs, proposals, and knowledge docs. Use when the user says /飞书发布, 飞书发布, Markdown 发布飞书, Markdown-first 飞书发布, or asks Codex to draft/revise a Markdown source document, preserve it as the source of truth, upload/import it to Feishu/Lark Docs, then post-process custom semantic markers into Feishu rich blocks such as callouts/highlight blocks, Mermaid text drawings shown as chart-only diagrams, structured decision/risk blocks, and final document polish.
---

# Feishu Markdown Publisher

## Core Rule

Treat Markdown as the source of truth. Use Feishu as the published collaboration surface.

Do not directly author long-form design docs only inside Feishu unless the user explicitly asks for direct Feishu editing. For deep docs, first produce or update a Markdown file, then publish and post-process.

## Workflow

1. Draft or revise the Markdown source.
   - Use clear heading hierarchy, concise section names, stable anchors, and semantic markers for rich Feishu blocks.
   - Keep the Markdown readable even before publishing.
   - Read `references/markup-spec.md` when creating or reviewing custom markers.

2. Validate the Markdown before upload.
   - Check that every custom block is closed.
   - Check Mermaid syntax mentally or with local tooling if available.
   - Confirm the document can still be read without Feishu-only rendering.

3. Upload or import the Markdown to Feishu.
   - If the task involves real Feishu Docs operations, use the relevant Lark/Feishu skill, usually `lark-doc` for document creation/editing and `lark-drive` for upload/import.
   - Keep the local Markdown path and the Feishu document URL/token in the work log or final response.

4. Post-process Feishu blocks.
   - Read `references/postprocess-feishu.md` before modifying the live Feishu document.
   - Convert semantic markers into Feishu-native blocks.
   - Convert Mermaid marker blocks into Feishu text drawing/Mermaid blocks, not plain code blocks.
   - Set converted Mermaid text drawings to chart-only display by default, hiding the source code panel/text when Feishu supports that property.
   - Convert callout markers into Feishu highlight/callout blocks.
   - Remove marker syntax from the final Feishu document after conversion.

5. Final-check both sources.
   - The Markdown source must remain complete and canonical.
   - The Feishu document must be readable, with rich blocks rendered in the intended places.
   - If manual follow-up remains, list exact markers or sections that need attention.

## Marker Policy

Use semantic markers for intent, not visual implementation. Prefer a small controlled vocabulary:

- `:::callout type="..." title="..."` for Feishu highlight/callout blocks.
- `:::mermaid title="..."` for Feishu text drawing blocks.
- `:::decision` for design decisions.
- `:::risk level="..."` for risks and mitigations.
- `:::todo owner="..."` for follow-up items.

Do not invent new marker types unless the document needs a repeated semantic block not covered by the current vocabulary. If adding a marker, define it in `references/markup-spec.md` first.

## Source Of Truth Rules

- Prefer editing Markdown, then republishing or patching Feishu.
- If Feishu is edited manually after publishing, ask whether to sync the change back to Markdown before making further structural changes.
- Do not let Feishu-only formatting become the only place where important meaning exists.
- Keep raw Mermaid code in Markdown even after Feishu conversion.

## When To Use Direct Feishu Editing

Use direct Feishu editing only for:

- Short documents with little need for version control.
- Small post-publish corrections.
- Converting existing marker blocks after Markdown import.
- User-requested live collaboration edits.

For long design docs, return to the Markdown-first workflow.

## References

- `references/markup-spec.md`: marker grammar, examples, and authoring rules.
- `references/postprocess-feishu.md`: practical post-upload conversion procedure for Feishu rich blocks.

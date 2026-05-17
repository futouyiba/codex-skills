---
name: feishu-markdown-publisher
description: Markdown-first Feishu/Lark document publishing workflow for long design docs, specs, proposals, and knowledge docs. Use when the user says /飞书发布, 飞书发布, Markdown 发布飞书, Markdown-first 飞书发布, or asks Codex to draft/revise a Markdown source document, preserve it as the source of truth, maintain a top-of-document revision table for new vs updated documents, upload/import it to Feishu/Lark Docs, then post-process custom semantic markers into Feishu rich blocks such as callouts/highlight blocks, Mermaid text drawings shown as chart-only diagrams, structured decision/risk blocks, and final document polish.
---

# Feishu Markdown Publisher

## Core Rule

Treat Markdown as the source of truth. Use Feishu as the published collaboration surface.

Do not directly author long-form design docs only inside Feishu unless the user explicitly asks for direct Feishu editing. For deep docs, first produce or update a Markdown file, then publish and post-process.

## Workflow

1. Draft or revise the Markdown source.
   - Use clear heading hierarchy, concise section names, stable anchors, and semantic markers for rich Feishu blocks.
   - Add or update the opening revision table before the main content.
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

## Revision Table

Every Feishu-published Markdown design document should begin with a revision table before the main title or immediately after the title if the title must remain first.

Use this shape:

```markdown
| 版本 | 内容 | 编辑人 | 时间 |
| --- | --- | --- | --- |
| V1.0 | 创建文档 | 作者 | 20251223 |
| v1.1 | 加入0.2.2数据表相关信息 | 作者 | 20251229 |
| v1.2 | 更新基本思路流程图 | 作者 | 20260302 |
```

Smart update rules:

- If creating a new document with no prior revision history, insert `V1.0 / 创建文档 / <editor> / <today as YYYYMMDD>`.
- If revising an existing Markdown file that already has the table, append one row instead of rewriting history.
- If revising a Feishu document that already has a similar opening table, preserve existing rows and append the next version row.
- If the document has no revision table but the task is clearly an update to existing content, create the table with `V1.0 / 创建文档 / <editor> / <unknown or inferred original date>` when the original date is available; otherwise use `V1.0 / 创建文档 / <editor> / 待补充`, then append the current update row.
- Increment minor versions by default: `V1.0 -> v1.1 -> v1.2`. Use a major version bump only when the user explicitly asks or the document is fundamentally rewritten.
- Summarize the current change in `内容` with one concise Chinese phrase, such as `更新基本思路流程图`, `补充战斗数值说明`, or `加入0.2.2数据表相关信息`.
- Resolve `编辑人` in this order: user-provided editor name, existing table convention, `FEISHU_PUBLISH_EDITOR` environment variable, Git `user.name`, then `作者`. Use `待补充` only if the editor is truly unknown and a neutral placeholder is preferable.
- Use the current local date in `YYYYMMDD` format for the new row unless the user provides a specific date.
- Do not add a blank trailing row in Markdown. Feishu may visually show an empty row, but the Markdown source should stay clean.

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

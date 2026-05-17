---
name: feishu-publish
description: Chinese trigger alias for Markdown-first Feishu/Lark publishing. Use when the user says /飞书发布, 飞书发布, 飞书文档发布, Markdown 发布飞书, 上传飞书后处理, or asks in Chinese to publish a Markdown-first long design document to Feishu/Lark Docs, maintain the opening revision table for new vs updated documents, and then post-process Mermaid diagrams, callouts/highlights, decision blocks, risk blocks, TODOs, and other rich formatting. Delegate to $feishu-markdown-publisher.
---

# Feishu Publish Alias

This is a Chinese trigger alias for `$feishu-markdown-publisher`.

When the user says:

- `/飞书发布 <Markdown file or request>`
- `飞书发布 <Markdown file or request>`
- `Markdown 发布飞书`
- `飞书文档发布`
- `上传飞书后处理`

Use the Markdown-first publishing workflow:

1. Treat Markdown as the canonical source.
2. Add or update the opening revision table with columns `版本`, `内容`, `编辑人`, `时间`.
3. For new documents, create `V1.0 / 创建文档 / 斧头 / <YYYYMMDD>`; for updates, append the next minor version row with a concise Chinese change description.
4. Use semantic markers such as `:::callout`, `:::mermaid`, `:::decision`, `:::risk`, and `:::todo`.
5. Upload or import the Markdown into Feishu.
6. After upload, convert Mermaid blocks into Feishu text drawing/Mermaid blocks.
7. Set Mermaid text drawings to chart-only / diagram-only display by default so source code is hidden.
8. Convert callout, decision, risk, and todo markers into Feishu-native rich blocks.
9. Report the Markdown source path, Feishu document URL/token, and any remaining manual post-processing items.

Read and follow:

- `$feishu-markdown-publisher`
- `feishu-markdown-publisher/references/markup-spec.md`
- `feishu-markdown-publisher/references/postprocess-feishu.md`

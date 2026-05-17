---
name: feishu-export
description: Chinese trigger alias for Feishu/Lark knowledge export. Use when the user says 飞书导出, 导出飞书, 飞书知识包, or asks in Chinese to export Feishu/Lark Docs/Wiki into an Agent-friendly knowledge package. Delegate to $feishu-knowledge-export and do not use raw lark or feishu-docx CLI calls except through the exporter.
---

# 飞书导出

这是 `$feishu-knowledge-export` 的短中文别名。

当用户说：

- `飞书导出 <链接>`
- `导出飞书 <链接>`
- `飞书知识包 <链接>`
- `把这个飞书文档导出`

必须使用这套知识包导出器，而不是直接裸用 `lark` CLI、`feishu-docx` CLI 或只导出普通 Markdown。

## 执行命令

优先使用共享 App 项目里的脚本：

使用 skill 入口。它会委托到共享 App 项目，并默认追加 `--multimodal-alt --vision-detail high`：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/feishu-knowledge-export/scripts/feishu_knowledge_export.py" export "<FEISHU_OR_LARK_URL>" -o "<OUTPUT_DIR>" --project-mode
```

如果本地环境有 `OPENAI_API_KEY`，会调用多模态模型为本地图片生成更表意的 alt text 和摘要；如果没有 key、图片未下载成功或图片格式不支持，会自动回退到上下文摘要。

## 输出要求

输出必须是知识包结构：

```text
knowledge-pack/
  doc.md
  manifest.json
  docast.json
  chatgpt-project-instructions.md
  conversion-report.md
  assets/
```

导出后检查：

- `doc.md` 是否存在。
- `manifest.json` 是否记录图片、表格、附件。
- `assets/` 是否包含本地表格或图片资源。
- `conversion-report.md` 是否列出 `Degraded Resources`。

如果图片或画板无法下载，必须明确告诉用户哪些资源降级为 `remote_image`。

## 资料库索引维护

如果当前工作区存在 `knowledge-library/index.md`，导出完成后必须更新该索引：

- 新增一个资料包条目，写明 `Path`、`Use when`、`Important resources`。
- 从该资料包的 `manifest.json` 提取标题、资源数量、资源类型和 asset 路径。
- 索引只写路由信息，不复制正文长内容。
- 最终回复中说明索引是否已更新。

如果索引不存在，但用户表现出要长期积累资料包，应建议创建 `knowledge-library/index.md`。

默认要求画板结构化导出。飞书权限允许时，知识包应包含：

- `assets/board-xxx.metadata.md`
- `assets/board-xxx.nodes.json`
- `assets/board-xxx.mermaid.md`

如果画板图片下载失败但节点元数据成功，也算部分成功；需要在结果中说明“图片失败，结构元数据成功”。

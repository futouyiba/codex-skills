#!/usr/bin/env python3
"""Build Agent-friendly knowledge packages from Feishu/Lark Markdown exports."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}
VISION_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MD_IMAGE_RE = re.compile(r"(?<!`)!\[([^\]]*)\]\(([^)]+)\)")
RESOURCE_SUMMARY_RE = re.compile(
    r"\n{0,2}Resource summary \(`fig-\d+`\):[^\n]*\nOpen when:[^\n]*\n?",
    re.MULTILINE,
)
PIPE_TABLE_LINE_RE = re.compile(r"^\s*\|.*\|\s*$")
PIPE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
BOARD_DETAILS_RE = re.compile(
    r"<details>\s*<summary>📊 画板结构信息</summary>(.*?)</details>",
    re.DOTALL,
)
BOARD_UNAVAILABLE_RE = re.compile(r"<!--\s*画板\s+([A-Za-z0-9_-]+)\s+需要相应权限才能(?:下载|导出)\s*-->")


@dataclass
class Resource:
    id: str
    type: str
    path: str | None
    source: str
    summary: str
    open_when: list[str]


def slugify(value: str, fallback: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:48] or fallback


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def find_markdown_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path] if input_path.suffix.lower() in {".md", ".markdown"} else []
    return sorted(
        p for p in input_path.rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".markdown"}
    )


def choose_main_markdown(input_path: Path) -> Path:
    files = find_markdown_files(input_path)
    if not files:
        raise SystemExit(f"No Markdown files found in {input_path}")
    preferred_names = {"index.md", "doc.md", "README.md"}
    for name in preferred_names:
        for path in files:
            if path.name == name:
                return path
    return max(files, key=lambda p: p.stat().st_size)


def is_remote_ref(ref: str) -> bool:
    parsed = urlparse(ref)
    return parsed.scheme in {"http", "https"}


def strip_ref_decoration(ref: str) -> str:
    ref = ref.strip()
    if ref.startswith("<") and ref.endswith(">"):
        ref = ref[1:-1]
    return ref.split("#", 1)[0].split("?", 1)[0]


def resolve_local_ref(ref: str, base_dir: Path) -> Path | None:
    clean = unquote(strip_ref_decoration(ref))
    if not clean or is_remote_ref(clean):
        return None
    candidate = Path(clean)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate if candidate.exists() else None


def copy_asset(src: Path, assets_dir: Path, prefix: str, index: int, alt: str) -> Path:
    suffix = src.suffix.lower() or ".bin"
    name_hint = slugify(alt or src.stem, file_hash(src))
    dest_name = f"{prefix}-{index:03d}-{name_hint}{suffix}"
    dest = assets_dir / dest_name
    counter = 2
    while dest.exists() and src.resolve() != dest.resolve():
        dest_name = f"{prefix}-{index:03d}-{name_hint}-{counter}{suffix}"
        dest = assets_dir / dest_name
        counter += 1
    shutil.copy2(src, dest)
    return dest


def infer_image_type(path_or_ref: str, alt: str) -> str:
    text = f"{path_or_ref} {alt}".lower()
    if any(word in text for word in ["flow", "流程", "架构", "diagram", "arch", "canvas", "mermaid"]):
        return "diagram"
    return "image"


def plain_markdown(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`*_>#|~<>{}\[\]()-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_weak_alt(alt: str) -> bool:
    value = alt.strip().lower()
    if not value:
        return True
    weak_values = {"image", "img", "图片", "截图", "画板", "diagram", "fig", "figure"}
    if value in weak_values:
        return True
    return bool(re.fullmatch(r"(image|img|fig|figure|图片|截图)[-_ ]?\d*", value))


def extract_current_heading(text_before: str) -> str:
    for line in reversed(text_before.splitlines()):
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                return plain_markdown(heading)
    return ""


def remove_existing_resource_summaries(content: str) -> str:
    return RESOURCE_SUMMARY_RE.sub("\n", content)


def context_excerpt(text: str, max_chars: int = 96, take: str = "first") -> str:
    lines = []
    for line in text.splitlines():
        if "![" in line or PIPE_TABLE_LINE_RE.match(line):
            continue
        stripped = plain_markdown(line)
        if not stripped:
            continue
        if stripped.startswith("Resource summary") or stripped.startswith("Open when"):
            continue
        if stripped.startswith("Table summary"):
            continue
        if stripped in {"列表", "概念", "背景", "问题", "解决", "图", "图示"}:
            continue
        lines.append(stripped)
    selected = lines[:2] if take == "first" else lines[-2:]
    excerpt = "；".join(selected)
    return excerpt[:max_chars].rstrip("；,，。 ")


def build_image_context(content: str, start: int, end: int) -> dict[str, str]:
    before = content[:start]
    after = content[end:]
    return {
        "heading": extract_current_heading(before),
        "before": context_excerpt(before[-700:], take="last"),
        "after": context_excerpt(after[:700], take="first"),
    }


def meaningful_label(alt: str, ref: str, context: dict[str, str], resource_id: str) -> str:
    if not is_weak_alt(alt):
        return plain_markdown(alt)
    heading = context.get("heading") or ""
    after = context.get("after") or ""
    before = context.get("before") or ""
    if heading and after:
        return f"{heading}：{after[:42].rstrip('；,，。 ')}"
    if heading:
        return heading
    if after:
        return after[:54].rstrip("；,，。 ")
    if before:
        return before[-54:].lstrip("；,，。 ")
    stem = Path(strip_ref_decoration(ref)).stem
    return stem if stem else resource_id


def image_summary(resource_id: str, alt: str, ref: str, resource_type: str, context: dict[str, str]) -> str:
    label = meaningful_label(alt, ref, context, resource_id)
    heading = context.get("heading") or ""
    before = context.get("before") or ""
    after = context.get("after") or ""

    evidence_parts = []
    if heading:
        evidence_parts.append(f"所在章节为“{heading}”")
    if before:
        evidence_parts.append(f"前文提到“{before}”")
    if after:
        evidence_parts.append(f"后文提到“{after}”")

    if evidence_parts:
        if resource_type in {"diagram", "remote_image"}:
            return f"{label}。该图用于补充说明：{'；'.join(evidence_parts[:2])}。"
        return f"{label}。该图片用于补充说明：{'；'.join(evidence_parts[:2])}。"

    if resource_type == "diagram":
        return f"{label}。该图可能承载流程、结构、节点关系或关键视觉说明。"
    return f"{label}。该图片可能承载正文未完全展开的视觉信息。"


def image_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def parse_model_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def generate_multimodal_image_text(
    image_path: Path,
    context: dict[str, str],
    fallback_alt: str,
    model: str,
    detail: str,
    api_key: str | None,
) -> tuple[str, str] | None:
    if not api_key:
        return None
    if image_path.suffix.lower() not in VISION_IMAGE_EXTS:
        return None

    prompt = {
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": (
                    "你是文档转换器。请结合图片内容和附近正文，为 Markdown 图片生成准确、简短、表意的中文 alt text 和资源摘要。\n"
                    "要求：\n"
                    "- alt_text 不超过 60 个汉字，直接描述图片主要表达的意思，不要写“图片显示/图片名为”。\n"
                    "- summary 用 1-2 句说明图片提供的主要信息，包含图中的关键结构、趋势、数值或关系。\n"
                    "- 如果图片文字很小或不确定，要明确说哪些细节需要打开原图复核。\n"
                    "- 只输出 JSON：{\"alt_text\":\"...\",\"summary\":\"...\"}\n\n"
                    f"所在章节：{context.get('heading') or '未知'}\n"
                    f"图片前文：{context.get('before') or '无'}\n"
                    f"图片后文：{context.get('after') or '无'}\n"
                    f"现有 alt：{fallback_alt or '无'}"
                ),
            },
            {"type": "input_image", "image_url": image_data_url(image_path), "detail": detail},
        ],
    }
    payload = {
        "model": model,
        "input": [prompt],
        "temperature": 0.2,
        "max_output_tokens": 500,
    }
    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"Multimodal alt generation failed for {image_path}: {exc}", file=sys.stderr)
        return None

    text = data.get("output_text")
    if not text:
        chunks = []
        for item in data.get("output", []):
            for content_item in item.get("content", []):
                if content_item.get("type") in {"output_text", "text"}:
                    chunks.append(content_item.get("text", ""))
        text = "\n".join(chunks).strip()
    if not text:
        return None
    try:
        parsed = parse_model_json(text)
    except Exception as exc:
        print(f"Could not parse multimodal JSON for {image_path}: {exc}", file=sys.stderr)
        return None

    alt_text = plain_markdown(str(parsed.get("alt_text") or "")).strip()
    summary = plain_markdown(str(parsed.get("summary") or "")).strip()
    if not alt_text or not summary:
        return None
    return alt_text[:90].rstrip("；,，。 "), summary


def read_openai_api_key_from_keychain() -> str | None:
    try:
        result = subprocess.run(
            [
                "/usr/bin/security",
                "find-generic-password",
                "-s",
                "FeishuKnowledgeExporterApp",
                "-a",
                "OpenAI",
                "-w",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    key = result.stdout.strip()
    return key or None


def get_openai_api_key() -> str | None:
    return os.environ.get("OPENAI_API_KEY") or read_openai_api_key_from_keychain()


def rewrite_images(
    content: str,
    md_base_dir: Path,
    assets_dir: Path,
    start_index: int = 0,
    multimodal_alt: bool = False,
    vision_model: str = "gpt-4.1-mini",
    vision_detail: str = "high",
    openai_api_key: str | None = None,
) -> tuple[str, list[Resource], int]:
    resources: list[Resource] = []
    image_counter = start_index

    def replace(match: re.Match[str]) -> str:
        nonlocal image_counter
        alt = match.group(1).strip()
        ref = match.group(2).strip()
        image_counter += 1
        resource_id = f"fig-{image_counter:03d}"
        resource_type = infer_image_type(ref, alt)
        context = build_image_context(content, match.start(), match.end())

        local_src = resolve_local_ref(ref, md_base_dir)
        local_asset_path: Path | None = None
        if local_src and local_src.suffix.lower() in IMAGE_EXTS:
            dest = copy_asset(local_src, assets_dir, "fig", image_counter, alt)
            local_asset_path = dest
            rel_path = f"./assets/{dest.name}"
            source = str(local_src)
            path = f"assets/{dest.name}"
            new_ref = rel_path
        else:
            source = ref
            path = None
            new_ref = ref
            resource_type = "remote_image" if is_remote_ref(ref) else resource_type

        summary = image_summary(resource_id, alt, ref, resource_type, context)
        multimodal_result = None
        if multimodal_alt and local_asset_path:
            multimodal_result = generate_multimodal_image_text(
                local_asset_path,
                context,
                alt,
                model=vision_model,
                detail=vision_detail,
                api_key=openai_api_key,
            )
        if multimodal_result:
            display_alt, summary = multimodal_result
        else:
            display_alt = alt if not is_weak_alt(alt) else summary.split("。", 1)[0]
            display_alt = display_alt[:90].rstrip("；,，。 ")

        resources.append(
            Resource(
                id=resource_id,
                type=resource_type,
                path=path,
                source=source,
                summary=summary,
                open_when=[
                    "需要确认小字、标签、箭头方向、布局或视觉细节",
                    "正文摘要不足以支持精确判断",
                ],
            )
        )
        return (
            f"![{display_alt}]({new_ref})\n\n"
            f"Resource summary (`{resource_id}`): {summary}\n"
            "Open when: need exact labels, arrows, numbers, layout, or visual details."
        )

    content = remove_existing_resource_summaries(content)
    return MD_IMAGE_RE.sub(replace, content), resources, image_counter


def parse_pipe_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def parse_board_metadata_table(markdown: str) -> list[dict]:
    lines = [line for line in markdown.splitlines() if PIPE_TABLE_LINE_RE.match(line)]
    if len(lines) < 3:
        return []
    headers = parse_pipe_row(lines[0])
    nodes = []
    for line in lines[2:]:
        cells = parse_pipe_row(line)
        if not cells or cells[0] == "...":
            continue
        row = dict(zip(headers, cells))
        nodes.append(
            {
                "node_id": row.get("节点ID", ""),
                "type": row.get("类型", "unknown"),
                "position": row.get("位置", ""),
                "size": row.get("大小", ""),
                "text": row.get("文本内容", ""),
            }
        )
    return nodes


def board_digest(nodes: list[dict]) -> str:
    if not nodes:
        return "画板结构元数据已导出，但未解析到可读节点。"
    type_counts: dict[str, int] = {}
    texts = []
    for node in nodes:
        node_type = node.get("type") or "unknown"
        type_counts[node_type] = type_counts.get(node_type, 0) + 1
        text = str(node.get("text") or "").strip()
        if text and text != "-":
            texts.append(text)
    type_summary = "、".join(f"{k} {v} 个" for k, v in sorted(type_counts.items()))
    text_summary = "；".join(texts[:8])
    if text_summary:
        return f"画板包含 {len(nodes)} 个可解析节点（{type_summary}）。主要文本节点包括：{text_summary}。"
    return f"画板包含 {len(nodes)} 个可解析节点（{type_summary}），但节点文本较少或未暴露。"


def board_mermaid(nodes: list[dict]) -> str:
    text_nodes = [
        str(node.get("text") or "").strip()
        for node in nodes
        if str(node.get("text") or "").strip() and str(node.get("text") or "").strip() != "-"
    ]
    if not text_nodes:
        return "graph TD\n  A[画板节点元数据已导出]\n"
    lines = ["graph TD"]
    limited = text_nodes[:12]
    for idx, text in enumerate(limited, start=1):
        safe_text = text.replace('"', "'").replace("[", "(").replace("]", ")")
        lines.append(f'  N{idx}["{safe_text[:48]}"]')
    for idx in range(1, len(limited)):
        lines.append(f"  N{idx} --> N{idx + 1}")
    return "\n".join(lines) + "\n"


def extract_board_resources(content: str, assets_dir: Path, start_index: int = 0) -> tuple[str, list[Resource], int]:
    resources: list[Resource] = []
    board_counter = start_index

    def replace_details(match: re.Match[str]) -> str:
        nonlocal board_counter
        board_counter += 1
        board_id = f"board-{board_counter:03d}"
        body = match.group(1).strip()
        full_md = "<details>\n<summary>📊 画板结构信息</summary>\n\n" + body + "\n</details>\n"
        nodes = parse_board_metadata_table(body)
        digest = board_digest(nodes)

        metadata_path = assets_dir / f"{board_id}.metadata.md"
        nodes_path = assets_dir / f"{board_id}.nodes.json"
        mermaid_path = assets_dir / f"{board_id}.mermaid.md"
        write_text(metadata_path, full_md)
        write_text(nodes_path, json.dumps({"schema": "feishu-board-nodes@0.1", "nodes": nodes}, ensure_ascii=False, indent=2) + "\n")
        write_text(mermaid_path, "```mermaid\n" + board_mermaid(nodes) + "```\n")

        resources.extend(
            [
                Resource(
                    id=board_id,
                    type="board_metadata",
                    path=f"assets/{board_id}.metadata.md",
                    source="Feishu whiteboard node metadata rendered by feishu-docx",
                    summary=digest,
                    open_when=["需要查看画板节点类型、位置、尺寸或文本内容"],
                ),
                Resource(
                    id=f"{board_id}-nodes",
                    type="board_nodes_json",
                    path=f"assets/{board_id}.nodes.json",
                    source=board_id,
                    summary=f"{board_id} 的结构化节点 JSON。",
                    open_when=["需要程序化分析画板节点、位置、类型或文本"],
                ),
                Resource(
                    id=f"{board_id}-mermaid",
                    type="board_mermaid",
                    path=f"assets/{board_id}.mermaid.md",
                    source=board_id,
                    summary=f"{board_id} 的 Mermaid 逻辑草图；仅表达文本节点顺序，不保证完整还原画布布局。",
                    open_when=["需要快速查看画板逻辑骨架，且不要求视觉排版完全一致"],
                ),
            ]
        )
        return (
            f"Board summary (`{board_id}`): {digest}\n"
            f"Board assets: `assets/{board_id}.metadata.md`, `assets/{board_id}.nodes.json`, `assets/{board_id}.mermaid.md`"
        )

    content = BOARD_DETAILS_RE.sub(replace_details, content)

    def replace_unavailable(match: re.Match[str]) -> str:
        nonlocal board_counter
        board_counter += 1
        board_id = f"board-{board_counter:03d}"
        token = match.group(1)
        summary = f"飞书画板 {token} 因权限不足未能导出图片或节点元数据。"
        resources.append(
            Resource(
                id=board_id,
                type="board_unavailable",
                path=None,
                source=token,
                summary=summary,
                open_when=["需要在飞书中补充授权后重新导出，或手动下载画板图片/结构"],
            )
        )
        return f"Board summary (`{board_id}`): {summary}"

    content = BOARD_UNAVAILABLE_RE.sub(replace_unavailable, content)
    return content, resources, board_counter


def find_table_blocks(lines: list[str]) -> list[tuple[int, int]]:
    blocks: list[tuple[int, int]] = []
    i = 0
    while i < len(lines) - 1:
        if PIPE_TABLE_LINE_RE.match(lines[i]) and PIPE_SEPARATOR_RE.match(lines[i + 1]):
            start = i
            i += 2
            while i < len(lines) and PIPE_TABLE_LINE_RE.match(lines[i]):
                i += 1
            blocks.append((start, i))
        else:
            i += 1
    return blocks


def table_to_csv(rows: list[list[str]], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def extract_tables(content: str, assets_dir: Path, start_index: int = 0) -> tuple[str, list[Resource], int]:
    lines = content.splitlines()
    blocks = find_table_blocks(lines)
    if not blocks:
        return content, [], start_index

    resources: list[Resource] = []
    output: list[str] = []
    last = 0
    table_counter = start_index

    for start, end in blocks:
        table_counter += 1
        output.extend(lines[last:start])
        table_lines = lines[start:end]
        output.extend(table_lines)

        data_lines = [line for idx, line in enumerate(table_lines) if idx != 1]
        rows = [parse_pipe_row(line) for line in data_lines]
        col_count = max((len(row) for row in rows), default=0)
        row_count = max(len(rows) - 1, 0)
        resource_id = f"table-{table_counter:03d}"
        md_path = assets_dir / f"{resource_id}.md"
        csv_path = assets_dir / f"{resource_id}.csv"
        write_text(md_path, "\n".join(table_lines) + "\n")
        table_to_csv(rows, csv_path)

        summary = f"{row_count} data rows x {col_count} columns. Open the table asset when exact values or column names matter."
        output.extend(
            [
                "",
                f"Table summary (`{resource_id}`): {summary}",
                "",
            ]
        )
        resources.append(
            Resource(
                id=resource_id,
                type="table",
                path=f"assets/{resource_id}.md",
                source=f"Markdown table lines {start + 1}-{end}",
                summary=summary,
                open_when=[
                    "需要精确行列值、字段名、公式或完整表格上下文",
                    "需要将表格交给程序处理或二次分析",
                ],
            )
        )
        resources.append(
            Resource(
                id=f"{resource_id}-csv",
                type="table_csv",
                path=f"assets/{resource_id}.csv",
                source=f"Derived from {resource_id}",
                summary=f"CSV copy of {resource_id}.",
                open_when=["需要用电子表格或脚本处理该表格"],
            )
        )
        last = end

    output.extend(lines[last:])
    return "\n".join(output) + ("\n" if content.endswith("\n") else ""), resources, table_counter


def fence_marker(line: str) -> tuple[str, int] | None:
    stripped = line.lstrip()
    match = re.match(r"(`{3,}|~{3,})", stripped)
    if not match:
        return None
    marker = match.group(1)
    return marker[0], len(marker)


def process_markdown_content(
    content: str,
    md_base_dir: Path,
    assets_dir: Path,
    multimodal_alt: bool = False,
    vision_model: str = "gpt-4.1-mini",
    vision_detail: str = "high",
    openai_api_key: str | None = None,
) -> tuple[str, list[Resource]]:
    """Process only prose Markdown, leaving fenced examples untouched."""
    lines = content.splitlines(keepends=True)
    output_parts: list[str] = []
    prose_buffer: list[str] = []
    resources: list[Resource] = []
    fence_char: str | None = None
    fence_len = 0
    image_counter = 0
    table_counter = 0
    board_counter = 0

    def flush_prose() -> None:
        nonlocal prose_buffer, image_counter, table_counter, board_counter
        if not prose_buffer:
            return
        chunk = "".join(prose_buffer)
        chunk, image_resources, image_counter = rewrite_images(
            chunk,
            md_base_dir,
            assets_dir,
            image_counter,
            multimodal_alt=multimodal_alt,
            vision_model=vision_model,
            vision_detail=vision_detail,
            openai_api_key=openai_api_key,
        )
        chunk, board_resources, board_counter = extract_board_resources(chunk, assets_dir, board_counter)
        chunk, table_resources, table_counter = extract_tables(chunk, assets_dir, table_counter)
        resources.extend(image_resources)
        resources.extend(board_resources)
        resources.extend(table_resources)
        output_parts.append(chunk)
        prose_buffer = []

    for line in lines:
        marker = fence_marker(line)
        if marker:
            marker_char, marker_len = marker
            if fence_char is None:
                flush_prose()
                fence_char = marker_char
                fence_len = marker_len
            elif marker_char == fence_char and marker_len >= fence_len:
                fence_char = None
                fence_len = 0
            output_parts.append(line)
            continue

        if fence_char is not None:
            output_parts.append(line)
        else:
            prose_buffer.append(line)

    flush_prose()
    return "".join(output_parts), resources


def title_from_markdown(content: str, fallback: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or fallback
    return fallback


def build_project_instructions(title: str) -> str:
    return f"""# ChatGPT Project Instructions for {title}

Use `doc.md` as the primary readable source.

Use `manifest.json` as the resource index. When `doc.md` mentions a resource id such as `fig-001` or `table-002`, check the manifest for its file name, summary, and `open_when` guidance.

Relative paths in Markdown are resource identifiers. They are not guaranteed automatic attachment links inside ChatGPT Projects. If a referenced asset is not available in the uploaded project files, ask the user to upload that specific file by id/name.

Do not infer exact numbers, labels, arrows, or table values from a summary when the manifest says to open the asset for those details.
"""


def build_docast(title: str, source_url: str | None, resources: Iterable[Resource]) -> dict:
    return {
        "schema": "feishu-knowledge-export/docast-lite@0.1",
        "title": title,
        "source_url": source_url,
        "resources": [asdict(resource) for resource in resources],
    }


def package_markdown(
    input_path: Path,
    output_dir: Path,
    title: str | None,
    source_url: str | None,
    project_mode: bool,
    multimodal_alt: bool = False,
    vision_model: str = "gpt-4.1-mini",
    vision_detail: str = "high",
) -> None:
    main_md = choose_main_markdown(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    content = read_text(main_md)
    doc_title = title or title_from_markdown(content, main_md.stem)
    openai_api_key = get_openai_api_key()
    content, resources = process_markdown_content(
        content,
        main_md.parent,
        assets_dir,
        multimodal_alt=multimodal_alt,
        vision_model=vision_model,
        vision_detail=vision_detail,
        openai_api_key=openai_api_key,
    )

    header = [
        f"# {doc_title}",
        "",
        "<!-- Generated by feishu-knowledge-export. Use manifest.json as the resource index. -->",
        "",
    ]
    if content.lstrip().startswith("# "):
        final_doc = content
    else:
        final_doc = "\n".join(header) + content

    write_text(output_dir / "doc.md", final_doc)
    manifest = {
        "schema": "feishu-knowledge-export/manifest@0.1",
        "title": doc_title,
        "source_url": source_url,
        "main": "doc.md",
        "assets_dir": "assets",
        "resource_count": len(resources),
        "resources": [asdict(resource) for resource in resources],
        "notes": [
            "Resource summaries are lightweight digests. Open the referenced asset when exact visual/table details matter.",
            "Markdown relative paths may not become automatic attachment links in ChatGPT Projects; upload referenced assets explicitly.",
        ],
    }
    write_text(output_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    write_text(output_dir / "docast.json", json.dumps(build_docast(doc_title, source_url, resources), ensure_ascii=False, indent=2) + "\n")
    write_text(output_dir / "chatgpt-project-instructions.md", build_project_instructions(doc_title))

    report_lines = [
        f"# Conversion Report: {doc_title}",
        "",
        f"- Source Markdown: `{main_md}`",
        f"- Output directory: `{output_dir}`",
        f"- Resources indexed: {len(resources)}",
        f"- Project mode: {'yes' if project_mode else 'no'}",
        f"- Multimodal alt text: {'yes' if multimodal_alt and openai_api_key else 'no'}",
        f"- Vision model: `{vision_model}`" if multimodal_alt and openai_api_key else "- Vision model: not used",
        f"- Vision detail: `{vision_detail}`" if multimodal_alt and openai_api_key else "- Vision detail: not used",
        "",
        "## Resource Index",
        "",
    ]
    if resources:
        for resource in resources:
            report_lines.append(f"- `{resource.id}` ({resource.type}): {resource.path or resource.source}")
    else:
        report_lines.append("- No image or table resources detected.")
    degraded = [resource for resource in resources if not resource.path]
    if degraded:
        report_lines.extend(["", "## Degraded Resources", ""])
        for resource in degraded:
            report_lines.append(
                f"- `{resource.id}` ({resource.type}) was not saved locally; retained source reference: {resource.source}"
            )
    write_text(output_dir / "conversion-report.md", "\n".join(report_lines) + "\n")


def run_feishu_docx_export(url: str, temp_dir: Path, board_mode: str = "all") -> None:
    cmd = shutil.which("feishu-docx")
    if not cmd:
        local_cmd = Path(__file__).resolve().parents[1] / ".venv" / "bin" / "feishu-docx"
        if local_cmd.exists():
            cmd = str(local_cmd)
    if not cmd:
        raise SystemExit(
            "feishu-docx is not installed. Install/configure it first, or run package mode on an existing Markdown export.\n"
            "Expected setup: python3 -m venv .venv && .venv/bin/pip install feishu-docx && .venv/bin/feishu-docx auth"
        )
    command = [cmd, "export", url, "-o", str(temp_dir), "--table", "md"]
    if board_mode in {"metadata", "all"}:
        command.append("--export-board-metadata")
    subprocess.run(command, check=True)


def export_url(
    url: str,
    output_dir: Path,
    title: str | None,
    project_mode: bool,
    multimodal_alt: bool = False,
    vision_model: str = "gpt-4.1-mini",
    vision_detail: str = "high",
    board_mode: str = "all",
) -> None:
    with tempfile.TemporaryDirectory(prefix="feishu-export-") as tmp:
        temp_dir = Path(tmp)
        run_feishu_docx_export(url, temp_dir, board_mode=board_mode)
        package_markdown(
            temp_dir,
            output_dir,
            title=title,
            source_url=url,
            project_mode=project_mode,
            multimodal_alt=multimodal_alt,
            vision_model=vision_model,
            vision_detail=vision_detail,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export Feishu/Lark docs into Agent-friendly knowledge packages.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export a Feishu/Lark URL using feishu-docx, then package it.")
    export_parser.add_argument("url")
    export_parser.add_argument("-o", "--output", required=True)
    export_parser.add_argument("--title")
    export_parser.add_argument("--project-mode", action="store_true")
    export_parser.add_argument("--multimodal-alt", action="store_true", help="Use OpenAI vision to generate alt text for local raster images.")
    export_parser.add_argument("--vision-model", default=os.environ.get("OPENAI_VISION_MODEL", "gpt-4.1-mini"))
    export_parser.add_argument("--vision-detail", choices=["low", "high", "auto", "original"], default=os.environ.get("OPENAI_VISION_DETAIL", "high"))
    export_parser.add_argument("--board-mode", choices=["off", "image", "metadata", "all"], default="all", help="How to request Feishu whiteboard export. metadata/all enables node metadata extraction when permissions allow.")

    package_parser = subparsers.add_parser("package", help="Package an existing Markdown file/directory.")
    package_parser.add_argument("input")
    package_parser.add_argument("-o", "--output", required=True)
    package_parser.add_argument("--title")
    package_parser.add_argument("--source-url")
    package_parser.add_argument("--project-mode", action="store_true")
    package_parser.add_argument("--multimodal-alt", action="store_true", help="Use OpenAI vision to generate alt text for local raster images.")
    package_parser.add_argument("--vision-model", default=os.environ.get("OPENAI_VISION_MODEL", "gpt-4.1-mini"))
    package_parser.add_argument("--vision-detail", choices=["low", "high", "auto", "original"], default=os.environ.get("OPENAI_VISION_DETAIL", "high"))

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "export":
            export_url(
                args.url,
                Path(args.output),
                title=args.title,
                project_mode=args.project_mode,
                multimodal_alt=args.multimodal_alt,
                vision_model=args.vision_model,
                vision_detail=args.vision_detail,
                board_mode=args.board_mode,
            )
        elif args.command == "package":
            package_markdown(
                Path(args.input),
                Path(args.output),
                title=args.title,
                source_url=args.source_url,
                project_mode=args.project_mode,
                multimodal_alt=args.multimodal_alt,
                vision_model=args.vision_model,
                vision_detail=args.vision_detail,
            )
        else:
            parser.error(f"Unknown command: {args.command}")
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with exit code {exc.returncode}: {' '.join(exc.cmd)}", file=sys.stderr)
        return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

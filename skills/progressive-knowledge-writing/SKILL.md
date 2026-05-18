---
name: progressive-knowledge-writing
description: Use when the user says /资料写作, 资料写作, 渐进式读取, 渐进式资料读取, 知识包写作, 基于资料包写文档, or asks Codex to search exported Feishu knowledge packs, progressively read relevant files, reason deeply, preserve consistency, and interactively draft or edit Markdown/design documents.
---

# Progressive Knowledge Writing

Use this skill to help the user write or revise documents from a growing local library of exported Feishu knowledge packs.

Default stance: when this skill is triggered, assume the user wants the answer grounded in the existing knowledge packs unless they explicitly say not to use them.

Context is not a source of truth. Prior conversation may contain compressed, partial, or stale summaries of a pack. Use conversation context only as orientation; for substantive analysis, outlines, drafts, edits, conflict checks, or claims about existing material, refresh from the library index and relevant source files.

## Default Library

Start with the configured knowledge library:

```text
${KNOWLEDGE_LIBRARY_DIR:-./knowledge-library}/index.md
```

Read only when the task needs imported Markdown routing:

```text
${KNOWLEDGE_LIBRARY_DIR:-./knowledge-library}/abstracts.md
```

Use `canon/*.md` as compact current conclusions when the topic matches. Use `abstracts.md` as the routing layer only before opening imported Markdown long source files.

If the files are missing, search the current workspace for `knowledge-library/index.md`, `knowledge-library/abstracts.md`, and `feishu-knowledge-pack-*/manifest.json`.

## Workflow

1. Identify the user's target: new document, revision, outline, critique, synthesis, or diagram plan.
2. Inspect the current working context:
   - Run `git status --short` if the directory is a git repo.
   - If the user is editing an existing file, inspect relevant unstaged diffs before changing it.
   - Treat user edits as active design intent. Do not overwrite them casually.
3. Read `knowledge-library/index.md` first, even if the user did not explicitly mention a pack.
4. Prefer `knowledge-library/canon/*.md` when the index routes to a canon file; open imported Markdown only when the canon is insufficient.
5. Read `knowledge-library/abstracts.md` only when opening imported Markdown documents is necessary.
6. Select only the knowledge packs and imported Markdown sources relevant to the task. State the selected sources briefly. If no source appears relevant, say that clearly before proceeding from general reasoning.
7. For each selected pack:
   - Read `manifest.json` first.
   - Read or re-read targeted sections of `doc.md`; use `rg` to locate topics before opening long spans.
   - Open table assets only for exact fields, formulas, values, or comparison.
   - Open images or whiteboards only for diagrams, visual relationships, arrows, labels, or layout.
   - Check `conversion-report.md` if resources appear missing or degraded.
8. For each selected imported Markdown document:
   - Respect status labels in `abstracts.md`: read `canonical` and `source` first; open `historical`, `derived`, `implementation`, or `metadata-only` files only when their status matches the task.
   - Use the abstract to explain why it was selected.
   - Use `rg` or section headings to open only relevant spans before reading the full file.
   - Re-read exact source sections before making strong claims, resolving conflicts, or writing final prose.
9. Before drafting, perform a consistency pass:
   - Existing commitments: claims, terms, assumptions, formulas, module relationships, player-stage logic, and design goals already present in the packs.
   - Conflicts: contradictions between the requested direction and existing packs, or between selected packs.
   - Gaps: missing definitions, missing causal links, unsupported claims, values that require table lookup, or diagrams that need inspection.
   - Open decisions: questions the user likely needs to decide before the document can be final.
10. Produce the smallest useful writing step first: structure, thesis, section rewrite, conflict list, or patch.
11. For edits, prefer modifying the Markdown/document directly when the user asks for implementation. Summarize changed files and source packs used.
12. Keep a source note in substantial drafts, for example:
   `Source packs: 搏金设计; 《钓鱼战斗切片》表格说明文档.`

## Interaction Pattern

For deep writing tasks, do not jump straight to a full final document unless the user asks. Prefer cycles:

1. Diagnose: what the current material is trying to say.
2. Retrieve: which packs/sections matter.
3. Check consistency: conflicts, contradictions, missing assumptions, terminology drift, and unsupported leaps.
4. Draft: one section or a concise outline.
5. Edit: apply changes to the target file if requested.

Ask a question only when the target audience, document type, or edit target is genuinely ambiguous and cannot be inferred from local files.

## Source Refresh Policy

Use this policy instead of relying only on chat context:

- Always read the library index at the start of a `/资料写作` task, unless the user explicitly says not to use the library.
- Read matching `canon/*.md` summaries before long historical drafts.
- Read `abstracts.md` only before opening long imported Markdown sources.
- Read relevant pack manifests before making claims about what a pack contains.
- Re-read source sections when making or revising important arguments, checking conflicts, using exact terminology, or writing final prose.
- Re-open tables for exact values, fields, formulas, and comparisons even if a previous turn summarized them.
- Re-open diagrams/whiteboards when reasoning depends on arrows, grouping, hierarchy, or spatial relationships.
- It is acceptable to skip re-reading only for trivial follow-ups inside the same uninterrupted turn where the exact source text was just read and is still visible in the current context.

## Git-Aware Collaboration

When git is available:

- Use `git status --short` to notice user-created or user-edited files.
- Use `git diff -- <file>` to understand recent edits before editing a file.
- Do not revert user changes.
- If the user asks "看我改了什么" or similar, summarize the unstaged diff as their latest thinking before proposing edits.

When git is not available:

- Use file modified times, targeted reads, and direct comparison only if there is an obvious previous version.
- Recommend initializing git if the user wants reliable collaboration history.

## Diagram Guidance

For diagrams:

- First write the concept in text: nodes, relationships, direction, hierarchy, and unresolved questions.
- Use Mermaid in Markdown for flowcharts, causal maps, system relationships, and iteration loops.
- Use Feishu/Lark whiteboards only when the diagram needs manual spatial layout, visual grouping, or workshop-style collaboration.
- Keep the Markdown source as the durable version, then migrate or paste into Feishu after the structure stabilizes.

# Codex Skills

Reusable Codex skills managed as source, then installed into `~/.codex/skills`.

## Skills

- `d2-diagram-harness`: YAML/JSON-source-driven D2 diagram pipelines.
- `develop-web-game`: Web game development and Playwright testing loop.
- `feishu-docx`: Feishu document export workflow through `feishu-docx`.
- `feishu-export`: Chinese trigger alias for `飞书导出`, `导出飞书`, and `飞书知识包`.
- `feishu-knowledge-export`: Feishu/Lark knowledge package exporter.
- `feishu-markdown-publisher`: Markdown-first publishing workflow for long Feishu/Lark design documents.
- `feishu-publish`: Chinese trigger alias for `/飞书发布` and `飞书发布`.
- `noos-consume-handoff`: Consume NOOS handoffs.
- `noos-hub-launcher`: Launch and inspect local NOOS Hub.
- `noos-transfer-handoff`: Transfer NOOS handoffs.
- `playwright`: Terminal Playwright workflow helper.
- `progressive-knowledge-writing`: Progressive knowledge-pack writing workflow.
- `vercel-deploy`: Vercel deployment workflow.

## Local Install

```bash
./scripts/install.sh
```

The installer links each directory under `skills/` into `${CODEX_HOME:-$HOME/.codex}/skills`.
If a skill already exists as a real directory on this machine, adopt the repository copy with:

```bash
./scripts/install.sh --replace-existing
```

Existing directories are moved aside with a `.bak-YYYYMMDDHHMMSS` suffix before links are created.

## Validate

```bash
./scripts/validate.sh
```

## skills.sh Install

After this repository is pushed to GitHub, individual skills can be installed with:

```bash
npx skills add <owner>/<repo> --skill feishu-markdown-publisher
npx skills add <owner>/<repo> --skill feishu-publish
```

Or install another skill by replacing the `--skill` value with one of the names above.

The Chinese trigger phrase is:

```text
/飞书发布
飞书发布
```

## Publishing Notes

Before making the repository public, audit skills for:

- API keys, cookies, tokens, or local credentials.
- Internal company documents or private examples.
- Absolute local paths that will not exist on another machine.
- Tool assumptions that should be described as dependencies instead of hard-coded.

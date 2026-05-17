# Codex Skills

Reusable Codex skills managed as source, then installed into `~/.codex/skills`.

## Skills

- `feishu-markdown-publisher`: Markdown-first publishing workflow for long Feishu/Lark design documents.
- `feishu-publish`: Chinese trigger alias for `/飞书发布` and `飞书发布`.

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

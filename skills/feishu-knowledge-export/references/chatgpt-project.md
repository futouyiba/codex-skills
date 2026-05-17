# ChatGPT Project Packaging Notes

ChatGPT Projects can use uploaded project files as context, but a Markdown relative link such as `./assets/fig-001.png` should be treated as a human/agent reference, not a guaranteed automatic attachment binding.

## Reliable Pattern

Upload these files together:

1. `doc.md`
2. `manifest.json`
3. `chatgpt-project-instructions.md`
4. The most important assets referenced by `manifest.json`

The instructions should tell ChatGPT:

- Use `doc.md` as the primary source.
- Use `manifest.json` as the resource index.
- When `doc.md` references `fig-001`, look for an uploaded file whose name contains `fig-001`.
- Ask the user to upload the missing asset if the referenced file is unavailable.

## Cost-Effectiveness

High value:

- A few important documents.
- A small number of key diagrams/tables.
- Stable project knowledge that will be reused often.

Lower value:

- Hundreds of images.
- Frequently changing source documents.
- Documents where exact table values matter constantly.

For large visual-heavy exports, prefer one of these:

- Upload `doc.md` plus only top-priority assets.
- Add a rendered PDF as a visual backup.
- Keep the full `assets/` folder in a repository or drive and use an external tool/agent to fetch resources by id.

## Project Instruction Template

```markdown
This project includes exported Feishu knowledge packages.

Use `doc.md` as the primary readable source.
Use `manifest.json` as the resource index. When the document mentions a resource id such as `fig-001` or `table-002`, check the manifest for its summary, file name, and open conditions.

Relative paths in Markdown are resource identifiers. If a referenced asset is not available in the uploaded project files, ask me to upload that specific file by id/name.

Do not infer exact numbers, labels, arrows, or table values from a summary when the manifest says to open the asset for those details.
```

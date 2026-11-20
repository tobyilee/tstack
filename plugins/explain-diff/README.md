# explain-diff

A Claude Code skill that turns a diff into a document you can learn from.

Give it a pasted diff, a patch file, a commit, a branch, or a pull request. It writes one self-contained HTML file with these parts:

1. **Background.** What you must know before you read the change.
2. **The idea.** The core intuition in one sentence, before any code.
3. **Explore it.** An interactive widget, only when it shows a real cause and effect.
4. **The change, step by step.** The hunks in the order of the reasoning, not the order of the files.
5. **Review notes.** Edge cases and risks, each marked as confirmed or guessed.
6. **A recall quiz.** About 5 questions that test structure and principle, not memory.

The skill writes the document in the language of your prompt.

## Install

Run these commands in a Claude Code session, one at a time. Paste one line each time.

```text
/plugin marketplace add tobyilee/tstack
```

```text
/plugin install explain-diff@tstack
```

## Use

```text
/explain-diff:explain-diff
```

You can also ask in your own words, for example "explain this PR to me" or "이 변경 이해하게 도와줘".

The skill saves the file in the current directory as `explain-diff-<short-slug>.html`.

## What is in this plugin

| Path | Role |
|---|---|
| `skills/explain-diff/SKILL.md` | The workflow and the writing rules. |
| `skills/explain-diff/assets/template.html` | The HTML skeleton: diff styles, light and dark themes, print styles, quiz script. |
| `skills/explain-diff/references/widgets.md` | Patterns and rules for interactive widgets. |
| `evals/` | 3 eval cases for `claude plugin eval`. |

## Limits

- The HTML template loads 2 font stylesheets from the network (jsDelivr and Google Fonts). Without a network connection, the page uses the system fonts. The layout does not change.
- The checks of this repository do not run the eval cases. An eval run calls a model and needs a login.

## Work on this plugin locally

Clone the repository. Then start Claude Code with the plugin folder. Claude Code reads the folder in place, so your edits apply in the next session.

```text
claude --plugin-dir ./plugins/explain-diff
```

## License

MIT. See [LICENSE](LICENSE).

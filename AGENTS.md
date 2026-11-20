# Agent instructions

Rules for a coding agent (Claude Code, Codex, Cursor, or other) in this repo. A person follows the same rules.

Read first:
- https://docs.scalargis.com/llms.txt: index of the docs site, Contributing first.
- https://docs.scalargis.com/contributing.md: the full rules for a change.

Hard rules:
1. No code comments. Allowed: a one-line docstring (`"""Does X."""`) and a section marker in a template block (`<!-- combo -->`). An explanation goes in the commit message or the pull request description.
2. Few tests. Write a test only when a break loses money, lets the wrong user in, leaks personal data, or opens SQL or a CSV export to injection. Call the real code with real inputs, with no fake database, session, or query. No test of a constant, an import, a log line, or a removed route. Verify all else in the running app.
3. No `README.md` and no docs folder inside the repo or an extension or plugin folder. The facts go to the docs site.
4. A change to a fact on the docs site names the page and the new fact in the pull request description. A maintainer updates the page.
5. Open an issue before you change the core: the app factory, `app/api/`, `app/models/`, `database/`, or `main.py`. An extension that more than one installation uses takes only additive, opt-in changes.
6. A commit title is one plain sentence. No prefixes such as `feat:`, no scopes, no ticket ids.

Before the pull request to `main`, from `scalargis/` with the venv Python (3.12):
```
python -m pytest tests app/utils/tests
```
Then start the server and use the changed route or feature.

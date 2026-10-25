# Contributing to opensurrogate

Welcome! You do **not** need any GitHub experience. This guide takes you from zero to your first merged contribution. Every step is copy-paste.

## 0. What you need (once)
1. A free account on https://github.com
2. [Git](https://git-scm.com/downloads) installed (Windows: accept the defaults)
3. [Python 3.10+](https://www.python.org/downloads/) (Windows: tick "Add Python to PATH")
4. A text editor, e.g. [VS Code](https://code.visualstudio.com/)

Check your setup in a terminal (Windows: "Git Bash" or PowerShell):
```
git --version
python --version
```

## 1. Pick an issue
Open the **Issues** tab and filter by the label **good first issue**. Each issue lists the problem, why it matters, what "done" looks like (acceptance criteria), the files to touch and a difficulty label (`beginner`, `intermediate`, `advanced`).
Comment "I'd like to work on this" and tell us how you plan to solve it. A mentor will reply. Wait for the thumbs-up before you start, so two people don't do the same work.

## 2. Fork and clone
1. Click **Fork** (top right of the repo page). This gives you your own copy.
2. Copy your fork to your computer (replace `YOURNAME`):
```
git clone https://github.com/YOURNAME/opensurrogate.git
cd opensurrogate
```

## 3. Set up and check it works
One command sets everything up and runs the tests. They should all pass **before** you change anything:
```
python start.py test
```
(The first run creates a private environment in `.venv` and installs what is needed; it needs internet and takes a minute.)

## 4. Make a branch
Never work on `main`. Use a short name that says what you do:
```
git checkout -b fix-typo-session-1
```

## 5. Make your change
Edit the files named in the issue. Re-run `python start.py test` and the session you touched (`python start.py 1`).

## 6. Commit
```
git status
git add path/to/changed_file
git commit -m "Fix typo in session 1 notes"
```
Commit message style: start with a verb (Add, Fix, Update, Explain), at most about 70 characters, one idea per commit.

## 7. Push and open a Pull Request
```
git push origin fix-typo-session-1
```
GitHub prints a link; open it and click **Create pull request**. In the description write "Closes #ISSUE_NUMBER" and a sentence about what you changed.

## 8. Review
A mentor reviews your PR and may ask for changes. That is normal. Push more commits to the same branch and the PR updates. When it is approved it is merged. You are now a contributor.

## Write a new session with Claude (optional)
This repo ships the `socratic-mastery-tutor` skill in `.claude/skills/`. In [Claude Code](https://claude.com/claude-code), open this folder and type
`/socratic-mastery-tutor`, then ask for the next session, for example: "Write Session 4 on the first roadmap milestone, in the same format as
Sessions 1-3." Read what it writes, run `python start.py test`, and open a pull request like any other change. The finished
Target code is private, so the skill teaches the path; the code is yours to write.

## Rules of the road
- One issue per pull request. Do not mix unrelated changes.
- Keep to the style of the surrounding code. Short functions, clear names, comments that explain *why*.
- Do not add large files (over 2 MB). Media for the Target section is added by maintainers.
- The Target results are a promo of what is possible. Rebuilding them is the point of the advanced issues, so be creative and write your own code.
- Be kind. We follow the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

## Stuck?
Ask on the issue thread or in the Hello FOSS Discord. Say what you tried and paste the exact error. Nobody minds a beginner question.

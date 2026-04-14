# Git & GitHub: Understanding the Relationship

*Lecture notes on local repos, remotes, credentials, and multi-machine workflows, created collaboratively with Claude Opus 4.6.*

---

## 1. Git vs. GitHub: The Fundamental Split

**Git** is a version control system — a program on your computer that tracks changes in files. It has no concept of the internet, accounts, or any particular server. You can use Git forever without ever touching GitHub.

**GitHub** is a website (owned by Microsoft) that hosts Git repositories and wraps collaboration features around them: issues, pull requests, Actions, profile pages. GitLab and Bitbucket are competitors doing the same thing.

> **Analogy:** Git is like email (the protocol). GitHub is like Gmail (one particular service that speaks email). You can send email without Gmail. You can use Git without GitHub.

When you clone "a GitHub repo," what's really happening:

1. Git (the program on your machine) contacts GitHub (a server)
2. Downloads the full repository
3. Stores it in a local folder

From that moment on, the copy on your machine is a **complete, independent, fully-functional Git repo**. If GitHub vanished tomorrow, you'd still have the whole history locally. This is the "distributed" in "distributed version control."

---

## 2. The Three Levels of Git Config

Git config lives in **three scopes** that stack — repo beats global beats system (like CSS specificity).

| Scope | Flag | Location | Applies to |
|-------|------|----------|------------|
| **System** | `--system` | `/etc/gitconfig` or `C:\Program Files\Git\etc\gitconfig` | Every user on the machine |
| **Global** | `--global` | `~/.gitconfig` or `C:\Users\you\.gitconfig` | Your OS user account on this machine |
| **Local** | `--local` (default) | `.git/config` inside the repo | One specific repo |

**Diagnostic command — your best friend:**

```bash
git config --list --show-origin --show-scope
```

This prints every setting with tags showing exactly which file it came from.

### Critical mental correction

**There is no such thing as a config tied to your GitHub account.** Your `~/.gitconfig` lives on *your computer*, not in the cloud. Nothing syncs between machines unless you manually sync dotfiles. This is why `user.name` and `user.email` have to be set on every new machine.

---

## 3. The "Remote" Concept

Your local repo knows about GitHub only because of a pointer called a **remote**.

```bash
git remote -v
# origin  https://github.com/jrkasprzyk/pareto-explorer.git (fetch)
# origin  https://github.com/jrkasprzyk/pareto-explorer.git (push)
```

`origin` is just a nickname — the conventional name for "the place I cloned from." You can:

- Rename it
- Add more remotes
- Remove it entirely
- Have zero remotes (fully local) or many (push to GitHub *and* GitLab *and* a university server)

**Operations:**

- `git push` — "take my local commits and send them to the remote"
- `git pull` — "fetch their commits and merge them into mine"
- `git fetch` — "download their commits but don't merge yet"

GitHub doesn't "own" your repo in any technical sense. It's just another copy, with the convention that it's the shared one everyone agrees to sync with.

---

## 4. Two Separate Identity Concepts

This is where people get confused. There are **two completely separate identities** in play.

### Identity #1: Who Git thinks you are (for commits)

Every commit gets stamped with a name and email:

```bash
git config --global user.name "Joseph Kasprzyk"
git config --global user.email "joe@example.com"
```

**This is self-declared and unverified.** You can put any name and email. Git won't care. GitHub uses the email to decide whose profile picture shows up next to the commit on the website — if the email matches one tied to a GitHub account, GitHub attributes the commit to that account.

> There's a cryptographic way to actually prove a commit is yours — signing with GPG or SSH keys, which gives the green "Verified" badge on GitHub. Optional, most people skip it.

### Identity #2: Who GitHub thinks you are (for pushing)

When you `git push`, GitHub needs to verify you have permission to write to that repo. This is **authentication**, totally separate from commit author info.

**Option A: HTTPS with a Personal Access Token (PAT)**
- Clone URL looks like `https://github.com/...`
- GitHub killed password authentication in 2021
- Generate a PAT on GitHub's website — a long random string acting like a scoped password
- Your OS stores it in a credential manager (Windows Credential Manager, macOS Keychain, Linux Secret Service)

**Option B: SSH keys**
- Clone URL looks like `git@github.com:...`
- Generate a keypair with `ssh-keygen`
- Upload the public half to GitHub
- Keep the private half secret on your computer
- SSH proves you have the private key without sending it
- No passwords, no tokens expiring

Most devs prefer SSH once set up.

---

## 5. The Multi-Machine Picture

In the case where you were to develop on multiple machines, each one is **completely independent**:

- Each has its own `~/.gitconfig` with its own `user.name` and `user.email` (hopefully the same email, so GitHub attributes everything to you)
- Each has its own credentials for pushing — its own PAT or SSH keypair
- Each has its own clones of repos, possibly at different commits

**GitHub is the meeting point.** Each machine independently pushes to and pulls from GitHub. There's no "my GitHub account's git config" — GitHub just receives commits and decides attribution based on authentication.

---

## 6. Line Endings: A Worked Example of Config Scope

One thing to watch for when doing development, especially on different machines, is line endings; in other words, how does a computer know that there is meant to be a line break within a text file? There are historically two different concepts, borrowed from the days of typewriters etc - carriage return (CR) and line feed (LF). You don't need to know what those two concepts mean; you just need to understand that Windows uses CRLF (`\r\n`) and Unix/Mac use LF (`\n`). Git has opinions about translating.

**The `core.autocrlf` setting:**

| Value | Behavior | Typical for |
|-------|----------|-------------|
| `true` | LF→CRLF on checkout, CRLF→LF on commit | Windows |
| `input` | Leave on checkout, CRLF→LF on commit | Mac/Linux |
| `false` | Touch nothing | Experts who know what they want |

### The better solution: `.gitattributes`

A `.gitattributes` file lives **in the repo itself** and overrides per-machine config. It travels with the repo, so every collaborator gets the same rules.

```
* text=auto eol=lf
*.bat text eol=crlf
*.sh text eol=lf
```

Commit it once, and the repo carries its own rules regardless of each machine's global config. **This is the robust fix for teams or future-you across multiple machines.**

### The gotcha

If `core.autocrlf` differs between your machines, you can end up with commits that look like "every line changed" because one machine normalized endings and another didn't. Git sees different bytes on every line and flags the whole file as modified.

---

## 7. What to Watch Out For

### Diverging clones
Commit on laptop A, push to GitHub. Work on laptop B without pulling first, make changes, try to push — Git refuses with `rejected, non-fast-forward`. You have to pull/merge/rebase first.

**Habit to build:** `git pull` before starting work on any machine, every time.

### Credential staleness
PATs expire. SSH keys can be revoked. If push suddenly fails with 403 or auth error, regenerate credentials on that machine.

### The identity/authentication mixup
You can authenticate successfully (push works) but have `user.email` set to something that doesn't match your GitHub account. Commits won't get attributed to your profile. Check `git log` — if avatars aren't showing up on GitHub, that's why.

### Configuration drift between machines
Anything in `.gitconfig` — line endings, merge tool, default branch name, aliases — can differ between machines and cause surprising behavior. Prefer `.gitattributes` (repo-level, travels with the project) over per-machine config for things that matter to the project.

### Force-pushing
`git push --force` overwrites GitHub's history with your local history. If a collaborator (or past-you on another machine) had commits you didn't have locally, they're gone.

**Always prefer `--force-with-lease`** — it refuses to force-push if GitHub has changes you haven't seen.

### Private repos on new machines
Public repos clone with no auth. Private ones need credentials. First clone on a new machine is often where people discover their auth setup isn't done.

---

## 8. Mental Model to Remember

> Picture each machine as a person holding a photocopy of a book. GitHub is a shared filing cabinet where everyone agrees to keep the "official" copy. Each person periodically walks to the cabinet, compares their copy, and either updates theirs (`pull`) or updates the cabinet's (`push`). Nobody's copy is more "real" than anyone else's — the cabinet copy is just the one everyone agrees to sync with. Your name is written inside every page you edit (commit author). The cabinet has a lock, and each person carries their own key (PAT or SSH key) to open it.

---

## 9. Quick Reference: Diagnostic Commands

```bash
# See all config with sources
git config --list --show-origin --show-scope

# See config at each scope
git config --global --list
git config --local --list      # run inside a repo

# See remotes
git remote -v

# See current branch state vs. remote
git status
git fetch && git status

# See commit author info on recent commits
git log --format="%an <%ae>" -5
```

---

## 10. VS Code–Specific Gotchas (Bonus)

When VS Code acts like "there's no git here" even though `.git/` exists:

1. **`safe.directory` refusal** — Git 2.35.2+ refuses repos owned by a different user. Fix: `git config --global --add safe.directory '<path>'`
2. **Git binary not found** — check Output panel → "Git" dropdown
3. **Git extension disabled** — check Extensions view or `"git.enabled": false`
4. **Wrong folder opened** — VS Code scans workspace root + `git.repositoryScanMaxDepth` (default 1) levels deep
5. **`.git` is a file, not a folder** — happens with worktrees/submodules; broken pointer across machines

**Diagnostic split:** open integrated terminal, `cd` to repo, run `git status`.
- Terminal gives a real answer → VS Code–side problem
- Terminal also complains → Git-level problem

---

## 11. Essential Habits & Concepts

### `.gitignore` — the cousin to `.gitattributes`
Same idea (a file in the repo that travels with it), but for telling Git which files to **ignore entirely**. Build artifacts, `node_modules/`, `.env` files with secrets, `.DS_Store`, etc. GitHub has good starter templates per language. Add one to every new repo on day one.

### Never commit secrets
API keys, passwords, `.env` contents. **Git history is forever** — even if you delete the file in a later commit, the secret is still in history and can be recovered. If it happens:

1. Assume the secret is compromised
2. Rotate it immediately
3. Then worry about cleaning history (or just accept it's public)

### Branches are cheap — use them
The instinct to work directly on `main` is strong when solo, but branches cost nothing and save you when experiments go sideways.

```bash
git switch -c feature-name    # create and switch
git switch main               # go back
```

Experiments that don't pan out get abandoned instead of polluting history.

### `git stash` — the "oh wait" button
You're mid-edit, uncommitted, and need to pull or switch branches.

```bash
git stash         # tuck changes away
git stash pop     # bring them back
```

### Reading history is a skill
| Command | What it shows |
|---------|---------------|
| `git log --oneline --graph --all` | Visual tree of branches and commits |
| `git blame <file>` | Who last touched each line |
| `git show <commit>` | What a specific commit changed |

When something breaks, these tell you *when* it broke, which usually tells you *why*.

### The reflog is your safety net
`git reflog` shows every state HEAD has been in for the last 90 days, even after "destructive" operations like rebases or resets. If you ever think you've lost commits, you almost certainly haven't — reflog will find them. Good thing to know exists so you don't panic.

---

## 12. The Staging Area (For Teaching)

The single biggest conceptual hurdle for beginners is usually the **staging area** (also called the "index"). The three-state model:

```
working directory  →  staging area  →  committed
     (edits)           (git add)       (git commit)
```

- `git add` stages changes
- `git commit` commits what's staged
- `git commit -a` commits all tracked changes, skipping staging

Many beginners think `-a` is the normal flow, but understanding *why* staging exists pays off once you want to commit only *some* of your changes — say, the feature code but not the debugging `print` statements you added while working. You can `git add` specific files, or even specific lines with `git add -p`.

**Teaching tip:** staging is the "which of my changes do I want to group into this commit?" step. Commits should be logical units, not "whatever happened to be on disk when I ran commit."
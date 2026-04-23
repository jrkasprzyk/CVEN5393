# Git Cheat Sheet

Small, safe Git workflow for this repository.

## Daily Flow

1. See what changed:

```powershell
git status --short
```

2. Review unstaged edits:

```powershell
git diff
```

3. Stage only what belongs in the next commit:

```powershell
git add path/to/file.py
```

4. Review exactly what will be committed:

```powershell
git diff --staged
```

5. Commit:

```powershell
git commit -m "Short descriptive message"
```

6. Push:

```powershell
git push
```

## Read `git status --short`

- ` M file` means modified but not staged.
- `M  file` means staged.
- `MM file` means staged, then changed again afterward.
- `R  old -> new` means Git detected a rename.
- `D  file` means staged deletion.
- `?? file` means new untracked file.

The left column is staged state. The right column is unstaged working-tree state.

## Safe Fixups

Unstage a file before commit:

```powershell
git restore --staged path/to/file.py
```

Discard unstaged changes in one file:

```powershell
git restore path/to/file.py
```

See the last commit:

```powershell
git log -1 --stat
```

See recent history:

```powershell
git log --oneline --decorate -n 10
```

## Good Habits

- Run `git status --short` before and after `git add`.
- Use `git diff --staged` before every commit.
- Stage specific files, not everything blindly.
- Keep each commit focused on one logical change.

## Typical Repo Workflow

```powershell
git status --short
git diff
git add <only the files for this task>
git diff --staged
git commit -m "Describe the change"
git push
```

# Recommended single-venv workflow for this repository

Goal: maintain one Python virtual environment at the repository root and install a small editable package so all subfolders use the same libraries.

Quick steps (Windows PowerShell):

```powershell
# from repository root
python -m venv .venv
& .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
# install the workspace package (editable) which pulls the shared deps
pip install -e .
```

Notes:
- The editable install (`pip install -e .`) installs the `CVEN5393-tools` package declared in `setup.cfg` and brings in the shared dependencies declared there.
- If you prefer a plain requirements file workflow, run `pip install -r requirements.txt` instead (or in addition).
- Configure VS Code to use the repository venv by setting `python.defaultInterpreterPath` to `.venv/Scripts/python.exe` (or use the interpreter picker).
- Avoid committing venv folders — the repository `.gitignore` already ignores common venv names such as `.venv/`, `venv/`, and `env/`.

Using the installed package:
- After installing editable, from any subfolder you can `import cvtools` in Python and shared utilities will be available.

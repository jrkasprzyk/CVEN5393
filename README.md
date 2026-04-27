# CVEN5393: Water Resource Systems and Management

This repository is for the course CVEN 5393: Water Resources Systems and Management, taught by Prof. Joseph Kasprzyk at the University of Colorado Boulder. The examples were started in Spring 2023 and have been continually updated.

Currently the folder structure is:
1. **AnalyticHierarchyProcess**: Source code and example AHP setup files for a [Streamlit app](https://ahp-yaml.streamlit.app/) that enables in-browser AHP calculations.
2. **Colab Notebooks**: Python notebooks intended to be opened in [Google Colab](https://colab.research.google.com/). Each notebook is self-contained and illustrates a principle in water resources and systems analysis. These can also be used on your own Jupyter notebook server.
3. **Data**: A few example datafiles that are used for loading into notebooks and elsewhere.
4. **RiverWare Example Models**: Example models implemented in [RiverWare](https://riverware.org/), a river basin and reservoir model developed by the [Center for Advanced Decision Support for Water and Environmental Systems](https://www.colorado.edu/cadswes/) at the University of Colorado Boulder.
5. **Training**: Lecture notes and explainers (git/GitHub, Python virtual environments, CDN and data distribution).
6. **exam_prep**: Question bank JSON files (promptukit format) consumed by downstream trivia tooling via jsDelivr.
7. **cvtools**: A small editable Python package of shared utilities for this workspace (installed via Poetry).
8. **scripts**: Maintenance scripts, including `tag-release.sh` for cutting versioned releases.
9. **archived**: Legacy `requirements.txt` and `setup.cfg`, kept for reference now that Poetry manages dependencies.

For more information, consult the webpage of the [Kasprzyk Research Group](https://www.colorado.edu/lab/krg).

## Versioning and external consumption

This repo serves dual roles: course materials **and** a versioned data source consumed by external tools (e.g. hardball-trivia) via [jsDelivr](https://www.jsdelivr.com/). jsDelivr resolves file URLs directly from GitHub tags, so **tags are the version** — independent of any package registry.

Rules that follow from this:
- Every release must be tagged (e.g. `v0.1.0`). Use `scripts/tag-release.sh`, which reads the version from `pyproject.toml` and creates a matching tag, keeping the two in sync.
- **Do not force-push or delete tags.** Downstream consumers pin specific tag versions; rewriting a tag silently breaks them.
- Bump `pyproject.toml` version and cut a new tag whenever files consumed via jsDelivr change.

To release a new version:

```bash
# 1. Commit and push your changes first
git add <files>
git commit -m "your message"
git push

# 2. Then tag the release (reads version from pyproject.toml, creates and pushes the tag)
./scripts/tag-release.sh
```

## Using Poetry

This repository can be managed with Poetry. Poetry's configuration is in `pyproject.toml`.

Installation and basic commands (see Poetry docs for platform-specific install):

```bash
# Install Poetry (see https://python-poetry.org/docs/#installation)
poetry install    # install dependencies and create virtual environment
poetry shell      # spawn a shell within the virtual environment
poetry run python -m pip install --upgrade pip
poetry lock       # (optional) refresh/produce `poetry.lock`
poetry build      # build distribution packages
```

The legacy `requirements.txt` and `setup.cfg` have been moved to `archived/` for reference; Poetry (`pyproject.toml` + `poetry.lock`) is now the source of truth for dependencies. Current dependencies include `promptukit` and `parasolpy` alongside the standard scientific Python stack.

## Poetry & promptukit workflow

The package version constraint is in `pyproject.toml`, and `poetry.lock` records which specific packages are currently installed. Both are committed to the GitHub repo.

Within this project, update and install the new `promptukit` release with:

```bash
poetry update promptukit        # update lock and install newest matching release
# or to pin an exact release:
poetry add promptukit==0.1.550  # updates pyproject, lock, and installs
```

- **Testing unreleased changes**: if the new version isn't published yet, use a VCS or local path dependency for testing:

```toml
promptukit = { git = "https://github.com/jrkasprzyk/promptukit.git", rev = "v0.1.550" }
```

or:

```bash
poetry add git+https://github.com/jrkasprzyk/promptukit.git@v0.1.550
```

- **Troubleshooting**: if `poetry lock`/`poetry update` complains "no versions of promptukit match ...":

	- Confirm the release exists on PyPI: `python -m pip index versions promptukit`
	- Clear Poetry's PyPI cache and retry: `poetry cache clear pypi --all`
	- Check for an alternate repository in Poetry config: `poetry config --list`

- **Verify installed version**:

```bash
poetry show promptukit
poetry run python -c "import importlib.metadata as m; print(m.version('promptukit'))"
```

## Using promptukit

Some sample commands assuming that `poetry` is installed and used to manage the environment.

Add a question to the `5393.sp26.exam2.review.json` question bank:

```bash
poetry run add-question ./exam_prep/5393.sp26.exam2.review.json
```

Open the `promptukit` graphical user interface (GUI) on the same bank:

```bash
poetry run promptukit-gui -f ./exam_prep/5393.sp26.exam2.review.json
```

Extract selected questions from a source bank (`--src`) to a new bank (`--dest`):

```bash
poetry run question-bank extract -i --src path/to/full/bank --dest path/to/extracted/bank
```

Create an exam PDF:

```bash
poetry run python -m promptukit.exams.create_exam -q name_of_bank.json -o name_of_exam.pdf
```


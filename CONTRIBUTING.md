# Contributing to this Project

Welcome, and thank you for considering contributing to this project.  Public contributions are currently limited to bug reports and feature requests. 

Reading and following these guidelines will help us make the contribution process easy and effective for everyone involved. It also communicates that you agree to respect the time of the developers managing and developing these open source projects. In return, we will reciprocate that respect by addressing your issue, assessing changes, and helping you finalize your pull requests.

## Code of Conduct

By participating and contributing to any Checkmarx projects, you agree to uphold our [Code of Conduct](CODE-OF-CONDUCT.md).

## Getting Started

If you have suggestions for how this project could be improved, or want to report a bug, open an issue.

Public contributions are made to this repo via Issues.  Internal contributions are made via Pull Requests (PRs). A few general guidelines that cover both:

- Search for existing Issues and PRs before creating your own to avoid duplicates.
- PRs will only be accepted if associated with an issue (enhancement or bug) that has been submitted and reviewed/labeled as *accepted* by a project maintainer.
- We will work hard to makes sure issues that are raised are handled in a timely manner.

## Development Setup

### Prerequisites

- **Python 3.10 or later.** The project declares `requires-python = ">=3.10"` in `pyproject.toml`; anything older will not resolve.
- **Visual Studio Code** with the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) (`ms-python.python`).

Confirm the interpreter you intend to use is new enough:

```
python --version
```

### Create the virtual environment with VS Code

1. Open the repository root folder in VS Code (**File > Open Folder...**).
2. Open the Command Palette (`Ctrl+Shift+P`, or `Cmd+Shift+P` on macOS) and run **Python: Create Environment...**.
3. Choose **Venv** as the environment type.
4. Choose a Python 3.10+ interpreter from the list.
5. When VS Code offers to install optional dependencies, **leave everything unselected** and confirm. Selecting `pyproject.toml` here makes VS Code run an editable install of this project.

VS Code creates `.venv/` in the repository root and selects it as the workspace interpreter. Any terminal you open afterwards with **Terminal > New Terminal** activates it automatically.

### Install dependencies without installing the project

Development is done against the sources in `src/`, so the `cxone_repo_tools` package itself should **not** be installed into the virtual environment — a copy in `site-packages` shadows your working tree, so the debugger steps through the installed copy instead of the code you are editing.

pip has no flag for "dependencies only", but `pip uninstall` removes only the package you name and leaves its dependencies behind. Install the project to pull the dependencies in, then uninstall the project. In a VS Code terminal (with `.venv` active), from the repository root:

```
pip install .
pip uninstall -y cxone_repo_tools
```

Confirm the result:

```
pip list
```

`cxone_repo_tools` should not appear in the output; the dependencies declared in `pyproject.toml` and their transitive dependencies should.

Run both commands again whenever the dependencies in `pyproject.toml` change.

### Running from source

Because the package is not installed, `src` must be on the module search path. From the repository root:

```
python -m cxone_repo_tools --help
```

with `PYTHONPATH` set to `src` (`$env:PYTHONPATH="src"` in PowerShell, `export PYTHONPATH=src` in a POSIX shell).

The repository root already contains a `.env` file that does this for you inside VS Code:

```
PYTHONPATH=src
```

The Python extension reads that file automatically, so running, debugging, and unit test discovery all resolve `cxone_repo_tools` from `src/` without any further setup.

### Debugging the module in VS Code

The debugger has to launch the code as a *module* rather than as a script, because there is no single entry point file to run — `python -m cxone_repo_tools` enters through `src/cxone_repo_tools/__main__.py`.

Create `.vscode/launch.json` (**Run and Debug** view, `Ctrl+Shift+D`, then **create a launch.json file**) with a module configuration:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug cxone-repo-tools",
      "type": "debugpy",
      "request": "launch",
      "module": "cxone_repo_tools",
      "args": ["--help"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env",
      "justMyCode": false
    }
  ]
}
```

The settings that matter:

- `module` runs the package the same way `python -m cxone_repo_tools` does. Use this instead of `program`, which expects a path to a script.
- `envFile` applies the `PYTHONPATH=src` from `.env`. This is what allows the debugger to import the package from the working tree while it is not installed. The Python extension would pick up `.env` by default, but naming it here keeps the configuration self-contained.
- `cwd` keeps relative paths — including the `src` in `PYTHONPATH` — resolving against the repository root.
- `args` holds the command line to debug. Replace `--help` with the arguments for the command you want to step through.
- `justMyCode` set to `false` lets you step into dependencies such as `cxone_api`. Remove it if you only want to stop in this project's code.

Select **Debug cxone-repo-tools** in the Run and Debug view and press `F5`. Breakpoints set in files under `src/` will be hit. Make sure `.venv` is the selected interpreter (**Python: Select Interpreter**) so the debugger runs with the dependencies you installed.

## Issues

Issues should be used to report problems with the solution / source code, request a new feature, or to discuss potential changes before a PR is created. When you create a new Issue, a template will be loaded that will guide you through collecting and providing the information we need to investigate.

If you find an Issue that addresses the problem you're having, please add your own reproduction information to the existing issue rather than creating a new one. Adding a [reaction](https://github.blog/news-insights/product-news/add-reactions-to-pull-requests-issues-and-comments/) can also help by indicating to our maintainers that a particular problem is affecting more than just the reporter.

### Templates

The following templates will be used within Checkmarx github repositories

- [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.yml)
- [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.yml)

## DCO Sign-off Requirement

All commits must include a `Signed-off-by` trailer.

- One commit:
  - `git commit -s -m "your message"`
- Existing commit (amend sign-off):
  - `git commit --amend -s`
- Entire branch:
  - `git rebase --signoff origin/master`

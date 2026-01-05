# Installation

You can install **BibTeX Validator** either to use it in your existing workflow (e.g., for a LaTeX project) or to contribute to its development.

## For Users (Integration)

If you just want to run the tool to validate your references, you don't need to clone the full repository. You can use `uv` or `pip` to install it directly.

### Option 1: Using `uv tool` (Recommended)

This is the easiest way to run the tool without manually managing virtual environments.

**One-off execution:**
Run the tool directly from the git repository:

```bash
uv tool run git+https://github.com/bet-lab/reference-validator.git bibtex-validator references.bib --gui
```

**Install as a tool:**
Make the command available globally on your system:

```bash
uv tool install git+https://github.com/bet-lab/reference-validator.git
bibtex-validator references.bib --gui
```

### Option 2: Installing in an Existing Environment

If you have an existing Python environment (e.g., for a specific project), you can install the package into it.

**Using uv:**

```bash
uv add git+https://github.com/bet-lab/reference-validator.git
```

**Using pip:**

```bash
pip install git+https://github.com/bet-lab/reference-validator.git
```

---

## For Developers (Contribution)

If you want to modify the code or contribute to the project, follow these steps.

### Prerequisites

- [uv](https://github.com/astral-sh/uv) installed on your system.
- Python 3.8 or higher.

### Setup

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/bet-lab/reference-validator.git
    cd reference-validator
    ```

2.  **Sync dependencies**:
    Run `uv sync` to create a virtual environment and verify lockfile.

    ```bash
    uv sync
    ```

3.  **Run the tool**:
    ```bash
    uv run bibtex-validator references.bib --gui
    ```

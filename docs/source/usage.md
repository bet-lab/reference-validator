# Usage

The **BibTeX Validator** can be run in two modes: Command Line Interface (CLI) and Graphical User Interface (GUI).

## Quick Start

::::{grid} 1 1 2 2
:gutter: 2

:::{grid-item-card} :octicon:`terminal` CLI Mode
Run in your terminal to validate a file.

```bash
uv run bibtex-validator references.bib
```

:::

:::{grid-item-card} :octicon:`browser` GUI Mode
Launch the visualization dashboard.

```bash
uv run bibtex-validator references.bib --gui
```

:::
::::

## Detailed Usage

.. tab-set::

    .. tab-item:: CLI
        :sync: cli

        Run the validator from the command line for automation or quick checks.

        **Basic Syntax**

        ```bash
        uv run bibtex-validator <bib_file> [options]
        ```

        **Arguments**

        - `bib_file`: Path to the input BibTeX file (Required).
        - `--output`, `-o`: Path to the output file (Optional).
        - `--update`: Automatically update the BibTeX file with fetched data.
        - `--no-cache`: Force fresh data fetch (ignore cache).

        **Examples**

        Validate and print results:
        ```bash
        uv run bibtex-validator references.bib
        ```

        Validate and update the file in-place:
        ```bash
        uv run bibtex-validator references.bib --update
        ```

    .. tab-item:: GUI
        :sync: gui

        The **GUI** is the recommended way to interactively review changes and resolve conflicts.

        **Launch Command**

        ```bash
        uv run bibtex-validator references.bib --gui
        ```

        **Key Features**

        - **Validation Table**: Color-coded rows (Green = Valid, Red = Issues).
        - **Diff View**: Side-by-side comparison of local vs. fetched data.
        - **Interactive Badges**: Click badges to toggle sources for specific fields.
        - **Bulk Actions**:
            - :gui-btn-accept:`Accept All`: Apply all suggested changes.
            - :gui-btn-reject:`Reject All`: Discard all changes.

    .. tab-item:: Python
        :sync: python

        You can import the validator class into your own Python scripts.

        ```python
        from validate_bibtex import BibTeXValidator

        # Initialize
        validator = BibTeXValidator(
            bib_file="references.bib",
            output_file="references_updated.bib"
        )

        # Run validation
        validator.validate_file()
        ```

# Usage

The **BibTeX Validator** can be run in two modes: Command Line Interface (CLI) and Graphical User Interface (GUI).

## Command Line Interface (CLI)

Run the validator on a BibTeX file from the terminal.

```bash
uv run bibtex-validator <bib_file> [options]
```

### Arguments

- `bib_file`: Path to the input BibTeX file (Required).
- `--output`, `-o`: Path to the output file (Optional). If not provided, it may overwrite the input based on configuration or default behavior.
- `--gui`: Launch the web-based interactive GUI.
- `--update`: Automatically update the BibTeX file with fetched data (CLI mode).
- `--no-cache`: key to ignore cache if implemented.

### Examples

**Validate and print results:**

```bash
uv run bibtex-validator references.bib
```

**Validate and update the file:**

```bash
uv run bibtex-validator references.bib --update
```

## Graphical User Interface (GUI)

The GUI provides a powerful way to review changes and resolve conflicts manually.

```bash
uv run bibtex-validator references.bib --gui
```

This will launch a local server and open your default web browser (usually at `http://127.0.0.1:8000`).

### GUI Features

- **Validation Table**: Shows all entries.
  - **Green header**: Entry is valid.
  - **Red header**: Entry has missing fields or invalid IDs.
- **Diff View**: Compare the current BibTeX value with the value fetched from APIs.
- **Source Selection**: Choose which source (Crossref, arXiv, Scholar, etc.) to use for each field.
- **Bulk Actions**: Accept all changes or apply updates entry-by-entry.

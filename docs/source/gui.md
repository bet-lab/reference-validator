# Interactive GUI Guide

The **BibTeX Validator** features a modern, web-based Graphical User Interface (GUI) that allows you to intuitively review, compare, and accept changes to your BibTeX entries.

## Interface Overview

The interface is divided into three main sections: **Summary**, **Navigation**, and the **Comparison Table**.

### 1. Validation Summary

At the top of the dashboard, you'll see a global summary of the validation results:

- **Need Attention**: A pie chart and counter showing the percentage of entries that require your input.
- **Reviews (Blue)**: Fields where the API found new data to update incomplete fields.
- **Conflicts (Orange)**: Critical mismatches between your local data and the API data (e.g., Year 2023 vs 2024).
- **Differences (Yellow)**: Minor styling or formatting differences.
- **Identical (Green)**: Fields that perfectly match the authoritative source.
- **Global Actions**: An **Accept All Entries** button allows you to batch-approve all non-conflicting changes at once.

### 2. Navigation Toolbar

Located below the summary, the toolbar helps you move through your bibliography:

- **Dropdown Menu**: Quickly jump to any entry by selecting its citation key. The dropdown also shows badges (e.g., `+2` updates, `!1` conflict) next to entries needing attention.
- **Previous / Next Buttons**: Navigate sequentially through the database.
- **Entry Stats**: A quick inline summary of the current entry's status (updates, conflicts, etc.).

### 3. Comparison Table

The core of the interface is the detailed comparison table for the selected entry.

#### Columns

- **Field**: The BibTeX field name (e.g., `title`, `author`, `year`).
- **BibTeX Value**: The current value in your local `.bib` file.
- **API Value**: The suggested value found from online sources.
- **Source**: The origin of the data, displayed with color-coded interactive badges:

  - <span style="background-color: #dbeafe; color: #1e40af; padding: 2px 6px; border-radius: 9999px; font-size: 0.75rem; border: 1px solid #bfdbfe;">CROSSREF</span> (Blue)
  - <span style="background-color: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 9999px; font-size: 0.75rem; border: 1px solid #fecaca;">ARXIV</span> (Red)
  - <span style="background-color: #e0e7ff; color: #3730a3; padding: 2px 6px; border-radius: 9999px; font-size: 0.75rem; border: 1px solid #c7d2fe;">SEMANTIC SCHOLAR</span> (Indigo)
  - <span style="background-color: #f3e8ff; color: #6b21a8; padding: 2px 6px; border-radius: 9999px; font-size: 0.75rem; border: 1px solid #e9d5ff;">DBLP</span> (Purple)
  - <span style="background-color: #e0f2fe; color: #075985; padding: 2px 6px; border-radius: 9999px; font-size: 0.75rem; border: 1px solid #bae6fd;">PUBMED</span> (Sky)
  - <span style="background-color: #dbeafe; color: #1e40af; padding: 2px 6px; border-radius: 9999px; font-size: 0.75rem; border: 1px solid #bfdbfe;">SCHOLAR</span> (Blue)

  _Clicking a badge with a dropdown arrow allows you to switch between different data sources for that specific field._

- **Status**: Indicates the type of change:

  - **Review (Blue)**: New data available.
  - **Conflict (Orange)**: Data mismatch.
  - **Different (Yellow)**: Minor difference.
  - **Identical (Green)**: Verified match.
  - **Local Only (Gray)**: No data found in API.

- **Actions**:
  - **Accept**: Applies the API value to your entry.
  - **Reject**: Keeps your local value.

### Footer Actions

At the bottom of the table, you can apply bulk actions to the current entry:

- **Reject All**: Discard all suggestions for this entry.
- **Accept All**: Apply all suggested changes for this entry.

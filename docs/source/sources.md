(sources)=

# Supported Data Sources

**BibTeX Validator** integrates with a wide range of academic databases to ensure your references are accurate and complete.

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} :gui-badge-crossref:`Crossref`
:link: https://www.crossref.org/
:columns: 12 6 6 4

**Primary Source for DOIs**

- **Validates**: DOIs
- **Fetches**: Title, Author, Journal, Year, Volume, Issue, Pages
- **Logic**: Queries directly using the DOI. If a DOI is missing, it attempts to find one via other sources.
  :::

:::{grid-item-card} :gui-badge-arxiv:`arXiv`
:link: https://arxiv.org/
:columns: 12 6 6 4

**Preprint Repository**

- **Validates**: arXiv IDs
- **Fetches**: Title, Author, Year, Abstract, Primary Category
- **Logic**: Detected via `eprint` field or DOI (e.g., `10.48550/arXiv...`). Handles versioning (v1, v2).
  :::

:::{grid-item-card} :gui-badge-scholar:`Google Scholar`
:link: https://scholar.google.com/
:columns: 12 6 6 4

**Citation & Search Backup**

- **Fetches**: Citation counts, missing DOIs
- **Logic**: Searches by title/author if other identifiers are missing. **Note**: Can be rate-limited.
  :::

:::{grid-item-card} :gui-badge-dblp:`DBLP`
:link: https://dblp.org/
:columns: 12 6 6 4

**Computer Science Bibliography**

- **Fetches**: Accurate conference/journal metadata
- **Logic**: Prioritized for Computer Science papers. Excellent for resolving abbreviations.
  :::

:::{grid-item-card} :gui-badge-pubmed:`PubMed`
:link: https://pubmed.ncbi.nlm.nih.gov/
:columns: 12 6 6 4

**Biomedical Literature**

- **Fetches**: Metadata via PMID
- **Logic**: Triggered if a `pmid` field is present.
  :::

:::{grid-item-card} :gui-badge-openalex:`OpenAlex`
:link: https://openalex.org/
:columns: 12 6 6 4

**Comprehensive Metadata**

- **Fetches**: High-quality open metadata
- **Logic**: Used as a robust backup for many fields using DOIs or Titles.
  :::

:::{grid-item-card} :gui-badge-zenodo:`Zenodo`
:link: https://zenodo.org/
:columns: 12 6 6 4

**General Purpose Repository**

- **Fetches**: Dataset and software citation metadata
- **Logic**: Triggered for Zenodo DOIs.
  :::

:::{grid-item-card} :gui-badge-datacite:`DataCite`
:link: https://datacite.org/
:columns: 12 6 6 4

**DOI Registration Agency**

- **Fetches**: General metadata for DOIs not in Crossref
- **Logic**: Fallback for non-Crossref DOIs.
  :::

::::

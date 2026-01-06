(sources)=

# Supported Data Sources

**BibTeX Validator** integrates with a wide range of academic databases to ensure your references are accurate and complete.

::::{grid} 1
:gutter: 3

:::{grid-item-card}
:link: https://www.crossref.org/

<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
  <span class="badge badge-source-crossref">Crossref</span>
  <span style="font-size: 1.1rem; font-weight: 600;">Primary Source for DOIs</span>
</div>

- **Validates**: DOIs
- **Fetches**: Title, Author, Journal, Year, Volume, Issue, Pages
- **Logic**: Queries directly using the DOI. If a DOI is missing, it attempts to find one via other sources.
  :::

:::{grid-item-card}
:link: https://arxiv.org/

<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
  <span class="badge badge-source-arxiv">arXiv</span>
  <span style="font-size: 1.1rem; font-weight: 600;">Preprint Repository</span>
</div>

- **Validates**: arXiv IDs
- **Fetches**: Title, Author, Year, Abstract, Primary Category
- **Logic**: Detected via `eprint` field or DOI (e.g., `10.48550/arXiv...`). Handles versioning (v1, v2).
  :::

:::{grid-item-card}
:link: https://scholar.google.com/

<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
  <span class="badge badge-source-semantic-scholar">Google Scholar</span>
  <span style="font-size: 1.1rem; font-weight: 600;">Citation & Search Backup</span>
</div>

- **Fetches**: Citation counts, missing DOIs
- **Logic**: Searches by title/author if other identifiers are missing. **Note**: Can be rate-limited.
  :::

:::{grid-item-card}
:link: https://dblp.org/

<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
  <span class="badge badge-source-dblp">DBLP</span>
  <span style="font-size: 1.1rem; font-weight: 600;">Computer Science Bibliography</span>
</div>

- **Fetches**: Accurate conference/journal metadata
- **Logic**: Prioritized for Computer Science papers. Excellent for resolving abbreviations.
  :::

:::{grid-item-card}
:link: https://pubmed.ncbi.nlm.nih.gov/

<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
  <span class="badge badge-source-pubmed">PubMed</span>
  <span style="font-size: 1.1rem; font-weight: 600;">Biomedical Literature</span>
</div>

- **Fetches**: Metadata via PMID
- **Logic**: Triggered if a `pmid` field is present.
  :::

:::{grid-item-card}
:link: https://openalex.org/

<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
  <span class="badge badge-source-openalex">OpenAlex</span>
  <span style="font-size: 1.1rem; font-weight: 600;">Comprehensive Metadata</span>
</div>

- **Fetches**: High-quality open metadata
- **Logic**: Used as a robust backup for many fields using DOIs or Titles.
  :::

:::{grid-item-card}
:link: https://zenodo.org/

<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
  <span class="badge badge-source-zenodo">Zenodo</span>
  <span style="font-size: 1.1rem; font-weight: 600;">General Purpose Repository</span>
</div>

- **Fetches**: Dataset and software citation metadata
- **Logic**: Triggered for Zenodo DOIs.
  :::

:::{grid-item-card}
:link: https://datacite.org/

<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
  <span class="badge badge-source-datacite">DataCite</span>
  <span style="font-size: 1.1rem; font-weight: 600;">DOI Registration Agency</span>
</div>

- **Fetches**: General metadata for DOIs not in Crossref
- **Logic**: Fallback for non-Crossref DOIs.
  :::

::::


BibTeX Validator
================

.. grid:: 1 1 2 2
    :gutter: 3

    .. grid-item-card:: :octicon:`check-circle;1em;sd-text-success` Validation
        :link: usage
        :link-type: doc

        Automatically validate **DOIs** and **arXiv IDs** in your BibTeX files to ensure all references are correct and accessible.

    .. grid-item-card:: :octicon:`database;1em;sd-text-primary` Enrichment
        :link: sources
        :link-type: doc

        Enrich your references with metadata from **Crossref**, **arXiv**, **Google Scholar**, **DBLP**, **PubMed**, **Zenodo**, **DataCite**, and **OpenAlex**.

    .. grid-item-card:: :octicon:`browser;1em;sd-text-warning` Interactive GUI
        :link: gui
        :link-type: doc

        Review changes, resolve conflicts, and manage your bibliography with a modern, interactive web-based interface.

    .. grid-item-card:: :octicon:`code;1em;sd-text-info` Python API
        :link: api
        :link-type: doc

        Integrate validation and enrichment logic directly into your own Python scripts and workflows.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   installation
   usage
   sources
   gui
   logic
   api

Features
--------

- **Validation**:
  Checks if DOIs and arXiv IDs are valid and reachable.

- **Enrichment**:
  Fetches metadata from multiple high-quality sources:

  :gui-badge-crossref:`Crossref` :gui-badge-arxiv:`arXiv` :gui-badge-scholar:`Google Scholar` :gui-badge-dblp:`DBLP` :gui-badge-pubmed:`PubMed` :gui-badge-zenodo:`Zenodo` :gui-badge-datacite:`DataCite` :gui-badge-openalex:`OpenAlex`

- **Visual Feedback**:
  Clear visual indicators for the status of each field:

  :gui-status-review:`Review` :gui-status-conflict:`Conflict` :gui-status-different:`Different` :gui-status-identical:`Identical`

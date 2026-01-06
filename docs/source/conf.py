import os
import sys
from datetime import date

# -- Project information -----------------------------------------------------
project = "BibTeX Validator"
copyright = f"{date.today().year}, Wonjun Choi"
author = "Wonjun Choi"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.mathjax",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_tabs.tabs",
    "sphinxext.opengraph",
    "sphinx_sitemap",
    "sphinxcontrib.mermaid",
    "sphinxext.rediraffe",
    "sphinx_last_updated_by_git",
]

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = "shibuya"
html_static_path = ["_static"]
html_title = "BibTeX Validator"

# Custom CSS and JavaScript files
# Load external resources (CDN) and local custom files
html_css_files = [
    # Inter font from Google Fonts
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    # Custom CSS with shadcn/ui styles and Tailwind utilities
    "custom.css",
]

html_js_files = [
    # Custom JavaScript for interactive features
    "custom.js",
]

# Shibuya theme options
html_theme_options = {
    "light_logo": "_static/logo-light.svg",  # Optional: add logo if available
    "dark_logo": "_static/logo-dark.svg",  # Optional: add logo if available
    "github_url": "https://github.com/bet-lab/reference-validator",
    "nav_links": [
        {
            "title": "Documentation",
            "url": "https://wonjun.github.io/reference-validator/",
        },
    ],
}

# -- Options for MyST Parser -------------------------------------------------
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
myst_heading_anchors = 3

# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here.
sys.path.insert(0, os.path.abspath("../.."))

# -- Options for sphinx-sitemap ----------------------------------------------
# GitHub Pages URL 설정 (실제 배포 URL로 변경 필요)
html_baseurl = "https://wonjun.github.io/reference-validator/"

# -- Options for sphinxext-opengraph -----------------------------------------
# Open Graph 메타 태그 설정
ogp_site_url = html_baseurl
ogp_description = (
    "BibTeX validator and enricher using Crossref, arXiv, and Google Scholar APIs"
)
ogp_image = f"{html_baseurl}_static/og-image.png"  # 선택사항: 이미지가 있는 경우

# -- Options for sphinx.ext.intersphinx -------------------------------------
# 외부 프로젝트 문서와의 상호 참조 설정
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "bibtexparser": ("https://bibtexparser.readthedocs.io/en/stable/", None),
    "requests": ("https://requests.readthedocs.io/en/stable/", None),
    "fastapi": ("https://fastapi.tiangolo.com/", None),
}

# -- Options for sphinx.ext.todo ---------------------------------------------
# TODO 항목 표시 설정
todo_include_todos = True
todo_link_only = False

# -- Options for sphinx-last-updated-by-git ----------------------------------
# Git 기반 마지막 업데이트 시간 표시
git_last_updated_timezone = "Asia/Seoul"

# -- Options for sphinxcontrib.mermaid ---------------------------------------
# Mermaid 다이어그램 설정 (MyST와 함께 사용 시)
# MyST Parser가 Mermaid를 직접 지원하므로 sphinxcontrib-mermaid는 선택사항
# mermaid_output_format = 'png'  # 또는 'svg'
# mermaid_cmd = 'mmdc'  # mermaid-cli가 설치된 경우에만 사용


# -- Custom Roles Setup (GUI Visuals) ---------------------------------------
rst_prolog = """
.. role:: gui-badge-crossref
   :class: badge badge-source-crossref

.. role:: gui-badge-arxiv
   :class: badge badge-source-arxiv

.. role:: gui-badge-scholar
   :class: badge badge-source-semantic-scholar

.. role:: gui-badge-dblp
   :class: badge badge-source-dblp

.. role:: gui-badge-pubmed
   :class: badge badge-source-pubmed

.. role:: gui-badge-zenodo
   :class: badge badge-source-zenodo

.. role:: gui-badge-datacite
   :class: badge badge-source-datacite

.. role:: gui-badge-openalex
   :class: badge badge-source-openalex

.. role:: gui-status-review
   :class: badge badge-status-review

.. role:: gui-status-conflict
   :class: badge badge-status-conflict

.. role:: gui-status-different
   :class: badge badge-status-different

.. role:: gui-status-identical
   :class: badge badge-status-identical

.. role:: gui-btn-accept
   :class: badge badge-status-accepted

.. role:: gui-btn-reject
   :class: badge badge-status-rejected
"""

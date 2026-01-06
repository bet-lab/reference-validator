import os
import sys
from datetime import date

# -- Project information -----------------------------------------------------
project = "BibTeX Validator"
copyright = f"{date.today().year}, Wonjun"
author = "Wonjun"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_tabs.tabs",
    "sphinxext.opengraph",
    "sphinx_sitemap",
]

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = "shibuya"
html_static_path = ["_static"]
html_title = "BibTeX Validator"

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
ogp_description = "BibTeX validator and enricher using Crossref, arXiv, and Google Scholar APIs"
ogp_image = f"{html_baseurl}_static/og-image.png"  # 선택사항: 이미지가 있는 경우

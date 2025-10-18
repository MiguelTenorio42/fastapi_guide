# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'FastAPI Guide'
copyright = '2025, FastAPI Guide'
author = 'FastAPI Guide'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx_copybutton',
    'sphinx_design',
    'sphinxcontrib.mermaid',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output ------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'quantecon_book_theme'
html_static_path = ['_static']

# -- MyST Parser configuration ----------------------------------------------

myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
    "attrs_inline",
    "attrs_block",
]

# MyST Parser additional configuration
myst_heading_anchors = 3
myst_fence_as_directive = ["mermaid"]

# -- HTML theme options -----------------------------------------------------

html_theme_options = {
    'repository_url': 'https://github.com/seu-usuario/fastapi_guide',
    'use_repository_button': True,
    'use_issues_button': True,
    'use_edit_page_button': True,
    'use_download_button': True,
    'use_fullscreen_button': True,
    'path_to_docs': 'docs/',
    'repository_branch': 'main',
    'launch_buttons': {
        'binderhub_url': '',
        'colab_url': '',
        'deepnote_url': '',
        'notebook_interface': 'classic',
        'thebe': False,
    },
    'home_page_in_toc': True,
    'show_navbar_depth': 2,
}

html_title = "FastAPI Guide - Guia Completo"
html_short_title = "FastAPI Guide"

# -- Copy button configuration ----------------------------------------------

copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# -- Internationalization ---------------------------------------------------

language = 'pt_BR'

# -- Custom CSS and JS ------------------------------------------------------

html_css_files = [
    'custom.css',
]

# -- Source file suffixes ---------------------------------------------------

source_suffix = {
    '.rst': None,
    '.md': None,
}

# -- Master document --------------------------------------------------------

master_doc = 'index'
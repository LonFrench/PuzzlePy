import sys

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PuzzlePy'
copyright = '2025, Lonnie French'
author = 'Lonnie French'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
	'sphinx.ext.autodoc',  # Built-in extension for automatically generating documentation from docstrings
    'sphinx_rtd_theme',
    'sphinx_markdown_builder',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'ui.py', 'drawing.py', 'x_*/*', '*.x_*', 'logs/*']

sys.path.insert(0, 'C:/Lonnie/HeadGamz/Website/puzzlepy/puzzles')
autoapi_dirs = ['../puzzles']

# exclude the below modules from document
autodoc_mock_imports = ['test_data', 'server_ui', 'sudoku_drawing']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
autodoc_member_order = 'bysource'
autodoc_default_options = {
        'members': True,
        'special-members': '__init__, __str__, __eq__',
        'undoc-members': True,
        'exclude-members': '__weakref__'
    }
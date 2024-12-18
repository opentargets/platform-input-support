"""Configuration file for the Sphinx documentation builder."""

import sphinx_rtd_theme
from sphinx.ext.autodoc import ClassDocumenter
from sphinx.locale import _

project = 'pis'
copyright = '2024, Open Targets Team'  # noqa: A001
author = 'Open Targets Team'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinxcontrib.autodoc_pydantic',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'sphinx_issues',
]

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

coverage_show_missing_items = True

# Uncomment the following line if you have defined custom style in ./_static/style.css
# html_css_files = ['style.css']


# -- Options for autodoc pydantic -------------------------------------------
autodoc_pydantic_model_show_json = True
autodoc_pydantic_settings_show_json = False


# -- Remove object base from class documentation -----------------------------
# https://stackoverflow.com/questions/46279030/how-can-i-prevent-sphinx-from-listing-object-as-a-base-class
add_line = ClassDocumenter.add_line
line_to_delete = _('Bases: %s') % ':py:class:`object`'


def add_line_no_object_base(self, text, *args, **kwargs):  # noqa: D103
    if text.strip() == line_to_delete:
        return

    add_line(self, text, *args, **kwargs)


add_directive_header = ClassDocumenter.add_directive_header


def add_directive_header_no_object_base(self, *args, **kwargs):  # noqa: D103
    self.add_line = add_line_no_object_base.__get__(self)
    return add_directive_header(self, *args, **kwargs)


ClassDocumenter.add_directive_header = add_directive_header_no_object_base

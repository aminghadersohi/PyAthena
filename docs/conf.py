# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import re
import subprocess
from datetime import UTC, datetime


def get_version():
    """Get version from git tags.

    This function is used to determine the version for documentation builds.
    For the master branch, we use the latest tag (--abbrev=0) instead of
    git describe's default behavior which would show a dev version like
    "v3.21.2-2-g8d4e41c" when HEAD is ahead of the latest tag.

    This ensures that when master and a tag point to the same commit,
    the documentation shows the clean version (e.g., "3.22.0") regardless
    of whether the tag was created before or after the docs build started.
    """
    # Try to get exact tag (for tagged commits)
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            capture_output=True,
            text=True,
            check=True,
        )
        tag = result.stdout.strip()
        if tag and tag.startswith("v"):
            return tag[1:]  # Remove 'v' prefix
        return tag
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Get the latest tag (without commit count suffix)
    # This is used for master branch builds to show a clean version
    # instead of a dev version like "v3.21.2-2-g8d4e41c"
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True,
        )
        tag = result.stdout.strip()
        if tag and tag.startswith("v"):
            return tag[1:]  # Remove 'v' prefix
        return tag
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback to _version.py (for local development builds)
    try:
        from pyathena._version import __version__

        return __version__
    except ImportError:
        pass

    # Final fallback to importlib.metadata
    try:
        from importlib.metadata import version

        return version("PyAthena")
    except Exception:
        return "unknown"


# -- Setup function ----------------------------------------------------------


def config_inited(app, config):
    """Handler for config-inited event to set version dynamically."""
    smv_current_version = getattr(config, "smv_current_version", None)

    if smv_current_version:
        # sphinx-multiversion sets this to the ref name (e.g., "v3.19.0" or "master")
        if smv_current_version.startswith("v") and smv_current_version[1:2].isdigit():
            # It's a version tag like "v3.19.0"
            ver = smv_current_version[1:]  # Remove 'v' prefix
        else:
            # It's a branch name like "master", use git to get version
            ver = get_version()
    else:
        # Not running under sphinx-multiversion, use git
        ver = get_version()

    config.version = f"v{ver}"
    config.release = f"v{ver}"


def _parse_version_tag(name):
    """Parse a release tag name.

    Args:
        name: Git ref name, e.g. ``v3.36.0`` or ``master``.

    Returns:
        The ``(major, minor, patch)`` integers, or None if the name is not a
        ``vX.Y.Z`` tag.
    """
    match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", name)
    return tuple(int(part) for part in match.groups()) if match else None


def add_versions_newest_first(app, pagename, templatename, context, doctree):
    """Handler for html-page-context event to order the version switcher.

    Adds ``versions_newest_first`` to the template context: the branches
    (``master``) first, then the tags from the newest version to the oldest.
    sphinx-multiversion's own ``versions`` lists tags in ref name order, which
    puts the oldest first and would sort ``v4.10.0`` before ``v4.9.0``.

    Args:
        app: Sphinx application.
        pagename: Name of the page being rendered.
        templatename: Name of the page template.
        context: Template context, updated in place.
        doctree: Doctree of the page, or None for generated pages.
    """
    versions = context.get("versions")
    if versions:
        context["versions_newest_first"] = [
            *versions.branches,
            *sorted(versions.tags, key=lambda item: _parse_version_tag(item.name), reverse=True),
        ]


def setup(app):
    """Sphinx setup hook."""
    app.connect("config-inited", config_inited)
    # Run after sphinx-multiversion adds ``versions`` at the default priority
    app.connect("html-page-context", add_versions_newest_first, priority=600)


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "PyAthena"
copyright = f"2017-{datetime.now(UTC).year}, The PyAthena authors"
author = "The PyAthena authors"
# Version will be set dynamically in setup() function
version = ""
release = ""

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
    "sphinx_multiversion",
    "sphinxext.opengraph",
    "sphinx_design",
]

try:
    import myst_parser  # noqa: F401

    extensions.append("myst_parser")
    source_suffix = {
        ".rst": "restructuredtext",
        ".md": "myst",
    }
    myst_enable_extensions = [
        "colon_fence",
        "fieldlist",
        "deflist",
    ]
except ImportError:
    pass

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

# Autosummary settings
autosummary_generate = True
autosummary_imported_members = False

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "pyarrow": ("https://arrow.apache.org/docs/", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_logo = "_static/icon.png"
html_static_path = ["_static"]
html_css_files = [
    "custom.css",
]

# Furo theme options
html_theme_options = {
    "source_repository": "https://github.com/pyathena-dev/PyAthena/",
    "source_branch": "master",
    "source_directory": "docs/",
}

# Sidebar templates
html_sidebars = {
    "**": [
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/scroll-start.html",
        "sidebar/navigation.html",
        "versioning.html",
        "sidebar/scroll-end.html",
    ]
}

# -- Open Graph protocol settings ----------------------------------------------

ogp_site_url = "https://pyathena.dev/"
ogp_image = "https://pyathena.dev/_static/ogp_white.png"
ogp_description_length = 200
ogp_type = "website"

# -- Sphinx-multiversion configuration ----------------------------------------

# Number of minor versions whose latest patch release is documented
SMV_MINOR_VERSIONS = 3


def _select_documented_tags(count):
    """Select the version tags to document.

    Picks the latest patch tag of each of the newest ``count`` minor versions,
    e.g. ``v3.36.0``, ``v3.35.4`` and ``v3.34.0``. The latest tag of the
    previous major version is added when those minor versions do not include
    it and it has the Sphinx documentation, e.g. ``v3.36.1`` after ``v4.2.0``,
    ``v4.1.0`` and ``v4.0.0``.

    Args:
        count: Number of minor versions to document.

    Returns:
        The selected tag names, newest first. Empty when git is unavailable
        or the configuration directory is not in a git repository, as when
        sphinx-multiversion reads each version's configuration from its
        exported tree. Only the selection from the invoking checkout is used.
    """
    try:
        result = subprocess.run(
            ["git", "tag", "--list", "v*"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    versions = sorted(
        (
            (version, tag)
            for tag in result.stdout.split()
            if (version := _parse_version_tag(tag)) is not None
        ),
        reverse=True,
    )
    if not versions:
        return []

    # Newest first, so the first tag seen for each minor version is its latest patch
    latest = {}
    for (major, minor, _), tag in versions:
        latest.setdefault((major, minor), tag)
    selected = list(latest.values())[:count]

    newest_major = versions[0][0][0]
    previous_major_latest = next(
        (tag for (major, _, _), tag in versions if major < newest_major), None
    )
    if (
        previous_major_latest
        and previous_major_latest not in selected
        and _has_sphinx_docs(previous_major_latest)
    ):
        selected.append(previous_major_latest)
    return selected


def _has_sphinx_docs(tag):
    """Return whether a tag contains the Sphinx documentation.

    Tags before ``v3.5.0``, including all ``v2`` tags, have no ``docs/conf.py``.

    Args:
        tag: Git tag name.

    Returns:
        True if ``docs/conf.py`` exists in the tag.
    """
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{tag}:docs/conf.py"],
        capture_output=True,
    )
    return result.returncode == 0


# Whitelist pattern for tags: only the tags selected above, or none
_documented_tags = _select_documented_tags(SMV_MINOR_VERSIONS)
smv_tag_whitelist = (
    "^(" + "|".join(re.escape(tag) for tag in _documented_tags) + ")$"
    if _documented_tags
    else r"^$"
)

# Whitelist pattern for branches
smv_branch_whitelist = r"^master$"  # Only build master branch

# Whitelist pattern for remotes
smv_remote_whitelist = r"^origin$"  # Only build from origin remote

# Output all versions to the root directory
smv_outputdir_format = "{ref.name}"

# Specify the latest version (used for stable redirect)
smv_latest_version = "master"

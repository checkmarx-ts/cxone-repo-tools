from cxone_api import CxOneClient
from typing import Dict, List
from cxone_api.high.sca.registry import (
    PackageRepositoryConfigurationTag,
    PackageManagerType,
)
from cxone_repo_tools.convert import InvalidRepositoryConfiguration


async def resolve_tag(
    client: CxOneClient, tag_id: str | None, tag_name: str | None
) -> PackageRepositoryConfigurationTag | None:
    """Loads a tag by id, or by name when the id is not given.

    Returns None when no tag matches the name.  Raises
    InvalidRepositoryConfiguration when more than one tag has the name.
    """
    if tag_id is not None:
        return await PackageRepositoryConfigurationTag.retrieve_by_id(client, tag_id)

    tags = await PackageRepositoryConfigurationTag.retrieve_by_name(client, tag_name)

    if len(tags) > 1:
        raise InvalidRepositoryConfiguration.ambiguous_tag_name(
            tag_name, [tag.tagid for tag in tags]
        )

    return tags[0] if len(tags) == 1 else None


# PackageManagerType is an aenum enum in cxone-async-api; pylint cannot infer
# that it is iterable, so iterate it once here.
PACKAGE_MANAGERS = list(PackageManagerType)  # pylint: disable=not-an-iterable

# One command line option per supported package manager type, e.g. --nuget FILE.
PM_OPTIONS = {pm: f"--{pm.value}" for pm in PACKAGE_MANAGERS}


def pm_usage_options() -> str:
    """The usage text for the optional package manager file options."""
    return " ".join(f"[{opt} FILE]" for opt in PM_OPTIONS.values())


def pm_option_docs() -> str:
    """The option description text for the package manager file options."""
    return "\n\n".join(
        f"    {opt + ' FILE':<30}Path to the {pm.value} configuration content file."
        for pm, opt in PM_OPTIONS.items()
    )


def pm_content_files(parsed_args: Dict) -> Dict[PackageManagerType, str]:
    """The file path given for each package manager option that was provided."""
    return {
        pm: parsed_args[opt]
        for pm, opt in PM_OPTIONS.items()
        if parsed_args[opt] is not None
    }


def parse_filters(filters: str | None) -> List[str]:
    """Splits a comma-separated string of ant-style filters into a list, dropping
    empty entries and surrounding whitespace."""
    if filters is None:
        return []
    return [f.strip() for f in filters.split(",") if len(f.strip()) > 0]


def config_file_exclusion(package_manager: PackageManagerType) -> str:
    """The ant-style exclusion filter for a package manager's configuration file."""
    return f"!**/{package_manager.config_file_name}"

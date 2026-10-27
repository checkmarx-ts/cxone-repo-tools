from cxone_api import CxOneClient
import asyncio, logging
from tqdm.asyncio import tqdm
from typing import Callable, Dict, List, Set, Tuple
from cxone_api.high.sca.registry import (
    PackageRepositoryConfiguration,
    PackageRepositoryConfigurationTag,
    PackageManagerType,
)
from cxone_api.high.scan_configuration import ProjectScanConfiguration
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


_log = logging.getLogger(__name__)


async def collect_project_exclusions(
    configs: List[PackageRepositoryConfiguration],
) -> Dict[str, Set[str]]:
    """Re-loads each configuration's project associations and returns, for every
    associated project, the set of SCA exclusion filters for the configuration
    files of the configurations it holds."""
    exclusions: Dict[str, Set[str]] = {}
    for cfg in configs:
        await cfg.refresh_associations()
        for project_id in cfg.associated_projects:
            exclusions.setdefault(project_id, set()).add(
                config_file_exclusion(cfg.packageManager)
            )
    return exclusions


async def __update_project_sca_exclusions(
    client: CxOneClient,
    project_exclusions: Dict[str, Set[str]],
    threads: int,
    compute: Callable[[List[str], Set[str]], Tuple[List[str], List[str]]],
    action: str,
) -> None:
    semaphore = asyncio.Semaphore(threads)

    async def update(project_id: str, filters: Set[str]) -> None:
        async with semaphore:
            project_cfg = ProjectScanConfiguration(client, project_id)
            current = parse_filters(await project_cfg.SCA.Exclusions.getValue())
            changed, new_value = compute(current, filters)
            if len(changed) == 0:
                _log.debug(f"Project {project_id} SCA exclusions already current.")
                return
            await project_cfg.SCA.Exclusions.setValue(",".join(new_value))
            await project_cfg.commit_config()
            _log.info(f"Project {project_id} SCA exclusions {action}: {changed}.")

    await tqdm.gather(
        *[update(pid, filters) for pid, filters in project_exclusions.items()],
        desc=f"{action.capitalize()} project SCA exclusions",
    )


async def add_project_sca_exclusions(
    client: CxOneClient, project_exclusions: Dict[str, Set[str]], threads: int
) -> None:
    """Appends the given exclusion filters to the SCA file exclusions of each
    project.  Filters already present are not added again and projects needing
    no change are not written."""

    def compute(current: List[str], filters: Set[str]) -> Tuple[List[str], List[str]]:
        added = [f for f in sorted(filters) if f not in current]
        return added, current + added

    await __update_project_sca_exclusions(
        client, project_exclusions, threads, compute, "added"
    )


async def remove_project_sca_exclusions(
    client: CxOneClient, project_exclusions: Dict[str, Set[str]], threads: int
) -> None:
    """Removes the given exclusion filters from the SCA file exclusions of each
    project.  Projects that have none of the filters are not written."""

    def compute(current: List[str], filters: Set[str]) -> Tuple[List[str], List[str]]:
        removed = [f for f in current if f in filters]
        return removed, [f for f in current if f not in filters]

    await __update_project_sca_exclusions(
        client, project_exclusions, threads, compute, "removed"
    )

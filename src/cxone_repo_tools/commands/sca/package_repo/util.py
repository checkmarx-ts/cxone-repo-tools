from cxone_api import CxOneClient
from cxone_api.high.sca.registry import PackageRepositoryConfigurationTag
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

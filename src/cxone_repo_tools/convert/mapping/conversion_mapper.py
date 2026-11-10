from abc import ABC, abstractmethod
from pathlib import PurePosixPath
from typing import Tuple
from urllib.parse import urlsplit, urlunsplit
from cxone_repo_tools.exceptions import MappingException


class ConversionMapper(ABC):
    """Base class for mapping the repository URL of a project being converted
    from a source SCM to the corresponding repository URL in the target SCM.

    `convert` replaces the source base URL with the target base URL and the
    organization path segment that follows the base URL with the target
    organization.  Subclasses implement `_map_repo_path` to produce the path
    that follows the target organization from the path that follows the
    source organization.
    """

    @staticmethod
    def __segments(path: str) -> Tuple[str, ...]:
        """Splits a URL path into its segments, without the root.

        :param path: The URL path.
        :type path: str

        :return: The path segments.
        :rtype: Tuple[str, ...]
        """
        return PurePosixPath(path).relative_to(PurePosixPath(path).anchor).parts

    @abstractmethod
    def _map_repo_path(self, path: str) -> str:
        """Maps the path that follows the organization in the source
        repository URL to the path that follows the organization in the
        target repository URL.

        :param path: The relative POSIX path that follows the source
                     organization, for example ``sub/group/repo.git``.  It is
                     ``.`` when the source URL ends at the organization.
        :type path: str

        :return: The relative POSIX path that follows the target organization.
        :rtype: str

        :raises NotImplementedError: The subclass does not implement this
                                     method.
        """
        raise NotImplementedError(ConversionMapper._map_repo_path.__name__)

    def convert(
        self,
        source_repo_base_url: str,
        source_repo_url: str,
        source_repo_org: str,
        target_repo_base_url: str,
        target_repo_org: str,
    ) -> str:
        """Builds the target repository URL for a source repository URL.

        The scheme, host, base path, and organization are compared without
        regard to case.  Trailing slashes on the base URLs are ignored, and the
        query and fragment of the source URL are kept.

        :param source_repo_base_url: The base URL of the source SCM, for
                                     example ``https://github.com``.
        :type source_repo_base_url: str

        :param source_repo_url: The URL of the source repository.
        :type source_repo_url: str

        :param source_repo_org: The organization that owns the source
                                repository.  It must be the path segment that
                                follows the source base URL.
        :type source_repo_org: str

        :param target_repo_base_url: The base URL of the target SCM.
        :type target_repo_base_url: str

        :param target_repo_org: The organization that owns the repository in
                                the target SCM.
        :type target_repo_org: str

        :return: The target repository URL.
        :rtype: str

        :raises MappingException: The source repository URL is not under the
                                  source base URL, or the path segment after
                                  the base URL is not the source organization.
        """
        source_base = urlsplit(source_repo_base_url)
        source = urlsplit(source_repo_url)

        base_segments = ConversionMapper.__segments(source_base.path)
        source_segments = ConversionMapper.__segments(source.path)
        prefix = source_segments[: len(base_segments)]

        if (
            source.scheme.casefold() != source_base.scheme.casefold()
            or source.netloc.casefold() != source_base.netloc.casefold()
            or [s.casefold() for s in prefix] != [s.casefold() for s in base_segments]
        ):
            raise MappingException.url_not_under_base(
                source_repo_url, source_repo_base_url
            )

        org_and_path = source_segments[len(base_segments) :]
        if (
            len(org_and_path) == 0
            or org_and_path[0].casefold() != source_repo_org.casefold()
        ):
            raise MappingException.org_not_in_url(source_repo_url, source_repo_org)

        mapped = self._map_repo_path(str(PurePosixPath(*org_and_path[1:])))

        target_base = urlsplit(target_repo_base_url)
        target_path = PurePosixPath(
            "/",
            *ConversionMapper.__segments(target_base.path),
            target_repo_org,
            *ConversionMapper.__segments(mapped),
        )

        return urlunsplit(
            (
                target_base.scheme,
                target_base.netloc,
                str(target_path),
                source.query,
                source.fragment,
            )
        )

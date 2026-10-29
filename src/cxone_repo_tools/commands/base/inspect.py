import aiofiles
from typing import Dict, List
from cxone_api.high.sca.registry import (
    PackageRepositoryConfiguration,
    PackageManagerType,
)
from .command import Command


class AbstractInspectCommand(Command):
    """Shared output formatting for commands that inspect SCA private package
    repository configurations."""

    # The subject named in the duplicate package manager warning.
    _DUPLICATE_SUBJECT = "the project"

    @classmethod
    def _configuration_warnings(
        cls,
        cfg: PackageRepositoryConfiguration,
        first_of_type: Dict[PackageManagerType, PackageRepositoryConfiguration],
    ) -> List[str]:
        warnings = []

        first = first_of_type.get(cfg.packageManager)
        if first is not None and first is not cfg:
            warnings.append(
                f"A {cfg.packageManager.value} configuration is already associated with "
                f"{cls._DUPLICATE_SUBJECT}: {first.name} ({first.configId}). Multiple "
                "configurations of the same package manager type produce undefined "
                "SCA scan results."
            )

        if len(cfg.associated_tags) > 1:
            warnings.append(
                f"The configuration is associated with {len(cfg.associated_tags)} tags. "
                "Multiple tags may make it difficult to manage updates to the configuration."
            )

        return warnings

    @classmethod
    def _format_configuration(
        cls,
        index: int,
        cfg: PackageRepositoryConfiguration,
        first_of_type: Dict[PackageManagerType, PackageRepositoryConfiguration],
    ) -> str:
        lines = [f"{index}. {cfg.name} ({cfg.configId}) [{cfg.packageManager.value}]"]

        lines.append("  Content:")
        lines.extend(f"    {line}" for line in (cfg.content or "").splitlines())

        lines.append("  Associated Projects:")
        lines.extend(
            [f"    {project_id}" for project_id in cfg.associated_projects]
            or ["    NONE"]
        )

        lines.append("  Tags:")
        lines.extend(
            [f"    {tag.name} ({tag.tagid})" for tag in cfg.associated_tags]
            or ["    NONE"]
        )

        warnings = cls._configuration_warnings(cfg, first_of_type)
        if len(warnings) > 0:
            lines.append("  Warnings:")
            lines.extend(f"    {warning}" for warning in warnings)

        return "\n".join(lines)

    @classmethod
    def _format_configurations(
        cls, heading: str, configs: List[PackageRepositoryConfiguration]
    ) -> str:
        first_of_type = {}
        for cfg in configs:
            first_of_type.setdefault(cfg.packageManager, cfg)

        text = heading + "\n"
        if len(configs) > 0:
            text += "\n---\n".join(
                cls._format_configuration(index, cfg, first_of_type)
                for index, cfg in enumerate(configs, start=1)
            )
            text += "\n"
        else:
            text += "  NONE\n"

        return text

    @staticmethod
    async def _write_output(text: str, out_file: str | None) -> None:
        if out_file is not None and len(out_file) > 0:
            async with aiofiles.open(out_file, "wt", encoding="UTF-8") as out:
                await out.write(text)
        else:
            print(text, end="", flush=True)

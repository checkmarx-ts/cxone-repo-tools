import aiocsv
from typing import List, Dict
from .base import BaseExport


class ScmExport(BaseExport):
    """Exports the SCMs configured in the tenant to a CSV file, using the SCM
    data held by the export's SCM project index."""

    async def _prep_for_export(self):
        """Retrieves the SCM list into the index before the CSV file is
        opened, so a retrieval failure does not leave an empty export.
        """
        await self._index.get_scm_ids()

    @property
    def _field_names(self) -> List[str]:
        return [
            "scm_id",
            "scm_type",
            "scm_base_url",
            "scm_instance_name",
            "scm_self_hosted",
        ]

    async def _generate_row(self, scm_dict: Dict) -> Dict:
        return {
            "scm_id": scm_dict.get("id"),
            "scm_type": scm_dict.get("type"),
            "scm_base_url": scm_dict.get("repoBaseUrl"),
            "scm_instance_name": scm_dict.get("instanceName"),
            "scm_self_hosted": scm_dict.get("onPrem", False),
        }

    async def _write_rows(self, writer: aiocsv.AsyncDictWriter) -> None:
        """Writes one row for each SCM in the index.

        :param writer: The CSV writer.
        :type writer: aiocsv.AsyncDictWriter
        """
        for scm_id in await self._index.get_scm_ids():
            scm = await self._index.get_scm_data(scm_id)
            await writer.writerow(await self._generate_row(scm))

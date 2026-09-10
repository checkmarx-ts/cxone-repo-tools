from __future__ import annotations
from typing import List, Iterable
from ..consts import DISCO_API_FLAG


class ConversionException(Exception):

    @staticmethod
    def incompatible(
        source_id: int, source_type: str, dest_id: int, dest_type: str
    ) -> ConversionException:
        return ConversionException(
            f"Source SCM {source_id} ({source_type}) is not compatible for converting to SCM {dest_id} ({dest_type})"
        )

    @staticmethod
    def target_scm_not_found(scm_id: int) -> ConversionException:
        return ConversionException(f"Target SCM ID {scm_id} not found")

    @staticmethod
    def source_scms_not_found(scm_ids: List[int]) -> ConversionException:
        return ConversionException(f"Source SCM IDs {scm_ids} not found")

    @staticmethod
    def scm_base_urls_different(base_urls: Iterable):
        return ConversionException(
            f"SCM base urls domains must be the same: {base_urls}"
        )

    @staticmethod
    def disconnect_api_ff_not_enabled():
        return ConversionException(
            f"Feature flag {DISCO_API_FLAG} is not enabled on this tenant."
        )

    @staticmethod
    def failure_enable_sast_incrementals(project_name: str):
        return ConversionException(
            f"Failed to enable SAST incremental scans for project {project_name}"
        )

"""Shared Apify client helpers."""

from __future__ import annotations


def get_default_dataset_id(run: object) -> str:
    """Extract default dataset ID from Apify run (dict or Run model)."""
    if isinstance(run, dict):
        dataset_id = run.get("defaultDatasetId") or run.get("default_dataset_id")
        if dataset_id:
            return str(dataset_id)
        raise KeyError("defaultDatasetId not found in Apify run response")

    dataset_id = getattr(run, "default_dataset_id", None) or getattr(run, "defaultDatasetId", None)
    if dataset_id:
        return str(dataset_id)

    raise TypeError(f"Unsupported Apify run type: {type(run)!r}")

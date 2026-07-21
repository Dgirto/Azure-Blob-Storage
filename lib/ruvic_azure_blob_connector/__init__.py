"""Conector Ruvic para gestión de blobs en Azure Blob Storage."""

from .client import AzureBlobClient
from .config import ENV_PREFIX, AzureBlobConfig
from .exceptions import (
    AzureBlobAuthError,
    AzureBlobConnectorError,
    AzureBlobDataError,
    AzureBlobNetworkError,
)
from .logging_utils import setup_logging

__all__ = [
    "ENV_PREFIX",
    "AzureBlobAuthError",
    "AzureBlobClient",
    "AzureBlobConfig",
    "AzureBlobConnectorError",
    "AzureBlobDataError",
    "AzureBlobNetworkError",
    "setup_logging",
]

__version__ = "1.0.0"

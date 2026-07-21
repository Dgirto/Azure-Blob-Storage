"""Excepciones propias del conector Azure Blob Storage.

Separan los tres tipos de fallo que el usuario debe distinguir:
autenticación, red/servidor y datos. Nunca exponemos excepciones
crípticas del SDK subyacente.
"""


class AzureBlobConnectorError(Exception):
    """Error base del conector."""


class AzureBlobAuthError(AzureBlobConnectorError):
    """Credenciales inválidas o permisos insuficientes."""


class AzureBlobNetworkError(AzureBlobConnectorError):
    """No se pudo alcanzar el servicio (red, timeout, error temporal de Azure)."""


class AzureBlobDataError(AzureBlobConnectorError):
    """La operación es válida pero el contenedor/blob no existe o los datos son inválidos."""

"""Cliente de gestión de blobs en Azure Blob Storage.

Capacidades:
- list_blobs():      listar blobs de un contenedor (con prefijo opcional).
- upload_blob():     subir contenido a un blob.
- download_blob():   descargar el contenido de un blob.

Las credenciales SIEMPRE provienen de variables de entorno
RUVIC_AZURE_BLOB_* (ver config.AzureBlobConfig.from_env). Prohibido
hardcodearlas.

El conector opera sobre un único contenedor configurado (principio de
mínimo privilegio: la Shared Access Signature o el rol RBAC del usuario
debe limitarse a ese contenedor).
"""

from __future__ import annotations

from typing import Any

from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ResourceNotFoundError,
    ServiceRequestError,
)
from azure.storage.blob import ContainerClient

from .config import AzureBlobConfig
from .exceptions import (
    AzureBlobAuthError,
    AzureBlobConnectorError,
    AzureBlobDataError,
    AzureBlobNetworkError,
)
from .logging_utils import get_logger

_MAX_LIST_LIMIT = 1_000


def _validate_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise AzureBlobDataError("name no puede estar vacío.")
    return name


def _wrap_error(exc: Exception, not_found_message: str) -> AzureBlobConnectorError:
    """Traduce un error del SDK de Azure a una excepción propia, sin dejar
    escapar nunca el tipo crudo del SDK."""
    if isinstance(exc, ClientAuthenticationError):
        return AzureBlobAuthError(
            "Credenciales inválidas o sin permiso suficiente sobre este "
            "contenedor. Revisa la clave de cuenta o el SAS token."
        )
    if isinstance(exc, ResourceNotFoundError):
        return AzureBlobDataError(not_found_message)
    if isinstance(exc, HttpResponseError):
        return AzureBlobDataError(f"Error de datos (HTTP {exc.status_code}): {exc.message}")
    return AzureBlobDataError(f"Error de datos: {exc}")


class AzureBlobClient:
    """Cliente de gestión de blobs en un contenedor de Azure Blob Storage.

    Args:
        config: configuración de conexión. Si se omite, se lee de las
            variables de entorno RUVIC_AZURE_BLOB_* (comportamiento
            estándar en el runtime de la plataforma).

    Ejemplo:
        >>> client = AzureBlobClient()      # lee RUVIC_AZURE_BLOB_* del entorno
        >>> client.list_blobs(prefix="reportes/")
        [{'name': 'reportes/2026-07.csv', 'size': 15234, 'last_modified': '2026-07-17T10:00:00Z'}]
    """

    def __init__(self, config: AzureBlobConfig | None = None) -> None:
        self.config = config or AzureBlobConfig.from_env()
        self._logger = get_logger()
        self._container_client: ContainerClient | None = None

    # ------------------------------------------------------------------ #
    # Conexión
    # ------------------------------------------------------------------ #

    def _get_container_client(self) -> ContainerClient:
        if self._container_client is not None:
            return self._container_client
        account_url = f"https://{self.config.account_name}.blob.core.windows.net"
        self._container_client = ContainerClient(
            account_url=account_url,
            container_name=self.config.container,
            credential=self.config.account_key,
            connection_timeout=self.config.connect_timeout,
        )
        return self._container_client

    def ping(self) -> bool:
        """Verifica la conexión comprobando que el contenedor existe.

        Returns:
            True si la conexión funciona.

        Raises:
            AzureBlobAuthError / AzureBlobNetworkError / AzureBlobDataError.
        """
        try:
            self._get_container_client().get_container_properties()
        except ClientAuthenticationError as exc:
            raise _wrap_error(exc, "") from exc
        except ResourceNotFoundError as exc:
            raise AzureBlobDataError(
                f"El contenedor {self.config.container!r} no existe."
            ) from exc
        except ServiceRequestError as exc:
            raise AzureBlobNetworkError(
                f"No se pudo conectar a la cuenta {self.config.account_name!r} "
                f"(timeout {self.config.connect_timeout}s). Verifica el nombre "
                "de la cuenta y el acceso de red."
            ) from exc
        except HttpResponseError as exc:
            raise _wrap_error(exc, "") from exc
        self._logger.info(
            "Ping exitoso al contenedor %s de %s", self.config.container, self.config.account_name
        )
        return True

    # ------------------------------------------------------------------ #
    # Capacidad 1: listar blobs
    # ------------------------------------------------------------------ #

    def list_blobs(self, prefix: str = "", limit: int = 100) -> list[dict[str, Any]]:
        """Lista los blobs del contenedor configurado.

        Args:
            prefix: solo blobs cuyo nombre empiece con este prefijo (ej.
                "reportes/"). Default "" (todos).
            limit: máximo de blobs a retornar (default 100, máximo 1000).

        Returns:
            Lista de dicts: {"name", "size", "last_modified"}.

        Ejemplo:
            >>> client.list_blobs(prefix="reportes/", limit=10)
            [{'name': 'reportes/2026-07.csv', 'size': 15234, 'last_modified': '2026-07-17T10:00:00Z'}]
        """
        limit = max(1, min(int(limit), _MAX_LIST_LIMIT))
        client = self._get_container_client()
        try:
            blobs = client.list_blobs(name_starts_with=prefix or None, results_per_page=limit)
            result = []
            for blob in blobs:
                result.append(
                    {
                        "name": blob.name,
                        "size": blob.size,
                        "last_modified": blob.last_modified.isoformat()
                        if blob.last_modified
                        else None,
                    }
                )
                if len(result) >= limit:
                    break
        except ClientAuthenticationError as exc:
            raise _wrap_error(exc, "") from exc
        except ResourceNotFoundError as exc:
            raise AzureBlobDataError(
                f"El contenedor {self.config.container!r} no existe."
            ) from exc
        except (ServiceRequestError, HttpResponseError) as exc:
            raise _wrap_error(exc, "") from exc

        self._logger.info(
            "Se listaron %d blobs (prefix=%r) en %s", len(result), prefix, self.config.container
        )
        return result

    # ------------------------------------------------------------------ #
    # Capacidad 2: subir un blob
    # ------------------------------------------------------------------ #

    def upload_blob(
        self,
        name: str,
        content: bytes | str,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        """Sube contenido a un blob del contenedor configurado (crea el
        blob o sobrescribe uno existente con el mismo nombre).

        Args:
            name: nombre (ruta) del blob dentro del contenedor.
            content: contenido a subir. Un str se codifica como UTF-8.
            content_type: MIME type del blob (opcional, ej. "text/csv").

        Returns:
            Dict con: name, size (bytes subidos).

        Ejemplo:
            >>> client.upload_blob("reportes/resumen.txt", "Ventas: 1200")
            {'name': 'reportes/resumen.txt', 'size': 12}
        """
        name = _validate_name(name)
        body = content.encode("utf-8") if isinstance(content, str) else content
        client = self._get_container_client()
        kwargs: dict[str, Any] = {"overwrite": True}
        if content_type:
            from azure.storage.blob import ContentSettings

            kwargs["content_settings"] = ContentSettings(content_type=content_type)
        try:
            client.upload_blob(name=name, data=body, **kwargs)
        except ClientAuthenticationError as exc:
            raise _wrap_error(exc, "") from exc
        except ResourceNotFoundError as exc:
            raise AzureBlobDataError(
                f"El contenedor {self.config.container!r} no existe."
            ) from exc
        except (ServiceRequestError, HttpResponseError) as exc:
            raise _wrap_error(exc, "") from exc
        self._logger.info('Subido blob "%s" (%d bytes)', name, len(body))
        return {"name": name, "size": len(body)}

    # ------------------------------------------------------------------ #
    # Capacidad 3: descargar un blob
    # ------------------------------------------------------------------ #

    def download_blob(self, name: str) -> dict[str, Any]:
        """Descarga el contenido de un blob del contenedor configurado.

        Args:
            name: nombre (ruta) del blob dentro del contenedor.

        Returns:
            Dict con: name, content (bytes), content_type, size.

        Ejemplo:
            >>> result = client.download_blob("reportes/resumen.txt")
            >>> result["content"].decode("utf-8")
            'Ventas: 1200'
        """
        name = _validate_name(name)
        client = self._get_container_client()
        try:
            downloader = client.download_blob(name)
            content = downloader.readall()
            content_type = downloader.properties.content_settings.content_type
        except ClientAuthenticationError as exc:
            raise _wrap_error(exc, "") from exc
        except ResourceNotFoundError as exc:
            raise AzureBlobDataError(
                f'El blob "{name}" no existe en el contenedor {self.config.container!r}.'
            ) from exc
        except (ServiceRequestError, HttpResponseError) as exc:
            raise _wrap_error(exc, "") from exc
        self._logger.info('Descargado blob "%s" (%d bytes)', name, len(content))
        return {
            "name": name,
            "content": content,
            "content_type": content_type,
            "size": len(content),
        }

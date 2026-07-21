"""Configuración del conector leída desde variables de entorno.

Convención de la plataforma: cada campo del formulario de configuración
llega como variable de entorno {ENV_PREFIX}{CAMPO} en mayúsculas.
Para este conector el prefijo es RUVIC_AZURE_BLOB_.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

ENV_PREFIX = "RUVIC_AZURE_BLOB_"


@dataclass(frozen=True)
class AzureBlobConfig:
    """Parámetros de conexión a Azure Blob Storage."""

    account_name: str
    account_key: str
    container: str
    connect_timeout: int = 10

    @classmethod
    def from_env(cls) -> "AzureBlobConfig":
        """Construye la configuración desde las variables RUVIC_AZURE_BLOB_*.

        Raises:
            ValueError: si falta alguna variable obligatoria.

        Ejemplo:
            >>> config = AzureBlobConfig.from_env()
            >>> config.container
            'mi-contenedor-produccion'
        """
        missing = [
            f"{ENV_PREFIX}{name}"
            for name in ("ACCOUNT_NAME", "ACCOUNT_KEY", "CONTAINER")
            if not os.environ.get(f"{ENV_PREFIX}{name}")
        ]
        if missing:
            raise ValueError(
                "Faltan variables de entorno del conector azure_blob: "
                + ", ".join(missing)
                + ". Configura el conector en Settings → Conectores."
            )
        return cls(
            account_name=os.environ[f"{ENV_PREFIX}ACCOUNT_NAME"],
            account_key=os.environ[f"{ENV_PREFIX}ACCOUNT_KEY"],
            container=os.environ[f"{ENV_PREFIX}CONTAINER"],
            connect_timeout=int(os.environ.get(f"{ENV_PREFIX}CONNECT_TIMEOUT", "10")),
        )

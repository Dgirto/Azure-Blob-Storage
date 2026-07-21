"""Prueba de conexión estándar del conector azure_blob.

Firma estándar Ruvic: def test_connection() -> tuple[bool, str]
- Lee la configuración EXCLUSIVAMENTE de las env vars RUVIC_AZURE_BLOB_*.
- Nunca lanza excepciones; retorna (ok, mensaje).

Ejecutable también como script para pruebas locales:
    python test_connection.py
"""

from __future__ import annotations


def test_connection() -> tuple[bool, str]:
    """Verifica acceso al contenedor configurado usando las env vars
    RUVIC_AZURE_BLOB_*."""
    try:
        from ruvic_azure_blob_connector import (
            AzureBlobAuthError,
            AzureBlobClient,
            AzureBlobDataError,
            AzureBlobNetworkError,
        )
    except ImportError:
        return (
            False,
            "La librería ruvic-azure-blob-connector no está instalada. "
            "Instala con: pip install git+https://github.com/Dgirto/"
            "Azure-Blob-Storage.git#subdirectory=lib",
        )

    try:
        client = AzureBlobClient()  # valida que existan las env vars
    except ValueError as exc:
        return False, str(exc)

    try:
        client.ping()
    except AzureBlobAuthError as exc:
        return False, f"Autenticación fallida: {exc}"
    except AzureBlobNetworkError as exc:
        return False, f"Error de red: {exc}"
    except AzureBlobDataError as exc:
        return False, f"Error de datos: {exc}"
    except Exception as exc:  # red de seguridad: jamás propagar
        return False, f"Error inesperado: {exc}"

    return (
        True,
        f"Conexión exitosa al contenedor {client.config.container!r} de "
        f"{client.config.account_name!r}",
    )


if __name__ == "__main__":
    ok, message = test_connection()
    print(f"{'OK' if ok else 'FALLO'}: {message}")
    raise SystemExit(0 if ok else 1)

---
name: azure-blob-storage
description: >
  Usa la librería ruvic_azure_blob_connector para gestionar blobs en un
  contenedor de Azure Blob Storage - listar blobs con prefijo
  (list_blobs), subir contenido a un blob (upload_blob) y descargar el
  contenido de un blob (download_blob). Úsala cuando el usuario pida
  subir, descargar o listar archivos en un contenedor de Azure Storage.
triggers:
- azure blob
- azure storage
- blob storage
- contenedor de azure
- subir archivo
- descargar archivo
---

# Conector Azure Blob Storage (ruvic_azure_blob_connector)

Librería Python para gestionar blobs en un contenedor de Azure Blob Storage. Está **preinstalada en el runtime** cuando el conector está configurado (si no, instálala con `pip install git+https://github.com/Dgirto/Azure-Blob-Storage.git#subdirectory=lib`).

## Regla crítica de credenciales

El código generado **NUNCA hardcodea credenciales**. Siempre se leen de variables de entorno, disponibles cuando el conector `azure_blob` está configurado:

| Variable | Contenido |
|----------|-----------|
| `RUVIC_AZURE_BLOB_ACCOUNT_NAME` | Nombre de la cuenta de almacenamiento |
| `RUVIC_AZURE_BLOB_ACCOUNT_KEY` | Clave de acceso de la cuenta |
| `RUVIC_AZURE_BLOB_CONTAINER` | Contenedor sobre el que opera el conector |
| `RUVIC_AZURE_BLOB_CONNECT_TIMEOUT` | (opcional) timeout en segundos |

Si estas variables NO existen, el conector no está configurado: no generes código que lo use; indica al usuario que lo configure en **Settings → Conectores**.

## Este conector escribe (upload)

`upload_blob` sube (o sobrescribe) contenido en el contenedor configurado. No es de solo lectura.

## Conexión (siempre igual)

```python
from ruvic_azure_blob_connector import AzureBlobClient

client = AzureBlobClient()  # lee RUVIC_AZURE_BLOB_* del entorno automáticamente
```

Todas las operaciones actúan sobre el contenedor único configurado en `RUVIC_AZURE_BLOB_CONTAINER`.

## Capacidad 1 — Listar blobs

```python
blobs = client.list_blobs(prefix="reportes/", limit=50)
for b in blobs:
    print(f"{b['name']}: {b['size']} bytes, modificado {b['last_modified']}")
```

## Capacidad 2 — Subir un blob

```python
client.upload_blob("reportes/resumen.txt", "Ventas: 1200 unidades")
client.upload_blob("reportes/datos.csv", contenido_bytes, content_type="text/csv")
```

`content` acepta `str` (se codifica como UTF-8) o `bytes` directamente.

## Capacidad 3 — Descargar un blob

```python
result = client.download_blob("reportes/resumen.txt")
texto = result["content"].decode("utf-8")
print(texto)
```

`content` siempre viene como `bytes`; decodifica según el tipo de archivo.

## Manejo de errores

```python
from ruvic_azure_blob_connector import (
    AzureBlobAuthError, AzureBlobDataError, AzureBlobNetworkError,
)

try:
    client.upload_blob("clave", "contenido")
except AzureBlobAuthError:
    print("Credenciales inválidas o sin permiso sobre el contenedor")
except AzureBlobNetworkError:
    print("No se pudo alcanzar Azure Storage — revisa el nombre de cuenta y el acceso de red")
except AzureBlobDataError as e:
    print(f"Error de datos: {e}")  # ej. el blob no existe
```

## Buenas prácticas al generar código

1. Lee credenciales SOLO de las variables `RUVIC_AZURE_BLOB_*` (el constructor de `AzureBlobClient` ya lo hace).
2. Nunca imprimas `RUVIC_AZURE_BLOB_ACCOUNT_KEY` en logs ni en la salida.
3. Usa `limit` razonable en `list_blobs` (default 100, máximo 1000); para contenedores grandes pide al usuario que acote el `prefix`.
4. `upload_blob` siempre sobrescribe si el blob ya existe; si eso no es lo que el usuario quiere, léelo primero con `download_blob` para confirmar.

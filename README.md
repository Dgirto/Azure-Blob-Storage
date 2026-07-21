# Conector Azure Blob Storage (CON-026)

Conector Ruvic para gestión de blobs en un contenedor de Azure Blob
Storage. Permite listar blobs, subir contenido y descargar blobs.

## Instalación

```bash
pip install git+https://github.com/Dgirto/Azure-Blob-Storage.git#subdirectory=lib
```

Python 3.10+. Dependencia única: `azure-storage-blob>=12.19,<13.0`.

## Permisos requeridos en Azure

Crea una cuenta de almacenamiento dedicada o usa un contenedor específico
con acceso restringido (no reutilizar la clave de administrador para
todo). Opciones:

**Opción A — Clave de cuenta** (más simple, acceso a toda la cuenta):
En Azure Portal → cuenta de almacenamiento → Claves de acceso → copia
`key1`. Nota: la clave de cuenta da acceso a **todos** los contenedores
de esa cuenta, no solo al configurado; para restringir el acceso usa la
Opción B.

**Opción B — SAS token restringido al contenedor** (recomendado para
producción): en el contenedor → Generar SAS → permisos Read, Write, List
→ copia el token generado y úsalo como `account_key` en su lugar (el SDK
acepta ambos formatos).

## Variables de entorno (`RUVIC_AZURE_BLOB_*`)

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `RUVIC_AZURE_BLOB_ACCOUNT_NAME` | Sí | Nombre de la cuenta de almacenamiento |
| `RUVIC_AZURE_BLOB_ACCOUNT_KEY` | Sí | Clave de acceso o SAS token |
| `RUVIC_AZURE_BLOB_CONTAINER` | Sí | Contenedor sobre el que opera el conector |
| `RUVIC_AZURE_BLOB_CONNECT_TIMEOUT` | No (default `10`) | Timeout de conexión en segundos |

## Pruebas locales

Con Azure real, o con [Azurite](https://github.com/Azure/Azurite) (emulador
local) para no tocar una cuenta real:

```bash
docker run -d --name azurite-test -p 10000:10000 mcr.microsoft.com/azure-storage/azurite

az storage container create --name ruvic-test --connection-string "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
```

> Azurite usa una cuenta y clave de desarrollo fijas y públicas (no son
> un secreto real). El SDK apunta al endpoint real de Azure por defecto;
> para usar Azurite con este conector tal cual está escrito necesitarías
> una cuenta y contenedor reales en Azure, o adaptar el cliente para
> aceptar un `account_url` alternativo.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ./lib

export RUVIC_AZURE_BLOB_ACCOUNT_NAME=tu-cuenta
export RUVIC_AZURE_BLOB_ACCOUNT_KEY=tu-clave-de-acceso
export RUVIC_AZURE_BLOB_CONTAINER=ruvic-test

python test_connection.py
python validate_local.py
```

Prueba también los casos de error (credenciales incorrectas, contenedor
inexistente, blob inexistente) y verifica que los mensajes sean claros.

## Notas de integración

- El conector opera sobre **un único contenedor** (configurado en
  `RUVIC_AZURE_BLOB_CONTAINER`).
- `upload_blob` acepta `str` (se codifica UTF-8) o `bytes` directamente;
  `download_blob` siempre retorna `bytes` en el campo `content`.
- `upload_blob` siempre usa `overwrite=True`: si el blob ya existe, se
  reemplaza sin aviso previo.

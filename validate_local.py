"""Validación local del conector azure_blob: ejercita las 3 capacidades.

Uso:
    python validate_local.py

Requiere las variables RUVIC_AZURE_BLOB_* exportadas en el entorno,
apuntando a un contenedor real (o Azurite para pruebas locales) donde la
cuenta tenga permiso de lectura y escritura. No necesita ningún blob
previo: sube uno de prueba, lo lista y lo descarga.
"""

from ruvic_azure_blob_connector import AzureBlobClient, setup_logging

setup_logging("INFO")
client = AzureBlobClient()

print("== 1. Subir blob de prueba ==")
uploaded = client.upload_blob(
    "ruvic/validate_local/prueba.txt", "Contenido de prueba de validate_local.py"
)
print(f"  {uploaded}")

print("== 2. Listar blobs (prefijo ruvic/validate_local/) ==")
blobs = client.list_blobs(prefix="ruvic/validate_local/", limit=10)
for blob in blobs:
    print(f"  {blob['name']} ({blob['size']} bytes, {blob['last_modified']})")
assert any(b["name"] == "ruvic/validate_local/prueba.txt" for b in blobs), "No aparece el blob subido"

print("== 3. Descargar el blob ==")
downloaded = client.download_blob("ruvic/validate_local/prueba.txt")
text = downloaded["content"].decode("utf-8")
print(f"  contenido={text!r} size={downloaded['size']}")
assert text == "Contenido de prueba de validate_local.py", "El contenido descargado no coincide"

print("\nTodo OK: upload_blob, list_blobs y download_blob funcionan.")

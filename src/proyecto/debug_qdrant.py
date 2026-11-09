# debug_qdrant.py
from qdrant_client import QdrantClient

QDRANT_PATH = "./qdrant_local"
COLLECTION_NAME = "vivo_knowledge_base"

client = QdrantClient(path=QDRANT_PATH)

# Inspeccionar información de la colección
info = client.get_collection(collection_name=COLLECTION_NAME)
print(f"Total de vectores almacenados en Qdrant: {info.points_count}")

# Scroll para ver los primeros 3 puntos almacenados
puntos, _ = client.scroll(
    collection_name=COLLECTION_NAME,
    limit=3,
    with_payload=True,
    with_vectors=False
)

print("\n--- Ejemplo de payloads en Qdrant ---")
for p in puntos:
    print(f"ID: {p.id} | Tipo: {p.payload.get('entity_type')} | Nombre/Título: {p.payload.get('name') or p.payload.get('title')}")

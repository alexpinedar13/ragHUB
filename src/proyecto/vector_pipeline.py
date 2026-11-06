# vector_pipeline.py
import json
import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configuración de rutas y parámetros
CORPUS_FILE = "vivo_corpus.json"
# Usamos un modelo multilingüe eficiente para procesar texto en español e inglés
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# Configuración de Qdrant (modo local basado en disco o cliente conectado a contenedor Docker)
# Si ejecutas Qdrant en Docker local: url="http://localhost:6333"
# Si prefieres almacenamiento puramente local sin levantar un servidor separado: path="./qdrant_local"
QDRANT_PATH = "./qdrant_local"
COLLECTION_NAME = "vivo_knowledge_base"

def cargar_corpus(filepath: str) -> list[dict]:
    """Carga el corpus JSON generado en el paso anterior."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No se encontró el archivo {filepath}. Ejecuta primero el etl_pipeline.py")
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def generarEmbeddingsGuardar():
    print("--- [RAG VIVO] Iniciando proceso de vectorización y almacenamiento ---")
    
    # 1. Cargar el corpus
    corpus = cargar_corpus(CORPUS_FILE)
    print(f"Se cargaron {len(corpus)} chunks desde el corpus.")
    
    # 2. Inicializar el modelo de embeddings local
    print(f"Cargando modelo de embeddings: {EMBEDDING_MODEL_NAME}...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    # 3. Inicializar el cliente de Qdrant en modo local (persiste en la carpeta indicada)
    print(f"Conectando a Qdrant (Ruta de almacenamiento local: {QDRANT_PATH})...")
    client = QdrantClient(path=QDRANT_PATH)
    
    # 4. Crear o recrear la colección en Qdrant
    # Obtenemos la dimensión del embedding automáticamente del modelo (ej: 384 para MiniLM)
    vector_size = model.get_sentence_embedding_dimension()
    
    if client.collection_exists(collection_name=COLLECTION_NAME):
        print(f"La colección '{COLLECTION_NAME}' ya existe. Actualizando/Agregando puntos...")
    else:
        print(f"Creando nueva colección en Qdrant: '{COLLECTION_NAME}' con dimensión {vector_size}...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE # Distancia Coseno para similitud semántica
            )
        )
    
    # 5. Preparar los datos para inserción por lotes
    textos = [item["text"] for item in corpus]
    
    print("Generando vectores de embedding localmente...")
    # encode genera los vectores de manera optimizada (puedes usar batch_size si el corpus es muy grande)
    embeddings = model.encode(textos, show_progress_bar=True, convert_to_numpy=True)
    
    puntos = []
    for idx, item in enumerate(corpus):
        # Qdrant requiere un ID numérico entero o UUID. Usaremos un índice incremental o el hash del ID.
        point_id = idx + 1 
        
        # Payload: Guardamos todo el metadato útil para que el LLM y el recuperador lo usen
        payload = {
            "chunk_id": item["chunk_id"],
            "entity_type": item["entity_type"],
            "uri": item["uri"],
            "text": item["text"],
            **item["metadata"] # Desempaqueta nombre, email, título, DOI, etc.
        }
        
        puntos.append(
            models.PointStruct(
                id=point_id,
                vector=embeddings[idx].tolist(),
                payload=payload
            )
        )
    
    # 6. Insertar los puntos en Qdrant
    print(f"Insertando {len(puntos)} vectores en Qdrant...")
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=puntos
    )
    
    print(f"\n¡Éxito! Base de datos vectorial creada y poblada correctamente en '{QDRANT_PATH}'.")

if __name__ == "__main__":
    generarEmbeddingsGuardar()
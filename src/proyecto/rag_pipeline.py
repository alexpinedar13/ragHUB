# rag_pipeline.py
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import ollama

# Configuración
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
QDRANT_PATH = "./qdrant_local"
COLLECTION_NAME = "vivo_knowledge_base"
OLLAMA_MODEL = "llama3"  # O puedes usar "mistral", "phi3", etc.

def buscar_en_qdrant(query: str, top_k: int = 3) -> list[dict]:
    """Vectoriza la pregunta y busca los chunks más relevantes en la base vectorial Qdrant."""
    print(f"\n[Retrieval] Vectorizando consulta y buscando en Qdrant...")
    
    # 1. Cargar modelo de embedding y vectorizar la pregunta
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    query_vector = model.encode(query).tolist()
    
    # 2. Conectar a Qdrant local
    client = QdrantClient(path=QDRANT_PATH)
    
    # 3. Realizar búsqueda por similitud de coseno
    search_results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k
    )
    
    # 4. Extraer el payload (texto y metadatos/URIs)
    resultados_recuperados = []
    for scored_point in search_results.points:
        payload = scored_point.payload
        resultados_recuperados.append({
            "text": payload.get("text"),
            "uri": payload.get("source_url"),
            "name_or_title": payload.get("name") or payload.get("title", "Recurso VIVO"),
            "score": scored_point.score
        })
        
    return resultados_recuperados

def generar_respuesta_rag(query: str):
    # Paso A: Recuperar contexto relevante (Retrieval)
    contextos = buscar_en_qdrant(query, top_k=3)
    
    if not contextos:
        print("No se encontró información relevante en la base de datos vectorial.")
        return

    # Construir el bloque de contexto para el prompt del LLM
    contexto_texto = ""
    referencias = set()
    
    for idx, ctx in enumerate(contextos, 1):
        contexto_texto += f"\n[Fuente {idx}]:\n{ctx['text']}\nURL Oficial: {ctx['uri']}\n"
        referencias.add(f"- [{ctx['name_or_title']}]({ctx['uri']})")

    # Paso B: Diseñar el System Prompt y User Prompt para el LLM
    system_prompt = (
        "Eres un asistente académico experto basado en el sistema VIVO Lyrasis. "
        "Responde a la pregunta del usuario utilizando **únicamente** la información provista en las Fuentes de Contexto. "
        "Al finalizar tu respuesta, debes listar obligatoriamente las fuentes oficiales utilizadas en formato de enlaces Markdown, "
        "empleando los links (URIs) provistos en el contexto."
    )

    user_prompt = f"""
Pregunta del usuario: {query}

Fuentes de Contexto:
{contexto_texto}
"""

    print(f"\n[Generation] Enviando contexto y pregunta al LLM local ({OLLAMA_MODEL} vía Ollama)...")
    
    # Paso C: Invocación al LLM local con Ollama
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        options={"temperature": 0.1} # Temperatura baja para que sea estrictamente fiel al contexto
    )

    # Mostrar la respuesta generada
    print("\n" + "="*50)
    print("RESPUESTA DEL ASISTENTE RAG:")
    print("="*50)
    print(response['message']['content'])
    print("\n" + "-"*50)
    print("ENLACES Y FUENTES OFICIALES DE VIVO RECUPERADAS:")
    print("-"*50)
    for ref in referencias:
        print(ref)
    print("="*50)

if __name__ == "__main__":
    # Ejemplo de consulta interactiva de prueba
    pregunta_usuario = "¿Quién es Juan Pérez y cuáles son sus publicaciones o áreas de investigación?"
    
    # Puedes cambiar la pregunta por lo que desees consultar en tu base de datos de VIVO
    print(f"Pregunta formulada: '{pregunta_usuario}'")
    generar_respuesta_rag(pregunta_usuario)
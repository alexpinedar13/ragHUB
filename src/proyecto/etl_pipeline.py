import requests
import json
from typing import List, Dict
from query.sparql_queries import QUERY_PEOPLE, QUERY_PUBLICATIONS

# URL del endpoint SPARQL de tu instancia de VIVO (ej: http://localhost:8080/vivo/sparql)
# VIVO_SPARQL_ENDPOINT = "http://localhost:8080/vivo/sparql"
VIVO_SPARQL_ENDPOINT = "http://10.194.194.96:8080/api/sparqlQuery"
VIVO_USER = "root-hub@urosario.edu.co"
VIVO_PASS = "I&PViV02025$"

def ejecutar_sparql(query: str) -> list[dict]:
    """Ejecuta una consulta SPARQL contra el endpoint de VIVO y retorna los resultados en JSON."""
    headers = {"Accept": "application/sparql-results+json"}
    data = {
	    "email": VIVO_USER,
        "password": VIVO_PASS,
        "query": query
    }
    response = requests.post(VIVO_SPARQL_ENDPOINT, data=data, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        bindings = data["results"]["bindings"]
        
        # Limpiar y extraer los valores del formato JSON de SPARQL
        resultados_limpios = []
        for row in bindings:
            item = {k: v["value"] for k, v in row.items()}
            resultados_limpios.append(item)
        return resultados_limpios
    else:
        raise Exception(f"Error en consulta SPARQL: {response.status_code} - {response.text}")

def construir_corpus_y_chunks(people_data: List[Dict], pub_data: List[Dict]) -> List[Dict]:
    """
    Transforma los datos tabulares de las tripletas en chunks semánticos narrativos,
    conservando la URI original para trazabilidad web por parte del LLM.
    """
    corpus_chunks = []

    # 1. Chunking de Investigadores (Personas)
    for p in people_data:
        uri = p.get("person")
        name = p.get("name", "Investigador sin nombre")
        email = p.get("email", "No registrado")
        overview = p.get("overview", "Sin biografía o descripción detallada disponible.")

        # Construcción del texto narrativo optimizado para modelos de embedding
        texto_narrativo = (
            f"Perfil de Investigador: {name}. "
            f"Correo de contacto: {email}. "
            f"Resumen profesional y líneas de investigación: {overview}"
        )

        corpus_chunks.append({
            "chunk_id": f"person_{abs(hash(uri))}",
            "entity_type": "person",
            "uri": uri,
            "text": texto_narrativo,
            "metadata": {
                "name": name,
                "email": email,
                "source_url": uri
            }
        })

    # 2. Chunking de Publicaciones
    for pub in pub_data:
        uri = pub.get("pub")
        title = pub.get("title", "Sin título")
        abstract = pub.get("abstract", "Sin resumen disponible.")
        date = pub.get("date", "Fecha desconocida")
        doi = pub.get("doi", "No disponible")
        type_doc = pub.get("typeDoc", "Documento académico")
        
        # Limpieza de autores concatenados por el GROUP_CONCAT
        autores_brutos = pub.get("autores", "")
        autores_lista = [a.strip() for a in autores_brutos.split("|") if a.strip()]
        autores_texto = f"Autores: {', '.join(autores_lista)}." if autores_lista else "Autores no especificados."

        # Construcción del texto narrativo optimizado
        texto_narrativo = (
            f"Tipo de documento: {type_doc}. "
            f"Título de la publicación: '{title}'. "
            f"Fecha de publicación: {date}. "
            f"{autores_texto} "
            f"Resumen: {abstract} "
            f"DOI: {doi}"
        )

        corpus_chunks.append({
            "chunk_id": f"pub_{abs(hash(uri))}",
            "entity_type": "publication",
            "uri": uri,
            "text": texto_narrativo,
            "metadata": {
                "title": title,
                "doi": doi,
                "date": date,
                "source_url": uri
            }
        })

    return corpus_chunks

if __name__ == "__main__":
    print("--- [ETL VIVO] Iniciando extracción de tripletas y generación de corpus ---")
    try:
        # Extracción ejecutando las consultas importadas de sparql_queries.py
        print("Ejecutando consulta SPARQL de Personas...")
        raw_people = ejecutar_sparql(QUERY_PEOPLE)
        
        print("Ejecutando consulta SPARQL de Publicaciones...")
        raw_pubs = ejecutar_sparql(QUERY_PUBLICATIONS)
        
        # Procesamiento y unificación en chunks
        corpus = construir_corpus_y_chunks(raw_people, raw_pubs)
        
        print(f"\n¡Proceso finalizado! Se generaron {len(corpus)} chunks semánticos.")
        
        if corpus:
            print("\nEjemplo de chunk procesado:")
            print(json.dumps(corpus[0], indent=2, ensure_ascii=False))
            
        # Guardado local del corpus para la siguiente fase de Embeddings
        output_filename = "vivo_corpus.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(corpus, f, ensure_ascii=False, indent=2)
            print(f"\nCorpus guardado exitosamente en '{output_filename}'.")
            
    except Exception as e:
        print(f"\n[Error en el pipeline]: {e}")
        print("Asegúrate de que el endpoint SPARQL de tu VIVO esté activo o ajusta la URL local.")
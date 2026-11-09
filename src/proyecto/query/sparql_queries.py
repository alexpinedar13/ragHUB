# sparql_queries.py

# 1. Consulta para extraer Investigadores (Personas) y sus URIs
QUERY_PEOPLE = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX vivo: <http://vivoweb.org/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX vcard:    <http://www.w3.org/2006/vcard/ns#>
PREFIX vlocal:   <http://research-hub.urosario.edu.co/ontology/vlocal#>
PREFIX obo:      <http://purl.obolibrary.org/obo/>

SELECT ?person ?name ?email ?overview 
WHERE {
    ?person a foaf:Person.
  	?person a vlocal:UREntity; rdfs:label ?name .
  	FILTER (LANGMATCHES(LANG(?name), "es") || LANG(?name) = "")
    OPTIONAL { ?person obo:ARG_2000028 ?nodo1.
      	       ?nodo1 vcard:hasEmail ?nodo2.
    			?nodo2 vcard:email ?email }
    OPTIONAL { ?person vivo:overview ?overview 
  				FILTER (LANGMATCHES(LANG(?overview), "es") || LANG(?overview) = "")
  }
}
#LIMIT 50
"""

# 2. Consulta para extraer Publicaciones, sus URIs y su autoría
QUERY_PUBLICATIONS = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX bibo: <http://purl.org/ontology/bibo/>
PREFIX vivo: <http://vivoweb.org/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX vitro:    <http://vitro.mannlib.cornell.edu/ns/vitro/0.7#>
PREFIX vlocal:   <http://research-hub.urosario.edu.co/ontology/vlocal#>

SELECT ?pub ?title ?abstract ?date ?doi (GROUP_CONCAT(?autor; SEPARATOR="|") AS ?autores)  (SAMPLE(?type) AS ?typeDoc)
WHERE {
    ?pub a bibo:Document; rdfs:label ?title.
  		FILTER (LANGMATCHES(LANG(?title), "es") || LANG(?title) = "")
    OPTIONAL { ?pub bibo:abstract ?abstract
  		FILTER (LANGMATCHES(LANG(?abstract), "es") || LANG(?abstract) = "")}
	OPTIONAL { ?pub bibo:doi ?doi }
	OPTIONAL {
    	?pub a bibo:Document; vitro:mostSpecificType ?nodo.
    	?nodo rdfs:label ?type
    	#FILTER (LANGMATCHES(LANG(?type), "es") || LANG(?type) = "").
    FILTER (LANGMATCHES(LANG(?type), "en-US"))
  		}
     OPTIONAL {
        ?pub a bibo:Document; vivo:dateTimeValue ?nodo2.
        ?nodo2 vivo:dateTime ?date		
      }
  	OPTIONAL{
  		?pub vivo:relatedBy ?nodo3.
        ?nodo3 a vivo:Authorship; vivo:relates ?autor.
        ?autor a vlocal:UREntity.	
  }
}
GROUP BY ?pub ?title ?abstract ?date ?doi ?autores
#LIMIT 50
"""

import os
import pandas as pd
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# Importación condicional para la parte opcional
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("Advertencia: sentence-transformers no está instalado. La parte opcional no funcionará.")

# Descargar recursos necesarios de NLTK (solo la primera vez)
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)

class MotorRecomendacion:
    def __init__(self, base_path_noticias):
        """
        Inicializa el motor, carga las noticias y entrena los modelos.
        :param base_path_noticias: Ruta a la carpeta raiz de noticias (ej: 'SSII/noticias')
        """
        self.base_path = base_path_noticias
        self.df = pd.DataFrame()
        
        # Modelos
        self.vectorizer_tfidf = None
        self.matrix_tfidf = None
        self.model_embeddings = None
        self.matrix_embeddings = None
        
        # 1. Cargar datos
        self._cargar_noticias()
        
        # 2. Preprocesar
        print("Preprocesando textos...")
        self.df['texto_procesado'] = self.df['contenido_completo'].apply(self._preprocesar_texto)
        
        # 3. Entrenar BoW + TF-IDF (Obligatorio)
        print("Generando vectores TF-IDF...")
        self._entrenar_tfidf()
        
        # 4. Entrenar Embeddings (Opcional)
        if EMBEDDINGS_AVAILABLE:
            print("Generando Embeddings (esto puede tardar un poco)...")
            self._generar_embeddings()

    def _cargar_noticias(self):
        """Recorre las carpetas y carga los .txt generados por el scraper."""
        data = []
        # Recorremos recursivamente
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith(".txt") and "enlaceen" not in file: # Ignoramos los archivos de control
                    path = os.path.join(root, file)
                    try:
                        # Asumimos el formato de tu scraper: fecha;titulo;cuerpo;fecha_extraccion
                        with open(path, "r", encoding="utf-8") as f:
                            line = f.read().strip()
                            parts = line.split(";")
                            if len(parts) >= 3:
                                # Unimos título y cuerpo para una mejor recomendación
                                titulo = parts[1]
                                cuerpo = parts[2]
                                contenido_completo = f"{titulo}. {cuerpo}"
                                
                                data.append({
                                    "filename": file,
                                    "titulo": titulo,
                                    "cuerpo": cuerpo,
                                    "contenido_completo": contenido_completo,
                                    "categoria": os.path.basename(os.path.dirname(os.path.dirname(path))) # Intentar sacar categoria del path
                                })
                    except Exception as e:
                        print(f"Error leyendo {file}: {e}")
        
        self.df = pd.DataFrame(data)
        # Creamos un ID numérico para facilitar referencias
        self.df['id'] = range(len(self.df))
        print(f"Noticias cargadas: {len(self.df)}")

    def _preprocesar_texto(self, texto):
        """Tokeniza, pasa a minúsculas y elimina stopwords."""
        if not isinstance(texto, str):
            return ""
        
        # 1. Minúsculas
        texto = texto.lower()
        
        # 2. Tokenización
        tokens = word_tokenize(texto, language='spanish')
        
        # 3. Stopwords (en español)
        stop_words = set(stopwords.words('spanish'))
        
        # Filtrado de tokens (quitamos signos de puntuación y stopwords)
        tokens_limpios = [word for word in tokens if word.isalnum() and word not in stop_words]
        
        return " ".join(tokens_limpios)

    def _entrenar_tfidf(self):
        """Configura y entrena el vectorizador TF-IDF (Bag of Words avanzado)."""
        # Usamos TfidfVectorizer que combina CountVectorizer (BoW) + TfidfTransformer
        self.vectorizer_tfidf = TfidfVectorizer()
        self.matrix_tfidf = self.vectorizer_tfidf.fit_transform(self.df['texto_procesado'])

    def _generar_embeddings(self):
        """Carga un modelo pre-entrenado y genera embeddings semánticos."""
        # 'paraphrase-multilingual-MiniLM-L12-v2' funciona muy bien para español
        self.model_embeddings = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        # Generamos embeddings del contenido original (los transformers manejan bien el contexto, no necesitan tanto preproceso)
        self.matrix_embeddings = self.model_embeddings.encode(self.df['contenido_completo'].tolist(), show_progress_bar=True)

    def _calcular_similitud(self, vector_query, matriz_documentos, top_n=5, exclude_index=None):
        """Función genérica para calcular coseno y ordenar resultados."""
        # Calcular similitud de coseno
        # cosine_similarity devuelve una matriz, tomamos la primera fila [0]
        similitudes = cosine_similarity(vector_query, matriz_documentos)[0]
        
        # Obtener índices ordenados de mayor a menor similitud
        indices_ordenados = similitudes.argsort()[::-1]
        
        resultados = []
        i = 0
        total_docs = len(indices_ordenados)
        
        # REFACTORIZADO: Usamos un while con condición compuesta para evitar 'break' y 'continue' (volvemos a resubir por este problema)
        while len(resultados) < top_n and i < total_docs:
            idx = indices_ordenados[i]
            
            # Solo procesamos si NO es el índice a excluir
            if exclude_index is None or idx != exclude_index:
                resultados.append({
                    "id": self.df.iloc[idx]['id'],
                    "titulo": self.df.iloc[idx]['titulo'],
                    "similitud": round(float(similitudes[idx]), 4),
                    "contenido_preview": self.df.iloc[idx]['cuerpo'][:150] + "..."
                })
            
            i += 1
                
        return resultados

    # --- FUNCIONES PÚBLICAS REQUERIDAS ---

    def recomendar_por_texto(self, query, metodo='tfidf', top_n=5):
        """
        Recomendación basada en una búsqueda de texto libre (Query).
        """
        print(f"--- Recomendando por Query ('{query}') usando {metodo} ---")
        
        if metodo == 'tfidf':
            query_procesada = self._preprocesar_texto(query)
            vector_query = self.vectorizer_tfidf.transform([query_procesada])
            return self._calcular_similitud(vector_query, self.matrix_tfidf, top_n)
        
        elif metodo == 'embeddings' and EMBEDDINGS_AVAILABLE:
            vector_query = self.model_embeddings.encode([query])
            return self._calcular_similitud(vector_query, self.matrix_embeddings, top_n)
        
        else:
            return []

    def recomendar_por_noticia(self, id_noticia, metodo='tfidf', top_n=5):
        """
        Recomendación basada en similitud con una noticia existente (Item-to-Item).
        """
        if id_noticia not in self.df['id'].values:
            print("ID de noticia no encontrado.")
            return []

        titulo_ref = self.df.loc[self.df['id'] == id_noticia, 'titulo'].values[0]
        print(f"--- Noticias similares a: '{titulo_ref}' usando {metodo} ---")
        
        # Obtenemos el índice numérico en el DataFrame
        idx = self.df.index[self.df['id'] == id_noticia][0]
        
        if metodo == 'tfidf':
            vector_ref = self.matrix_tfidf[idx]
            return self._calcular_similitud(vector_ref, self.matrix_tfidf, top_n, exclude_index=idx)
        
        elif metodo == 'embeddings' and EMBEDDINGS_AVAILABLE:
            # Reshape necesario para que sea (1, n_features)
            vector_ref = self.matrix_embeddings[idx].reshape(1, -1)
            return self._calcular_similitud(vector_ref, self.matrix_embeddings, top_n, exclude_index=idx)
        
        else:
            return []

    def comparar_resultados(self, query=None, id_noticia=None):
        """Imprime una comparación visual entre ambos métodos."""
        if not EMBEDDINGS_AVAILABLE:
            print("No se puede comparar, Embeddings no disponibles.")
            return

        print("\n" + "="*60)
        print(" COMPARACIÓN DE MODELOS")
        print("="*60)

        if query:
            res_tfidf = self.recomendar_por_texto(query, metodo='tfidf')
            res_emb = self.recomendar_por_texto(query, metodo='embeddings')
            label = f"Query: {query}"
        elif id_noticia is not None:
            res_tfidf = self.recomendar_por_noticia(id_noticia, metodo='tfidf')
            res_emb = self.recomendar_por_noticia(id_noticia, metodo='embeddings')
            label = f"Noticia ID: {id_noticia}"
        else:
            return

        print(f"\nResultados para [{label}]:\n")
        
        # Crear un DataFrame temporal para mostrar lado a lado
        data_comp = []
        max_len = max(len(res_tfidf), len(res_emb))
        
        for i in range(max_len):
            row = {}
            if i < len(res_tfidf):
                row['TF-IDF Título'] = res_tfidf[i]['titulo'][:40]
                row['TF-IDF Score'] = res_tfidf[i]['similitud']
            if i < len(res_emb):
                row['Embeddings Título'] = res_emb[i]['titulo'][:40]
                row['Embeddings Score'] = res_emb[i]['similitud']
            data_comp.append(row)
            
        df_comp = pd.DataFrame(data_comp)
        print(df_comp.to_string(index=False))
        print("="*60 + "\n")

# --- USO DEL CÓDIGO (EJEMPLO MAIN) ---
if __name__ == "__main__":
    # Ajusta esta ruta a donde tengas tu carpeta 'noticias'
    # Como el script está en src/, subimos un nivel para encontrar 'noticias'
    ruta_noticias = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "noticias")
    
    motor = MotorRecomendacion(ruta_noticias)
    
    if not motor.df.empty:
        # 1. Ejemplo Query
        resultados = motor.recomendar_por_texto("caída de bitcoin y criptomonedas", metodo='tfidf')
        
        # 2. Ejemplo por ID (usamos la primera noticia cargada como ejemplo)
        primer_id = motor.df.iloc[0]['id']
        motor.recomendar_por_noticia(primer_id, metodo='tfidf')
        
        # 3. Comparación (Opcional)
        motor.comparar_resultados(query="hackers roban millones en cripto")
    else:
        print("No se encontraron noticias. Ejecuta primero scraping.py")
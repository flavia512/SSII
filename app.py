# app.py
import os
import sys
import re
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

NOTICIAS_DIR_DEFAULT = os.path.join(BASE_DIR, "noticias")


@st.cache_resource(show_spinner=False)
def build_engine(noticias_dir: str):
    """
    Construye el motor UNA sola vez (cacheado por Streamlit).
    Si NLTK no tiene recursos (punkt/stopwords), el motor puede fallar:
    lo capturamos arriba en la UI con un mensaje claro.
    """
    from motor_recomendacion import MotorRecomendacion  # del ZIP
    return MotorRecomendacion(base_path_noticias=noticias_dir)


def _format_date_maybe(value) -> str:
    if value is None:
        return "Sin fecha"
    try:
        dt = pd.to_datetime(value, errors="coerce")
        if pd.isna(dt):
            return str(value)
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(value)


def _extract_id_from_label(label: str) -> int | None:
    """
    Extrae el id desde un label tipo: "[123] (cat) titulo..."
    Devuelve None si no encuentra el patrón.
    """
    if label is None:
        return None
    m = re.search(r"\[(\d+)\]", str(label))
    if not m:
        return None
    return int(m.group(1))


def main():
    st.set_page_config(page_title="Recomendador de Noticias", layout="wide")
    st.title("Recomendador de Noticias")

    # -------------------------
    # Sidebar: configuración
    # -------------------------
    st.sidebar.header("Configuración")

    noticias_dir = st.sidebar.text_input(
        "Ruta carpeta noticias/",
        value=os.getenv("NEWS_DIR", NOTICIAS_DIR_DEFAULT),
        help="Debe apuntar a la carpeta que contiene las categorías con .txt",
    )

    metodo = st.sidebar.selectbox(
        "Método de recomendación",
        options=["tfidf", "embeddings"],
        index=0,
        help="TF-IDF es el obligatorio. Embeddings es opcional si está instalado sentence-transformers.",
    )

    top_n = st.sidebar.slider("Top N recomendaciones", 3, 15, 5, 1)

    st.sidebar.divider()
    modo = st.sidebar.radio(
        "Modo",
        options=[
            "Lista + búsqueda (ver detalle y recomendar por noticia)",
            "Recomendar por query (texto libre)",
        ],
    )

    # -------------------------
    # Construir motor
    # -------------------------
    try:
        with st.spinner("Inicializando motor de recomendación..."):
            motor = build_engine(noticias_dir)
    except Exception as e:
        st.error("No se pudo inicializar el motor de recomendación.")
        st.code(str(e))
        st.info(
            "Posibles causas típicas:\n"
            "- La ruta 'noticias/' no existe o no contiene .txt.\n"
            "- NLTK no tiene recursos descargados (punkt/stopwords).\n\n"
            "Solución recomendada (una vez):\n"
            "python -m nltk.downloader punkt stopwords\n"
        )
        return

    df = motor.df.copy()
    if df.empty:
        st.warning("El motor cargó 0 noticias. Verifica la ruta a la carpeta 'noticias/'.")
        return

    # -------------------------
    # Layout principal
    # -------------------------
    col_left, col_right = st.columns([1, 2], gap="large")

    # =========================================================
    # MODO 1: Lista + búsqueda + seleccionar noticia + recomendar
    # =========================================================
    if modo.startswith("Lista"):
        with col_left:
            st.subheader("Lista de noticias")

            search = st.text_input("Buscar (título o cuerpo)", value="")

            if search.strip():
                # regex=False para tratar el texto literalmente (frases, símbolos, etc.)
                mask = (
                    df["titulo"].astype(str).str.contains(search, case=False, na=False, regex=False)
                    | df["cuerpo"].astype(str).str.contains(search, case=False, na=False, regex=False)
                )
                view = df[mask].copy()
            else:
                view = df.copy()

            st.caption(f"Mostrando: {len(view)} / {len(df)}")

            # Si no hay resultados, no intentes construir selectbox ni hacer split
            if view.empty:
                st.warning("No hay resultados para esa búsqueda.")
                st.stop()

            # Label legible (id + título + categoría)
            view = view.reset_index(drop=True)
            view["label"] = view.apply(
                lambda r: f"[{r['id']}] ({r.get('categoria','')}) {str(r.get('titulo',''))[:90]}",
                axis=1,
            )

            labels = view["label"].tolist()
            selected_label = st.selectbox("Selecciona una noticia", labels)

            selected_id = _extract_id_from_label(selected_label)
            if selected_id is None:
                st.error("No pude extraer el ID de la noticia seleccionada.")
                st.stop()

        with col_right:
            selected_rows = df[df["id"] == selected_id]
            if selected_rows.empty:
                st.error(f"No existe una noticia con id={selected_id} en el dataset.")
                st.stop()

            sel = selected_rows.iloc[0]

            st.subheader("Detalle de la noticia seleccionada")
            st.markdown(f"**Título:** {sel.get('titulo','')}")
            st.markdown(f"**Categoría:** {sel.get('categoria','')}")
            st.markdown(f"**Fecha:** {_format_date_maybe(sel.get('fecha', None))}")
            st.markdown(f"**Enlace:** {sel.get('enlace','') if 'enlace' in sel else 'No disponible en dataset'}")

            with st.expander("Contenido", expanded=True):
                # El motor guarda "contenido_completo" según el loader
                st.write(sel.get("contenido_completo", sel.get("cuerpo", "")))

            st.divider()
            st.subheader("Recomendaciones (por noticia)")

            try:
                recs = motor.recomendar_por_noticia(selected_id, metodo=metodo, top_n=top_n)
            except Exception as e:
                st.error("Error generando recomendaciones.")
                st.code(str(e))
                return

            if not recs:
                st.info("No hay recomendaciones para esta noticia (o el método no está disponible).")
                return

            # Mostrar recomendaciones enriquecidas con datos reales del df
            for rec in recs:
                rec_id = rec.get("id", None)
                sim = rec.get("similitud", None)

                if rec_id is not None and (df["id"] == rec_id).any():
                    row = df[df["id"] == rec_id].iloc[0]
                    title = row.get("titulo", rec.get("titulo", ""))
                    cat = row.get("categoria", "")
                    body = row.get("contenido_completo", row.get("cuerpo", ""))
                else:
                    title = rec.get("titulo", "")
                    cat = ""
                    body = rec.get("contenido_preview", "")

                st.markdown(f"**[{rec_id}] {title}**")
                st.caption(f"Categoría: {cat} | Similitud: {sim}")
                with st.expander("Ver contenido"):
                    st.write(body)
                st.divider()

    # =========================================================
    # MODO 2: Recomendación por query (texto libre)
    # =========================================================
    else:
        with col_left:
            st.subheader("Query (texto libre)")
            query = st.text_area(
                "Escribe una consulta (keywords, frase, tema)",
                value="",
                height=120,
            )
            st.caption("Este modo es obligatorio según el enunciado (recomendar a partir de una consulta).")

        with col_right:
            st.subheader("Recomendaciones (por query)")

            if not query.strip():
                st.info("Escribe una query para generar recomendaciones.")
                return

            try:
                recs = motor.recomendar_por_texto(query, metodo=metodo, top_n=top_n)
            except Exception as e:
                st.error("Error generando recomendaciones por query.")
                st.code(str(e))
                return

            if not recs:
                st.info("No hubo recomendaciones para esa query.")
                return

            for rec in recs:
                rec_id = rec.get("id", None)
                sim = rec.get("similitud", None)

                if rec_id is not None and (df["id"] == rec_id).any():
                    row = df[df["id"] == rec_id].iloc[0]
                    title = row.get("titulo", rec.get("titulo", ""))
                    cat = row.get("categoria", "")
                    body = row.get("contenido_completo", row.get("cuerpo", ""))
                else:
                    title = rec.get("titulo", "")
                    cat = ""
                    body = rec.get("contenido_preview", "")

                st.markdown(f"**[{rec_id}] {title}**")
                st.caption(f"Categoría: {cat} | Similitud: {sim}")
                with st.expander("Ver contenido"):
                    st.write(body)
                st.divider()


if __name__ == "__main__":
    main()

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import datetime

options = webdriver.EdgeOptions()
options.add_argument("--log-level=3")
options.add_argument("--disable-logging")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")

driver = webdriver.Edge(
    service=Service(os.path.join(os.getcwd(), "msedgedriver.exe")),
    options=options
)

driver.get("https://news.bitcoin.com/es/")

wait = WebDriverWait(driver, 10)

# Aceptar cookies
try:
    boton_rechazar = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.fc-button.fc-cta-do-not-consent.fc-secondary-button")
        )
    )
    boton_rechazar.click()
except:
    print("No apareció el botón de rechazar consentimiento")
time.sleep(5)  # Espera a que la página cargue después de rechazar cookies
contenedor = wait.until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, "div.sc-bfabSb.gvquir")
    )
)
time.sleep(10)  # Espera adicional para asegurar que el contenido dinámico se cargue
# Scroll varias veces para cargar todo el contenido dinámico
for _ in range(5):  # Ajusta el rango según lo que observes en la web
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # Espera a que cargue más contenido

# Diccionario de palabras clave para cada archivo
CLASIFICACION = {
    "tecnologia": ["seguridad", "tecnologia", "defi","fintech", "tecnología","defi"],
    "finanzas": ["finanzas", "economía", "economia", "mercados", "precio", "markets", "economics"],
    "gobiernos": ["regulacion", "regulación", "gobierno", "politica", "ley"],
}

# Diccionario para almacenar los enlaces por archivo
enlaces_por_categoria = {cat: [] for cat in CLASIFICACION}

print("\nTodos los h2 que están envueltos por un enlace (a):")
all_h2s = driver.find_elements(By.TAG_NAME, "h2")
for h2 in all_h2s:
    try:
        parent_a = h2.find_element(By.XPATH, "./ancestor::a[1]")
        nombre_categoria = h2.text.strip().lower()
        href_categoria = parent_a.get_attribute("href")
        print(f"h2: {nombre_categoria} | Enlace: {href_categoria}")
        # Clasificar y guardar (sin break)
        for cat, palabras in CLASIFICACION.items():
            if any(palabra in nombre_categoria for palabra in palabras):
                if href_categoria not in enlaces_por_categoria[cat]:
                    enlaces_por_categoria[cat].append(href_categoria)
    except:
        continue

# Guardar los enlaces en archivos por categoría, evitando duplicados
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
noticias_dir = os.path.join(base_dir, "noticias")
os.makedirs(noticias_dir, exist_ok=True)

for cat, enlaces in enlaces_por_categoria.items():
    if not enlaces:
        continue
    subfolder = os.path.join(noticias_dir, cat)
    os.makedirs(subfolder, exist_ok=True)
    file_path = os.path.join(subfolder, f"{cat}.txt")

    # Leer enlaces existentes
    enlaces_existentes = set()
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            enlaces_existentes = set(line.strip() for line in f if line.strip())

    # Guardar solo los nuevos enlaces
    nuevos_enlaces = [enlace for enlace in enlaces if enlace not in enlaces_existentes]
    with open(file_path, "a", encoding="utf-8") as f:
        for enlace in nuevos_enlaces:
            f.write(enlace + "\n")
    print(f"Guardados {len(nuevos_enlaces)} enlaces nuevos en {file_path}")

    # Ahora, para cada enlace, entra y guarda todos los <a href="..."> dentro del div.sc-bfabSb.gvquir en enlaceen.txt, evitando duplicados
    enlaces_extraidos = set()
    max_paginas = 3  # Cambia este valor si quieres más o menos páginas

    for enlace in enlaces:
        for pagina in range(1, max_paginas + 1):
            if pagina == 1:
                url = enlace
            else:
                if enlace.endswith('/'):
                    url = f"{enlace}page/{pagina}/"
                else:
                    url = f"{enlace}/page/{pagina}/"
            try:
                driver.get(url)
                time.sleep(5)  # Espera a que cargue la página
                for _ in range(3):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(4)
                # Buscar solo dentro del div con la clase específica
                try:
                    div_contenedor = driver.find_element(By.CSS_SELECTOR, "div.sc-bfabSb.gvquir")
                    a_tags = div_contenedor.find_elements(By.TAG_NAME, "a")
                    for a in a_tags:
                        href = a.get_attribute("href")
                        if href and href.startswith("http"):
                            enlaces_extraidos.add(href)
                except Exception as e:
                    print(f"No se encontró el div principal en {url}: {e}")
            except Exception as e:
                print(f"Error accediendo a {url}: {e}")

    # Guardar los enlaces extraídos en enlaceen.txt, evitando duplicados
    enlaceen_path = os.path.join(subfolder, "enlaceen.txt")
    enlaces_en_archivo = set()
    if os.path.exists(enlaceen_path):
        with open(enlaceen_path, "r", encoding="utf-8") as f:
            enlaces_en_archivo = set(line.strip() for line in f if line.strip())

    nuevos_enlaces_extraidos = [href for href in enlaces_extraidos if href not in enlaces_en_archivo]
    with open(enlaceen_path, "a", encoding="utf-8") as f:
        for href in nuevos_enlaces_extraidos:
            f.write(href + "\n")
    print(f"Guardados {len(nuevos_enlaces_extraidos)} enlaces nuevos en {enlaceen_path}")

# EXTRAER Y GUARDAR TODAS LAS NOTICIAS INDIVIDUALES EN FORMATO CSV
for cat in CLASIFICACION:
    subfolder = os.path.join(noticias_dir, cat)
    noticias_folder = os.path.join(subfolder, "noticias")
    os.makedirs(noticias_folder, exist_ok=True)
    enlaceen_path = os.path.join(subfolder, "enlaceen.txt")
    if not os.path.exists(enlaceen_path):
        continue

    with open(enlaceen_path, "r", encoding="utf-8") as f:
        enlaces_noticias = [line.strip() for line in f if line.strip()]

    # Procesar todas las noticias
    for url in enlaces_noticias:
        try:
            driver.get(url)
            time.sleep(4)
            # Fecha de publicación
            try:
                fecha_pub = driver.find_element(By.CSS_SELECTOR, "span.sc-dhNZpn.bSTjtI").text.strip()
            except:
                fecha_pub = "Fecha no encontrada"
            # Título
            try:
                titulo = driver.find_element(By.CSS_SELECTOR, "h1.sc-hrAiUm.hEjuKt").text.strip()
                nombre_archivo = "_".join(titulo.split()[:4]).replace("/", "-").replace("\\", "-")
            except:
                titulo = "Título no encontrado"
                nombre_archivo = "noticia_sin_titulo"
            # Texto de la noticia
            cuerpo = []
            try:
                div_body = driver.find_element(By.CSS_SELECTOR, "div.article__body")
                p_tags = div_body.find_elements(By.XPATH, "./p[not(*)]")
                for p in p_tags:
                    texto = p.text.strip()
                    if texto:
                        cuerpo.append(texto)
            except:
                cuerpo = []

            # Fecha de extracción
            fecha_extraccion = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Guardar noticia en formato CSV-like (separado por ;)
            noticia_path = os.path.join(noticias_folder, f"{nombre_archivo}.txt")
            with open(noticia_path, "w", encoding="utf-8") as nf:
                cuerpo_unido = " | ".join(cuerpo)
                nf.write(f"{fecha_pub};{titulo};{cuerpo_unido};{fecha_extraccion}\n")
            print(f"Guardada noticia: {noticia_path}")
        except Exception as e:
            print(f"Error procesando noticia {url}: {e}")

driver.quit()
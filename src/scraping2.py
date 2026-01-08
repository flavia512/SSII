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

driver.get("https://elpais.com/")

CLASIFICACION = {
    "tecnologia": ["tecnología"],
    "finanzas": ["economía"],
    "gobiernos": ["España"],
}

wait = WebDriverWait(driver, 10)
contenedor_categoria = wait.until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, "div.sm._df")
    )
)

enlaces_categorias = contenedor_categoria.find_elements(By.TAG_NAME, "a")
for enlace in enlaces_categorias:
    print(enlace.get_attribute("href"))
    print(enlace.text)

enlaces_por_categoria = {cat: [] for cat in CLASIFICACION}
for enlace in enlaces_categorias:
    texto = enlace.text.strip()
    if texto:
        for categoria, palabras_clave in CLASIFICACION.items():
            for palabra in palabras_clave:
                if palabra.lower() in texto.lower():
                    archivo = os.path.join(os.path.dirname(__file__), f"..", "noticias", categoria, f"{categoria}.txt")
                    archivo = os.path.abspath(archivo)
                    href = enlace.get_attribute("href")
                    existe = False
                    if os.path.exists(archivo):
                        with open(archivo, "r", encoding="utf-8") as f:
                            if href in [line.strip() for line in f]:
                                existe = True
                    if not existe:
                        with open(archivo, "a", encoding="utf-8") as f:
                            f.write(href + "\n")
                        print(f"Guardado: '{texto}' en {archivo}")
                    else:
                        print(f"Ya existe: '{texto}' en {archivo}")
                    if href not in enlaces_por_categoria[categoria]:
                        enlaces_por_categoria[categoria].append(href)

for categoria, urls in enlaces_por_categoria.items():
    for url in urls:
        print(f"Procesando {url} para categoría {categoria}")
        driver2 = webdriver.Edge(
            service=Service(os.path.join(os.getcwd(), "msedgedriver.exe")),
            options=options
        )
        try:
            driver2.get(url)
            time.sleep(2)
            driver2.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(15)
            wait2 = WebDriverWait(driver2, 10)
            divs_clave = []
            try:
                divs_clave.append(wait2.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.z.z-hi"))))
            except:
                pass
            try:
                divs_clave.append(wait2.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.z.z-fe"))))
            except:
                pass
            for div in divs_clave:
                enlaces = div.find_elements(By.XPATH, ".//a")
                print(f"Total de enlaces encontrados en este div: {len(enlaces)}")
                for enlace in enlaces:
                    texto_enlace = enlace.text.strip()
                    href_enlace = enlace.get_attribute("href")
                    if href_enlace:
                        archivo = os.path.join(os.path.dirname(__file__), f"..", "noticias", categoria, "enlaceen2.txt")
                        archivo = os.path.abspath(archivo)
                        existe = False
                        if os.path.exists(archivo):
                            with open(archivo, "r", encoding="utf-8") as f:
                                if href_enlace in [line.strip() for line in f]:
                                    existe = True
                        if not existe:
                            with open(archivo, "a", encoding="utf-8") as f:
                                f.write(href_enlace + "\n")
                            print(f"Guardado: '{texto_enlace}' en {archivo}")
                        else:
                            print(f"Ya existe: '{texto_enlace}' en {archivo}")
        except Exception as e:
            print(f"Error procesando {url}: {e}")
        finally:
            driver2.quit()

for categoria in CLASIFICACION:
    subfolder = os.path.join(os.path.dirname(__file__), "..", "noticias", categoria)
    noticias_folder = os.path.join(subfolder, "noticias")
    os.makedirs(noticias_folder, exist_ok=True)
    enlaceen_path = os.path.join(subfolder, "enlaceen2.txt")
    if not os.path.exists(enlaceen_path):
        continue

    with open(enlaceen_path, "r", encoding="utf-8") as f:
        enlaces_noticias = [line.strip() for line in f if line.strip()]


    noticias_guardadas = set()

    for url in enlaces_noticias:
        try:
            driver2 = webdriver.Edge(
                service=Service(os.path.join(os.getcwd(), "msedgedriver.exe")),
                options=options
            )
            driver2.get(url)
            time.sleep(4)

            # Fecha de publicación
            try:
                fecha_pub = driver2.find_element(By.CSS_SELECTOR, "div.a_md_f").text.strip()
            except:
                fecha_pub = "Sin fecha de publicación"

            # Título
            try:
                titulo_elem = driver2.find_element(By.CSS_SELECTOR, "h1.a_t")
                titulo = titulo_elem.text.strip()
                nombre_archivo = "_".join(titulo.split()[:4]).replace("/", "-").replace("\\", "-")
            except:
                titulo = "Sin título"
                nombre_archivo = "noticia_sin_titulo"

            # Contexto
            try:
                contexto_elem = driver2.find_element(By.CSS_SELECTOR, "p.a_st")
                contexto = contexto_elem.text.strip()
            except:
                contexto = "Sin contexto"

            # Fecha de extracción
            fecha_extraccion = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Evitar duplicados por título y archivo
            noticia_path = os.path.join(noticias_folder, f"{nombre_archivo}.txt")
            if titulo not in noticias_guardadas and not os.path.exists(noticia_path):
                with open(noticia_path, "w", encoding="utf-8") as nf:
                    nf.write(f"{fecha_pub};{titulo};{contexto};{fecha_extraccion}\n")
                print(f"Guardada noticia: {noticia_path}")
                noticias_guardadas.add(titulo)

            driver2.quit()
        except Exception as e:
            print(f"Error procesando noticia {url}: {e}")
            try:
                driver2.quit()
            except:
                pass

driver.quit()
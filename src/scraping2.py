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


# buscaremos el contenedor central donde estan los links de las categorias 
wait = WebDriverWait(driver, 10)
# El nombre de la clase es 'sm _df', pero los selectores de CSS no aceptan espacios, así que se debe usar un punto por cada parte:
contenedor_categoria = wait.until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, "div.sm._df")
    )
)

# imprimir todos los enlaces que hay en el contenedor
enlaces_categorias = contenedor_categoria.find_elements(By.TAG_NAME, "a")
# aqui imprimimos todos los enlaces encontrados solo el texto de a
for enlace in enlaces_categorias:
    print(enlace.get_attribute("href"))
    print(enlace.text)


# Imprimir solo el texto de cada enlace <a>
for enlace in enlaces_categorias:
    texto = enlace.text.strip()
    if texto:
        # Buscar a qué categoría pertenece el texto
        for categoria, palabras_clave in CLASIFICACION.items():
            for palabra in palabras_clave:
                # tomar el cuenta el acento en la comparación
                if palabra.lower() in texto.lower():
                    # Construir la ruta del archivo
                    archivo = os.path.join(os.path.dirname(__file__), f"..", "noticias", categoria, f"{categoria}.txt")
                    archivo = os.path.abspath(archivo)
                    href = enlace.get_attribute("href")
                    # Verificar si el enlace ya está guardado
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
        
driver.quit()
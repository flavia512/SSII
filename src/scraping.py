from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time

options = webdriver.EdgeOptions()
options.add_argument("--headless")  # quítalo si quieres ver el navegador

driver = webdriver.Edge(
    service=Service(EdgeChromiumDriverManager().install()),
    options=options
)

# EJEMPLO: lista de links (esto vendría del paso anterior)
urls = [
    "https://news.bitcoin.com/es/ejemplo-noticia/"
]

for url in urls:
    driver.get(url)
    time.sleep(4)

    # 1. TÍTULO (h1 con clase específica)
    try:
        titulo = driver.find_element(
            By.CSS_SELECTOR,
            "h1.sc-hrAiUm.hEjuKt"
        ).text.strip()
    except:
        titulo = "Sin título"

    # 2. CONTENIDO (todos los <p> dentro del div article__body)
    try:
        cuerpo = driver.find_element(
            By.CSS_SELECTOR,
            "div.article__body"
        )
        parrafos = cuerpo.find_elements(By.TAG_NAME, "p")
        contenido = "\n".join(p.text for p in parrafos if p.text.strip())
    except:
        contenido = "Sin contenido"

    print("TÍTULO:")
    print(titulo)
    print("\nCONTENIDO:")
    print(contenido)
    print("-" * 40)

driver.quit()

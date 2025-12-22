from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, requests

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




contenedor = wait.until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, "div.sc-bfabSb.gvquir")
    )
)


# Diccionario de categorías
CATEGORIAS = {
    "crypto_blockchain_defi": [
        "defi", "ethereum", "bitcoin", "blockchain", "crypto", "nft"
    ],
    "finanzas_economia": [
        "markets", "economia", "precio", "mercado"
    ],
    "gobiernos_regulacion": [
        "regulacion", "gobierno", "politica", "ley"
    ]
}

# Buscar todos los bloques de noticias por categoría
categorias_links = {cat: [] for cat in CATEGORIAS}

# Encuentra todos los divs que contienen noticias (puede requerir ajuste de selector)
noticia_divs = contenedor.find_elements(By.XPATH, ".//div")

for div in noticia_divs:
    try:
        # Buscar el enlace de categoría dentro del bloque de noticia
        categoria_encontrada = None
        categoria_links = div.find_elements(By.XPATH, ".//a")
        for a in categoria_links:
            categoria_text = a.text.lower()
            for cat, palabras in CATEGORIAS.items():
                if any(palabra in categoria_text for palabra in palabras):
                    categoria_encontrada = cat
                    break
            if categoria_encontrada:
                break
        if categoria_encontrada:
            # Buscar el enlace principal de la noticia (usualmente el h2 contiene el link)
            h2s = div.find_elements(By.TAG_NAME, "h2")
            for h2 in h2s:
                noticia_links = h2.find_elements(By.TAG_NAME, "a")
                for link in noticia_links:
                    href = link.get_attribute("href")
                    if href:
                        categorias_links[categoria_encontrada].append(href)
    except Exception as e:
        print(f"Error en div: {e}")
        continue

# Guardar los links en archivos txt en la carpeta correspondiente
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
noticias_dir = os.path.join(base_dir, "noticias")

for cat in categorias_links:
    # Determinar subcarpeta
    if cat == "crypto_blockchain_defi":
        subfolder = "crypto"
    elif cat == "finanzas_economia":
        subfolder = "finanzas"
    elif cat == "gobiernos_regulacion":
        subfolder = "gobiernos_regulacion"
    else:
        subfolder = "otros"
    folder_path = os.path.join(noticias_dir, subfolder)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{cat}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        for link in categorias_links[cat]:
            f.write(link + "\n")

print("Links guardados por categoría.")
print("ANTES DE CERRAR")
driver.quit()
print("DESPUÉS DE CERRAR")


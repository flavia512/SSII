from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time


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
# Nueva lógica: imprimir nombre de la categoría (h2) y el enlace (a) de cada div de categoría
categoria_divs = contenedor.find_elements(By.XPATH, "./div")
print(f"Divs de categoría encontrados: {len(categoria_divs)}")

# Hacer scroll para cargar todos los bloques dinámicos
import time
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)  # Espera a que cargue el contenido


# Diccionario de palabras clave para cada archivo
CLASIFICACION = {
    "tecnologia": ["seguridad", "tecnologia", "defi"],
    "finanzas": ["finanzas", "economía", "economia", "mercados", "precio", "markets", "economics"],
    "gobiernos": ["regulacion", "regulación", "gobierno", "politica", "ley"],
    "crypto": ["crypto", "noticias crypto"]
}

# Diccionario para almacenar los enlaces por archivo
enlaces_por_categoria = {cat: [] for cat in CLASIFICACION}

for div in categoria_divs:
    encontrados = div.find_elements(By.XPATH, ".//a[h2]")
    if not encontrados:
        print("No se encontró patrón a > h2 en este mini div.")
    for enlace in encontrados:
        try:
            h2 = enlace.find_element(By.TAG_NAME, "h2")
            nombre_categoria = h2.text.strip().lower()
            href_categoria = enlace.get_attribute("href")
            print(f"Categoría: {nombre_categoria} | Enlace: {href_categoria}")
            # Clasificar y guardar
            for cat, palabras in CLASIFICACION.items():
                if any(palabra in nombre_categoria for palabra in palabras):
                    enlaces_por_categoria[cat].append(href_categoria)
                    break
        except Exception as e:
            print(f"Error extrayendo a > h2: {e}")

# Guardar los enlaces en archivos por categoría
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
noticias_dir = os.path.join(base_dir, "noticias")
os.makedirs(noticias_dir, exist_ok=True)
for cat, enlaces in enlaces_por_categoria.items():
    if not enlaces:
        continue
    subfolder = os.path.join(noticias_dir, cat)
    os.makedirs(subfolder, exist_ok=True)
    file_path = os.path.join(subfolder, f"{cat}.txt")
    with open(file_path, "a", encoding="utf-8") as f:
        for enlace in enlaces:
            f.write(enlace + "\n")
    print(f"Guardados {len(enlaces)} enlaces en {file_path}")

# Mostrar todos los h2 encontrados en la página para depuración
print("\nTodos los h2 encontrados en la página:")
all_h2s = driver.find_elements(By.TAG_NAME, "h2")
for h2 in all_h2s:
    try:
        print(f"h2: {h2.text.strip()}")
    except Exception:
        continue

driver.quit()
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, requests

options = webdriver.EdgeOptions()
options.add_argument("--log-level=3")

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

try:
    contenedor = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.sc-kzjtPO.sc-ghJsoU.iRfmZn.eMfLiH")
        )
    )
    print("Contenedor encontrado")
except:
    print("No se encontró el contenedor")

# Encuentra todos los enlaces dentro del contenedor
enlaces = contenedor.find_elements(By.TAG_NAME, "a")

print(f"Se encontraron {len(enlaces)} enlaces:")

for e in enlaces:
    url = e.get_attribute("href")  # obtener la URL
    texto = e.text.strip()         # obtener el texto visible
    if url:  # asegurarse de que tenga href
        print(f"{texto} -> {url}")

driver.quit()

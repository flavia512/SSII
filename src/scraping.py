from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
import time
import os

driver = webdriver.Edge(
    service=Service(os.path.join(os.getcwd(), "msedgedriver.exe"))
)

driver.get("https://news.bitcoin.com/es/")
time.sleep(5)

contenedor = driver.find_element(
    By.CSS_SELECTOR,
    "div.sc-kzjtPO.sc-ghJsoU.iRfmZn.eMfLiH"
)

links = contenedor.find_elements(By.TAG_NAME, "a")

for link in links:
    print(link.get_attribute("href"))

driver.quit()

from flask import Flask, render_template, request, jsonify, send_from_directory

import time

import os

import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup

# Configurar Chrome
chrome_options = Options()
chrome_options.add_argument("--disable-dev-shm-usage")  
chrome_options.add_argument("--no-sandbox")  
chrome_options.add_argument("--headless")  # Ejecuta sin interfaz gráfica (opcional)

app = Flask(__name__)

#Carpeta donde se descarga
DOWNLOAD_FOLDER = 'Scraping'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Página principal

@app.route('/')
def index():
    return render_template('index.html')

def realizar_scraping(busqueda, ciudades, max_scroll=10):
    # Crear servicio y driver correctamente
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    resultados = []  

    for ciudad in ciudades:
        ciudad = ciudad.strip()  
        if not ciudad:  
            continue

        url = f"https://www.google.com/maps/search/{busqueda}+{ciudad}"
        driver.get(url)
        time.sleep(5)

        try:
            scrollable_div = driver.find_element(By.CSS_SELECTOR, "div[rol='feed']")
            for _ in range(max_scroll):
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                time.sleep(2)
        except Exception as e:
            print(f"❌ Error al hacer scroll en {ciudad}: {e}")

        # Extraer el HTML
        soup = BeautifulSoup(driver.page_source, "html.parser")
        negocios = soup.find_all("div", class_="Nv2PK")

        for negocio in negocios:
            try:
                # Extraer información del negocio
                nombre_tag = negocio.find("div", class_="qBF1Pd fontHeadlineSmall")
                nombre = nombre_tag.text.strip() if nombre_tag else "n/a"

                direccion_tag = negocio.find_all("div", class_="W4Efsd")
                direccion = direccion_tag[-1].text.strip() if direccion_tag else "n/a"

                enlace_tag = negocio.find("a", class_="hfpxzc")
                enlace = "https://www.google.com" + enlace_tag["href"] if enlace_tag else "n/a"

                telefono_tag = negocio.find("span", class_="UsdlK")
                telefono = telefono_tag.text.strip() if telefono_tag else "n/a"  

                calificacion_tag = negocio.find("span", class_="MW4etd")
                calificacion = calificacion_tag.text.strip() if calificacion_tag else "n/a"

                reseñas_tag = negocio.find("span", class_="UY7F9")
                reseñas = reseñas_tag.text.strip() if reseñas_tag else "n/a"

                sitio_web = "n/a"
                enlaces_externos = negocio.find_all("a", href=True)
                for enlace in enlaces_externos:
                    if "http" in enlace["href"] and "google" not in enlace["href"]:
                        sitio_web = enlace["href"]
                        break

                resultados.append({
                    "Ciudad": ciudad,  # Agregamos la ciudad en la que se encontró
                    "Nombre": nombre,
                    "Teléfono": telefono,
                    "Calificación": calificacion,
                    "Reseñas": reseñas,
                    "Sitio Web": sitio_web
                })
            except Exception as e:
                print(f"⚠️ Error al extraer un negocio en {ciudad}: {e}")
                continue

    # Crear un DataFrame y guardarlo como archivo Excel
    df = pd.DataFrame(resultados)
    archivo_path = os.path.join(DOWNLOAD_FOLDER, f"scraping_{busqueda}.xlsx")
    df.to_excel(archivo_path, index=False)
    print(archivo_path)
    driver.quit()

    return archivo_path


@app.route('/buscar', methods=['POST'])
def buscar():
    data = request.get_json()
    keyword = data.get("keyword")
    cities = data.get("cities", [])

    if not keyword or not cities:
        return jsonify({"message": "Debe completar todos los campos"}), 400

    archivo_generado = realizar_scraping(keyword, cities)
    return jsonify({"message": "Scraping completado!", "archivo": archivo_generado, "keyword": keyword})

@app.route('/downloads/<filename>')
def descargar_archivo(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)



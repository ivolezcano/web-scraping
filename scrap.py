import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# 🔹 Configurar Chrome
options = webdriver.ChromeOptions()
options.headless = False  # Para ver el navegador
driver = webdriver.Chrome(options=options)

# 🔹 Set global para almacenar los teléfonos únicos
telefonos_vistos = set()

def telefono_repetido(telefono):
    """Función para verificar si un teléfono ya fue registrado"""
    if telefono in telefonos_vistos:
        return True
    telefonos_vistos.add(telefono)
    return False

def buscar_negocios(busqueda, ciudad, max_scroll=10):
    url = f"https://www.google.com/maps/search/{busqueda}+{ciudad}"
    driver.get(url)
    time.sleep(5)

    # 🔹 Scroll en la lista de resultados
    try:
        scrollable_div = driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
        for _ in range(max_scroll):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(2)
    except Exception as e:
        print(f"❌ Error al hacer scroll en {ciudad}: {e}")

    # 🔹 Extraer HTML
    soup = BeautifulSoup(driver.page_source, "html.parser")
    negocios = soup.find_all("div", class_="Nv2PK")

    resultados = []
    for negocio in negocios:
        try:
            # 📌 Nombre
            nombre_tag = negocio.find("div", class_="qBF1Pd fontHeadlineSmall")
            nombre = nombre_tag.text.strip() if nombre_tag else "N/A"

            # 📌 Dirección
            direccion_tag = negocio.find_all("div", class_="W4Efsd")
            direccion = direccion_tag[-1].text.strip() if direccion_tag else "N/A"

            # 📌 Enlace a Google Maps
            enlace_tag = negocio.find("a", class_="hfpxzc")
            enlace = "https://www.google.com" + enlace_tag["href"] if enlace_tag else "N/A"

            # 📌 Teléfono
            telefono_tag = negocio.find("span", class_="UsdlK")
            telefono = telefono_tag.text.strip() if telefono_tag else "N/A"

            # Verificar si el teléfono ya fue registrado globalmente
            if telefono_repetido(telefono):
                continue  # Si el teléfono ya está en la lista global, saltar a la siguiente entrada

            # 📌 Calificación y reseñas
            calificacion_tag = negocio.find("span", class_="MW4etd")
            calificacion = calificacion_tag.text.strip() if calificacion_tag else "N/A"

            reseñas_tag = negocio.find("span", class_="UY7F9")
            reseñas = reseñas_tag.text.strip() if reseñas_tag else "N/A"

            # 📌 Sitio web (si tiene)
            sitio_web = "N/A"
            enlaces_externos = negocio.find_all("a", href=True)
            for enlace in enlaces_externos:
                if "http" in enlace["href"] and "google" not in enlace["href"]:
                    sitio_web = enlace["href"]
                    break  # Tomamos el primer sitio web válido

            resultados.append({
                "Ciudad": ciudad,  # 🔹 Agregamos la ciudad en la que se encontró
                "Nombre": nombre,
                "Teléfono": telefono,
                "Calificación": calificacion,
                "Reseñas": reseñas,
                "Sitio Web": sitio_web
            })
        except Exception as e:
            print(f"⚠️ Error al extraer un negocio en {ciudad}: {e}")
            continue

    return resultados

# 🔹 Lista de ciudades para buscar
caba = ["Caballito", "Flores", "Floresta", "Paternal", "Villa Crespo", "Almagro", "Villa Urquiza", "Agronomia", "Saavedra", "Villa Ortuzar", "Villa Pueyrredon", "Parque chas", "Belgrano", "Chacarita", "Coghlan", "Colegiales", "Nuñez", "San cristobal", "San Nicolas", "San Telmo", "Puerto Madero", "Monserrat", "Boedo", "Parque Avellaneda", "parque chacabuco", "Liniers", "Mataderos", "Villa luro", "Barracas", "Constitucion", "La Boca", "Nueva Pompeya", "Parque Patricios", "Villa lugano", "Villa Soldati", "Recoleta", "Retiro", "Palermo", "Monte Castro", "Velez Sarfield", "Versalles", "Villa del parque", "Villa devoto", "Villa general Mitre", "Villa real", "Villa Santa rita"]
ciudades = caba

# 🔹 Lista de palabras clave (search terms)
busquedas = ["Productoras de tv"]

# 🔹 Guardar todas las ciudades en un solo DataFrame
todos_los_datos = []

for busqueda in busquedas:  # Iterar sobre las palabras clave
    for ciudad in ciudades:  # Y por cada ciudad
        print(f"🔍 Buscando '{busqueda}' en {ciudad}...")
        datos_ciudad = buscar_negocios(busqueda, ciudad)
        todos_los_datos.extend(datos_ciudad)  # Agregar los datos a la lista

# 🔹 Guardar en Excel
df = pd.DataFrame(todos_los_datos)
df.to_excel("ProductorasTV.xlsx", index=False)

# 🔹 Cerrar navegador
driver.quit()

print("✅ Scraping finalizado. Datos guardados")
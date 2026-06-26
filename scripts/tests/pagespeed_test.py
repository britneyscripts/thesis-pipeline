import requests
import json

def analizar_pdp(url_objetivo, api_key):
    # 1. Configuración de la llamada
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        'url': url_objetivo,
        'key': api_key,
        'category': ['PERFORMANCE', 'ACCESSIBILITY', 'SEO'],
        'strategy': 'desktop'
    }

    print(f"Analizando: {url_objetivo}...")
    
    # 2. Hacer la petición
    response = requests.get(endpoint, params=params)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    
    # 3. Extraer solo lo que importa para tu tesis (El "Resumen Ejecutivo")
    lh = data['lighthouseResult']
    
    resumen = {
        "url": url_objetivo,
        "scores": {
            "performance": lh['categories']['performance']['score'] * 100,
            "accessibility": lh['categories']['accessibility']['score'] * 100,
            "seo": lh['categories']['seo']['score'] * 100
        },
        "agente_ready_checks": {
            # ¿Tiene etiquetas ALT en las imágenes? (Vital para agentes)
            "tiene_alt_text": lh['audits']['image-alt']['score'] == 1,
            # ¿Los botones tienen nombres legibles?
            "botones_legibles": lh['audits']['button-name']['score'] == 1,
            # ¿La página carga rápido para un bot? (LCP)
            "velocidad_carga": lh['audits']['largest-contentful-paint']['displayValue']
        }
    }

    return resumen

# --- CONFIGURACIÓN ---
MI_API_KEY = "TU_API_KEY_AQUI"
URL_JUMBO = "https://www.jumbo.cl/pan-ciabatta-rustico-jumbo-granel/p"

resultado = analizar_pdp(URL_JUMBO, MI_API_KEY)

# 4. Ver el resultado limpio
if resultado:
    print("\n--- RESULTADO PARA GHOSTPROD ---")
    print(json.dumps(resultado, indent=4, ensure_ascii=False))
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        print("Iniciando Chromium local...")
        # Rodando headless (invisível) para imitar um agente/robô de servidor
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url_alvo = "https://www.mercadolivre.com.br/hidratante-facial-hydro-boost-water-gel-50g-neutrogena/p/MLB19899495"
        print(f"Acessando: {url_alvo}")
        
        # Acessa a URL
        response = await page.goto(url_alvo)
        
        # Espera 5 segundos para dar tempo do Mercado Livre fazer o redirecionamento ou carregar o CAPTCHA
        await page.wait_for_timeout(5000)
        
        # Tira um print da tela para você ver o que o robô está vendo
        screenshot_path = "resultado_teste_meli.png"
        await page.screenshot(path=screenshot_path)
        
        print("\n--- RESULTADOS ---")
        print(f"Status da resposta HTTP: {response.status if response else 'Desconhecido'}")
        print(f"URL Final (Para onde fomos redirecionados?): {page.url}")
        print(f"Print da tela salvo em: {screenshot_path}")
        print("------------------\n")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())

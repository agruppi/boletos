#!/home/playwright/venv/bin/python
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os, time, re

load_dotenv(override=True)
CPF = os.getenv('CPF')
SENHA = os.getenv('SENHA')

def login_if_needed(page):
    """Faz login na Unimed"""
    print("Abrindo página de login...")
    time.sleep(1)
    
    try:
        page.goto("https://www.unimedfortaleza.com.br/minha-unimed", timeout=5000, wait_until="domcontentloaded")
        time.sleep(2)
    except:
        print("Timeout ao carregar, continuando...")
    
    print("URL: " + page.url)
    
    # Rejeita cookies
    try:
        page.click("button:has-text('Rejeitar cookies')")
        print("Cookies rejeitados")
        time.sleep(2)
    except:
        print("Botao rejeitar nao encontrado")
    
    # Preenche e faz login
    try:
        print("Preenchendo CPF...")
        page.locator("input[placeholder*='Digite seu login'], input[name*='j_username'], input[id*='inputUsuario']").first.fill(CPF, timeout=5000)
        
        print("Preenchendo senha...")
        page.locator("input[type='password']").first.fill(SENHA, timeout=5000)
        print("CPF e senha preenchidos")
        time.sleep(1)
        
        print("Clicando em Entrar...")
        try:
            page.locator("button:has-text('Entrar')").first.click(timeout=5000)
            print("Clique normal funcionou")
        except:
            try:
                page.locator("button:has-text('Entrar')").first.click(force=True, timeout=5000)
                print("Clique forcado funcionou")
            except:
                page.evaluate("document.querySelector('button[title=\"Entrar\"]').click()")
                print("Clique JavaScript funcionou")
        
        time.sleep(3)
        print("Login realizado")

    except Exception as e:
        print("Erro ao fazer login: " + str(e))
    
    print("Pagina carregada")
     
    # 5. CLICA "Continuar para o Minha Unimed"
    try:
        time.sleep(2)
        page.click("button:has-text('Continuar para o Minha Unimed'), a:has-text('Continuar para o Minha Unimed')")
        print("Continuando...")
    except:
        print("Botao Continuar nao encontrado")
   
    return page

def download_pdfs():
    print("Unimed - DOWNLOAD DE PDFS")
    print("")
    
    os.makedirs("screenshots", exist_ok=True)
    os.makedirs("pdfs", exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
        
        try:
            page = login_if_needed(page)
            print("")
            print("URL final: " + page.url)
            print("")
            
            # Navega para faturas
            if "cliente" in page.url:
                print("Navegando para faturas...")
                try:
                    page.goto("https://www.unimedfortaleza.com.br/minha-unimed/cliente/splash/fatura-digital", timeout=10000, wait_until="domcontentloaded")
                    time.sleep(2)
                except:
                    print("Timeout ao navegar, continuando...")
                    time.sleep(2)
            
            print("Buscando botoes de download...")
            time.sleep(2)
            
            # Procura botoes de download
            buttons = page.locator("button[onclick*='gerarSegundaVia']").all()
            
            if len(buttons) == 0:
                print("Nenhum botao encontrado!")
                all_buttons = page.locator("button").all()
                print("Total de botoes: " + str(len(all_buttons)))
                for i, btn in enumerate(all_buttons[:20]):
                    text = btn.text_content().strip()[:40]
                    onclick = btn.get_attribute("onclick")
                    cls = btn.get_attribute("class")
                    print("  " + str(i) + ": text='" + text + "' class='" + str(cls) + "'")
                context.close()
                browser.close()
                return
            
            print("Encontrados " + str(len(buttons)) + " botoes")
            print("")
            
            # Extrai datas dos botoes
            dates = []
            for button in buttons:
                onclick_attr = button.get_attribute("onclick")
                if onclick_attr:
                #  <button type="button" class="btn btn-sm btn-laranja" onclick="gerarSegundaVia('2026-02-10');"><span class="fa-cloud-download"></span></button>
                    match = re.search(r"gerarSegundaVia\('(\d{4}-\d{2}-\d{2})'\)", onclick_attr)
                    if match:
                        dates.append(match.group(1))
                    else:
                        dates.append("desconhecida")
                else:
                    dates.append("sem_data")
            
            # Baixa cada PDF
            print("INICIANDO DOWNLOADS (" + str(len(buttons)) + " arquivos)...")
            print("")
            
            for i, button in enumerate(buttons):
                try:
                    date_str = dates[i] if i < len(dates) else "item_" + str(i+1)
                    print("[" + str(i+1) + "/" + str(len(buttons)) + "] Baixando fatura_" + date_str + ".pdf...")
                    
                    with page.expect_download(timeout=10000) as download_info:
                        button.click()
                        time.sleep(1)
                    
                    download = download_info.value
                    file_path = "pdfs/fatura_" + date_str + ".pdf"
                    download.save_as(file_path)
                    print("Salvo: " + file_path)
                    
                except Exception as e:
                    print("Erro: " + str(e))
                
                time.sleep(1)
            
            print("")
            print("DOWNLOAD CONCLUIDO!")
            
        except Exception as e:
            print("ERRO: " + str(e))
            import traceback
            traceback.print_exc()
            page.screenshot(path="screenshots/ERROR.png")
        
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    download_pdfs()

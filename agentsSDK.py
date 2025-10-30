import asyncio
import os
import json
import time
import re
from typing import List, Dict

# Importações do Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Importações do Agents SDK
from agents import Agent, Runner, function_tool, set_default_openai_key
import pandas as pd
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# -----------------------------------------------------------
# 1. CONFIGURAÇÃO DE AMBIENTE E MODELO
# -----------------------------------------------------------

# Configuração da Chave de API
try:
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = OPENAI_KEY 
    set_default_openai_key(key=OPENAI_KEY)
    print("Chave de API configurada no Agents SDK.")
except Exception:
    print("AVISO: Chave de API não configurada corretamente.")

MODEL_NAME = "gpt-4o-mini"

# -----------------------------------------------------------
# 2. DEFINIÇÃO DAS FERRAMENTAS (TOOLS)
# -----------------------------------------------------------

def initialize_selenium_driver():
    """
    Inicializa o driver do Chrome com configurações otimizadas.
    """
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Remove propriedades que indicam automação
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        return f"ERRO NO DRIVER: Falha ao inicializar o driver Selenium. Mensagem: {e}"

@function_tool
def extract_amazon_search_data(url: str) -> str:
    """
    Extrai dados de produtos diretamente da página de busca da Amazon usando regex otimizado.
    """
    driver_or_error = initialize_selenium_driver()
    
    if isinstance(driver_or_error, str):
        return driver_or_error 
    
    driver = driver_or_error
    print(f"[TOOL] 🔍 Extraindo dados da Amazon: {url}")
    
    try:
        driver.get(url)
        time.sleep(5)  # Aguarda carregamento
        
        html_content = driver.page_source
        print(f"[TOOL] 📄 HTML capturado: {len(html_content)} caracteres")
        
        products = []
        
        # Regex para extrair contêineres de produto com data-asin
        product_pattern = r'<div[^>]*data-asin="([A-Z0-9]{10})"[^>]*data-component-type="s-search-result"[^>]*>(.*?)</div>\s*</div>\s*</div>\s*</span>'
        
        matches = re.findall(product_pattern, html_content, re.DOTALL)
        print(f"[TOOL] 🎯 {len(matches)} produtos encontrados")
        
        for i, (asin, product_html) in enumerate(matches[:10], 1):  # Limita a 10 produtos
            print(f"  > Processando produto {i}: ASIN {asin}")
            
            # Extrai título
            title_patterns = [
                r'<h2[^>]*>(.*?)</h2>',
                r'<span[^>]*class="[^"]*a-size-base-plus[^"]*"[^>]*>([^<]*)</span>',
                r'title":{"text":"([^"]*)"'
            ]
            
            title = "N/A"
            for pattern in title_patterns:
                title_match = re.search(pattern, product_html, re.DOTALL)
                if title_match:
                    title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                    if title and len(title) > 10:  # Título válido
                        break
            
            # Extrai preço
            price = 0.0
            price_patterns = [
                r'<span class="a-price-whole">([0-9,]+)</span><span class="a-price-fraction">([0-9]{2})</span>',
                r'R\$\s*([0-9,]+[.,][0-9]{2})',
                r'"price":([0-9.]+)'
            ]
            
            for pattern in price_patterns:
                price_match = re.search(pattern, product_html)
                if price_match:
                    if len(price_match.groups()) == 2:  # Padrão whole/fraction
                        whole, fraction = price_match.groups()
                        price = float(whole.replace(',', '') + '.' + fraction)
                    else:  # Padrão único
                        price_str = price_match.group(1).replace(',', '.')
                        price = float(price_str)
                    break
            
            # Extrai avaliação
            rating = 0.0
            rating_patterns = [
                r'aria-hidden="true" class="a-size-small a-color-base">([0-9,]+)</span>',
                r'"rating_average":([0-9.]+)',
                r'([0-9,]+) de 5 estrelas'
            ]
            
            for pattern in rating_patterns:
                rating_match = re.search(pattern, product_html)
                if rating_match:
                    rating_str = rating_match.group(1).replace(',', '.')
                    rating = float(rating_str)
                    break
            
            # URL do produto
            product_url = f"https://www.amazon.com.br/dp/{asin}"
            
            # Disponibilidade (assume em estoque se tem preço)
            availability = "Em estoque" if price > 0 else "Indisponível"
            
            product_data = {
                "Nome do Produto": title,
                "Preço (R$)": price,
                "Avaliação (estrelas)": rating,
                "URL": product_url,
                "Disponibilidade": availability,
                "ASIN": asin
            }
            
            products.append(product_data)
            print(f"    ✅ {title[:50]}... - R$ {price}")
        
        return json.dumps(products, ensure_ascii=False)
        
    except Exception as e:
        return f"ERRO: {e}"
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

@function_tool
def extract_mercadolivre_search_data(url: str) -> str:
    """
    Extrai dados de produtos diretamente da página de busca do Mercado Livre usando seletores CSS 
    baseados no scraper Scrapy funcional.
    """
    driver_or_error = initialize_selenium_driver()
    
    if isinstance(driver_or_error, str):
        return driver_or_error 
    
    driver = driver_or_error
    print(f"[TOOL] 🔍 Extraindo dados do Mercado Livre: {url}")
    
    try:
        driver.get(url)
        time.sleep(5)  # Aguarda carregamento
        
        html_content = driver.page_source
        print(f"[TOOL] 📄 HTML capturado: {len(html_content)} caracteres")
        
        products = []
        
        # Usa os mesmos seletores CSS que funcionam no scraper Scrapy
        # Busca por containers de produto
        container_patterns = [
            r'<li[^>]*class="[^"]*ui-search-layout__item[^"]*"[^>]*>(.*?)</li>',
            r'<div[^>]*class="[^"]*andes-card[^"]*poly-card[^"]*"[^>]*>(.*?)</div>'
        ]
        
        containers = []
        for pattern in container_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            if matches:
                containers = matches
                print(f"[TOOL] � {len(containers)} containers encontrados com padrão: {pattern[:50]}...")
                break
        
        if not containers:
            print("[TOOL] ⚠️ Nenhum container de produto encontrado")
            return json.dumps([])
        
        # Limita a 10 produtos
        for i, container_html in enumerate(containers[:10], 1):
            print(f"  > Processando container {i}")
            
            # Extrai título usando padrões mais robustos
            title = "N/A"
            title_patterns = [
                # Padrões mais específicos primeiro
                r'<h2[^>]*class="[^"]*ui-search-item__title[^"]*"[^>]*>([^<]+)</h2>',
                r'<a[^>]*class="[^"]*ui-search-item__group__element[^"]*"[^>]*title="([^"]+)"',
                r'class="[^"]*ui-search-item__title[^"]*"[^>]*>([^<]+)<',
                r'<span[^>]*class="[^"]*ui-search-item__title[^"]*"[^>]*>([^<]+)</span>',
                r'<a[^>]*class="[^"]*poly-component__title[^"]*"[^>]*>([^<]+)</a>',
                # Padrões mais genéricos
                r'ui-search-item__title[^>]*>([^<]{10,})<',  # Título com pelo menos 10 caracteres
                r'title="([^"]{10,})"[^>]*ui-search',  # Atributo title
                r'<a[^>]*>([^<]{15,})</a>[^<]*cartucho|hp',  # Link com texto relacionado
            ]
            
            for pattern in title_patterns:
                title_match = re.search(pattern, container_html, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1).strip()
                    # Remove tags HTML residuais
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    if title and len(title) > 5 and not title.isdigit():
                        break
            
            # Extrai link usando padrões do scraper Scrapy
            link = ""
            link_patterns = [
                r'<a[^>]*class="[^"]*ui-search-item__group__element[^"]*"[^>]*href="([^"]*)"',
                r'<a[^>]*class="[^"]*ui-search-link[^"]*"[^>]*href="([^"]*)"',
                r'<a[^>]*class="[^"]*poly-component__title[^"]*"[^>]*href="([^"]*)"'
            ]
            
            for pattern in link_patterns:
                link_match = re.search(pattern, container_html)
                if link_match:
                    link = link_match.group(1)
                    if not link.startswith('http'):
                        link = f"https://www.mercadolivre.com.br{link}"
                    break
            
            # Extrai preço usando padrões do scraper Scrapy
            price = 0.0
            price_patterns = [
                r'class="[^"]*andes-money-amount__fraction[^"]*"[^>]*>([^<]*)</span>',
                r'ui-search-price__second-line[^>]*>.*?andes-money-amount__fraction[^>]*>([^<]*)</span>',
                r'poly-price__current[^>]*>.*?andes-money-amount__fraction[^>]*>([^<]*)</span>'
            ]
            
            for pattern in price_patterns:
                price_match = re.search(pattern, container_html, re.DOTALL)
                if price_match:
                    price_str = price_match.group(1).replace('.', '').replace(',', '.')
                    try:
                        price = float(price_str)
                        break
                    except ValueError:
                        continue
            
            # Extrai avaliação usando padrões testados que funcionam
            rating = 0.0
            rating_patterns = [
                # Padrões que funcionaram no teste
                r'rating[^>]*>([0-9,\.]+)</span>',  # Padrão 5 (funciona)
                r'reviews__rating[^>]*>([0-9,\.]+)',  # Padrão 9 (funciona)
                # Padrões adicionais de backup
                r'class="[^"]*ui-search-reviews__rating-number[^"]*"[^>]*>([0-9,\.]+)</span>',
                r'ui-search-reviews__rating-number[^>]*>([0-9,\.]+)</span>',
                r'class="[^"]*ui-search-reviews__rating[^"]*"[^>]*>([0-9,\.]+)</span>',
                r'rating-number[^>]*>([0-9,\.]+)</span>',
                r'<span[^>]*>([0-9,\.]+)\s*</span>[^<]*<span[^>]*>\([0-9,\.]+\)</span>',
                r'([0-9,\.]+)\s*de\s*5\s*estrelas',
                r'([0-9,\.]+)\s*estrelas?'
            ]
            
            for pattern in rating_patterns:
                rating_match = re.search(pattern, container_html, re.IGNORECASE)
                if rating_match:
                    rating_str = rating_match.group(1).replace(',', '.')
                    try:
                        rating = float(rating_str)
                        if 0 <= rating <= 5:  # Validação de range válido
                            break
                    except ValueError:
                        continue
            
            # Extrai ID MLB do link
            mlb_id = "N/A"
            if link:
                mlb_match = re.search(r'(MLB-[0-9]+)', link)
                if mlb_match:
                    mlb_id = mlb_match.group(1)
            
            # URL do produto
            product_url = link if link else f"https://www.mercadolivre.com.br/{mlb_id}"
            
            # Disponibilidade (assume em estoque se tem preço)
            availability = "Em estoque" if price > 0 else "Indisponível"
            
            product_data = {
                "Nome do Produto": title,
                "Preço (R$)": price,
                "Avaliação (estrelas)": rating,
                "URL": product_url,
                "Disponibilidade": availability,
                "MLB_ID": mlb_id
            }
            
            products.append(product_data)
            print(f"    ✅ {title[:50]}... - R$ {price}")
        
        return json.dumps(products, ensure_ascii=False)
        
    except Exception as e:
        return f"ERRO: {e}"
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

@function_tool
def csv_writer_tool(json_data_str: str, filename: str = 'hp_cartridges_search_data.csv') -> str:
    """
    Salva os dados em formato CSV.
    """
    print(f"\n[TOOL] 💾 Gravando dados no arquivo: {filename}")
    
    try:
        data_list = json.loads(json_data_str)
    except json.JSONDecodeError:
        return "Erro: A string de dados não está em formato JSON válido."
    
    if isinstance(data_list, list) and data_list:
        df = pd.DataFrame(data_list)
        df.to_csv(filename, index=False, encoding='utf-8')
        return f"Dados de {len(data_list)} produtos salvos com sucesso em {filename}."
    else:
        return "A lista de dados estava vazia. Arquivo CSV não gerado."

# -----------------------------------------------------------
# 3. DEFINIÇÃO DOS AGENTES
# -----------------------------------------------------------

# AGENTE AMAZON: Extrai dados da página de busca da Amazon
amazon_agent = Agent(
    name="Agente Amazon Search",
    model=MODEL_NAME, 
    instructions="""
    Use a ferramenta 'extract_amazon_search_data' para extrair dados de produtos diretamente da página de busca da Amazon.
    Esta ferramenta já faz toda a extração usando regex otimizado.
    Retorne APENAS o resultado da ferramenta, sem nenhum texto adicional.
    O resultado já é um JSON válido de lista de produtos.
    """,
    tools=[extract_amazon_search_data], 
)

# AGENTE MERCADO LIVRE: Extrai dados da página de busca do Mercado Livre
mercadolivre_agent = Agent(
    name="Agente Mercado Livre Search",
    model=MODEL_NAME, 
    instructions="""
    Use a ferramenta 'extract_mercadolivre_search_data' para extrair dados de produtos diretamente da página de busca do Mercado Livre.
    Esta ferramenta já faz toda a extração usando seletores CSS otimizados.
    Retorne APENAS o resultado da ferramenta, sem nenhum texto adicional.
    O resultado já é um JSON válido de lista de produtos.
    """,
    tools=[extract_mercadolivre_search_data], 
)

# AGENTE CONSOLIDADOR: Combina e salva dados
consolidator_agent = Agent(
    name="Agente Consolidador",
    model=MODEL_NAME, 
    instructions="Receba listas de dados de produtos, combine-as em uma única lista JSON e use a 'csv_writer_tool' para salvar.",
    tools=[csv_writer_tool],
)

# -----------------------------------------------------------
# 4. ORQUESTRAÇÃO PRINCIPAL
# -----------------------------------------------------------

async def main():
    print("🚀 INÍCIO DO SCRAPING DE CARTUCHOS HP - PÁGINAS DE BUSCA")
    print("="*60)
    
    all_products = []
    
    search_configs = [
        {
            "name": "Amazon Brasil",
            "url": "https://www.amazon.com.br/s?k=cartucho+hp+664+original",
            "agent": amazon_agent
        },
        {
            "name": "Mercado Livre Brasil", 
            "url": "https://lista.mercadolivre.com.br/cartucho-hp-662",
            "agent": mercadolivre_agent
        }
    ]
    
    # ETAPA 1: EXTRAÇÃO DE DADOS DAS PÁGINAS DE BUSCA
    print(f"\n[FLUXO] 📊 Extraindo dados de {len(search_configs)} páginas de busca...")
    
    for config in search_configs:
        print(f"\n  🌐 Processando: {config['name']}")
        print(f"     URL: {config['url']}")
        
        try:
            result = await Runner.run(
                config['agent'], 
                input=f"Extraia todos os dados de produtos desta URL: {config['url']}"
            )
            
            products_data = json.loads(result.final_output.strip())
            
            if isinstance(products_data, list) and products_data:
                all_products.extend(products_data)
                print(f"     ✅ {len(products_data)} produtos extraídos")
                
                # Mostra amostra dos produtos encontrados
                for i, product in enumerate(products_data[:3], 1):
                    name = product.get('Nome do Produto', 'N/A')[:40]
                    price = product.get('Preço (R$)', 0)
                    print(f"       {i}. {name}... - R$ {price}")
                
                if len(products_data) > 3:
                    print(f"       ... e mais {len(products_data) - 3} produtos")
            else:
                print(f"     ❌ Nenhum produto encontrado")
        
        except Exception as e:
            print(f"     ❌ Erro: {e}")
    
    print(f"\n[FLUXO] 📋 Total de produtos coletados: {len(all_products)}")
    
    # ETAPA 2: CONSOLIDAÇÃO E SALVAMENTO
    if all_products:
        print(f"\n[FLUXO] 💾 Consolidando e salvando dados...")
        
        # Remove duplicatas baseado no nome do produto
        unique_products = []
        seen_names = set()
        
        for product in all_products:
            name = product.get('Nome do Produto', '').lower().strip()
            if name and name not in seen_names and len(name) > 5:
                seen_names.add(name)
                unique_products.append(product)
        
        print(f"[FLUXO] 🔧 {len(unique_products)} produtos únicos após remoção de duplicatas")
        
        # Ordena por preço
        unique_products.sort(key=lambda x: x.get('Preço (R$)', 0), reverse=True)
        
        data_json = json.dumps(unique_products, ensure_ascii=False)
        
        final_result = await Runner.run(
            consolidator_agent,
            input=f"Salve estes {len(unique_products)} produtos únicos: {data_json}"
        )
        
        print(f"\n✅ {final_result.final_output}")
        
        # ETAPA 3: MOSTRA RESULTADO FINAL
        try:
            df = pd.read_csv('hp_cartridges_search_data.csv')
            print(f"\n📊 RESUMO DOS DADOS COLETADOS:")
            print(f"   • Total de produtos: {len(df)}")
            print(f"   • Preço médio: R$ {df['Preço (R$)'].mean():.2f}")
            print(f"   • Preço mínimo: R$ {df['Preço (R$)'].min():.2f}")
            print(f"   • Preço máximo: R$ {df['Preço (R$)'].max():.2f}")
            print(f"   • Avaliação média: {df['Avaliação (estrelas)'].mean():.1f} estrelas")
            
            print(f"\n🏆 TOP 5 PRODUTOS POR PREÇO:")
            top_5 = df.nlargest(5, 'Preço (R$)')
            for i, (_, row) in enumerate(top_5.iterrows(), 1):
                name = row['Nome do Produto'][:50]
                price = row['Preço (R$)']
                rating = row['Avaliação (estrelas)']
                print(f"   {i}. {name}... - R$ {price} ({rating}⭐)")
            
        except Exception as e:
            print(f"❌ Erro ao ler CSV final: {e}")
    else:
        print("❌ Nenhum dado válido foi coletado")
    
    print(f"\n🎉 SCRAPING CONCLUÍDO!")
    print("="*60)

# Comando de execução final:
if __name__ == "__main__":
    asyncio.run(main())
import boto3
from dotenv import load_dotenv
import os
from playwright.sync_api import sync_playwright, Error as PlaywrightError
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Carregar variáveis do .env
load_dotenv()

# Configuração do S3
s3 = boto3.client(
    's3',
    region_name=os.getenv('AWS_DEFAULT_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=os.getenv('AWS_SESSION_TOKEN') 
)

# Nome do bucket do ambiente
bucket_name = os.getenv('S3_BUCKET_NAME')
if not bucket_name:
    print("Erro: Variável de ambiente 'S3_BUCKET_NAME' não definida.")
    sys.exit(1) # Sai com erro se o bucket não estiver configurado


# Prefixo de S3 para dados brutos com particionamento diário (ex: raw/date=2025-07-18)
current_date = datetime.now().strftime("%Y-%m-%d")
raw_prefix = f'raw/date={current_date}'

# URL da página da B3
url = 'https://sistemaswebb3-listados.b3.com.br/indexPage/day/IBOV?language=pt-br'

# Nome do arquivo Parquet
file_name = f"ibov_{datetime.now().strftime('%Y%m%d')}.parquet"

# Caminho local para salvar temporariamente (ex: data/raw/date=2023-10-27/ibov_20231027.parquet)
local_raw_path = Path("data") / raw_prefix
file_path = local_raw_path / file_name


def scrape_b3_data():
    """
    Realiza o scraping dos dados da B3 usando Playwright,
    processa com BeautifulSoup e retorna um DataFrame.
    """
    print("Iniciando o scraping de dados da B3...")
    with sync_playwright() as p:
        browser = None # Inicializa browser como None para garantir que seja fechado no finally
        try:
            # Iniciar navegador (headless=True por padrão)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print(f"🌐 Acessando a página: {url}")
            page.goto(url, timeout=60000) # Aumenta o timeout para goto (60 segundos)

            print("🔄 Aguardando carregamento da tabela principal...")
            
            # Espera por um seletor específico da tabela com um timeout
            page.wait_for_selector('table.table', timeout=30000) # Aumenta o timeout (30 segundos)
            page.wait_for_load_state("networkidle", timeout=30000) # Espera por inatividade da rede

            print("🔽 Selecionando 120 resultados por página...")
            # Seleciona a opção e espera por inatividade da rede novamente para carregar os novos dados
            
            page.select_option('#selectPage', label='120')
            print("🔄 Aguardando nova carga dos dados após seleção de 120...")
            page.wait_for_load_state("networkidle", timeout=30000) # Substitui o wait_for_timeout fixo
            
            # Pequena espera adicional se networkidle não for suficiente para renderização
            page.wait_for_timeout(1000)

            print("📄 Pegando HTML após carregar dados...")
            html = page.content()
            return html
        except PlaywrightError as e:
            print(f"Erro do Playwright durante o scraping: {e}")
            return None
        except Exception as e:
            print(f"Erro inesperado durante o scraping: {e}")
            return None
        finally:
            if browser:
                browser.close()
                print("Browser do Playwright fechado.")

def parse_html_to_dataframe(html_content):
    """
    Analisa o HTML e extrai os dados para um DataFrame Pandas.
    """
    print("Analisando o conteúdo HTML com BeautifulSoup...")
    soup = BeautifulSoup(html_content, 'html.parser')

    # Identificar a tabela correta
    table = soup.find('table', {'class': 'table table-responsive-sm table-responsive-md'})

    if not table:
        print("Erro: Tabela de dados não encontrada na página. Verifique o seletor ou se a estrutura da página mudou.")
        return None

    rows = table.find_all('tr')

    # Verifica se há linhas suficientes (pelo menos cabeçalho e uma linha de dados)
    if len(rows) < 2:
        print("Aviso: Nenhuma linha de dados encontrada na tabela (apenas cabeçalho ou tabela vazia).")
        return pd.DataFrame(columns=['codigo', 'acao', 'tipo', 'qtde_teorica', 'part_porcentagem'])

    data = []

    # Itera sobre as linhas, pulando o cabeçalho se houver (o cabeçalho geralmente não tem 5 <td>s)
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 5: # Assegura que estamos pegando linhas de dados completas
            data.append([col.text.strip() for col in cols])

    # Se não houver dados, retorna um DataFrame vazio com as colunas corretas
    if not data:
        print("Aviso: Nenhum dado de ações extraído da tabela.")
        return pd.DataFrame(columns=['codigo', 'acao', 'tipo', 'qtde_teorica', 'part_porcentagem'])

    # Converter para DataFrame
    columns = ['codigo', 'acao', 'tipo', 'qtde_teorica', 'part_porcentagem']
    df = pd.DataFrame(data, columns=columns)
    
    return df

def save_to_parquet_and_upload_to_s3(dataframe, local_path, s3_bucket, s3_key):
    """
    Salva o DataFrame localmente em Parquet e faz upload para S3.
    """
    print("Preparando para salvar e enviar para S3...")
    # Criar diretório local se não existir
    local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        dataframe.to_parquet(local_path)
        print(f"✅ Dados brutos salvos localmente em: {local_path}")
    except Exception as e:
        print(f"Erro ao salvar arquivo Parquet localmente: {e}")
        return False

    try:
        s3.upload_file(str(local_path), s3_bucket, s3_key)
        print(f"✅ Dados salvos no S3 em: s3://{s3_bucket}/{s3_key}")
        return True
    except Exception as e:
        print(f"Erro ao enviar arquivo para S3: {e}")
        return False
    finally:
        # Remover o arquivo local após o upload para S3 (limpeza)
        #if os.path.exists(local_path):
        #    os.remove(local_path)
            print(f"🗑️ Arquivo local {local_path} removido.")

# --- Execução Principal ---
if __name__ == "__main__":
    html_content = scrape_b3_data()

    if html_content:
        df = parse_html_to_dataframe(html_content)
        if df is not None and not df.empty: # Verifica se o DataFrame não é None e não está vazio
            s3_upload_key = f"{raw_prefix}/{file_name}"
            if not save_to_parquet_and_upload_to_s3(df, file_path, bucket_name, s3_upload_key):
                sys.exit(1) # Sai com erro se o upload falhar
        elif df is not None and df.empty:
            print("Nenhum dado foi extraído. Não será salvo ou enviado ao S3.")
        else: # df is None
            print("Falha na análise do HTML, não foi possível criar o DataFrame.")
            sys.exit(1)
    else:
        print("Falha no scraping, nenhum conteúdo HTML foi obtido.")
        sys.exit(1) # Sai com erro se o scraping falhar

    print("Processo de scraping da B3 finalizado.")
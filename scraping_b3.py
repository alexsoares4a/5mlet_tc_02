import boto3
from dotenv import load_dotenv
import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from pathlib import Path

# Carregar variáveis do .env
load_dotenv()

# Configuração do S3
s3 = boto3.client(
    's3',
    region_name=os.getenv('AWS_DEFAULT_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')

)

print("AWS_ACCESS_KEY_ID:", os.getenv('AWS_ACCESS_KEY_ID'))
print("AWS_SECRET_ACCESS_KEY:", os.getenv('AWS_SECRET_ACCESS_KEY'))
print("WS_DEFAULT_REGION:", os.getenv('AWS_DEFAULT_REGION'))


bucket_name = 'bucket-ibov-988621824675'
raw_prefix = f'raw/date={datetime.now().strftime("%Y-%m-%d")}'

url = 'https://sistemaswebb3-listados.b3.com.br/indexPage/day/IBOV?language=pt-br'

with sync_playwright() as p:
    # Iniciar navegador (headless=True por padrão)
    browser = browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("🌐 Acessando a página...")
    page.goto(url)

    print("🔄 Aguardando carregamento da tabela...")
    page.wait_for_selector('table.table')
    page.wait_for_load_state("networkidle") # para garantir que todas as requisições sejam concluídas

    print("🔽 Selecionando 120 resultados por página...")
    page.select_option('#selectPage', label='120')

    print("🔄 Aguardando nova carga dos dados...")
    page.wait_for_timeout(5000)  # 5 segundos

    print("📄 Pegando HTML após carregar dados...")
    html = page.content()

    browser.close()

# Analisar o conteúdo com BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Identificar a tabela correta
table = soup.find('table', {'class': 'table table-responsive-sm table-responsive-md'})

rows = table.find_all('tr')
data = []
for row in rows:
    cols = row.find_all('td')
    if len(cols) == 5:
        data.append([col.text.strip() for col in cols])

# Converter para DataFrame
columns = ['codigo', 'acao', 'tipo', 'qtde_teorica', 'part_porcentagem']
df = pd.DataFrame(data, columns=columns)

# Definir estrutura local
local_raw_path = Path("data/" + raw_prefix)

# Criar diretório se não existir
local_raw_path.mkdir(parents=True, exist_ok=True)

# Salvar com estrutura particionada
file_name = f"ibov_{datetime.now().strftime('%Y%m%d')}.parquet"
file_path = local_raw_path / file_name

df.to_parquet(file_path)
print(f"✅ Dados brutos salvos em: {file_path}")

# Enviar para S3
s3.upload_file(str(file_path), bucket_name, f"{raw_prefix}/{file_name}")

print("✅ Dados salvos no S3!")
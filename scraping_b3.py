from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import boto3
from datetime import datetime
from pathlib import Path

# Configuração do S3
s3 = boto3.client('s3')
bucket_name = 'seu-bucket-name'
raw_prefix = f'raw/date={datetime.now().strftime("%Y-%m-%d")}'

url = ' https://sistemaswebb3-listados.b3.com.br/indexPage/day/IBOV?language=pt-br'

with sync_playwright() as p:
    # Iniciar navegador (headless=True por padrão)
    browser = browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("🌐 Acessando a página...")
    page.goto(url)

    print("🔄 Aguardando carregamento da tabela...")
    page.wait_for_selector('table.table')

    print("🔽 Selecionando 120 resultados por página...")
    page.select_option('#selectPage', label='120')

    print("🔄 Aguardando nova carga dos dados...")
    page.wait_for_timeout(5000)  # 5 segundos (ajuste se necessário)

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
columns = ['Código', 'Ação', 'Tipo', 'Qtde. Teórica', 'Part. (%)']
df = pd.DataFrame(data, columns=columns)

# Limpar números com pontos e vírgulas (ex: "476.976.044" → 476976044)
#df['Qtde. Teórica'] = df['Qtde. Teórica'].str.replace('.', '', regex=False).astype(int)
#df['Part. (%)'] = df['Part. (%)'].str.replace(',', '.').astype(float)

# Visulizando os resultados
print(df)

# Definir estrutura local
date_str = datetime.now().strftime("%Y-%m-%d")
local_raw_path = Path("data/raw/date=" + date_str)

# Criar diretório se não existir
local_raw_path.mkdir(parents=True, exist_ok=True)

# Salvar com estrutura particionada
file_name = f"b3_{datetime.now().strftime('%Y%m%d')}.parquet"
file_path = local_raw_path / file_name

df.to_parquet(file_path)
print(f"✅ Dados brutos salvos em: {file_path}")

# Enviar para S3
#s3.upload_file(file_name, bucket_name, f"{raw_prefix}/{file_name}")

print("✅ Dados salvos no S3!")
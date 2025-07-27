# 📊 Tech Challenge - Fase 2: Pipeline Batch Bovespa na AWS

Este repositório contém a implementação do projeto "Tech Challenge" da Fase 2 da Pós-Graduação em Machine Learning Engineering, focado na construção de um pipeline de dados batch robusto e automatizado para o mercado financeiro brasileiro.

O objetivo principal é extrair, processar e analisar dados do pregão da B3 (Bolsa de Valores do Brasil) utilizando uma combinação estratégica de serviços da AWS (S3, Glue, Lambda, Athena) e automatizando a ingestão de dados com GitHub Actions.

## ✨ Funcionalidades Principais

*   **Web Scraping Automatizado:** Coleta diária de dados do pregão da B3, orquestrada por **GitHub Actions**.
*   **Armazenamento em Camadas:** Dados brutos (`raw/`) e refinados (`refined/`) persistidos no Amazon S3, otimizados com particionamento por data.
*   **ETL Visual com AWS Glue:** Processamento, limpeza e transformação dos dados utilizando o AWS Glue Studio, com o Glue Data Catalog para gerenciamento de metadados.
*   **Orquestração Orientada a Eventos:** O pipeline de transformação é disparado automaticamente por eventos no S3, coordenados por AWS Lambda e Amazon EventBridge, garantindo a atualização do Glue Data Catalog antes do processamento.
*   **Análise Interativa:** Dados refinados disponíveis para consulta e análise via SQL no Amazon Athena.
*   **Governança e Segurança:** Utilização de variáveis de ambiente e GitHub Secrets para credenciais AWS, seguindo boas práticas de segurança.

## 🏗️ Arquitetura do Pipeline

O pipeline segue uma arquitetura em camadas, totalmente automatizada, desde a coleta dos dados até a disponibilização para análise:

[GITHUB ACTIONS]
     ↓ (diariamente às 20h UTC)
[Web Scraping → S3 raw/date=YYYY-MM-DD/]
     ↓ (S3 Event)
[Lambda 1 → Start Glue Crawler]
     ↓
[Glue Crawler → Glue Data Catalog]
     ↓ (Success Event)
[EventBridge → Lambda 2]
     ↓
[Glue Job (Visual ETL)]
     ↓
[S3 refined/date_ingestao=/ticker=/]
     ↓
[Glue Data Catalog → Athena]


### Detalhamento do Fluxo:

1.  Um workflow no GitHub Actions executa o script Python de web scraping (`scraping_b3.py`) diariamente.
2.  O script coleta os dados da B3 e os envia diretamente para a pasta `raw/` no S3, em formato Parquet e particionados por data.
3.  O upload de novos dados no S3 dispara uma AWS Lambda (`ibovespa-start-crawler-lambda`), que inicia o Glue Crawler.
4.  O Glue Crawler (`bovespa_raw_crawler`) varre a pasta `raw/`, detecta novas partições e atualiza o Glue Data Catalog.
5.  Após o sucesso do Crawler, o Amazon EventBridge (monitorando eventos do Glue) dispara outra AWS Lambda (`ibovespa-lambda-trigger`).
6.  Esta Lambda inicia o AWS Glue Job (`ibovespa-glue-job`), que processa os dados brutos com as transformações necessárias (agrupamento, renomeação de colunas, cálculo com datas).
7.  Os dados transformados são salvos na pasta `refined/` no S3, também em Parquet e particionados por data e `ticker`.
8.  O Glue Job automaticamente atualiza o Glue Data Catalog com os metadados dos dados refinados.
9.  Por fim, os dados refinados ficam acessíveis para consultas SQL interativas via Amazon Athena, utilizando o Glue Data Catalog.

## ⚙️ Tecnologias Utilizadas

*   **Automação/CI/CD:** [GitHub Actions](https://docs.github.com/en/actions)
*   **Web Scraping:** [Python](https://www.python.org/) com [Playwright](https://playwright.dev/) e [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
*   **Manipulação de Dados:** [Pandas](https://pandas.pydata.org/)
*   **Armazenamento de Dados:** [Amazon S3](https://aws.amazon.com/s3/)
*   **ETL & Catálogo de Dados:** [AWS Glue](https://aws.amazon.com/glue/)
*   **Orquestração de Eventos:** [AWS Lambda](https://aws.amazon.com/lambda/) e [Amazon EventBridge](https://aws.amazon.com/eventbridge/)
*   **Consulta SQL:** [Amazon Athena](https://aws.amazon.com/athena/)
*   **SDK AWS para Python:** [Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

## 🚀 Como Executar o Projeto

Para replicar e executar este pipeline, siga os passos abaixo:

### Pré-requisitos

*   Conta AWS ativa.
*   Um bucket S3 criado (ex: `ibovespa-bucket-data`) com pastas `raw/` e `refined/`.
*   Credenciais AWS (`Access Key ID` e `Secret Access Key`) com permissões para:
    *   Escrever no bucket S3.
    *   Criar e gerenciar funções Lambda.
    *   Criar e gerenciar Glue Crawlers e Jobs.
    *   Acesso ao EventBridge.
*   Repositório no GitHub.

### 🔐 Configuração das Credenciais AWS no GitHub Secrets

As credenciais AWS necessárias para o script de scraping são gerenciadas de forma segura através dos GitHub Secrets.

1.  No seu repositório GitHub, navegue até `Settings > Secrets and variables > Actions`.
2.  Clique em `New repository secret` e adicione as seguintes secrets:
    *   `AWS_ACCESS_KEY_ID`: Sua AWS Access Key ID.
    *   `AWS_SECRET_ACCESS_KEY`: Sua AWS Secret Access Key.

### 📂 Estrutura do Projeto

Clone o repositório e observe a seguinte estrutura:

techchallenge-fase2/
├── src/
│   └── scraping_b3.py          # Script principal de scraping
├── .github/
│   └── workflows/
│       └── scraping-b3.yml     # Workflow do GitHub Actions
├── requirements.txt            # Dependências Python
├── .env.example                # Modelo de variáveis de ambiente
├── .gitignore
└── README.md                   # Este arquivo


### 🏃 Executando o Pipeline

A etapa de web scraping e ingestão de dados brutos é totalmente automatizada via GitHub Actions.

*   **Agendamento:** O workflow `scraping-b3.yml` está configurado para executar diariamente às **8h da manhã (UTC)** automaticamente.
*   **Disparo Manual:** Para testar ou executar o scraping sob demanda, você pode disparar o workflow manualmente:
    1.  No seu repositório GitHub, navegue até a aba `Actions`.
    2.  No menu lateral esquerdo, clique em `Scraping B3 - Execução Diária`.
    3.  No lado direito, clique no botão `Run workflow` e confirme.

O restante do pipeline (Lambda, EventBridge, Glue, Athena) é orquestrado por eventos na AWS, sendo disparado automaticamente após o sucesso da ingestão de dados brutos no S3.

## 📄 Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
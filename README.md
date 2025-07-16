# Tech Challenge Fase 2 - Pipeline Batch Bovespa na AWS

Este projeto implementa um pipeline completo de dados para extração, transformação e disponibilização dos dados do pregão da B3 (Bolsa de Valores do Brasil), utilizando serviços da AWS:
- **Amazon S3**: Armazenamento em camadas raw e refined.
- **AWS Glue**: Processamento ETL visual.
- **AWS Lambda**: Gatilho automático para iniciar o Glue.
- **Amazon Athena**: Consulta SQL dos dados refinados.

---

## 🧰 Objetivo

Criar um **pipeline batch** automatizado para extrair dados do site da B3, processá-los com AWS Glue e torná-los disponíveis no Amazon Athena para análise.

---

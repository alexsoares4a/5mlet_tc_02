import boto3

# Inicializa o cliente Glue fora da função lambda_handler para reuso
# Isso otimiza a performance em múltiplas invocações (warm start)
glue_client = boto3.client('glue')

def lambda_handler(event, context):
    """
    Função Lambda responsável por iniciar um AWS Glue Crawler.

    Esta função é acionada por um evento de criação de objeto no Amazon S3
    (indicando a chegada de novos dados brutos) e tem como objetivo acionar
    o Crawler do Glue para atualizar o Glue Data Catalog com os metadados
    desses novos dados e suas partições.

    Args:
        event (dict): O objeto de evento JSON passado pela origem do evento (S3).
                      Contém detalhes sobre o objeto S3 que disparou a função.
        context (LambdaContext): O objeto de contexto do Lambda que fornece
                                 informações sobre a invocação, função e ambiente de execução.

    Returns:
        dict: Um dicionário contendo o status HTTP e uma mensagem, indicando
              o sucesso ou falha da tentativa de iniciar o Crawler.
              Também trata o caso em que o Crawler já está em execução.
    """

    # Define o nome do Crawler que será iniciado
    crawler_name = 'ibovespa-crawler'

    # Imprime uma mensagem indicando que o Crawler será iniciado
    print(f"Recebido evento do S3. Iniciando o Crawler: {crawler_name}")

    try:
        # Tenta iniciar o Glue Crawler
        response = glue_client.start_crawler(Name=crawler_name)
        # Se o Crawler for iniciado com sucesso, imprime a resposta da API
        print(f"Crawler '{crawler_name}' iniciado com sucesso. Response: {response}")
        # Retorna uma resposta de sucesso
        return {
            'statusCode': 200,
            'body': 'Crawler iniciado com sucesso!'
        }
    except glue_client.exceptions.CrawlerRunningException:
        # Captura a exceção se o Crawler já estiver em execução
        print(f"Crawler '{crawler_name}' já está em execução. Ignorando a solicitação.")
        # Retorna uma resposta de sucesso com uma mensagem informativa
        return {
            'statusCode': 200,
            'body': 'Crawler já está em execução, requisição ignorada.'
        }
    except Exception as e:
        # Captura qualquer outra exceção que possa ocorrer durante a tentativa de iniciar o Crawler
        print(f"Erro ao iniciar o Crawler '{crawler_name}': {e}")
        # Retorna uma resposta de falha com a mensagem de erro
        return {
            'statusCode': 500,
            'body': f'Falha ao inicializar o Crawler: {e}'
        }

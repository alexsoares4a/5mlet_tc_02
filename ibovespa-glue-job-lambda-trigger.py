import boto3

# Inicializa o cliente Glue fora da função lambda_handler para reuso
# Isso otimiza a performance em múltiplas invocações (warm start)
glue = boto3.client('glue')

def lambda_handler(event, context):
    """
    Função Lambda responsável por iniciar um AWS Glue Job.

    Esta função é acionada por um evento do Amazon EventBridge (geralmente
    após o sucesso da execução de um Crawler do Glue) e tem como objetivo
    acionar o Job ETL principal do Glue para processamento de dados refinados.

    Args:
        event (dict): O objeto de evento JSON passado pela origem do evento (EventBridge).
                      Contém metadados sobre o evento que disparou a função.
        context (LambdaContext): O objeto de contexto do Lambda que fornece
                                 informações sobre a invocação, função e ambiente de execução.

    Returns:
        dict: Um dicionário contendo o status HTTP e uma mensagem, indicando
              o sucesso ou falha da tentativa de iniciar o Job Glue.
    """
    # Define o nome do Job Glue que será iniciado
    job_name = 'ibovespa-glue-job'

    # Para fins de depuração: imprime o evento recebido e a tentativa de início do Job
    print(f"Evento recebido: {event}")
    print(f"Tentando iniciar o Job Glue: {job_name}")

    try:
        # Inicia a execução do Job Glue especificado
        response = glue.start_job_run(JobName=job_name)
        # Se o job for iniciado com sucesso, imprime o JobRunId
        print(f"Job Glue '{job_name}' iniciado com sucesso. Run ID: {response['JobRunId']}")
        # Retorna uma resposta de sucesso
        return {'statusCode': 200, 'body': 'Job Glue iniciado com sucesso'}
    except Exception as e:
        # Em caso de erro ao iniciar o job, imprime a mensagem de erro
        print(f"Erro ao iniciar o Job Glue '{job_name}': {e}")
        # Retorna uma resposta de falha com o erro
        return {'statusCode': 500, 'body': f"Erro ao iniciar Job Glue: {str(e)}"}

import os

def apagar_arquivos_pasta(caminho_pasta):
    # Verificar se o caminho é um diretório
    if not os.path.isdir(caminho_pasta):
        print("O caminho especificado não é um diretório.")
        return

    # Iterar sobre os arquivos na pasta
    for arquivo in os.listdir(caminho_pasta):
        caminho_arquivo = os.path.join(caminho_pasta, arquivo)
        
        # Verificar se o caminho é um arquivo (não é um diretório)
        if os.path.isfile(caminho_arquivo):
            # Remover o arquivo
            os.remove(caminho_arquivo)
            print(f"Arquivo removido: {caminho_arquivo}")

# Substitua 'caminho_pasta' pelo caminho da pasta que você deseja limpar
caminho_pasta_1 = './tmp'
caminho_pasta_2 = './reports'

apagar_arquivos_pasta(caminho_pasta_1)
apagar_arquivos_pasta(caminho_pasta_2)
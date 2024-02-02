import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

altura = 1.68
peso_usuario = 54.2
imc_usuario = peso_usuario / (altura * altura)

top_range_wheit = 121
if peso_usuario >= 120:
  top_range_wheit = peso_usuario + 20


# Lista para armazenar os dados
dados = []

for i in range(0, top_range_wheit):
    imc = i / (altura * altura)
    imc = round(imc, 2)

    if imc < 18.5:
        categoria = 'baixo peso'
    elif 18.5 <= imc < 24.9:
        categoria = 'intervalo normal'
    elif 25 <= imc < 29.9:
        categoria = 'sobrepeso'
    elif 30 <= imc < 34.9:
        categoria = 'obesidade classe I'
    elif 35 <= imc < 39.9:
        categoria = 'obesidade classe II'
    else:
        categoria = 'obesidade classe III'

    # Adicionar os dados a lista
    dados.append({'Peso': i, 'IMC': imc, 'Categoria': categoria})

# Criar DataFrame a partir da lista
df = pd.DataFrame(dados)
# print(df)
round_peso_usuario = round(peso_usuario, 0)
print(round_peso_usuario)
peso_base = round_peso_usuario - 10
peso_top = round_peso_usuario + 10

df_filter = df[df['Peso'].between(peso_base, peso_top)]
print(df_filter.to_string(index=False))
df = df[df['Peso'] % 10 == 0]

# Criar gráfico de linha com degradê
cores = {'baixo peso': 'blue', 'intervalo normal': 'green', 'sobrepeso': 'yellow',
         'obesidade classe I': 'orange', 'obesidade classe II': 'red', 'obesidade classe III': 'purple'}

fig, ax = plt.subplots()

for categoria, cor in cores.items():
    subset = df[df['Categoria'] == categoria]
    ax.scatter(subset['Peso'], subset['IMC'], c=[cor], label=categoria, cmap='viridis', s=100)

# Adicionar o ponto do usuário com quadrado transparente e borda colorida
borda_cor = cores[dados[int(peso_usuario)]['Categoria']]  # Cor da borda de acordo com a categoria
ax.scatter(peso_usuario, imc_usuario, color='none', edgecolors=borda_cor, linewidths=2, label='Usuário', s=150, marker='s')

# Adicionar linhas de grade
ax.grid(True, linestyle='--', alpha=0.5)

# Adicionar rótulos e título
ax.set_xlabel('Peso (kg)')
ax.set_ylabel('IMC')
ax.set_title('Distribuição de IMC por Categoria e Peso')

# Adicionar legenda
ax.legend()

# Definir rótulos no eixo horizontal a cada intervalo de 10 kg
ax.set_xticks(range(0, top_range_wheit, 10))

# Exibir o gráfico
plt.show()
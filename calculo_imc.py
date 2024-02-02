import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from prettytable import PrettyTable

altura = 1.68
peso_usuario = 60
imc_usuario = peso_usuario / (altura * altura)
usuario = 'usuário_teste'

top_range_weight = 121
if peso_usuario >= 120:
  top_range_weight = peso_usuario + 20


# Lista para armazenar os dados
dados = []
ideal_weight = []

for i in range(0, top_range_weight):
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

    
    if 18.5 <= imc < 24.9:
      ideal_weight.append({'Peso': i, 'IMC': imc, 'Categoria': categoria}) 

# Criar DataFrame a partir da lista
df = pd.DataFrame(dados)
df_ideal_weight = pd.DataFrame(ideal_weight)
# print(df)

# Modelando Tabela 2
round_peso_usuario = round(peso_usuario, 0)
peso_base = round_peso_usuario - 10
peso_top = round_peso_usuario + 10

categoria_usuario = df.loc[df['IMC'] <= imc_usuario, 'Categoria'].iloc[-1]

if categoria_usuario != 'intervalo normal':
  # descobrindo peso ideal
  if categoria_usuario == 'baixo peso':
    categoria_top = 'intervalo normal'
    categoria_base = categoria_usuario
  else:
    categoria_top = categoria_usuario
    categoria_base = 'intervalo normal'
    
    # print(f'ora, ora, temos um problema aqui...{categoria_usuario}')

  df_filter = df[df['Categoria'].between(categoria_base, categoria_top)]
  df_filter.loc[df_filter['Peso'] == round_peso_usuario, 'user_'] = 'você'
  df_filter = df_filter.fillna('-')

else:  
  df_filter = df[df['Peso'].between(peso_base, peso_top)]
  df_filter.loc[df_filter['Peso'] == round_peso_usuario, 'user_'] = 'você'
  df_filter = df_filter.fillna('-')

# print(df_filter.to_string(index=False))

# Imprimir a tabela ajustada

print('Tabela 1: Pesos ideais.')

tabela_pretty = PrettyTable(df_ideal_weight.columns.tolist())
tabela_pretty.add_rows(df_ideal_weight.values)
print(tabela_pretty)

print('Tabela 2: Comparativo.')

tabela_pretty = PrettyTable(df_filter.columns.tolist())
tabela_pretty.add_rows(df_filter.values)
print(tabela_pretty)

print('Tabela 3: Dados usuário.')

x = PrettyTable()
x.field_names = ["Nome", "Peso", "IMC", "Categoria"]
x.add_row([usuario, peso_usuario, round(imc_usuario, 2), categoria_usuario])
print(x)


# Ajuste df para indices do grafico
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
ax.scatter(peso_usuario, imc_usuario, color='none', edgecolors=borda_cor, linewidths=2, label=usuario, s=150, marker='s')

# Adicionar linhas de grade
ax.grid(True, linestyle='--', alpha=0.5)

# Adicionar rótulos e título
ax.set_xlabel('Peso (kg)')
ax.set_ylabel('IMC')
ax.set_title('Distribuição de IMC por Categoria e Peso')

# Adicionar legenda
ax.legend()

# Definir rótulos no eixo horizontal a cada intervalo de 10 kg
ax.set_xticks(range(0, top_range_weight, 10))

# Exibir o gráfico
plt.show()
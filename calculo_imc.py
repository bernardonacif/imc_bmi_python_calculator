import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from prettytable import PrettyTable
import yaml
import sqlite3

# Carregar dados YAML do arquivo
with open('./cfg/appsettings.yml', 'r') as arquivo:
    cfg_data = yaml.load(arquivo, Loader=yaml.FullLoader)


unit_type = cfg_data['user_cfg']['unit']

altura = 1.68
peso_usuario = 60
imc_usuario = peso_usuario / (altura * altura)
usuario = 'usuário_teste'
user_email = 'user4.test@tesmail.com'


if cfg_data['sql_cfg']['use_sql'] == 1:
    try:
        conn = sqlite3.connect('./SQLite/imc_bmi.db')
        cursor = conn.cursor()
        #verificar se o usr existe
        cursor.execute('''select email, id from user where email = ?''',(user_email,))
        existing_user = cursor.fetchone()
        if existing_user is None:
            try:
                # Se o usuário não existir, inserir um novo usuário
                cursor.execute('''INSERT INTO "USER" ("name", "email", "create")
                                  VALUES (?, ?, CURRENT_TIMESTAMP)''', (usuario, user_email))
                conn.commit()
                cursor.execute('''SELECT last_insert_rowid()''')
                user_id = cursor.fetchone()[0]
            except sqlite3.Error as e:
                print(f'Erro: SQLite insert error. {e}')          
        else:
            email, user_id = existing_user 
    except sqlite3.Error as e:
       print(f'Error to connect database. {e}')
    finally:
       conn.close()
# else:
#    print('sql config OFF')
    

top_range_weight = 121
if peso_usuario >= 120:
  top_range_weight = peso_usuario + 20


# Lista para armazenar os dados
dados = []
ideal_weight = []

# Underweight = <18.5
# Normal weight = 18.5–24.9
# Overweight = 25–29.9
# Obesity = BMI of 30 or greater


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

# Gravar dados do usuario na tbl SQLite

categoria_usuario = df.loc[df['IMC'] <= imc_usuario, 'Categoria'].iloc[-1]

if cfg_data['sql_cfg']['use_sql'] == 1:
    try:
        conn = sqlite3.connect('./SQLite/imc_bmi.db')
        cursor = conn.cursor()
        try:
            # report_id|user_id|weight|height|imc_bmi|category|measures_type|date|
            cursor.execute('''INSERT INTO "user_reports" ("user_id", "weight", "height", "imc_bmi", "category", "measures_type", "date")
          VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''', (user_id, peso_usuario, altura, imc_usuario, categoria_usuario, unit_type))
            conn.commit()
        except sqlite3.Error as e:
                   print(f'Erro: SQLite insert error. {e}')     
    except sqlite3.Error as e:
       print(f'Error to connect database. {e}')
    finally:
       conn.close()

# Modelando Tabela 2
round_peso_usuario = round(peso_usuario, 0)
peso_base = round_peso_usuario - 10
peso_top = round_peso_usuario + 10


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
# print(tabela_pretty)

print('Tabela 2: Comparativo.')

tabela_pretty = PrettyTable(df_filter.columns.tolist())
tabela_pretty.add_rows(df_filter.values)
# print(tabela_pretty)

print('Tabela 3: Dados usuário.')

x = PrettyTable()
x.field_names = ["Nome", "Peso", "IMC", "Categoria"]
x.add_row([usuario, peso_usuario, round(imc_usuario, 2), categoria_usuario])
# print(x)


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
# plt.show()
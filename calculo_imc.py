import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from prettytable import PrettyTable
import yaml
import sqlite3

class App:
    def __init__(self, name, age, weight, height, user, user_email):
        self.name = name
        self.age = age
        self.weight = weight 
        self.height = height
        self.user = user
        self.user_email = user_email
        self.top_range_weight = 121  # Definindo top_range_weight como variável de instância

        
    def config(self):

        # Carregar dados YAML do arquivo
        with open('./cfg/appsettings.yml', 'r') as arquivo:
            self.cfg_data = yaml.load(arquivo, Loader=yaml.FullLoader)
        # Definindo cfgs como variaveis
            self.unit_type = self.cfg_data['user_cfg']['unit']

# altura = 1.68
# peso_usuario = 60
# imc_usuario = peso_usuario / (altura * altura)
# usuario = 'usuário_teste'
# user_email = 'user4.test@tesmail.com'
    
    def check_user(self):

        if self.cfg_data['sql_cfg']['use_sql'] == 1:
            try:
                conn = sqlite3.connect('./SQLite/imc_bmi.db')
                cursor = conn.cursor()
                #verificar se o usr existe
                cursor.execute('''select email, id from user where email = ?''',(self.user_email,))
                existing_user = cursor.fetchone()
                if existing_user is None:
                    try:
                        # Se o usuário não existir, inserir um novo usuário
                        cursor.execute('''INSERT INTO "USER" ("name", "email", "create")
                                          VALUES (?, ?, CURRENT_TIMESTAMP)''', (self.user, self.user_email))
                        conn.commit()
                        cursor.execute('''SELECT last_insert_rowid()''')
                        self.user_id = cursor.fetchone()[0]
                    except sqlite3.Error as e:
                        print(f'Erro: SQLite insert error. {e}')          
                else:
                    email, self.user_id = existing_user 
            except sqlite3.Error as e:
               print(f'Error to connect database. {e}')
            finally:
               conn.close()
        # else:
        #    print('sql config OFF')
            

    def calculate(self):
        
        self.ideal_weight = []  # Definindo self.ideal_weight antes de usá-lo
        self.dados = []
        self.imc_usuario = self.weight / (self.height ** 2)
        
        if self.weight >= 120:
          self.top_range_weight = self.weight + 20
        
        # Underweight = <18.5
        # Normal weight = 18.5–24.9
        # Overweight = 25–29.9
        # Obesity = BMI of 30 or greater
        
        
        for i in range(0, self.top_range_weight):
            imc = i / (self.height ** 2)
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
            self.dados.append({'Peso': i, 'IMC': imc, 'Categoria': categoria})
        
            # Adicionar dados a lista de pesos ideal 
            if 18.5 <= imc < 24.9:
              self.ideal_weight.append({'Peso': i, 'IMC': imc, 'Categoria': categoria}) 

    def generate_data(self):
        # Criar DataFrame's a partir das listas
        self.df = pd.DataFrame(self.dados)
        df_ideal_weight = pd.DataFrame(self.ideal_weight)
        # print(df)
        
        # Gravar dados do usuario na tbl SQLite
        categoria_usuario = self.df.loc[self.df['IMC'] <= self.imc_usuario, 'Categoria'].iloc[-1]
        
        if self.cfg_data['sql_cfg']['use_sql'] == 1:
            try:
                conn = sqlite3.connect('./SQLite/imc_bmi.db')
                cursor = conn.cursor()
                try:
                    # report_id|user_id|weight|height|imc_bmi|category|measures_type|date|
                    cursor.execute('''INSERT INTO "user_reports" ("user_id", "weight", "height", "imc_bmi", "category", "measures_type", "date")
                  VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''', (self.user_id, self.weight, self.height, self.imc_usuario, categoria_usuario, self.unit_type))
                    conn.commit()
                except sqlite3.Error as e:
                           print(f'Erro: SQLite insert error. {e}')     
            except sqlite3.Error as e:
               print(f'Error to connect database. {e}')
            finally:
               conn.close()
        
        # Modelando Tabela 2
        round_peso_usuario = round(self.weight, 0)
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
        
          df_filter = self.df[self.df['Categoria'].between(categoria_base, categoria_top)]
          df_filter.loc[df_filter['Peso'] == round_peso_usuario, 'user_'] = 'você'
          df_filter = df_filter.fillna('-')
        
        else:  
          df_filter = self.df[self.df['Peso'].between(peso_base, peso_top)]
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
        x.add_row([self.user, self.weight, round(self.imc_usuario, 2), categoria_usuario])
        print(x)

    def generate_graph(self):
        # Ajuste df para indices do grafico
        self.df = self.df[self.df['Peso'] % 10 == 0]
        
        # Criar gráfico de linha com degradê
        cores = {'baixo peso': 'blue', 'intervalo normal': 'green', 'sobrepeso': 'yellow',
                 'obesidade classe I': 'orange', 'obesidade classe II': 'red', 'obesidade classe III': 'purple'}
        
        fig, ax = plt.subplots()
        
        for categoria, cor in cores.items():
            subset = self.df[self.df['Categoria'] == categoria]
            ax.scatter(subset['Peso'], subset['IMC'], c=[cor], label=categoria, cmap='viridis', s=100)
        
        # Adicionar o ponto do usuário com quadrado transparente e borda colorida
        borda_cor = cores[self.dados[int(self.weight)]['Categoria']]  # Cor da borda de acordo com a categoria
        ax.scatter(self.weight, self.imc_usuario, color='none', edgecolors=borda_cor, linewidths=2, label=self.user, s=150, marker='s')
        
        # Adicionar linhas de grade
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Adicionar rótulos e título
        ax.set_xlabel('Peso (kg)')
        ax.set_ylabel('IMC')
        ax.set_title('Distribuição de IMC por Categoria e Peso')
        
        # Adicionar legenda
        ax.legend()
        
        # Definir rótulos no eixo horizontal a cada intervalo de 10 kg
        ax.set_xticks(range(0, self.top_range_weight, 10))
        
        # Exibir o gráfico
        plt.show()

if __name__ == "__main__":
    # Exemplo de uso:
    app = App(name="João", age=30, weight=70, height=1.75, user="joao123", user_email="joao@example.com")
    app.config()
    app.check_user()
    app.calculate()
    app.generate_data()
    app.generate_graph()
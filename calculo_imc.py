import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from prettytable import PrettyTable
import yaml
import sqlite3
from datetime import date

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
            self.cfg_unit_type = self.cfg_data['user_cfg']['unit']

    def unit_type(self, unit):
        cfg_unit_type = self.cfg_data['user_cfg']['unit']
        conn = sqlite3.connect('./SQLite/imc_bmi.db')
        cursor = conn.cursor()
        cursor.execute(f'''SELECT "{cfg_unit_type}" FROM units WHERE alias = ?''', (unit,))
        result = cursor.fetchone()
        if result:
            self.text = result[0]  # Extrai o texto da tupla
            return self.text
        else:
            return None  # Retorna None se não houver correspondência para o alias
        
    def select_text(self, alias):
        language = self.cfg_data['user_cfg']['language']
        conn = sqlite3.connect('./SQLite/imc_bmi.db')
        cursor = conn.cursor()
        cursor.execute(f'''SELECT "{language}" FROM language WHERE alias = ?''', (alias,))
        result = cursor.fetchone()
        if result:
            self.text = result[0]  # Extrai o texto da tupla
            return self.text
        else:
            return None  # Retorna None se não houver correspondência para o alias
    
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
                categoria = self.select_text('underweight')
            elif 18.5 <= imc < 24.9:
                categoria = self.select_text('normal_weight')
            elif 25 <= imc < 29.9:
                categoria = self.select_text('overweight')
            elif 30 <= imc < 34.9:
                categoria = self.select_text('obesity_1')
            elif 35 <= imc < 39.9:
                categoria = self.select_text('obesity_2')
            else:
                categoria = self.select_text('obesity_3')
        
            # Adicionar os dados a lista
            self.dados.append({self.select_text('weight'): i, self.select_text('imc'): imc, self.select_text('category'): categoria})
        
            # Adicionar dados a lista de pesos ideal 
            if 18.5 <= imc < 24.9:
              self.ideal_weight.append({self.select_text('weight'): i, self.select_text('imc'): imc, self.select_text('category'): categoria}) 

    def generate_data(self):
        # Criar DataFrame's a partir das listas
        self.df = pd.DataFrame(self.dados)
        self.df_ideal_weight = pd.DataFrame(self.ideal_weight)
        # print(df)
        
        # Gravar dados do usuario na tbl SQLite
        self.categoria_usuario = self.df.loc[self.df[self.select_text('imc')] <= self.imc_usuario, self.select_text('category')].iloc[-1]
        
        if self.cfg_data['sql_cfg']['use_sql'] == 1:
            try:
                conn = sqlite3.connect('./SQLite/imc_bmi.db')
                cursor = conn.cursor()
                try:
                    # report_id|user_id|weight|height|imc_bmi|category|measures_type|date|
                    cursor.execute('''INSERT INTO "user_reports" ("user_id", "weight", "height", "imc_bmi", "category", "measures_type", "date")
                  VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''', (self.user_id, self.weight, self.height, self.imc_usuario, self.categoria_usuario, self.unit_type))
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
        
        
        if self.categoria_usuario != self.select_text('normal_weight'):
          # descobrindo peso ideal
          if self.categoria_usuario == self.select_text('underweight'):
            categoria_top = self.select_text('normal_weight')
            categoria_base = self.categoria_usuario
          else:
            categoria_top = self.categoria_usuario
            categoria_base = self.select_text('normal_weight')
            
            # print(f'ora, ora, temos um problema aqui...{categoria_usuario}')

          a = self.select_text('weight')
        
          self.df_filter = self.df[self.df[self.select_text('category')].between(categoria_base, categoria_top)]
          self.df_filter.loc[self.df_filter[self.select_text('weight')] == round_peso_usuario, 'user_'] = self.select_text('you')
          self.df_filter = self.df_filter.fillna('-')
        
        else:  
          self.df_filter = self.df[self.df[self.select_text('weight')].between(peso_base, peso_top)]
          self.df_filter.loc[self.df_filter[self.select_text('weight')] == round_peso_usuario, 'user_'] = self.select_text('you')
          self.df_filter = self.df_filter.fillna('-')
        
        # print(df_filter.to_string(index=False))
        print(self.df)
        print(self.df_filter)

        # Lista de DF Gerados 
        # df_ideal_weight -> Pesos Ideais. Todos os pesos para aquele tamanho
        # df_filter -> Comparativo. Onde o user está dentro da tbl
        # 
        
        
        def print_tables():
            # Imprimir a tabelas ajustadas - desabilitado - apenas para debug ou visualizar no terminal
            print('Tabela 1: Pesos ideais.')
            
            tabela_pretty = PrettyTable(self.df_ideal_weight.columns.tolist())
            tabela_pretty.add_rows(self.df_ideal_weight.values)
            print(tabela_pretty)
            
            print('Tabela 2: Comparativo.')
            
            tabela_pretty = PrettyTable(self.df_filter.columns.tolist())
            tabela_pretty.add_rows(self.df_filter.values)
            print(tabela_pretty)
            
            print('Tabela 3: Dados usuário.')
        
            x = PrettyTable()
            x.field_names = ["Nome", "Peso", "IMC", "Categoria"]
            x.add_row([self.user, self.weight, round(self.imc_usuario, 2), self.categoria_usuario])
            print(x)

    def generate_graph(self):
        # Ajuste df para indices do grafico
        self.df = self.df[self.df[self.select_text('weight')] % 10 == 0]
        
        # Criar gráfico de linha com degradê
        cores = {self.select_text('underweight'): 'blue', self.select_text('normal_weight'): 'green', self.select_text('overweight'): 'yellow',
                 self.select_text('obesity_1'): 'orange', self.select_text('obesity_2'): 'red', self.select_text('obesity_3'): 'purple'}
        
        fig, ax = plt.subplots()
        
        for categoria, cor in cores.items():
            subset = self.df[self.df[self.select_text('category')] == categoria]
            ax.scatter(subset[self.select_text('weight')], subset[self.select_text('imc')], c=[cor], label=categoria, cmap='viridis', s=100)
        
        # Adicionar o ponto do usuário com quadrado transparente e borda colorida
        borda_cor = cores[self.dados[int(self.weight)][self.select_text('category')]]  # Cor da borda de acordo com a categoria
        ax.scatter(self.weight, self.imc_usuario, color='none', edgecolors=borda_cor, linewidths=2, label=self.user, s=150, marker='s')
        
        # Adicionar linhas de grade
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Adicionar rótulos e título
        ax.set_xlabel(self.select_text('weight')+'('+app.unit_type("weight")+')')
        ax.set_ylabel(self.select_text('imc'))
        ax.set_title(self.select_text('gaph_title'))
        
        # Adicionar legenda
        ax.legend()
        
        # Definir rótulos no eixo horizontal a cada intervalo de 10 kg
        ax.set_xticks(range(0, self.top_range_weight, 10))
        
        # Exibir o gráfico
        # plt.show()
        plt.savefig('./tmp/grafico.png')

    # Funcoes propriedades para gerar PDF
    
if __name__ == "__main__":
    # Exemplo de uso:
    app = App(name="João", age=30, weight=70, height=1.75, user="joao123", user_email="joao@example.com")
    app.config()
    app.check_user()
    app.calculate()
    app.generate_data()
    app.generate_graph()
    # app.generate_pdf_v4()
    # app.generate_pfd_v5()
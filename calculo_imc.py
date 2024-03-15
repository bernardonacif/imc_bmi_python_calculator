import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from prettytable import PrettyTable
import yaml
import sqlite3
from datetime import datetime, timezone, timedelta

# Local Libraries

from select_text import MyClass

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
    
    def set_gmt(self):
        if self.cfg_data['sql_cfg']['type'] == 'sqlite':
            gmt = self.cfg_data['user_cfg']['GMT']
            fuso_horario_local = datetime.now(timezone(timedelta(hours=gmt)))
            timestamp_local = fuso_horario_local.strftime('%Y-%m-%d %H:%M:%S')
        return(timestamp_local)
    
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
                        timestamp_local = self.set_gmt()
                        # Se o usuário não existir, inserir um novo usuário
                        cursor.execute('''INSERT INTO "USER" ("name", "email", "create")
                                          VALUES (?, ?, ?)''', (self.user, self.user_email, timestamp_local))
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
        # print('foi o sql grava dados')
        # else:
        #    print('sql config OFF')

    def grava_sql(self):
        unit_type = self.cfg_data['user_cfg']['unit']
        if self.cfg_data['sql_cfg']['use_sql'] == 1:
            try:
                conn = sqlite3.connect('./SQLite/imc_bmi.db')
                cursor = conn.cursor()
                try:
                    timestamp_local = self.set_gmt()
                    # report_id|user_id|weight|height|imc_bmi|category|measures_type|date|
                    cursor.execute('''INSERT INTO "user_reports" ("user_id", "weight", "height", "imc_bmi", "category", "measures_type", "date")
                  VALUES (?, ?, ?, ?, ?, ?, ?)''', (self.user_id, self.weight, self.height, self.imc_usuario, self.categoria, unit_type, timestamp_local))
                    conn.commit()
                except sqlite3.Error as e:
                           print(f'Erro: SQLite insert error. {e}')     
            except sqlite3.Error as e:
               print(f'Error to connect database. {e}')
            finally:
               conn.close()

    def category(self):
        imc = self.weight / (self.height ** 2) 
        
        if imc < 18.5:
            self.categoria = self.select_text('underweight')
        elif 18.5 <= imc < 24.9:
            self.categoria = self.select_text('normal_weight')
        elif 25 <= imc < 29.9:
            self.categoria = self.select_text('overweight')
        elif 30 <= imc < 34.9:
            self.categoria = self.select_text('obesity_1')
        elif 35 <= imc < 39.9:
            self.categoria = self.select_text('obesity_2')
        else:
            self.categoria = self.select_text('obesity_3')

        return(self.categoria)


    def calculate(self):
        self.ideal_weight = []  # Definindo self.ideal_weight antes de usá-lo
        self.dados = []
        self.imc_usuario = self.weight / (self.height ** 2)  
        if self.weight >= 120:
          self.top_range_weight = self.weight + 20
        
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

            # gerar lista

            self.dados.append({self.select_text('weight'): i, self.select_text('imc'): imc, self.select_text('category'): categoria})

        return(self.imc_usuario)
    
    def generate_table(self):
        # print('retorno dos dados df')
        self.df = pd.DataFrame(self.dados)

        return(self.df)
    
    def generate_graph(self):
        # Ajuste df para indices do grafico
        self.generate_table()
        self.df = self.df[self.df[self.select_text('weight')] % 10 == 0]
        
        # Criar gráfico de linha com degradê
        cores = {self.select_text('underweight'): 'blue', self.select_text('normal_weight'): 'green', self.select_text('overweight'): 'yellow',
                 self.select_text('obesity_1'): 'orange', self.select_text('obesity_2'): 'red', self.select_text('obesity_3'): 'purple'}
        
        fig, ax = plt.subplots()
        
        # for categoria, cor in cores.items():
        #     subset = self.df[self.df[self.select_text('category')] == categoria]
        #     ax.scatter(subset[self.select_text('weight')], subset[self.select_text('imc')], c=[cor], label=categoria, cmap='viridis', s=100)
        for categoria, cor in cores.items():
            subset = self.df[self.df[self.select_text('category')] == categoria]
            ax.scatter(subset[self.select_text('weight')], subset[self.select_text('imc')], c=[cor], label=categoria, s=100)



        # Adicionar o ponto do usuário com quadrado transparente e borda colorida
        borda_cor = cores[self.dados[int(self.weight)][self.select_text('category')]]  # Cor da borda de acordo com a categoria
        ax.scatter(self.weight, self.imc_usuario, color='none', edgecolors=borda_cor, linewidths=2, label=self.user, s=150, marker='s')
        
        # Adicionar linhas de grade
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Adicionar rótulos e título
        ax.set_xlabel(self.select_text('weight')+'('+MyClass().select_units('weight', 'units')+')')
        ax.set_ylabel(self.select_text('imc'))
        ax.set_title(self.select_text('gaph_title'))
        
        # Adicionar legenda
        ax.legend()
        
        # Definir rótulos no eixo horizontal a cada intervalo de 10 kg
        ax.set_xticks(range(0, self.top_range_weight, 10))
        
        # Exibir o gráfico
        # plt.show()
        plt.savefig('./tmp/grafico.png')

    def generate_graph_v2(self):
        # Ajuste df para índices do gráfico
        self.generate_table()
        self.df = self.df[self.df[self.select_text('weight')] % 10 == 0]
        
        # Criar gráfico de dispersão com cores para cada categoria
        cores = {
            self.select_text('underweight'): 'blue',
            self.select_text('normal_weight'): 'green',
            self.select_text('overweight'): 'yellow',
            self.select_text('obesity_1'): 'orange',
            self.select_text('obesity_2'): 'red',
            self.select_text('obesity_3'): 'purple'
        }
        
        fig, ax = plt.subplots()
        
        for categoria, cor in cores.items():
            subset = self.df[self.df[self.select_text('category')] == categoria]
            ax.scatter(subset[self.select_text('weight')], subset[self.select_text('imc')], color=cor, label=categoria, s=100)
        
        # Adicionar o ponto do usuário com quadrado transparente e borda colorida
        categoria_usuario = self.dados[int(self.weight)][self.select_text('category')]
        borda_cor = cores[categoria_usuario]  # Cor da borda de acordo com a categoria
        ax.scatter(self.weight, self.imc_usuario, edgecolors=borda_cor, linewidths=2, label=self.user, s=150, marker='s')
        
        # Adicionar linhas de grade
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Adicionar rótulos e título
        ax.set_xlabel(self.select_text('weight') + '(' + MyClass().select_units('weight', 'units') + ')')
        ax.set_ylabel(self.select_text('imc'))
        ax.set_title(self.select_text('graph_title'))
        
        # Adicionar legenda
        ax.legend()
        
        # Definir rótulos no eixo horizontal a cada intervalo de 10 kg
        ax.set_xticks(range(0, self.top_range_weight, 10))
        
        # Exibir o gráfico
        # plt.show()
        plt.savefig('./tmp/grafico.png')

    
    def historical_graph_old(self, table):
        # print(self.user_id)
        gera_grafico = 0
        try:
            conn = sqlite3.connect('./SQLite/imc_bmi.db')
            cursor = conn.cursor()
            try:
                query = f'SELECT weight, date FROM {table} WHERE "user_id" = {self.user_id}'
                cursor.execute(query)
                resultados = cursor.fetchall()
                gera_grafico = 1
            except sqlite3.Error as e:
                       print(f'Erro: SQLite insert error. {e}')     
        except sqlite3.Error as e:
           print(f'Error to connect database. {e}')
        finally:
           conn.close()

        if gera_grafico == 1:
            weight = [resultado[0] for resultado in resultados]
            date = [resultado[1] for resultado in resultados]

            plt.bar(date, weight)
            plt.xlabel('data')
            plt.ylabel('peso')
            plt.title('Contagem de itens por categoria')
            plt.savefig('./tmp/grafico_1.png')
            # plt.show()
    
    def historical_graph(self, table):
        # print(self.user_id)
        gera_grafico = 0
        try:
            conn = sqlite3.connect('./SQLite/imc_bmi.db')
            cursor = conn.cursor()
            try:
                query = f'SELECT weight, date FROM {table} WHERE "user_id" = {self.user_id}'
                cursor.execute(query)
                resultados = cursor.fetchall()
                gera_grafico = 1
            except sqlite3.Error as e:
                print(f'Erro: SQLite insert error. {e}')     
        except sqlite3.Error as e:
            print(f'Error to connect database. {e}')
        finally:
            conn.close()
    
        if gera_grafico == 1:
            weight = [resultado[0] for resultado in resultados]
            date = [resultado[1] for resultado in resultados]
    
            # Criar uma nova figura para o segundo gráfico
            plt.figure()
    
            plt.bar(date, weight)
            plt.xlabel('data')
            plt.ylabel('peso')
            plt.title('Contagem de itens por categoria')
            plt.xticks(rotation=90)
            plt.savefig('./tmp/grafico_1.png')
            # plt.show()

    





      

if __name__ == "__main__":
    # Exemplo de uso:
    print('hello, my friends :)')

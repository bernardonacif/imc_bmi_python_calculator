# Python libraries
from fpdf import FPDF, XPos, YPos

from datetime import datetime, timedelta, date
import yaml
import sqlite3
# import os

# Local libraries
from calculo_imc import App as calculo

class App:
    def __init__(self, name, age, weight, height, user, user_email):
        self.name = name
        self.age = age
        self.weight = weight 
        self.height = height
        self.user = user
        self.user_email = user_email
        

    def config(self):
        with open('./cfg/appsettings.yml', 'r') as arquivo:
            self.cfg_data = yaml.load(arquivo, Loader=yaml.FullLoader)
        # Definindo cfgs como variaveis
            self.unit_type = self.cfg_data['user_cfg']['unit']
            self.language = self.cfg_data['user_cfg']['language']
            self.unit = self.cfg_data['user_cfg']['unit']
            

    # Gerando Elementos do PDF

    def background(self, pdf, WIDTH):
        # language = self.cfg_data['user_cfg']['language']
        if self.language == 'PT/BR':
            self.background_img = './resources/IMC-DATA_v3.png'
        elif self.language == 'ENG/US':
            self.background_img = './resources/BMI-DATA.png'
        else:
            self.background_img = './resources/BMI-DATA.png'
        pdf.image(self.background_img, 0, 0, WIDTH) 

    def select_text(self, alias):
        # language = self.cfg_data['user_cfg']['language']
        conn = sqlite3.connect('./SQLite/imc_bmi.db')
        cursor = conn.cursor()
        cursor.execute(f'''SELECT "{self.language}" FROM language WHERE alias = ?''', (alias,))
        result = cursor.fetchone()
        if result:
            self.text = result[0]  # Extrai o texto da tupla
            return self.text
        else:
            return None  # Retorna None se não houver correspondência para o alias
    
    def insert_datetime(self, today, pdf):
        if self.language == 'PT/BR':
            today = date.today().strftime("%d-%m-%Y")
        elif self.language == 'ENG/US':
            today = date.today().strftime("%Y-%m-%d")
        else:
            today = date.today().strftime("%Y-%m-%d")
        pdf.set_font('helvetica', '', 16)
        pdf.set_text_color(255, 255, 255)
        pdf.ln(30)
        pdf.write(4, f' {today}')    
        pdf.set_text_color(0, 0, 0)
    
    
    def create_title(self, today, pdf):
        if self.language == 'PT/BR':
            today = date.today().strftime("%d-%m-%Y")
        elif self.language == 'ENG/US':
            today = date.today().strftime("%Y-%m-%d")
        else:
            today = date.today().strftime("%Y-%m-%d")
        pdf.set_font('helvetica', 'B', 24)
        pdf.ln(55)
        pdf.write(5, self.select_text("report_title"))
        pdf.ln(10)
        pdf.set_font('helvetica', '', 16)
        pdf.write(4, f'{today}')
        pdf.ln(12)

    def use_data_info_v2(self, pdf, name, age, weight, height, bmi, category):
        pdf.ln(12)
        pdf.set_font('helvetica', '', 10)
        # Supondo que a largura da página seja 210mm (padrão A4)
        pagina_largura = 210
        
        # Dividindo a largura da página em três colunas
        coluna_largura = pagina_largura / 3
        
        # Configurando o alinhamento para centralizar horizontalmente as células
        alinhamento = "L"
        
        # Adicionando as células em três colunas de duas
        pdf.cell(coluna_largura, 10, f'{self.select_text("name_title")} {name}', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, f'{self.select_text("age_title")} {age}', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, f'{self.select_text("weight_title")} {weight} ', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, '', 0, 1, alinhamento)
        
        # pdf.cell(coluna_largura, 10, '', 0, 1, alinhamento)
        
        pdf.cell(coluna_largura, 10, f'{self.select_text("height_title")} {height} ', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, f'{self.select_text("imc_title")} {round(bmi, 3)}', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, f'{self.select_text("category_title")} {category}', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, '', 0, 1, alinhamento)
    
    def add_data(self, pdf, name, age, weight, height, bmi, category):
        pagina_largura = 210
        coluna_largura = pagina_largura / 3
        alinhamento = "L"  # Alterado para alinhar à direita

        pdf.cell(coluna_largura, 10, f'{self.select_text("name_title")} {name}', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, f'{self.select_text("age_title")} {age}', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, f'{self.select_text("weight_title")} {weight}', 0, 1, alinhamento)  # Ajustado para nova linhpdf
        pdf.cell(coluna_largura, 10, f'{self.select_text("height_title")} {height}', 0, 0, alinhamento)  # Adicionado 0 para não mover para uma nova linha
        pdf.cell(coluna_largura, 10, f'{self.select_text("imc_title")} {round(bmi, 3)}', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, f'{self.select_text("category_title")} {category}', 0, 1, alinhamento)  # Ajustado para nova linha

    def objective(self, pdf):
        # y_position = pdf.get_y()
        # pdf.set_y(y_position + 5)
        pdf.set_font('helvetica', 'B', 10)
        y_position = pdf.get_y()
        pdf.cell(0, 10, self.select_text("objective_title"))
        pdf.set_font('helvetica', '', 8)
        pdf.set_y(y_position + 10)
        # Definindo a margem direita como a largura do documento menos a margem esquerda
        right_margin = pdf.w - pdf.l_margin
        # Definindo a altura da célula para 5 (altere conforme necessário)
        cell_height = 5
        # Escrevendo o texto dentro do espaço disponível
        pdf.set_x(pdf.l_margin)  # Definindo a posição x para a margem esquerda
        pdf.multi_cell(right_margin - pdf.get_x(), cell_height, self.select_text("objective_text"), align='J')

    def graph_main(self, pdf):
        image_path = "./tmp/grafico.png" 
        x_position = (pdf.w - 100) / 2  # Centralizar horizontalmente (ajustar conforme necessário)
        y_position = pdf.get_y() + 40  # Posicionar após o elemento app.use_data_info_v2() com um espaço de 10 unidades
        # Adicionar o gráfico ao PDF
        pdf.image(image_path, x=x_position, y=y_position, w=100)

    def disclaimer(self, pdf):
        pdf.set_font('helvetica','' , 8)
        pdf.set_text_color(255, 0, 0)
        pdf.ln(130)
        pdf.write(5, self.select_text('disclaimer_resumido'))
    
    def footer(self, pdf, number_page):
        pdf.set_y(-31)
        pdf.set_font('helvetica', 'I', 8)
        pdf.set_text_color(0, 0, 0)
        # pdf.cell(0, 10, 'Página ' + str(self.page_no()), 0, 0, 'C')
        page = self.select_text('page')
        pdf.cell(0, 10, f'{page} {number_page}', 0, 0, 'C')

    # Gerando PDF

    def generate_report(self, user_bmi, user_category):
        self.config()
        today = date.today().strftime("%Y-%m-%d")
        pdf_filename = self.cfg_data['report_cfg']['format_name'].format(user=self.user, today=today)
        pdf = FPDF() # A4 (210 by 297 mm)

        WIDTH = 210
        HEIGHT = 297

        #  Firts Page
        pdf.add_page()
        self.background(pdf, WIDTH)
        self.insert_datetime(today,pdf)
        # self.create_title(today, pdf) 
        self.use_data_info_v2(pdf, self.name, self.age, self.weight, self.height, user_bmi, user_category)
        # self.add_data(pdf, self.name, self.age, self.weight, self.height, user_bmi, user_category)
        self.graph_main(pdf)
        self.objective(pdf)
        self.disclaimer(pdf)
        


        # Gerar PDF
        pdf.output(pdf_filename)

    
if __name__ == "__main__":    
    name = "000teste_import_file"
    age = 30
    weight = 70  # Coloque o peso desejado aqui
    height = 1.75  # Coloque a altura desejada aqui
    user = "teste_import_file"
    user_email = "exemplo@example.com"

    # executando calculos
    a = calculo(name, age, weight, height, user, user_email)
    a.config()
    a.check_user()
    bmi = a.calculate()
    print(bmi)
    bmi = round(bmi, 3)
    category = a.category()
    print(category)
    a.grava_sql()
    graph = a.generate_graph()
    graph_1 = a.historical_graph('user_reports')

    graph_1

    # montando pdf

    b = App(name, age, weight, height, user, user_email)
    b.config()
    b.generate_report(bmi, category)


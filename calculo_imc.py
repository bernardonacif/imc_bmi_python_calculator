import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from prettytable import PrettyTable
import yaml
import sqlite3
from datetime import date


from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer, KeepTogether, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, HRFlowable


# new PDF LIB v5

from fpdf import FPDF



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
        self.df_ideal_weight = pd.DataFrame(self.ideal_weight)
        # print(df)
        
        # Gravar dados do usuario na tbl SQLite
        self.categoria_usuario = self.df.loc[self.df['IMC'] <= self.imc_usuario, 'Categoria'].iloc[-1]
        
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
        
        
        if self.categoria_usuario != 'intervalo normal':
          # descobrindo peso ideal
          if self.categoria_usuario == 'baixo peso':
            categoria_top = 'intervalo normal'
            categoria_base = self.categoria_usuario
          else:
            categoria_top = self.categoria_usuario
            categoria_base = 'intervalo normal'
            
            # print(f'ora, ora, temos um problema aqui...{categoria_usuario}')
        
          self.df_filter = self.df[self.df['Categoria'].between(categoria_base, categoria_top)]
          self.df_filter.loc[self.df_filter['Peso'] == round_peso_usuario, 'user_'] = 'você'
          self.df_filter = self.df_filter.fillna('-')
        
        else:  
          self.df_filter = self.df[self.df['Peso'].between(peso_base, peso_top)]
          self.df_filter.loc[self.df_filter['Peso'] == round_peso_usuario, 'user_'] = 'você'
          self.df_filter = self.df_filter.fillna('-')
        
        # print(df_filter.to_string(index=False))
        
        
        def print_tables():
            # Imprimir a tabelas ajustadas - deabilitado - apenas para debug ou visualizar no terminal
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
        # plt.show()
        plt.savefig('./tmp/grafico.png')

    # Funcoes propriedades para gerar PDF

    def mm_to_point(self, mm):
        return mm / 0.352777
    
    def posicionar_texto_centro(self, pdf_canvas, text, page_width, page_height, y_distance):
        text_width = pdf_canvas.stringWidth(text)
        x_coordinate = (page_width - text_width) / 2
        y_coordinate = (page_height - y_distance)
        pdf_canvas.drawString(x_coordinate, y_coordinate, text)

    def posicionar_texto_canto(self, pdf_canvas, text, page_height, y_distance):    
        # Calcular a coordenada x para começar a partir da margem esquerda
        x_coordinate = self.mm_to_point(20)
        # Calcular a coordenada y
        y_coordinate = page_height - y_distance
        # Desenhar o texto
        pdf_canvas.drawString(x_coordinate, y_coordinate, text)

    def dataframe_to_table(self, dataframe):
        data = [list(dataframe.columns)]
        for row in dataframe.itertuples(index=False):
            data.append(list(row))
        return data
    
    def generate_pdf_v4(self):
        today = date.today().strftime("%Y-%m-%d")
        pdf_filename = self.cfg_data['report_cfg']['format_name'].format(user=self.user, today=today)
    
        # Criação do documento PDF
        doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
        elements = []
    
        # Estilo de parágrafo
        styles = getSampleStyleSheet()
        estilo_normal = styles['Normal']
        estilo_titulo = styles['Heading1']
        estilo_titulo.alignment = 1  # 0 para alinhar à esquerda, 1 para centralizar, 2 para alinhar à direita

        # Estilo para subtítulos
        estilo_subtitulo = ParagraphStyle(name='Subtitulo', parent=estilo_normal)
        estilo_subtitulo.fontSize = 11
        estilo_subtitulo.textColor = colors.gray
        estilo_subtitulo.alignment = 1
        
        # Título
        titulo = Paragraph("Relatório IMC", estilo_titulo)
        elements.append(titulo)
    
        # Data de Emissão
        data_emissao = f'<b>Data Emissão:</b> {date.today().strftime("%d-%m-%y")}'
        elements.append(Paragraph(data_emissao, estilo_normal))
    
        # Linha divisória
        elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.black))
    
        # Dados do usuário
        elementos_usuario = [
            [Paragraph(f'<b>Nome:</b> {self.name}', estilo_normal)],
            [Paragraph(f'<b>Idade:</b> {self.age}', estilo_normal)],
            [Paragraph(f'<b>Peso:</b> {self.weight} kg', estilo_normal)],
            [Paragraph(f'<b>Altura:</b> {self.height} m', estilo_normal)],
            [Paragraph(f'<b>IMC:</b> {round(self.imc_usuario, 2)}', estilo_normal)],
            [Paragraph(f'<b>Categoria:</b> {self.categoria_usuario.title()}', estilo_normal)],
        ]
        tabela_usuario = Table(elementos_usuario)
        elements.append(tabela_usuario)
    
        # Linha divisória
        elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.black))
        elements.append(Paragraph("<br/><br/>", estilo_normal))
    
        # Grafico

        image_path = "./tmp/grafico.png"  # Substitua pelo caminho da sua imagem
        
        # Obtendo as dimensões originais da imagem
        imagem = Image(image_path)
        largura_original, altura_original = imagem.drawWidth, imagem.drawHeight
        
        # Reduzindo a imagem em 20%
        largura_reduzida = largura_original * 0.8
        altura_reduzida = altura_original * 0.8
        
        imagem_reduzida = Image(image_path, width=largura_reduzida, height=altura_reduzida)
        elements.append(imagem_reduzida)


        
        # Tabela_1: Pesos Ideais
        subtitulo_pesos_ideais = Paragraph("Tabela 1: Pesos Ideais:", estilo_subtitulo)
        pula_linha = Paragraph("<br/><br/>", estilo_normal)

        tabela_pesos_ideais = Table(self.dataframe_to_table(self.df_ideal_weight))
        tabela_pesos_ideais.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        # elements.append(tabela_pesos_ideais)
        elements.append(KeepTogether([subtitulo_pesos_ideais, pula_linha, tabela_pesos_ideais]))

        elements.append(Paragraph("<br/><br/>", estilo_normal))

        # Tabela_2: Coparativo
        subtitulo_comparativo = Paragraph("Tabela 2: Comparativo:", estilo_subtitulo)
        pula_linha = Paragraph("<br/><br/>", estilo_normal)

        tabela_comparativo = Table(self.dataframe_to_table(self.df_filter))
        tabela_comparativo.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        # elements.append(tabela_comparativo)
        elements.append(KeepTogether([subtitulo_comparativo, pula_linha, tabela_comparativo]))

    
        # Construir o PDF
        doc.build(elements)

    # ----- V5 -----
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

    def create_title(self, today, pdf):
        today = date.today().strftime("%Y-%m-%d")
        pdf.set_font('Arial', 'B', 24)
        pdf.ln(65)
        # pdf.write(5, self.select_text('report_title'))
        pdf.write(5, self.select_text("report_title"))
        pdf.ln(10)
        pdf.set_font('Arial', '', 16)
        pdf.write(4, f'{today}')
        pdf.ln(12)

    def footer(self, pdf, number_page):
        # footer_height = 10  # Altura do rodapé em pontos
        # page_height = pdf.h  # Altura da página em pontos
        # footer_y = page_height - footer_height  # Calcula a posição y do rodapé    
        pdf.set_y(-31)
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(0, 0, 0)
        # pdf.cell(0, 10, 'Página ' + str(self.page_no()), 0, 0, 'C')
        page = self.select_text('page')
        pdf.cell(0, 10, f'{page} {number_page}', 0, 0, 'C')

    def header(self, pdf):
        pdf.set_font('Arial','', 11)

    # def use_data_info(self, pdf, bold_text, normal_text):
    #     bold_width = pdf.get_string_width(bold_text)
    #     pdf.set_font('Arial', 'B', 11)
    #     pdf.cell(bold_width, 10, bold_text, 0, 0)
    #     pdf.set_font('Arial', '', 11)
    #     pdf.cell(0, 10, normal_text, 0, 1)

    def use_data_info_v2(self, pdf, name, age, weight, height, bmi, category):
        pdf.set_font('Arial', '', 10)
        # pdf.cell(0, 10, f'{self.select_text("name")} {name}', 0, 1)
        # pdf.cell(0, 10, f'{self.select_text("age")} {age}', 0, 1)
        # pdf.cell(0, 10, f'{self.select_text("weight")} {weight} ', 0, 1)
        # pdf.cell(0, 10, f'{self.select_text("height")} {height} ', 0, 1)
        # pdf.cell(0, 10, f'{self.select_text("imc")} {round(bmi, 3)}', 0, 1)
        # pdf.cell(0, 10, f'{self.select_text("category")} {category}', 0, 1)
        # pdf.ln()
        # Supondo que a largura da página seja 210mm (padrão A4)
        pagina_largura = 210
        
        # Dividindo a largura da página em três colunas
        coluna_largura = pagina_largura / 3
        
        # Configurando o alinhamento para centralizar horizontalmente as células
        alinhamento = "L"
        
        # Adicionando as células em três colunas de duas
        pdf.cell(coluna_largura, 10, f'{self.select_text("name")} {name}', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, f'{self.select_text("age")} {age}', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, '', 0, 1, alinhamento)
        
        pdf.cell(coluna_largura, 10, f'{self.select_text("weight")} {weight} ', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, f'{self.select_text("height")} {height} ', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, '', 0, 1, alinhamento)
        
        pdf.cell(coluna_largura, 10, f'{self.select_text("imc")} {round(bmi, 3)}', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, f'{self.select_text("category")} {category}', 0, 0, alinhamento)
        pdf.cell(coluna_largura, 10, '', 0, 1, alinhamento)



    def graph_main(self, pdf):
        image_path = "./tmp/grafico.png" 
        imagem = Image(image_path)
        original_width, original_height = imagem.drawWidth, imagem.drawHeight
        reduced_width = original_width * 0.2 # Reduzir a largura
        reduced_height = original_height * 0.2 # Reduzir a altura
        x_position = (pdf.w - reduced_width) / 2  # Centralizar horizontalmente
        y_position = pdf.get_y() + 1 # Posicionar após o elemento app.use_data_info_v2() com um espaço de 10 unidades
        
        pdf.image(image_path, x_position, y_position, reduced_width, reduced_height)

    def disclaimer(self, pdf):
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color(255, 0, 0)
        pdf.ln(130)
        pdf.write(5, self.select_text('disclaimer_resumido'))
        
    def generate_pfd_v5(self):
        today = date.today().strftime("%Y-%m-%d")
        pdf_filename = self.cfg_data['report_cfg']['format_name'].format(user=self.user, today=today)

        WIDTH = 210
        HEIGHT = 297

        # config pdf
        pdf = FPDF()

        #  first page
        pdf.add_page()
        pdf.image('./resources/image.png', 0, 0, WIDTH) #descomentar depois 
        app.create_title(today, pdf)
        app.use_data_info_v2(pdf, self.name, self.age, self.weight, self.height, self.imc_usuario, self.categoria_usuario)
        app.graph_main(pdf) 
        app.disclaimer(pdf)
        app.footer(pdf, 1)
        

        # second page
        pdf.add_page()

        # Definindo margens esquerda, topo e direita como 20 mm
        pdf.set_margins(5, 5, 5)

        pdf.output(pdf_filename)




    
if __name__ == "__main__":
    # Exemplo de uso:
    app = App(name="João", age=30, weight=70, height=1.75, user="joao123", user_email="joao@example.com")
    app.config()
    app.check_user()
    app.calculate()
    app.generate_data()
    app.generate_graph()
    # app.generate_pdf_v4()
    app.generate_pfd_v5()
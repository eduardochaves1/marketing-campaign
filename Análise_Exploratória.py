import streamlit as st
import pandas as pd
import plotly.express as px
import locale

st.set_page_config(page_title='Análise Exploratória', page_icon='📊', layout='wide')
st.write('''
<style>
  section.main > div {max-width:75em}
</style>
''', unsafe_allow_html=True)

color_pallete = px.colors.sequential.matter_r


class AnaliseExploratoria:
  def __init__(self):
    """ Iniciando as principais variáveis que serão usadas na página """

    self.df = self.pipeline('assets/data.csv')

    self.start_end_dates = [self.df['date'].iloc[1], self.df['date'].iloc[-1]]

    self.reset_date() if 'start_date' and 'end_date' not in st.session_state else None

    self.start_date_filter = st.sidebar.date_input('Data Início:', min_value=self.start_end_dates[0], key='start_date')
    self.end_date_filter = st.sidebar.date_input('Data Fim:', min_value=self.start_end_dates[0], key='end_date')
    st.sidebar.button('Resetar Data', type='primary', on_click=self.reset_date)

    self.df = self.filter_df(self.df)


  def pipeline(self, path):
    """ Pipeline a qual realiza o tratamento necessário no dado importado """

    df = (pd
      .read_csv(path, parse_dates=['date'])
      .drop_duplicates()
      .dropna())

    df['sales_channel'] = df['sales_channel'].str.capitalize()
    df = df.drop(df.query('invested < 1 or returned < 1').index)

    df['roi'] = ((df['returned'] - df['invested']) / df['invested']) * 100
    df['month'] = df['date'].dt.month_name()
    df['day_of_week'] = df['date'].dt.day_name()

    df['date'] = df['date'].dt.date
    return df.reset_index(drop=True)


  def reset_date(self):
    """ Resetar a data da variável de sessão para o padrão original do dataset importado """

    st.session_state['start_date'] = self.start_end_dates[0]
    st.session_state['end_date'] = self.start_end_dates[1]


  def filter_df(self, df):
    """ Filtrar os dados do DataFrame de acordo com o intervalo de data definido no input da página """
    return df[(df['date'] >= st.session_state['start_date']) & (df['date'] <= st.session_state['end_date'])]


  def get_stats(self, title: str, value, column, type: str='currency', delta=None):
    """ Método usado para simplificar e minificar o uso de código necessário
    para utilizar o componente metric do streamlit """

    if type == 'currency':
      if delta:
        return column.metric(title, locale.currency(value, grouping=True), delta=locale.currency(delta, grouping=True))
      else:
        return column.metric(title, locale.currency(value, grouping=True))
    elif type == 'percentage':
      return column.metric(title, f'{value.round()}%')
    else:
      return column.metric(title, locale.format_string('%.0f', value, grouping=True))


  def plot_plotly(self, fig):
    """ Fazer update gerais nas figuras geradas pelo Plotly e retornar o método do
    streamlit para realizar o plot da figura com a configuração padrão """

    fig.update_layout(margin_t=10, margin_b=0, margin_r=0, hoverlabel_font_size=14, separators=',.', bargap=.1)
    return st.plotly_chart(fig, use_container_width=True, theme='streamlit')


  def main_section(self, fig, title:str=None, type:str=None):
    """ Um componente usado para simplificar e minificar o uso de código
    para gerar a parte mais comum da página """

    st.write('---')
    st.write(f'## {title}')

    if type == 'dataframe':
      st.dataframe(fig, use_container_width=True)
    else:
      self.plot_plotly(fig)


  def view(self):
    """ Principal método da classe onde gerará todos os componentes visuais da página """

    st.write('# 📊 Análise Exploratória')

    st.write("""
    - Made by [Eduardo Chaves](https://www.linkedin.com/in/edu-chaves/)
    - [GitHub Repo Link](https://github.com/eduardochaves1/marketing-campaign)
    """)

    st.write('> **OBS.:** As informações e gráficos deste projeto são baseados em dados gerados artificalmente e randômicamente por mim, criador deste projeto, logo, não refletem a realidade.')

    basic_viz, advanced_viz = st.tabs(['Estatísticas Gerais', 'Estatísticas Gerais (Avançado)'])

    with basic_viz:
      c1, c2 = st.columns(2)
      c1.metric('Primeira Data', str(st.session_state['start_date']))
      c2.metric('Última Data', str(st.session_state['end_date']))

      invested = self.df['invested'].sum()
      returned = self.df['returned'].sum()
      roi = (returned - invested)/invested * 100

      c1, c2, c3 = st.columns(3)
      self.get_stats('Total Investido', invested, column=c1)
      self.get_stats('Retorno Total', returned, delta = returned-invested, column=c2)
      self.get_stats('ROI Total', roi, column=c3, type='percentage')

    with advanced_viz:
      st.write('`>> df.describe().round()`')
      st.dataframe(self.df.describe().round(), use_container_width=True)


    self.main_section(title='📝 Amostra dos Dados', fig = self.df, type='dataframe')

    self.main_section(title='🥊 Investimento vs Retorno', fig = px.line(self.df, x='date', y=['invested', 'returned'],
      color_discrete_sequence=[color_pallete[0], color_pallete[-2]]))

    self.main_section(title='🤝 Relação Investimento-Retorno', fig = px.scatter(self.df, x='invested', y='returned',
      color='month', color_discrete_sequence=color_pallete))

    self.main_section(title='🏆 Melhores Canais de Venda', fig = px.histogram(self.df, x='sales_channel', color='month',
      category_orders={'sales_channel': self.df['sales_channel'].value_counts().index}, color_discrete_sequence=color_pallete))


    st.write('## ℹ️ Distribuições')

    invested_returned, roi_box, roi_hist = st.tabs(['Investimento vs Retorno', 'ROI (Boxplot)', 'ROI (Histograma)'])

    with invested_returned:
      self.plot_plotly(px.box(self.df, y=['invested', 'returned'], color_discrete_sequence=[color_pallete[-2]]))
    with roi_box:
      self.plot_plotly(px.box(self.df['roi'], color_discrete_sequence=[color_pallete[-2]]))
    with roi_hist:
      self.plot_plotly(px.histogram(self.df['roi'], color_discrete_sequence=[color_pallete[-2]]))

AnaliseExploratoria().view()

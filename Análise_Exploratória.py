import streamlit as st
import pandas as pd
import plotly.express as px
import locale

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
st.set_page_config(page_title='Análise Exploratória', page_icon='📊', layout='wide')
st.write('''
<style>
  section.main > div {max-width:75em}
</style>
''', unsafe_allow_html=True)


class AnaliseExploratoria:
  def __init__(self):
    self.df = pd.read_csv('assets/data.csv', parse_dates=['date'])
    self.df['date'] = self.df['date'].dt.date

    self.start_end_dates = [self.df['date'].iloc[1], self.df['date'].iloc[-1]]

    self.reset_date() if 'start_date' and 'end_date' not in st.session_state else None

    self.start_date_filter = st.sidebar.date_input('Data Início:', min_value=self.start_end_dates[0], key='start_date')
    self.end_date_filter = st.sidebar.date_input('Data Fim:', min_value=self.start_end_dates[0], key='end_date')
    st.sidebar.button('Resetar Data', type='primary', on_click=self.reset_date)

    self.df = self.filter_df(self.df)


  def reset_date(self):
    st.session_state['start_date'] = self.start_end_dates[0]
    st.session_state['end_date'] = self.start_end_dates[1]


  def filter_df(self, df):
    return df[(df['date'] >= st.session_state['start_date']) & (df['date'] <= st.session_state['end_date'])]


  def get_stats(self, title: str, value, column, type: str='currency', delta=None):
    if type == 'currency':
      if delta:
        return column.metric(title, locale.currency(value, grouping=True), delta=locale.currency(delta, grouping=True))
      else:
        return column.metric(title, locale.currency(value, grouping=True))
    elif type == 'percentage':
      return column.metric(title, f'{value.round()}%')
    else:
      return column.metric(title, locale.format_string('%.0f', value, grouping=True))


  def line(self):
    st.write('---')


  def plot_plotly(self, fig):
    fig.update_layout(margin_t=10, margin_b=0, margin_r=0, hoverlabel_font_size=14, separators=',.')
    return st.plotly_chart(fig, use_container_width=True, theme='streamlit')


  def main_section(self, fig, title:str=None, type:str=None):
    self.line()
    st.write(f'## {title}')
    
    if type == 'dataframe':
      return st.dataframe(fig, use_container_width=True)
    else:
      return self.plot_plotly(fig)


  def view(self):
    st.write('# 📊 Análise Exploratória')

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

    self.main_section(title='🥊 Investimento vs Retorno', fig = px.line(self.df, x='date', y=['invested', 'returned']))

    self.main_section(title='🤝 Relação Investimento-Retorno', fig = px.scatter(self.df, x='invested', y='returned', color='month'))

    self.main_section(title='🔝 Melhores Canais de Venda', fig = px.histogram(self.df, x='selling_chanel', color='month',
      category_orders={'selling_chanel': self.df['selling_chanel'].value_counts().index}))


    st.write('## ℹ️ Distribuições')

    invested_returned, roi_box, roi_hist = st.tabs(['Investimento vs Retorno', 'ROI (Boxplot)', 'ROI (Histograma)'])

    with invested_returned:
      self.plot_plotly(px.box(self.df, y=['invested', 'returned']))
    with roi_box:
      self.plot_plotly(px.box(self.df['roi']))
    with roi_hist:
      self.plot_plotly(px.histogram(self.df['roi']))

AnaliseExploratoria().view()

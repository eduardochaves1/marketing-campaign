import streamlit as st
import pandas as pd
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import joblib
from PIL import Image as img

st.set_page_config(page_title='Modelo Preditivo', page_icon='🤖', layout='wide')
st.write('''
<style>
  section.main > div {max-width:65em}
</style>
''', unsafe_allow_html=True)

class ModeloPreditivo:
  def __init__(self):
    """ Iniciando a classe da página com as principais variáveis usadas """

    self.model = joblib.load('assets/model.jbl')
    self.minMaxScaler_fit = joblib.load('assets/minMaxScaler_fit.jbl')
    self.labelEncoder_fit = joblib.load('assets/labelEncoder_fit.jbl')
    self.feature_importance_img = img.open('assets/feature_importance.png')
    self.today = pd.to_datetime(pd.to_datetime(dt.today()))
    self.sales_channel_options = ['Social media', 'Tv', 'Radio', 'Print advertising']
    self.make_inputs()
    self.df = self.get_data()


  def make_inputs(self):
    """ (Sem Retorno) Método usado para criar os inputs de forma dinâmica, para evitar que o usuário
    acabe selecionando uma data anterior ao momento atual e que seja de acordo com as
    variâncias de data, ou seja, meses que tem quantidade de dias diferentes e etc. """

    def get_all_days():
      return st.sidebar.selectbox('**Dia:**', options=['Auto']+[i for i in range(31+1) if i > 0])

    self.invested = st.sidebar.number_input('**Valor a Investir:**', min_value=1_000, max_value=500_000, value=20_000, step=1_000)

    self.sales_channel = st.sidebar.selectbox('**Canal de Venda:**', options=['Auto']+self.sales_channel_options)

    self.year = st.sidebar.selectbox('**Ano:**', options=pd.date_range(self.today, periods=3, freq='Y').year)

    if self.year == self.today.year:
      self.month = st.sidebar.selectbox('**Mês:**', options=['Auto']+list(pd.date_range(
        start=self.today.date(),
        end=str(self.today.year)+'-12-31',
        freq='M'
      ).month_name()))

      if self.month == 'Auto' or self.month == self.today.month_name():
        self.day = st.sidebar.selectbox('**Dia:**', options=['Auto']+list(pd.date_range(
        start=self.today,
        end=pd.to_datetime(str(self.today.to_period('M'))+'-01') + relativedelta(months=1),
        freq='D'
      ).day))
      else:
        self.day = get_all_days()

    else:
      self.month = st.sidebar.selectbox('**Mês:**',
        options=['Auto']+[(pd.to_datetime('2000') + relativedelta(months=i)).month_name() for i in range(12)])

      self.day = get_all_days()


  def get_data(self):
    """ Retornando o dataframe para demonstrar ao usuário final e usar na previsão do modelo,
    tomando cuidado de utilizar os dados gerados pelos inputs de forma adequada, seguindo a
    dinamicidade que foi requisitada pelos mesmos inputs """

    if self.year == self.today.year:
      date = pd.date_range(start=self.today, end=str(self.today.year)+'-12-31')
    else:
      date = pd.date_range(start=str(self.year), end=str(self.year)+'-12-31')

    df = pd.DataFrame({'date': date})
    df['invested'] = self.invested

    if self.month != 'Auto':
      df = df.query('date.dt.month_name() == @self.month')
    if self.day != 'Auto':
      df = df.query('date.dt.day == @self.day')

    if self.sales_channel != 'Auto':
      df['sales_channel'] = self.sales_channel
    else:
      dfs_to_concat = []

      for sales_channel in self.sales_channel_options:
        new_df = df.copy()
        new_df['sales_channel'] = sales_channel
        dfs_to_concat.append(new_df)

      df = pd.concat(dfs_to_concat)

    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_of_week'] = df['date'].dt.day_name()
    df = df.drop('date', axis=1)
    
    return df.reset_index(drop=True)


  def predict_inputs(self):
    """ Método que fará o tratamento dos dados gerados para testar no modelo e retornar
    um dataframe formatado, servindo de output com as 5 melhores previsões """

    df_treated = self.df.copy()
    
    df_treated['invested'] = self.minMaxScaler_fit[0][1].transform(df_treated['invested'].values.reshape(-1,1))
    
    for feature, fit in self.labelEncoder_fit:
      df_treated[feature] = fit.transform(df_treated[feature])

    predict = pd.Series(self.model.predict(df_treated)).sort_values(ascending=False)
    predict = pd.DataFrame(self.minMaxScaler_fit[1][1].inverse_transform(predict.values.reshape(-1,1)), index=predict.index)

    best_campaigns = self.df.iloc[predict[:5].index]
    best_campaigns['RETURN'] = predict.round()
    best_campaigns['PROFIT'] = best_campaigns['RETURN'] - best_campaigns['invested']
    best_campaigns['ROI'] = ((best_campaigns['RETURN'] - best_campaigns['invested']) / best_campaigns['RETURN'] * 100).round(1)
    best_campaigns['ROI'] = best_campaigns['ROI'].apply(lambda x: str(x)+'%')

    return st.dataframe(best_campaigns, use_container_width=True)


  def view(self):
    """ (Sem Retorno) Código dos componentes visuais da página """

    st.write('# 🤖 Modelo Preditivo')
    st.write('> **OBS.:** As informações e gráficos deste projeto são baseados em dados gerados artificalmente e randômicamente por mim, criador deste projeto, logo, não refletem a realidade, assim como também o modelo foi treinado nesses dados e consequentemente fará previsões fora do comum ao comparar com a vida real.')
    st.write('---')

    st.write("""
    ## ❔ Como usar a ferramenta?

    Você pode fornecer ao modelo algumas variáveis que estão na *sidebar* à esquerda desta página, alguns desses inputs você pode deixar no automático, dessa forma o modelo irá testar todas as possibilidades para cada input que você deixar assim.

    Por padrão será fornecido um valor a investir de R$20.000 no ano atual em que você estiver vizualizando esta página. Para os inputs que ficarem no *auto*, ele levará em conta todas as possibilidades para cada variável, vale lembrar que ele nunca receberá datas anteriores ao momento que você estiver utilizando esta ferramenta, até porque não é possível realizarmos uma campanha de marketing no passado 😅.

    ---
    """)

    st.write('## 📝 Dados de Input:')
    st.write(f'Baseado nos inputs selecionados, foi registrado **{len(self.df)}** possibilidades a serem previstas.')
    st.dataframe(self.df, use_container_width=True)
    st.write('---')

    st.write(f'## 🏆 Top 5 Melhores Campanhas de Marketing para {self.year}:')
    st.write('Estas são as 5 melhores campanhas de marketing a serem realizadas (maior retorno / ROI) de acordo com as possibilidades previstas pelo modelo.')
    self.predict_inputs()
    st.write('---')

    st.write('## 🤔 Como o Modelo Chegou a esta Conclusão?')
    st.write('O gráfico abaixo demonstra quais são as variáveis que mais impactam nas previsões dada pelo modelo. E baseado nos inputs das variáveis preditivas que ele recebeu foi feito a predição e então selecionado aqueles inputs com o maiores valores de retorno verificado.')
    st.image(self.feature_importance_img)

ModeloPreditivo().view()

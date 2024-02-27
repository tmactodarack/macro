import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

################################ Fetch data ######################################################
# API key for FRED 
api_key = '&api_key=82309bb88c2901b87dc6e40182e47496'
tickers = {'CPIAUCSL': 'CPI', #all cpi related are SA 
           'CPILFESL': 'Core CPI', 
           'CPIUFDSL': 'CPI Food', 
           'CPIENGSL': 'CPI Energy', 
           'PCEPI': 'PCE', 
           'PCEPILFE': 'Core PCE'
           } 

@ st.cache_data
def fetchFred(api_key, tickers):
  combine = pd.DataFrame()
  updates = pd.Series(dtype='float')

  for i in tickers.keys(): 
      url = f'https://api.stlouisfed.org/fred/series?series_id={i}{api_key}' # get latest release date
      df = pd.read_xml(url, parse_dates=['last_updated'])
      updates[tickers[i]] = (df['last_updated'][0])

      url = f'https://api.stlouisfed.org/fred/series/observations?series_id={i}{api_key}' # get data
      df = pd.read_xml(url, parse_dates=['date'])
      df.set_index('date', inplace=True)
      filt = (df['value'] != '.') # some data from fred is in weird . string
      single = df[filt]['value'].apply(lambda x: float(x)).to_frame(tickers[i]) # excluding . and turn into float
      combine = pd.concat([combine, single], axis=1)

  combine.index.name = None
  combine = combine.sort_index()
  return updates, combine
updates, combine = fetchFred(api_key, tickers)


tab1, tab2 = st.tabs(['CPI YoY vs Core CPI YoY', 'with 6m Annualized'])
with tab1:
###################################### CPI YoY ######################################
  def cpi_yoy(start, end):
    data = combine[['CPI', 'Core CPI']].pct_change(12).dropna().loc[start:end]
    update = updates['CPI']
    title = 'CPI YoY vs Core CPI YoY'

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['CPI'], name='CPI YoY', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Core CPI'], name='Core CPI YoY', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=[data.index[-1]], y=[fig.data[0]['y'][-1]-0.002], mode='markers', marker_symbol='triangle-up', marker_color='red', name='Latest Release: ' + f"{update:%m/%d/%y}" + f" ({data.index[-1]:%b})"))
    # fig.add_vline(x=data.index[-1], line_width=3, line_dash="dash", line_color="green")
    fig.update_layout(template='seaborn', 
                      showlegend=True,
                      title=dict(text=title, font=dict(size=25)),
                      margin=dict(b=0,t=80,r=0,l=0),
                      legend = dict(orientation='h',x=1, y=-0.15, xanchor='right', yanchor='top'),
                      xaxis=dict(fixedrange=True), 
                      yaxis=dict(tickformat='.1%', fixedrange=True))
    return fig, data

  if 'cpi_yoy_fig_period' not in st.session_state: 
    st.session_state['cpi_yoy_fig_period'] = 'Past 2 Years'
  ##### Trigger function below #####
  fig, data = cpi_yoy( dt.today()-timedelta(days=365*float(st.session_state['cpi_yoy_fig_period'][5])), dt.today() )
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='cpi_yoy_fig_period', horizontal=True, label_visibility='collapsed')  
  st.plotly_chart(fig, use_container_width=True)
  # st.write(fig.data[0]['y'])
with tab2:
###################################### CPI YoY + 6m annualized ######################################
  def cpi_6m(start, end):
    data = combine[['CPI', 'Core CPI']].pct_change(12).dropna().loc[start:end]
    data2 = ( combine[['CPI', 'Core CPI']].pct_change().add(1).rolling(6).apply(np.prod)**2-1 ).loc[start:end]
    update = updates['CPI']
    title = 'CPI YoY vs Core CPI YoY'

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['CPI'], name='CPI YoY', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Core CPI'], name='Core CPI YoY', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=data2.index, y=data2['CPI'], name='CPI 6m annualized', line=dict(dash='dot')))
    fig.add_trace(go.Scatter(x=data2.index, y=data2['Core CPI'], name='Core CPI 6m annualized', line=dict(dash='dot')))
    fig.add_trace(go.Scatter(x=[data.index[-1]], y=[fig.data[0]['y'][-1]-0.002], mode='markers', marker_symbol='triangle-up', marker_color='red', name='Latest Release: ' + f"{update:%m/%d/%y}" + f" ({data.index[-1]:%b})"))
    fig.update_layout(template='seaborn', 
                      margin=dict(b=0, t=80, l=0, r=0),
                      title=dict(text=title, font=dict(size=25)),
                      legend = dict(orientation='h',x=1, y=-0.15, xanchor='right', yanchor='top'),
                      # xaxis=dict(fixedrange=True, dtick='M1' if float(st.session_state['cpi_6m_fig_period'][5])<3 else None, tickformat="%b\n%Y" if float(st.session_state['cpi_6m_fig_period'][5])<3 else None ),
                      xaxis=dict(fixedrange=True), 
                      yaxis=dict(tickformat='.1%', fixedrange=True))
    return fig, data

  if 'cpi_6m_fig_period' not in st.session_state: 
    st.session_state['cpi_6m_fig_period'] = 'Past 2 Years'
  ##### Trigger function below #####
  fig, data = cpi_6m( dt.today()-timedelta(days=365*float(st.session_state['cpi_6m_fig_period'][5])), dt.today() )
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='cpi_6m_fig_period', horizontal=True, label_visibility='collapsed')
  st.plotly_chart(fig, use_container_width=True)



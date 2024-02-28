import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

################################ Fetch data ######################################################
# API key for FRED 
api_key = '&api_key=82309bb88c2901b87dc6e40182e47496'
tickers = {'CPIAUCSL': 'CPI', #all cpi related are SA 
           'CPILFESL': 'Core CPI', 
           'CPIUFDSL': 'CPI Food', 
           'CPIENGSL': 'CPI Energy', 
           'PCEPI': 'PCE', 
           'PCEPILFE': 'Core PCE',
           'CUSR0000SACL1E': 'CPI Core Goods',
           'CUSR0000SASLE': 'CPI Core Service',
           'CUSR0000SAH1': 'Shelter',
           'CUSR0000SAM2': 'Medical Care', 
           'CUSR0000SAS4': 'Transportation',
           'CPIEDUSL':'Education and Communication', 
           'CPIRECSL':'Recreation'
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
                      # legend = dict(x=0.01, y=0.99, xanchor='left', yanchor='top'),
                      xaxis=dict(fixedrange=True), 
                      yaxis=dict(tickformat='.1%', fixedrange=True))
    return fig, data

  if 'cpi_yoy_fig_period' not in st.session_state: 
    st.session_state['cpi_yoy_fig_period'] = 'Past 2 Years'
  ##### Trigger function below #####
  fig, data = cpi_yoy( dt.today()-timedelta(days=365*float(st.session_state['cpi_yoy_fig_period'][5])), dt.today() )
  st.plotly_chart(fig, use_container_width=True)
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='cpi_yoy_fig_period', horizontal=True)  
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
  st.plotly_chart(fig, use_container_width=True)
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='cpi_6m_fig_period', horizontal=True) # label_visibility='collapsed'



st.markdown('***')
###################################### CPI MoM ######################################
def cpi_mom(start, end):
  data = combine[['CPI', 'Core CPI', 'CPI Food', 'CPI Energy']].pct_change().dropna().loc[start:end]
  update = updates['CPI']
  title = 'CPI MoM Breakdown'

  fig = make_subplots(rows=2, cols=2, subplot_titles=("Headline CPI MoM", "Core CPI MoM", "CPI Food MoM", "CPI Energy MoM"))
  fig.add_trace(go.Bar(x=data.index, y=data['CPI'], name='CPI MoM'), row=1, col=1)
  fig.add_trace(go.Bar(x=data.index, y=data['Core CPI'], name='Core CPI MoM'), row=1, col=2)
  fig.add_trace(go.Bar(x=data.index, y=data['CPI Food'], name='CPI Food MoM'), row=2, col=1)
  fig.add_trace(go.Bar(x=data.index, y=data['CPI'], name='CPI Energy MoM'), row=2, col=2)
  # fig.add_trace(go.Scatter(x=[data.index[-1]], y=[fig.data[0]['y'][-1]-0.002], mode='markers', marker_symbol='triangle-up', marker_color='red', name='Latest Release: ' + f"{update:%m/%d/%y}" + f" ({data.index[-1]:%b})"))
  # fig.add_vline(x=data.index[-1], line_width=3, line_dash="dash", line_color="green")
  fig.update_layout(template='seaborn', 
                    title=dict(text=title, font=dict(size=25)),
                    margin=dict(b=0,t=80,r=0,l=0),
                    legend = dict(orientation='h',x=1, y=-0.15, xanchor='right', yanchor='top'))

  fig.update_yaxes(tickformat='.1%',fixedrange=True)
  fig.update_xaxes(fixedrange=True)
  
  return fig, data

if 'cpi_mom_fig_period' not in st.session_state: 
  st.session_state['cpi_mom_fig_period'] = 'Past 2 Years'
##### Trigger function below #####
fig, data = cpi_mom( dt.today()-timedelta(days=365*float(st.session_state['cpi_mom_fig_period'][5])), dt.today() )
st.plotly_chart(fig, use_container_width=True)
st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='cpi_mom_fig_period', horizontal=True) # label_visibility='collapsed'  
# st.write(fig.data[0]['y'])



st.markdown('***')
tab1, tab2 = st.tabs(['Core Breakdown YoY', 'Core Breakdown MoM'])
with tab1:
###################################### CPI YoY ######################################
  def core_yoy(start, end):
    data = combine[['CPI Core Goods', 'CPI Core Service']].pct_change(12).dropna().loc[start:end]
    update = updates['CPI']
    title = 'Core Goods vs Core Service YoY'

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['CPI Core Goods'], name='Core Goods YoY', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=data.index, y=data['CPI Core Service'], name='Core Service YoY', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=[data.index[-1]], y=[fig.data[0]['y'][-1]-0.004], mode='markers', marker_symbol='triangle-up', marker_color='red', name='Latest Release: ' + f"{update:%m/%d/%y}" + f" ({data.index[-1]:%b})"))
    # fig.add_vline(x=data.index[-1], line_width=3, line_dash="dash", line_color="green")
    fig.update_layout(template='seaborn', 
                      showlegend=True,
                      title=dict(text=title, font=dict(size=25)),
                      margin=dict(b=0,t=80,r=0,l=0),
                      legend = dict(orientation='h',x=1, y=-0.15, xanchor='right', yanchor='top'), 
                      # legend = dict(x=0.01, y=0.99, xanchor='left', yanchor='top'),
                      xaxis=dict(fixedrange=True), 
                      yaxis=dict(tickformat='.1%', fixedrange=True))
    return fig, data

  if 'core_yoy_fig_period' not in st.session_state: 
    st.session_state['core_yoy_fig_period'] = 'Past 2 Years'
  ##### Trigger function below #####
  fig, data = core_yoy( dt.today()-timedelta(days=365*float(st.session_state['core_yoy_fig_period'][5])), dt.today() )
  st.plotly_chart(fig, use_container_width=True)
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='core_yoy_fig_period', horizontal=True)  

with tab2:
###################################### CPI MoM ######################################
  def core_mom(start, end):
    data = combine[['CPI Core Goods', 'CPI Core Service']].pct_change().dropna().loc[start:end]
    update = updates['CPI']
    title = 'Core Goods vs Core Service MoM'

    fig = go.Figure()
    fig.add_trace(go.Bar(x=data.index, y=data['CPI Core Goods'], name='Core Goods MoM'))
    fig.add_trace(go.Bar(x=data.index, y=data['CPI Core Service'], name='Core Service MoM'))
    # fig.add_trace(go.Scatter(x=[data.index[-1]], y=[fig.data[0]['y'][-1]-0.003], mode='markers', marker_symbol='triangle-up', marker_color='red', name='Latest Release: ' + f"{update:%m/%d/%y}" + f" ({data.index[-1]:%b})"))
    # fig.add_vline(x=data.index[-1], line_width=3, line_dash="dash", line_color="green")
    fig.update_layout(template='seaborn', 
                      title=dict(text=title, 
                      font=dict(size=25)), 
                      margin=dict(b=0,t=80,r=0,l=0), 
                      legend = dict(orientation='h',x=1, y=-0.15, xanchor='right', yanchor='top'),
                      xaxis=dict(fixedrange=True),
                      yaxis=dict(tickformat='.1%', fixedrange=True))
    return fig, data

  if 'core_mom_fig_period' not in st.session_state: 
    st.session_state['core_mom_fig_period'] = 'Past 2 Years'
  ##### Trigger function below #####
  fig, data = core_mom( dt.today()-timedelta(days=365*float(st.session_state['core_mom_fig_period'][5])), dt.today() )
  st.plotly_chart(fig, use_container_width=True)
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='core_mom_fig_period', horizontal=True)  


st.markdown('***')
tab1, tab2, tab3, tab4 = st.tabs(['1','2','3', '4'])
with tab1:
###################################### CPI service yoy ######################################
  def core_service(start, end):
    data = combine[['CPI Core Service']].pct_change(12).dropna().loc[start:end]
    update = updates['CPI']
    title = 'Core Service YoY'

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['CPI Core Service'], mode='lines+markers', name='Core Service MoM'))
    fig.add_trace(go.Scatter(x=[data.index[-1]], y=[fig.data[0]['y'][-1]-0.003], mode='markers', marker_symbol='triangle-up', marker_color='red', name='Latest Release: ' + f"{update:%m/%d/%y}" + f" ({data.index[-1]:%b})"))
    # fig.add_vline(x=data.index[-1], line_width=3, line_dash="dash", line_color="green")
    fig.update_layout(template='seaborn', 
                      title=dict(text=title, font=dict(size=25)), 
                      margin=dict(b=0,t=80,r=0,l=0), 
                      legend=dict(orientation='h',x=1, y=-0.15, xanchor='right', yanchor='top'),
                      xaxis=dict(fixedrange=True),
                      yaxis=dict(tickformat='.1%', fixedrange=True))
    return fig, data

  if 'core_service_fig_period' not in st.session_state: 
    st.session_state['core_service_fig_period'] = 'Past 2 Years'
  ##### Trigger function below #####
  fig, data = core_service( dt.today()-timedelta(days=365*float(st.session_state['core_service_fig_period'][5])), dt.today() )
  st.plotly_chart(fig, use_container_width=True)
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='core_service_fig_period', horizontal=True)  

with tab2:
###################################### CPI shelter yoy ######################################
  def shelter_yoy(start, end):
    data = combine[['Shelter']].pct_change(12).dropna().loc[start:end]
    update = updates['CPI']
    title = 'Shelter YoY'

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Shelter'], mode='lines+markers', name='Shelter YoY'))
    fig.add_trace(go.Scatter(x=[data.index[-1]], y=[fig.data[0]['y'][-1]-0.003], mode='markers', marker_symbol='triangle-up', marker_color='red', name='Latest Release: ' + f"{update:%m/%d/%y}" + f" ({data.index[-1]:%b})"))
    # fig.add_vline(x=data.index[-1], line_width=3, line_dash="dash", line_color="green")
    fig.update_layout(template='seaborn', 
                      title=dict(text=title, font=dict(size=25)), 
                      margin=dict(b=0,t=80,r=0,l=0), 
                      legend=dict(orientation='h',x=1, y=-0.15, xanchor='right', yanchor='top'),
                      xaxis=dict(fixedrange=True),
                      yaxis=dict(tickformat='.1%', fixedrange=True))
    return fig, data

  if 'shelter_yoy_fig_period' not in st.session_state: 
    st.session_state['shelter_yoy_fig_period'] = 'Past 2 Years'
  ##### Trigger function below #####
  fig, data = shelter_yoy( dt.today()-timedelta(days=365*float(st.session_state['shelter_yoy_fig_period'][5])), dt.today() )
  st.plotly_chart(fig, use_container_width=True)
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='shelter_yoy_fig_period', horizontal=True)  

with tab3:
###################################### CPI shelter mom ######################################
  def shelter_yoy(start, end):
    data = combine[['Shelter']].pct_change().dropna().loc[start:end]
    update = updates['CPI']
    title = 'Shelter MoM'

    fig = go.Figure()
    fig.add_trace(go.Bar(x=data.index, y=data['Shelter'], name='Shelter MoM')) #mode='lines+markers'
    fig.add_trace(go.Scatter(x=[data.index[-1]], y=[fig.data[0]['y'][-1]-0.003], mode='markers', marker_symbol='triangle-up', marker_color='red', name='Latest Release: ' + f"{update:%m/%d/%y}" + f" ({data.index[-1]:%b})"))
    # fig.add_vline(x=data.index[-1], line_width=3, line_dash="dash", line_color="green")
    fig.update_layout(template='seaborn', 
                      title=dict(text=title, font=dict(size=25)), 
                      margin=dict(b=0,t=80,r=0,l=0), 
                      legend=dict(orientation='h',x=1, y=-0.15, xanchor='right', yanchor='top'),
                      xaxis=dict(fixedrange=True),
                      yaxis=dict(tickformat='.1%', fixedrange=True))
    return fig, data

  if 'shelter_mom_fig_period' not in st.session_state: 
    st.session_state['shelter_mom_fig_period'] = 'Past 2 Years'
  ##### Trigger function below #####
  fig, data = shelter_yoy( dt.today()-timedelta(days=365*float(st.session_state['shelter_mom_fig_period'][5])), dt.today() )
  st.plotly_chart(fig, use_container_width=True)
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='shelter_mom_fig_period', horizontal=True)  

with tab4:
  def service_others_mom(start, end):
    data = combine[['Medical Care', 'Transportation', 'Education and Communication', 'Recreation']].pct_change().dropna().loc[start:end]
    update = updates['CPI']
    title = 'Other Core Service MoM'

    fig = make_subplots(rows=2, cols=2, subplot_titles=('Medical Care MoM', 'Transportation MoM', 'Education and Communication MoM', 'Recreation MoM'))
    fig.add_trace(go.Bar(x=data.index, y=data['Medical Care'], name='Medical Care MoM'), row=1, col=1)
    fig.add_trace(go.Bar(x=data.index, y=data['Transportation'], name='Transportation MoM'), row=1, col=2)
    fig.add_trace(go.Bar(x=data.index, y=data['Education and Communication'], name='Education and Communication MoM'), row=2, col=1)
    fig.add_trace(go.Bar(x=data.index, y=data['Recreation'], name='Recreation MoM'), row=2, col=2)
    # fig.add_trace(go.Scatter(x=[data.index[-1]], y=[fig.data[0]['y'][-1]-0.002], mode='markers', marker_symbol='triangle-up', marker_color='red', name='Latest Release: ' + f"{update:%m/%d/%y}" + f" ({data.index[-1]:%b})"))
    # fig.add_vline(x=data.index[-1], line_width=3, line_dash="dash", line_color="green")
    fig.update_layout(template='seaborn', 
                      title=dict(text=title, font=dict(size=25)),
                      margin=dict(b=0,t=80,r=0,l=0),
                      legend = dict(orientation='h',x=1, y=-0.15, xanchor='right', yanchor='top'))

    fig.update_yaxes(tickformat='.1%',fixedrange=True)
    fig.update_xaxes(fixedrange=True)
    
    return fig, data

  if 'service_others_mom_fig_period' not in st.session_state: 
    st.session_state['service_others_mom_fig_period'] = 'Past 2 Years'
  ##### Trigger function below #####
  fig, data = service_others_mom( dt.today()-timedelta(days=365*float(st.session_state['service_others_mom_fig_period'][5])), dt.today() )
  st.plotly_chart(fig, use_container_width=True)
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='service_others_mom_fig_period', horizontal=True) # label_visibility='collapsed' 
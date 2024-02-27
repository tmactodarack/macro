import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio


st.markdown('# Wage Inflation')
st.markdown('''
            Wage inflation is a crucial metrics for Fed to **gauge potential core price pressure**. 
            Here we focus on employment cost index(ECI) and average hourly earning(AHE).
            '''
            )


################################ Fetch data ######################################################
# API key for FRED 
api_key = '&api_key=82309bb88c2901b87dc6e40182e47496'
tickers = {'ECIWAG': 'Employment Cost Index', # ECIWAG is SA, using NSA for yoy might be wrong
           'CES0500000003': 'Average Hourly Earnings', # CES0500000003 is SA
           'PCEPILFE': 'Core PCE' # PCEPILFE is SA
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

###################################### Long Term ######################################
longTerm = combine[['Employment Cost Index', 'Average Hourly Earnings', 'Core PCE']].resample('q').mean().dropna().pct_change(4)
longTerm_fig = go.Figure()
longTerm_fig.add_trace(go.Line(x=longTerm.index, y=longTerm['Employment Cost Index'], name='ECI YoY'))
longTerm_fig.add_trace(go.Line(x=longTerm.index, y=longTerm['Average Hourly Earnings'], name='AHE YoY'))
longTerm_fig.add_trace(go.Line(x=longTerm.index, y=longTerm['Core PCE'], name='Core PCE YoY'))
longTerm_fig.update_layout(template='seaborn', 
                    showlegend=True,
                    title=dict(text='Long Term Relationship between Wage Inflation and Core Inflation', font=dict(size=20)),
                    # title_x=0.1,
                    legend = dict(orientation='h', x=1, y=1, xanchor='right', yanchor='bottom'),
                    # margin=dict(b=50,l=70,r=70,t=70),
                    xaxis=dict(fixedrange=True),
                    yaxis=dict(tickformat='.1%', fixedrange=True))
# longTerm_fig.update_yaxes(automargin=True)
# longTerm_fig.update_xaxes(automargin=True)
st.plotly_chart(longTerm_fig, use_container_width=True)
# st.markdown('''
#             The core inflation is not highly tied to wage inflation, or to put it more generally, 
#             they may be affected by a more high level macro environment. For ECI and ACH, they may share somewhat similar
#             long-term trend like 2010 to 2020 they both ticked up gradually; however, for short term movement they are very noisy during this period.
#             Especially in 2020 after COVID, AHE jumped while ECI dipped, reflecting AHE does not track the same employees components while
#             ECI does. Speaking back to the relationship between core PCE and wage inflation, we can see n at least i2013 - 2015 and 2019-2020, they
#             moved in the opposite way which may be counter intuition.  
#             ***
#             ''')

tab1, tab2 = st.tabs(['QoQ', 'YoY'])
###################################### ECI QoQ ######################################
with tab1:
  def eci_qoq(start, end):
    data = combine['Employment Cost Index'].dropna().pct_change().loc[start:end]
    update = updates['Employment Cost Index']
    title = 'Employment Cost Index QoQ'

    fig = go.Figure()
    fig.add_trace(go.Bar(x=data.index, y=data, name='ECI QoQ'))
    fig.add_trace(go.Scatter(x=[data.index[-1]], 
                            y=[data[-1]], 
                            mode='markers',
                            marker_symbol='star',
                            marker_size=11 , 
                            name='Release: ' + f"{update:%m/%d/%y}"))
    fig.update_layout(template='seaborn', 
                      showlegend=True,
                      title=dict(text=title, font=dict(size=20)),
                      legend = dict(orientation='h',x=1, y=1, xanchor='right', yanchor='bottom'),
                      xaxis=dict(tickvals = data.index, ticktext = data.index.to_period('q').to_series().astype(str), fixedrange=True), 
                      yaxis=dict(tickformat='.1%', fixedrange=True))
    return fig, data

  if 'eci_qoq_fig_period' not in st.session_state: 
    st.session_state['eci_qoq_fig_period'] = 'Past 2 Years'
  fig, data = eci_qoq( dt.today()-timedelta(days=365*float(st.session_state['eci_qoq_fig_period'][5])), dt.today() )
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='eci_qoq_fig_period', horizontal=True, label_visibility='collapsed')
  st.plotly_chart(fig, use_container_width=True)
  
  # st.slider('Custom Period', value=(data.index[0].date(), data.index[-1].date()))


###################################### ECI YoY ######################################
with tab2:
  def eci_yoy(start, end):
    data = combine['Employment Cost Index'].dropna().pct_change().loc[start:end]
    update = updates['Employment Cost Index']
    title = 'Employment Cost Index YoY'

    fig = go.Figure()
    fig.add_trace(go.Bar(x=data.index, y=data, name='ECI YoY'))
    fig.add_trace(go.Scatter(x=[data.index[-1]], y=[data[-1]], mode='markers', marker_symbol='star', marker_size=11, name='Release: ' + f"{update:%m/%d/%y}"))
    fig.update_layout(template='seaborn', 
                      title=dict(text=title, font=dict(size=20)),
                      legend = dict(orientation='h',x=1, y=1, xanchor='right', yanchor='bottom'),
                      xaxis=dict(tickvals = data.index, ticktext = data.index.to_period('q').to_series().astype(str), fixedrange=True), 
                      yaxis=dict(tickformat='.1%', fixedrange=True))
    return fig, data

  if 'eci_yoy_fig_period' not in st.session_state: 
    st.session_state['eci_yoy_fig_period'] = 'Past 2 Years'
  fig, data = eci_yoy( dt.today()-timedelta(days=365*float(st.session_state['eci_yoy_fig_period'][5])), dt.today() )
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='eci_yoy_fig_period', horizontal=True, label_visibility='collapsed')
  st.plotly_chart(fig, use_container_width=True)
  # st.slider('Custom Period', value=(data.index[0].date(), data.index[-1].date()))
  # st.markdown('***')


tab1, tab2 = st.tabs(['MoM', 'YoY'])
###################################### AHE MoM ######################################
with tab1:
  def ahe_mom(start, end):
    data = combine['Average Hourly Earnings'].pct_change().dropna().loc[start:end]
    update = updates['Average Hourly Earnings']
    title = 'Average Hourly Earnings MoM'

    fig = go.Figure()
    fig.add_trace(go.Bar(x=data.index, y=data, name='AHE MoM'))
    fig.add_trace(go.Scatter(x=[data.index[-1]], y=[data[-1]], mode='markers', marker_symbol='star', marker_size=11 , name='Release: ' + f"{update:%m/%d/%y}"))
    fig.update_layout(template='seaborn', 
                      # showlegend=True,
                      title=dict(text=title, font=dict(size=20)),
                      legend = dict(orientation='h',x=1, y=1, xanchor='right', yanchor='bottom'),
                      xaxis=dict(fixedrange=True), 
                      yaxis=dict(tickformat='.1%', fixedrange=True))
    return fig, data

  if 'ahe_qoq_fig_period' not in st.session_state: 
    st.session_state['ahe_qoq_fig_period'] = 'Past 2 Years'
  fig, data = ahe_mom( dt.today()-timedelta(days=365*float(st.session_state['ahe_qoq_fig_period'][5])), dt.today() )
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='ahe_qoq_fig_period', horizontal=True, label_visibility='collapsed')
  st.plotly_chart(fig, use_container_width=True)

with tab2:
###################################### AHE YoY ######################################
  def ahe_yoy(start, end):
    data = combine['Average Hourly Earnings'].pct_change(12).dropna().loc[start:end]
    update = updates['Average Hourly Earnings']
    title = 'Average Hourly Earnings YoY'

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data,mode='lines+markers', name='AHE YoY'))
    fig.add_trace(go.Scatter(x=[data.index[-1]], y=[data[-1]], mode='markers', marker_symbol='star', marker_size=11 , name='Release: ' + f"{update:%m/%d/%y}"))
    fig.update_layout(template='seaborn', 
                      title=dict(text=title, font=dict(size=20)),
                      legend=dict(orientation='h',x=1, y=1, xanchor='right', yanchor='bottom'),
                      xaxis=dict(fixedrange=True), 
                      yaxis=dict(tickformat='.1%', fixedrange=True))
    return fig, data

  if 'ahe_yoy_fig_period' not in st.session_state: 
    st.session_state['ahe_yoy_fig_period'] = 'Past 2 Years'
  fig, data = ahe_yoy( dt.today()-timedelta(days=365*float(st.session_state['ahe_yoy_fig_period'][5])), dt.today() )
  st.radio('Display Period', ['Past 1 Year', 'Past 2 Years', 'Past 3 Years', 'Past 5 Years'], key='ahe_yoy_fig_period', horizontal=True, label_visibility='collapsed')
  st.plotly_chart(fig, use_container_width=True)

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

import yfinance as yf
import requests
from matplotlib import pyplot as plt
plt.style.use('ggplot')


from matplotlib import dates as mdates # DateFormatter
from matplotlib import ticker as mtick # PercentFormatter, StrMethodFormatter

from io import StringIO

import selenium
from selenium import webdriver

st.write('hi')

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')  # Run in headless mode (no browser window)
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)

tickers = ['AMAT','NVDA']

# Get market cap / trailing PE / foward PE from Yahoo Finance
combine = pd.DataFrame()
combine_historical_PE = pd.DataFrame()

for tick in tickers:
    url = 'https://finance.yahoo.com/quote/' + tick + '/key-statistics'

    # Get yahoo financial statistics data
    driver.get(url)
    html = driver.page_source
    tables = pd.read_html(StringIO(html))

    # get current metrics table
    single = tables[0]
    single.set_index(single.columns[0], inplace=True)
    single.index.name=None

    single_metrics = single.iloc[[0, 2, 3], 0]
    single_metrics.name = tick
    combine = pd.concat([combine, single_metrics], axis=1)

    # get past five year PE
    single.rename(columns = {single.columns[0]:date.today()+pd.offsets.MonthEnd(3)},inplace=True)
    single.columns = pd.to_datetime(single.columns)

    single_ttm_pe_hist = single.loc['Trailing P/E'].astype(float)
    single_ttm_pe_hist.name = tick + ' Trailing P/E'
    single_fwd_pe_hist = single.loc['Forward P/E'].astype(float)
    single_fwd_pe_hist.name = tick + ' Forward P/E'
    combine_historical_PE = pd.concat([combine_historical_PE, single_ttm_pe_hist, single_fwd_pe_hist], axis=1)

# combine.columns = ['Market Cap', 'Trailing P/E', 'Forward P/E']

cap = combine

st.dataframe(cap)

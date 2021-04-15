import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from indicators import MACD, BBANDS
from functions import * 
import matplotlib.pyplot as plt
import altair as alt
plt.style.use("default")
st.set_option('deprecation.showPyplotGlobalUse', False)


st.write("""
   # Trading strategy backtester
   ### This strategy defines entry point with MACD and exit with B. Bands
""")
st.sidebar.write("Select asset to backtest")
ticker = st.sidebar.text_input("Enter ticker here", "USDCAD=X")
start, end = st.sidebar.beta_columns(2)
start = st.sidebar.text_input("Enter start date of backtest", "2000-01-01")
end = st.sidebar.text_input("Enter end date of backtest", "2020-01-01")
freq = st.sidebar.selectbox('Select Frequency', ('1d','1h'))
initial_cap = st.sidebar.text_input("Select initial capital", 1000)
stop_loss = float(st.sidebar.text_input("Enter Stop Loss", 0.1))

st.sidebar.write("""
   ## MACD parameters
""")
a = st.sidebar.slider("MACD EMA 1", 10, 40, 12, 1)
b = st.sidebar.slider("MACD EMA 2", 10, 40, 26, 1)
signal = st.sidebar.slider("MACD Signal line", 0, 40, 9, 1) 

st.sidebar.write("""
    ## Bollinger Bands parameters
""")
std = st.sidebar.slider("Bollinger Bands STD", 0.01, 4.0, 2.0, 0.01)
days = st.sidebar.slider("Bollinger Bands Rolling Mean", 0, 100, 35, 1)

st.sidebar.write("Created by Juan Rossi")
st.sidebar.write("Contact me at jrossi@udesa.edu.ar")


short = st.selectbox('Select Strategy', ('Long-short','Long only'))
if short == "Long only":
    short_allowed = False
else:
    short_allowed = True

data=create_df("USDCAD=X", 20,1,12,26,9,"2010-01-01","2020-01-01", "1d")

if st.button('Perform Backtest'):
    data = create_df(ticker, days, std, a, b, signal, start, end, freq)
    buy_sell = buy_sell_func(data, stop_loss, short_allowed)
    pl = performance(data, buy_sell)
    capital = capital_func(data, pl, float(initial_cap), buy_sell)
    st.write("## Capital evolution plot")
    lista = [pl[2],pl[3]-pl[2]]
    st.line_chart(pd.DataFrame({'Algorithm': capital[0], 'BuynHold':capital[1]}))
    
    st.write("## The algo executed {} trades of which {} were profitable, the win ratio is {}%".format(pl[3], pl[2], round(pl[1]*100,2)))
    pnl_df = pd.DataFrame(lista, columns=["Trades"],index=['Winners','Losers'])
    pnl_df['Index'] = pnl_df.index
    base = alt.Chart(pnl_df).mark_bar().encode(x='Trades',y='Index',color='Index')
    st.altair_chart(base, use_container_width=True)
    
    st.write("## The total return for the period was {}%, vs Buy n' Hold {}%".format(round(capital[2]*100,2), round(capital[3]*100,2)))    
    st.write("Plotting signals generated by the algorithm")
    st.write("- Green lines are long positions and red lines are shorts")
    ohlc = data[['Open', 'High', 'Low', 'Close']]
    ohlc['Date'] = ohlc.index
    ohlc['Buy'] = [abs(i) for i in buy_sell[0]]
    ohlc['Sell'] = [abs(i) for i in buy_sell[1]]         
    if short == "Long-short":
   
        base = alt.Chart(ohlc)
        line = base.mark_line().encode(x='Date', y='Close').interactive()
        buys = base.mark_rule(color='green').encode(x='Date', y='Buy')        
        sells = base.mark_rule(color='red').encode(x='Date', y='Sell')
        st.altair_chart(line+buys+sells, use_container_width=True)
    else:
        base = alt.Chart(ohlc)
        line = base.mark_line().encode(x='Date', y='Close').interactive()
        buys = base.mark_rule(color='green').encode(x='Date', y='Buy')        
        st.altair_chart(line+buys, use_container_width=True)
        


        









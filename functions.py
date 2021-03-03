import yfinance as yf
import numpy as np
import pandas as pd
from indicators import MACD, BBANDS

def create_df(ticker, plot, days, std, a, b, signal, start, end, freq):
    df = yf.download(ticker, start = start, end=end, interval = freq)
    data = pd.DataFrame()
    data['Close'] = df['Close']
    data = BBANDS(df,days,std)
    data['Macd'] = MACD(df, a, b, signal)[0]
    data['Signal_line'] = MACD(df, 12, 26, 9)[1]
    data['EWMA_short'] = df['Close'].ewm(span=20, adjust=False).mean()
    data['EWMA_long'] = df['Close'].ewm(span=40, adjust=False).mean()
        
    return data

def buy_sell_func(data, stop_loss):
    """  
    Esta funcion contiene las reglas que el algoritmo sigue para dar las señales
    Parameters
    ----------
    data : Matriz que contiene los precios de cierre y los parametros del indicador
    take_profit : Float con el movimiento porcbuyentual para tomar ganancia
    stop_loss : Float con el movimiento porcentual para cerrar operacion negativa

    Returns
    -------
    listas: buy_sell[0] son las compras y buy_sell[1] son las ventas en el momento que se produjeron.        
    """
    sig_buy_price = []
    buy_price = []
    sell_price = []
    sig_sell_price = []
    indexes = data.index.tolist()
    index=[indexes[0]]
    buy = 0
    
    for i in range(len(data)):
        if buy == 1:      
            if data['Close'][i] > data['Upper'][i]:                                                              
                sig_buy_price.append(np.nan)
                sig_sell_price.append(data['Close'][i])
                sell_price.append(data['Close'][i])    
                buy = 0
                index.append(indexes[i])                                        
            elif data['Close'][i] < (buy_price[-1]*(1-stop_loss)):
                sig_buy_price.append(np.nan)
                sig_sell_price.append(data['Close'][i])
                sell_price.append(data['Close'][i])            
                buy = 0 
                index.append(indexes[i])
            else:
                sig_buy_price.append(np.nan)
                sig_sell_price.append(np.nan)
                buy = 1
        else:                    
            if data['Macd'][i] > data['Signal_line'][i] and data['Macd'][i-1] < data['Signal_line'][i-1] \
               and data['EWMA_short'][i] > data['EWMA_long'][i]:
                sig_buy_price.append(data['Close'][i])
                buy_price.append(data['Close'][i])
                sig_sell_price.append(np.nan)            
                buy = 1                
            else:
                sig_buy_price.append(np.nan)
                sig_sell_price.append(np.nan)
                buy = 0
                
                                                                                                         
    return [sig_buy_price, sig_sell_price, buy_price, sell_price, index]

"""PERFORMANCE ANALISYS"""
def performance(data, bs_data):
    """
    Esta funcion calcula el "pl" que es la ganancia y perdida por cada transaccion,
    el "pl_returns" que es la ganancia porcentual de cada operacion.
    Tambien calcula el win ratio, la cantidad de operaciones exitosas sobre el total
    la media y la varianza de los retornos
    """        
    pl = [] #Calculo los retornos diarios
    buy = 0    
    prof = 0
    total = 0
    for i in range(len(data)):
        if buy==0:
            if bs_data[0][i] > 0:
                buy=1
                index_open=i
                pl.append(1)                  
            else:
                pl.append(1)
                
        elif buy==1:
            if bs_data[1][i] > 0:
                pl.append(data['Close'][i]/data['Close'][i-1])
                buy=0
                total+=1
                index_close = i 
                if data['Close'][i]>data['Close'][index_open]:
                    prof+=1
                      
                elif data['Close'][i]<data['Close'][index_open]:
                    total += 1
            else:
                pl.append(data['Close'][i]/data['Close'][i-1])
                
                
    if total > 0:                 
        win_ratio = prof/total    
    else:
        win_ratio = 0
    return [pl, win_ratio, prof, total]

def capital_func(data,pl_data,initial_cap, plot, buy_sell):   
    """    
    Parameters
    ----------
    initial_cap : El input es el capital inicial con el cual operara el algo
    
    Returns
    -------
    cap : Evolucion del capital a medida que el algo tradea 
    tot_return : Retorno desde que el algo comenzo a operar
    """    
    cap = np.cumprod(pl_data[0])*1000
    
    stock_performance = data['Close']/data['Close'].shift(1)
    stock_reference = np.cumprod(stock_performance)*1000
    stock_reference[0]=initial_cap
    stock_performance = stock_reference[-1]/stock_reference[0]-1        
           
    tot_return = (cap[-1]-initial_cap)/initial_cap  
    
    return cap, stock_reference, tot_return, stock_performance

import yfinance as yf
import numpy as np
import pandas as pd
from indicators import MACD, BBANDS


def create_df(ticker, days, std, a, b, signal, start, end, freq):
    df = yf.download(ticker, start = start, end=end, interval = freq)
    data = pd.DataFrame()
    data['Close'] = df['Close']
    data = BBANDS(df,days,std)
    data['Macd'] = MACD(df, a, b, signal)[0]
    data['Signal_line'] = MACD(df, 12, 26, 9)[1]
    data['EWMA_short'] = df['Close'].ewm(span=20, adjust=False).mean()
    data['EWMA_long'] = df['Close'].ewm(span=40, adjust=False).mean()
        
    return data

def buy_sell_func(data, stop_loss=0.1, short_allowed=True):
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
    long_positions = []
    short_positions = []
    last_entry = 0
    long = 0
    short = 0 
    
    for i in range(len(data)):
        if long == 1:  #Long position exit conditions   
            short_positions.append(np.nan)
            if data['Close'][i] > data['Upper'][i]:   #Exit with upper bband                                                           
                long_positions.append(-data['Close'][i])
                long = 0
                last_entry = 0                                        
            elif data['Close'][i] < (last_entry*(1-stop_loss)): #Stop loss triger 
                long_positions.append(-data['Close'][i])       
                long = 0 
                last_entry = 0 
            else:                                           #Holding the stock
                long_positions.append(np.nan)
        
        elif short == 1: #Short position exit conditions
            long_positions.append(np.nan)
            if data['Close'][i] < data['Lower'][i]:   #Exit with lower bband                                                           
                short_positions.append(-data['Close'][i])
                short = 0
                last_entry = 0   
                                 
            elif data['Close'][i] > (last_entry*(1-stop_loss)): #Stop loss triger 
                short_positions.append(-data['Close'][i])        
                short = 0
                last_entry = 0 
            else:                                           #Holding the stock
                short_positions.append(np.nan) 
                
        elif short == 0 and long ==0: #Short position entry conditions                 
            if data['Macd'][i] < data['Signal_line'][i] and data['Macd'][i-1] > data['Signal_line'][i-1] \
               and data['EWMA_short'][i] < data['EWMA_long'][i] and short_allowed==True: #Short position entry conditions
                long_positions.append(np.nan)
                short_positions.append(data['Close'][i])                
                short = 1   
                last_entry = data['Close'][i] 
                    
            elif data['Macd'][i] > data['Signal_line'][i] and data['Macd'][i-1] < data['Signal_line'][i-1] \
               and data['EWMA_short'][i] > data['EWMA_long'][i]: #Long position entry conditions
                long_positions.append(data['Close'][i])
                short_positions.append(np.nan)            
                long = 1
                last_entry = data['Close'][i]             
            else:
                long_positions.append(np.nan)
                short_positions.append(np.nan)
                
    df = pd.DataFrame({'index':data.index,'Longs':long_positions,'Shorts':short_positions})
                                                                                                 
    return [long_positions, short_positions, df]

"""PERFORMANCE ANALISYS"""
def performance(data, bs_data):
    """
    Esta funcion calcula el "pl" que es la ganancia y perdida por cada transaccion,
    el "pl_returns" que es la ganancia porcentual de cada operacion.
    Tambien calcula el win ratio, la cantidad de operaciones exitosas sobre el total
    la media y la varianza de los retornos
    """        
    pl = [] #Calculo los retornos diarios
    long = 0
    short = 0
    prof = 0
    total = 0
    for i in range(len(data)):
        if long == 0 and short == 0:
            if bs_data[0][i] > 0:
                long=1
                index_open=i
                pl.append(1)
            elif bs_data[1][i] > 0:
                short=1
                index_open=i
                pl.append(1)                      
            else:
                pl.append(1)
                
        elif long==1:
            if bs_data[0][i] < 0:
                pl.append(data['Close'][i]/data['Close'][i-1])
                long=0
                total += 1
                if data['Close'][i]>data['Close'][index_open]:
                    prof += 1
            else:
                pl.append(data['Close'][i]/data['Close'][i-1])
                
        elif short==1:
            if bs_data[1][i] < 0:
                pl.append(data['Close'][i-1]/data['Close'][i])
                short=0
                total += 1
                if data['Close'][i]<data['Close'][index_open]:
                    prof += 1

            else:
                pl.append(data['Close'][i-1]/data['Close'][i])
                                
    if total > 0:                 
        win_ratio = prof/total    
    else:
        win_ratio = 0
    return [pl, win_ratio, prof, total]

def capital_func(data,pl_data,initial_cap, buy_sell):   
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
    stock_reference[0] = initial_cap
    stock_performance = stock_reference[-1]/stock_reference[0]-1        
           
    tot_return = cap[-1]/initial_cap-1
    
    return cap, stock_reference, tot_return, stock_performance
"""
data=create_df("AAPL", 20,1,12,26,9,"2010-01-01","2020-01-01", "1d")
bs_data=buy_sell_func(data,0.1,False)
pl_data=performance(data,bs_data)
cap=capital_func(data,pl_data,1000, bs_data)
"""
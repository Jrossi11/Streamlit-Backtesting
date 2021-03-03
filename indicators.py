#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 09:59:52 2020

@author: juanrossi
"""
import numpy as np
import statsmodels.api as sm

def MACD(DF,a, b, c):
    df = DF.copy()
    df['Ema1'] = df['Close'].ewm(span=a, adjust=False).mean()
    df['Ema2'] = df['Close'].ewm(span=b, adjust=False).mean()
    df['MACD'] = df['Ema1']-df['Ema2']
    df['Signal_line'] = df['MACD'].ewm(span=c, adjust=False).mean()
    return (df['MACD'], df['Signal_line'])

def BBANDS(DF,lenght, std):
    df = DF.copy()
    df['Sma'] = df['Close'].rolling(window=lenght).mean()
    df['Upper'] = df['Close'].rolling(window=lenght).mean()+df['Close'].rolling(window=lenght).std()*std
    df['Lower'] = df['Close'].rolling(window=lenght).mean()-df['Close'].rolling(window=lenght).std()*std
    return df

def slope(ser, n):
    "function to calculate the slope of n consecutive points on a plot"
    slopes = [i*0 for i in range(n-1)]
    for i in range(n,len(ser)+1):
        y = ser[i-n:i]
        x = np.array(range(n))
        y_scaled = (y - y.min())/(y.max() - y.min())
        x_scaled = (x - x.min())/(x.max() - x.min())
        x_scaled = sm.add_constant(x_scaled)
        model = sm.OLS(y_scaled,x_scaled)
        results = model.fit()
        slopes.append(results.params[-1])
    slope_angle = (np.rad2deg(np.arctan(np.array(slopes))))
    return np.array(slope_angle)

def ATR(DF, n):
    df = DF.copy()
    df['H-L'] = abs(df['High']-df['Low'])
    df['H-PC'] = abs(df['High']-df['Close'].shift(1))
    df['L-PC'] = abs(df['Low']-df['Close'].shift(1))
    df['TR'] = df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    df2 = df.drop(['H-L','H-PC', 'L-PC'],axis=1)
    return df2

def ADX(DF,n):
    df2 = DF.copy()
    df2['TR'] = ATR(df2,n)['TR']
    df2['DMplus']=np.where((df2['High']-df2['High'].shift(1))>(df2['Low'].shift(1)-df2['Low']),df2['High']-df2['High'].shift(1),0)
    df2['DMplus']=np.where(df2['DMplus']<0,0,df2['DMplus'])
    df2['DMinus']=np.where((df2['Low'].shift(1)-df2['Low'])>(df2['High']-df2['High'].shift(1)),df2['Low'].shift(1)-df2['Low'],0)
    df2['DMinus']=np.where(df2['DMinus']<0,0,df2['DMinus'])
    TRn = []
    DMplusN = []
    DMinusN = []
    TR = df2['TR'].tolist()
    DMplus = df2['DMplus'].tolist()
    DMinus = df2['DMinus'].tolist()
    for i in range(len(df2)):
        if i < n:
            TRn.append(np.NaN)
            DMplusN.append(np.NaN)
            DMinusN.append(np.NaN)
        elif i == n:
            TRn.append(df2['TR'].rolling(n).sum().tolist()[n])
            DMplusN.append(df2['DMplus'].rolling(n).sum().tolist()[n])
            DMinusN.append(df2['DMinus'].rolling(n).sum().tolist()[n])
        elif i > n:
            TRn.append(TRn[i-1]-(TRn[i-1]/14) + TR[i])
            DMplusN.append(DMplusN[i-1]-(DMplusN[i-1]/14)+DMplus[i])
            DMinusN.append(DMinusN[i-1]-(DMinusN[i-1]/14)+DMinus[i])
    df2['TRn']=np.array(TRn)
    df2['DMplusN']=np.array(DMplusN)
    df2['DMinusN']=np.array(DMinusN)
    df2['DIplusN']=100*(df2['DMplusN']/df2['TRn'])
    df2['DIminusN']=100*(df2['DMinusN']/df2['TRn'])
    df2['DIdiff']=abs(df2['DIplusN']-df2['DIminusN'])
    df2['DIsum']=df2['DIplusN']+df2['DIminusN']
    df2['DX']=100*(df2['DIdiff']/df2['DIsum'])
    ADX = []
    DX = df2['DX'].tolist()
    for j in range(len(df2)):
        if j < 2*n-1:
            ADX.append(np.NaN)
        elif j == 2*n-1:
            ADX.append(df2['DX'][j-n+1:j+1].mean())
        elif j > 2*n-1:
            ADX.append(((n-1)*ADX[j-1] + DX[j]) /n)
    df2['ADX'] = np.array(ADX)
    return df2['ADX']
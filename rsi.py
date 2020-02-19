import numpy as np
import pandas as pd
import FinanceDataReader as fdr
import datetime
import pandas_datareader as web

start = datetime.datetime(2019,10,1)
end = datetime.datetime(2019,11,6)
stock_ds = web.DataReader('035250.KS','yahoo',start,end)
date_index = stock_ds.index.astype('str')

def calcRSI(df,period):
    U = np.where(df.diff(1)['Close']>0,df.diff(1)['Close'],0)
    D = np.where(df.diff(1)['Close']<0, df.diff(1)['Close']*(-1),0)
    AU = pd.DataFrame(U,index=date_index).rolling(window=period).mean()
    AD = pd.DataFrame(D,index=date_index).rolling(window=period).mean()
    RSI = AU/(AU+AD)

    return RSI*100

def calMACD(df,short=12, long=26):
    df['MACD'] = df['Close'].ewm(span=short,min_periods=short-1,adjust=False).mean()-df['Close'].ewm(span=long,min_periods=long-1,adjust=False).mean()
    return df

stock_ds.insert(len(stock_ds.columns),"RSI",calcRSI(stock_ds,14))
#stock_ds.insert(len(stock_ds.columns),"RSI signal", stock_ds['RSI'].rolling(window=9).mean())
calMACD(stock_ds)
print(stock_ds)

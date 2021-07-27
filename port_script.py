## Connect to External Sources
import requests
from bs4 import BeautifulSoup
import yfinance as yf

## Interactive Visualization
import plotly.figure_factory as ff
import plotly.express as px
import plotly.graph_objects as go

## Data Manipulation
import pandas as pd
import numpy as np
from scipy.optimize import minimize
import datetime

## Web Framework
import streamlit as st
import base64

def download_link(object_to_download, download_filename, download_link_text):

    ## Create Download Link
    if isinstance(object_to_download,pd.DataFrame):
        object_to_download = object_to_download.to_csv(index=False)

    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(object_to_download.encode()).decode()

    return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{download_link_text}</a>'

def negative_red(val):
    
    ## Red-Green Style for Dataframe
    color = 'red' if val < 0 else 'green'
    return 'color: %s' % color

@st.cache
def get_ticker():
    
    ## Connect to Wikipedia
    url ='https://id.wikipedia.org/wiki/Daftar_perusahaan_yang_tercatat_di_Bursa_Efek_Indonesia'
    page = requests.get(url)
    
    ## Parse Page Content
    soup = BeautifulSoup(page.content, 'html.parser')
    tags = soup.find_all('tr')
    
    ## Collect Ticker Information
    ticker_list = []
    for i in range(1,len(tags)):
        row = tags[i]
        text = row.text.split('\n')
        idx = text[1].replace('IDX: ', '')
        date = text[3].split('\xa0')[0]
        value = [idx, text[2], date]
        ticker_list.append(value)
            
    ## Change to DataFrame and Return
    tickers = pd.DataFrame(ticker_list, columns=['Kode', 'Nama Perusahaan', 'Tanggal Pencatatan'])
    return tickers

@st.cache(allow_output_mutation=True)
def get_data(tickers, start_date):
    
    ## Download Datasets
    adj_ticker = [x + '.JK' for x in tickers]
    prices = yf.download(adj_ticker, start_date)['Adj Close']
    data_returns = prices.pct_change().dropna()
    data_returns.columns = [x.replace('.JK', '') for x in data_returns.columns]
    return data_returns

@st.cache
def core_plot_data(returns, weights, conf  = 95):
        
    if 'Portfolio' in returns.columns:
        returns = returns.drop(columns=['Portfolio'])
    
    ## Get Tickers and Date Range First
    tickers = [x for x in returns.columns]
    
    ## Correlation of Individual Asset
    ind_asset_corr = round(returns.corr(), 3).values.tolist()
    
    ## Calculate Cumulative Returns for Portfolio and Individually
    returns['Portfolio'] = returns.mul(weights, axis=1).sum(axis=1)
    ret_cum = round((returns + 1).cumprod() - 1, 3)
    
    ## Reorganise Dataframe
    new_ret = ret_cum.unstack().reset_index().set_index('Date')
    new_ret.columns = ['Perusahaan', 'Returns']
    new_ret = new_ret.pivot(columns = 'Perusahaan', values = 'Returns')
    new_ret = new_ret[['Portfolio'] + tickers]
    
    ## Calculate Historical Drawdown
    running_max = np.maximum.accumulate(new_ret['Portfolio'].add(1))
    drawdown = new_ret['Portfolio'].add(1).div(running_max).sub(1)
    max_drawdown = np.minimum.accumulate(drawdown)
    hist_draw = round(pd.DataFrame([drawdown, max_drawdown]).transpose(), 3)
    hist_draw.columns = ['Drawdown', 'Max Drawdown']
    hist_draw = hist_draw.reset_index()
    
    ## Calculate the risk metrics
    var = round(np.percentile(returns['Portfolio'], 100 - conf), 3)
    cvar = round(returns['Portfolio'][returns['Portfolio'] <= var].mean(), 3)
    
    ## Recap Key Value
    summary = {}
    summary['Returns Saat Ini'] = round(returns['Portfolio'][-1]*100, 3)
    summary['Returns Annual'] = round((((1+np.mean(returns['Portfolio']))**252)-1)*100, 3)
    summary['Volatilitas Annual'] = round(np.std(returns['Portfolio']) * np.sqrt(252)*100, 3)
    summary['Sharpe Ratio'] = round(summary['Returns Annual'] / summary['Volatilitas Annual'], 3)
    summary['VaR'] = round(var*100, 3)
    summary['CVaR'] = round(cvar*100, 3)
    summary['Max Drawdown'] = round(max_drawdown[-1]*100, 3)
    
    return [summary, new_ret, returns, hist_draw, ind_asset_corr, tickers]

@st.cache
def asset_corr_plot(asset_corr, tickers):
    
    ## Create Heatmap of Tickers Correlation
    corr_heatmap = ff.create_annotated_heatmap(z = asset_corr, x = tickers, y = tickers,
                                  colorscale = "YlGnBu", showscale = True)
    corr_heatmap = corr_heatmap.update_layout(title = '<b>Korelasi Antar Saham dalam Portfolio</b>', width=550, height=550)
    
    return corr_heatmap

@st.cache
def asset_cumulative_return(new_ret, ticker):
    
    ## Create Faceted Area Chart for Cumulative Returns
    start = new_ret.index[0].strftime("%d %b %Y")
    end = new_ret.index[-1].strftime("%d %b %Y")
    new_ret = new_ret[ticker]
    facet_plot = px.area(new_ret, facet_col="Perusahaan", facet_col_wrap=2)
    facet_plot = facet_plot.update_layout(title = '<b>Nilai Returns Kumulatif Dari {} hingga {}</b>'.format(start, end))
    facet_plot = facet_plot.update_layout(xaxis=dict(rangeslider=dict(visible=True),type="date"))
    
    return facet_plot

@st.cache
def rolling_volatility(returns, interval):

    ## Create Rolling Volatility Plot
    rolling_vol = returns['Portfolio'].rolling(interval).std().dropna() * np.sqrt(252)
    rol_vol_plot = px.line(rolling_vol, labels={"Date": "Tanggal", "value": "Volatilitas"},
                 title="<b>Rolling Volatilitas Annual dengan Rentang Waktu {} Hari</b>".format(interval))
    rol_vol_plot = rol_vol_plot.update_layout(showlegend = False)
    rol_vol_plot = rol_vol_plot.update_layout(xaxis=dict(rangeselector=dict(buttons=list([
                dict(count=1,
                     label="1 Bulan",
                     step="month",
                     stepmode="backward"),
                dict(count=6,
                     label="6 Bulan",
                     step="month",
                     stepmode="backward"),
                dict(count=1,
                     label="Year to Date",
                     step="year",
                     stepmode="todate"),
                dict(count=1,
                     label="1 Tahun",
                     step="year",
                     stepmode="backward"),
                dict(label="Semua",
                    step="all")])),
            rangeslider=dict(visible=True),type="date"))
    
    return rol_vol_plot

@st.cache
def drawdown_vis(hist_draw):
    
    ## Visualize Drawdown
    drawdown_plot = px.area(x = hist_draw['Date'], y = hist_draw['Max Drawdown'],
              title = "<b>Data Historical Drawdown</b>", labels = {"x": "Tanggal", "y": "Max Drawdown"})
    drawdown_plot = drawdown_plot.add_trace(go.Scatter(x = hist_draw['Date'], y = hist_draw['Drawdown'],
                            fill = 'tozeroy', name = 'Drawdown', mode = 'none'))
    
    return drawdown_plot

@st.cache
def var_cvar(returns, conf = 95):
    
    ## Calculate the risk metrics
    var = round(np.percentile(returns['Portfolio'], 100 - conf), 3)
    cvar = round(returns['Portfolio'][returns['Portfolio'] <= var].mean(), 3)

    ## Visualize Histogram
    hist_plot = px.histogram(returns['Portfolio'], labels={"value": "Returns", "count": "Frekuensi"},
                      title="<b>Histogram Nilai Return Portfolio dengan Level Kepercayaan {}%</b>".format(conf))
    hist_plot = hist_plot.add_vline(x = var, line_dash="dot", line_color = 'green',
              annotation_text=" VaR {}".format(var), 
              annotation_position="top right",
              annotation_font_size=12,
              annotation_font_color="green"
             )
    hist_plot = hist_plot.add_vline(x = cvar, line_dash="dot", line_color = 'red',
              annotation_text="CVaR {} ".format(cvar), 
              annotation_position="top left",
              annotation_font_size=12,
              annotation_font_color="red"
             )
    hist_plot = hist_plot.update_layout(showlegend = False)
    
    return hist_plot, (var, cvar)

def get_market_cap(tickers):
    
    ## Download Datasets
    start_date = datetime.date.today() - datetime.timedelta(7)
    adj_ticker = [x + '.JK' for x in tickers]
    prices = yf.download(adj_ticker, start_date)[['Adj Close', 'Volume']]
    
    recent_market = (prices['Adj Close']*prices['Volume']).iloc[-1]
    market_weight = recent_market.div(sum(recent_market)).tolist()
    return market_weight

def portfolio_performance(weights, my_data, risk_free = 0, target = 'all'):
    
    ## Evaluate Portfolio Performance
    port_return = my_data.mul(weights, axis=1).sum(axis=1)
    annual_return = (((1+np.mean(port_return))**252)-1)*100
    annual_vol = np.std(port_return) * np.sqrt(252)*100
    sharpe_ratio = (annual_return - risk_free)/annual_vol
    evaluasi = {'Return Annual':annual_return, 'Volatilitas Annual':annual_vol, 'Sharpe Ratio':sharpe_ratio}
    
    ## Return Based on Target
    if target == 'all':
        return evaluasi
    if target == 'max_sharpe_ratio':
        return -sharpe_ratio
    if target == 'min_volatility':
        return annual_vol
    
def optimize(my_data, target, risk_free_rate = 0):
    
    ## Set Optimum Weights for Desired Target
    num_assets = len(my_data.columns)
    args = (my_data, risk_free_rate, target)
    initial = num_assets*[1./num_assets,]
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bound = (0.0,1.0)
    bounds = tuple(bound for asset in range(num_assets))
    result = minimize(portfolio_performance, x0 = initial, args = args, bounds=bounds, constraints=constraints)
    return result

def efficient_return(my_data, expectation, risk_free_rate = 0):

    ## Retrieve Returns as Constraint
    def portfolio_return(weights):
        return portfolio_performance(weights, my_data)['Return Annual']

    ## Optimum Weights Based on Expected Risk
    target = 'min_volatility'
    num_assets = len(my_data.columns)
    args = (my_data, risk_free_rate, target)
    initial = num_assets*[1./num_assets,]
    constraints = ({'type': 'eq', 'fun': lambda x: portfolio_return(x) - expectation},
                   {'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0,1) for asset in range(num_assets))
    result = minimize(portfolio_performance, x0 = initial, args=args, bounds=bounds, constraints=constraints)
    return result

def efficient_frontier(my_data, expectation_range, risk_free_rate = 0):
    efficients = []
    for exp in expectation_range:
        efficients.append(efficient_return(my_data, exp, risk_free_rate))
    return efficients

@st.cache
def markowitz_portfolio(my_data, max_exp, rf = 0):

    ## Individual Assets Performance
    ind_stocks = {}
    for each in my_data.columns:
        stock_return = my_data[each]
        annual_stock_return = round((((1+np.mean(stock_return))**252)-1)*100, 3)
        annual_stock_vol = round(np.std(stock_return) * np.sqrt(252)*100, 3)
        evaluasi_stock = {'Return Annual':annual_stock_return, 'Volatilitas Annual':annual_stock_vol}
        ind_stocks[each] = evaluasi_stock
    ticker = [x for x in my_data.columns]

    ## Equal Weight Portfolio
    num_assets = len(my_data.columns)
    ew_weights = num_assets*[1./num_assets,]
    ew = portfolio_performance(ew_weights, my_data, rf)
    for key, value in ew.items():
        ew[key] = round(value, 3)
    for i in range(0, num_assets):
        ew[ticker[i]] = ew_weights[i]
    
    ## Market Cap Weight Portfolio
    mcap_weights = get_market_cap(ticker)
    mcap = portfolio_performance(mcap_weights, my_data, rf)
    for key, value in mcap.items():
        mcap[key] = round(value, 3)
    for i in range(0, num_assets):
        mcap[ticker[i]] = mcap_weights[i]
        
    ## MSR Portfolio
    msr_obj = optimize(my_data = my_data, target = 'max_sharpe_ratio', risk_free_rate = rf)
    msr = portfolio_performance(msr_obj['x'], my_data, rf)
    for key, value in msr.items():
        msr[key] = round(value, 3)
    msr_weights = [round(x, 3) for x in msr_obj['x']]
    for i in range(0, num_assets):
        msr[ticker[i]] = msr_weights[i]
    
    ## GMV Portfolio
    gmv_obj = optimize(my_data = my_data, target = 'min_volatility', risk_free_rate = rf)
    gmv = portfolio_performance(gmv_obj['x'], my_data, rf)
    for key, value in gmv.items():
        gmv[key] = round(value, 3)
    gmv_weights = [round(x, 3) for x in gmv_obj['x']]
    for i in range(0, num_assets):
        gmv[ticker[i]] = gmv_weights[i]
    
    ## Efficient Frontier Portfolio
    min_exp = gmv['Return Annual']
    max_exp = max_exp + 5
    range_exp = np.linspace(min_exp, max_exp, 50)
    ef = efficient_frontier(my_data, range_exp, rf)
    
    ## Organize Portfolio Results
    key_port = round(pd.DataFrame([ew, mcap, msr, gmv]), 3)
    key_port.index = ['Equal Weight', 'Market Cap', 'Max Sharpe Ratio', 'Global Min Volatility']
    
    ef_port = []
    for i in range(0,len(ef)):
        ef_value = []
        ef_weight = ef[i]['x'].tolist()
        ef_result = [x for x in portfolio_performance(ef_weight, my_data, rf).values()]
        ef_value = ef_result + ef_weight
        ef_port.append(ef_value)
    col_name = ['Return Annual', 'Volatilitas Annual', 'Sharpe Ratio'] + [x for x in my_data.columns]
    ef_port = round(pd.DataFrame(ef_port, columns=col_name), 3)
    
    return [ind_stocks, key_port, ef_port]

def visualize_ef(result):
    
    ## Breakdown Result to Plots
    layer_one = result[0]
    c1 = [x for x in layer_one]
    x1 = [layer_one[x]['Volatilitas Annual'] for x in layer_one]
    y1 = [layer_one[x]['Return Annual'] for x in layer_one]

    layer_two = result[1]
    c2 = ['EW', 'MCap', 'MSR', 'GMV']
    x2 = layer_two['Volatilitas Annual']
    y2 = layer_two['Return Annual']

    layer_three = result[2]
    x3 = layer_three['Volatilitas Annual']
    y3 = layer_three['Return Annual']

    ## Overlay Chart: Individual Stocks, Notable Portfolio, Efficient Frontier
    fig = go.Figure()
    fig = fig.add_trace(
        go.Scatter(mode='markers+text', x = x1, y = y1, text = c1, name = 'Saham Individual',
               marker_symbol = 'x', textposition='bottom right', textfont=dict(color='#E58606'),
               marker=dict(color = 'LightSkyBlue', size = 20, line = dict(color = 'MediumPurple', width = 2))))
    fig = fig.add_trace(
        go.Scatter(mode='markers+text', x = x2, y = y2, text = c2, name = 'Strategi Portfolio Umum',
               marker_symbol = 'star', textposition='bottom right', textfont=dict(color='#E58606'),
               marker=dict(color = 'red', size = 15, line = dict(color = 'MediumPurple', width = 2))))
    fig = fig.add_trace(
        go.Scatter(mode='lines+markers', x = x3, y = y3, name = 'Efficient Frontier',
              line=dict(color='black', dash='dot')))
    
    ## Finalize Plot
    fig = fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig = fig.update_layout(
        title = "<b>Optimisasi Komposisi Portfolio Berdasarkan Nilai Return dan Volatilitas</b>",
        xaxis_title="<b>Volatilitas Annual</b>",
        yaxis_title="<b>Return Annual</b>")
    
    return fig

@st.cache
def cumulative_performance(my_data, port_strategy, cust_weight):
    
    ## Cumulative Returns DataFrame
    cumulative_return = []
    cum_return = my_data.mul(cust_weight, axis=1).sum(axis=1)
    ret_cum = round((cum_return + 1).cumprod() - 1, 3)
    cumulative_return.append(ret_cum)
    for i in range(0,4):
        weight = port_strategy.iloc[i,3:].tolist()
        cum_return = my_data.mul(weight, axis=1).sum(axis=1)
        ret_cum = round((cum_return + 1).cumprod() - 1, 3)
        cumulative_return.append(ret_cum)
        
    cum_df = pd.DataFrame(cumulative_return).transpose()
    cum_df.columns = ['Custom', 'EW', 'MCap', 'MSR', 'GMV']
    
    ## Cumulative Returns Plot
    cum_fig = px.line(cum_df, title = '<b>Perbandingan Return Kumulatif Dari Beberapa Strategi Portfolio</b>',
              labels = {'value':'Return Kumulatif', 'variable':'Strategi Portfolio'})
    cum_fig = cum_fig.update_layout(xaxis=dict(rangeselector=dict(buttons=list([
                dict(count=1,
                     label="1 Bulan",
                     step="month",
                     stepmode="backward"),
                dict(count=6,
                     label="6 Bulan",
                     step="month",
                     stepmode="backward"),
                dict(count=1,
                     label="Year to Date",
                     step="year",
                     stepmode="todate"),
                dict(count=1,
                     label="1 Tahun",
                     step="year",
                     stepmode="backward"),
                dict(label="Semua",
                    step="all")])),
            rangeslider=dict(visible=True),type="date"))
        
    return cum_df, cum_fig
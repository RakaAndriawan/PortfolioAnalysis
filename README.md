# Analysis and Simulation of Portfolio Analysis
Powerful analysis tools to help us understand and evaluate our portfolio using streamlit framework<br>
It is easy to find historical performance and analysis of individual assets, whether it's a built-in feature of the trading app or information from other websites. However, we do not know how that individual assets might affect our portfolio performance in general. Thus, this app is created to simulate and help determine whether we build our portfolio well enough and carefully deciding what is the best course of action.<br>

## Data Source
Currently, this app only listed Indonesian stocks as assets. The stocks that are listed can be seen here [Daftar perusahaan yang tercatat di Bursa Efek Indonesia](https://id.wikipedia.org/wiki/Daftar_perusahaan_yang_tercatat_di_Bursa_Efek_Indonesia). As for market data, we used historical data from yahoo finance using python package called [yfinance](https://pypi.org/project/yfinance/).<br>

## Features
This project is made of two sections:
1. Portfolio Performance: In this page, we're trying to assess assess how our portfolio perform based on historical data. We're trying to provide key value to be considered such as sharpe ratio and several risk metrics. We also provide a correlation plot in order to give a sense of the relationship between individual stocks.
2. Backtesting Portfolio: This is where the cooking takes place. User are encouraged to pick the best possible compostion of portfolio given their expected result and risk tolerance. Some of the methods available in app are efficient portfolios, equal weight portfolio and market cap weighted portfolio.

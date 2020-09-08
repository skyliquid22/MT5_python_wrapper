# MT5_python_wrapper
A python algorithmic trading template for MetaTrader5.
 
## Features
- Push and Pull sockets are handled through MT5 python lib.
- DB connection for orders and historical market data.
- A full wrapper class for all MT5 methods.
- Ability to allow PUB/SUB through MT5's Expert Advisors to stream live market data using ØMQ.
- A base strategy class to build upon.
- Run multiple Traders for each strategy based on the number of symbols the strategy trades. 

## TODO
- Add Benchmark Strategies
- Add a market watch method that finds the best symbols for a given strategy based on fundamental analysis.
- Add bet sizing method that allocates a strategy's balance to traders based on some metrics (Profit/Loss, 24h volume, market spread, price volatility, backtests...etc)
- Create a portfolio optimization method that identifies best parameters for the Trader class (max # traders, max volume, max open trades)
- Calculate technical analysis metrics from the live market stream.
- Utilize asyncio lib with Threading lib to minimize DB and MT5 network runtime.
- Create a dashboard to view each strategy metrics. (Profit/Loss, # of open trades, ...etc.)
-- Since the MT5 terminal is the server and the strategies will be the client, the dashboard will act as a stand-alone class that will fetch strategies performance from the MT5 terminal. Strategies/Traders can be identified from the magic number or order comment.


## Licence
This project is licensed under an MIT license.

from src.connector import Connector


class BaseStrategy(object):

    def __init__(self, name="Base Strategy", symbols=None, broker_tz_offset=0, verbose=True):
        self.name = name
        self.symbols = symbols
        self.broker_tz_offset = broker_tz_offset
        self.verbose = verbose

        self.conn = Connector()

        # Strategy's ON/OFF switch
        self.isON = True

    def run(self):
        pass

    def stop(self):
        self.isON = False


class CoinFlipStrategy(BaseStrategy):

    def __init__(self, name="CoinFlip_Traders", symbols=None, broker_tz_offset=0, verbose=True, max_trades=1,
                 delay=0.1):
        super().__init__(name, symbols, broker_tz_offset, verbose)

        self.traders = []
        self.market_open = True
        self.max_trades = max_trades
        self.delay = delay

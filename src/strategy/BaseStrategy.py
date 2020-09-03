"""
TODO: Use expert advisor to stream market data.
"""

from src.connector import Connector
from time import sleep
from threading import Thread, Lock


class BaseStrategy(object):

    def __init__(self, name="Base Strategy", symbols=None, broker_tz_offset=0, verbose=True):
        self.name = name
        self.symbols = symbols
        self.broker_tz_offset = broker_tz_offset
        self.verbose = verbose

        self.conn = Connector()

        # Strategy's ON/OFF switch
        self.isON = True

        self.lock = Lock()


class CoinFlipStrategy(BaseStrategy):

    def __init__(self, name="CoinFlip_Traders", symbols=None, broker_tz_offset=0, verbose=True, max_trades=1,
                 delay=0.01):
        super().__init__(name, symbols, broker_tz_offset, verbose)

        self.traders = []
        self.market_open = True
        self.max_trades = max_trades
        self.delay = delay

        self.updater = None

    def run(self):
        for symbol in self.symbols:
            _t = Thread(name='{}_Trader'.format(symbol),
                        target=self._trader,
                        args=(symbol, self.max_trades))
            _t.daemon = True
            _t.start()
            print('[{}_Trader] Alright, here we go..!  ..... xD'.format(symbol))
            self.traders.append(_t)

        # Updater thread
        self.updater = Thread(name='Live_Updater',
                              target=self._updater,
                              args=(self.delay,))

    def stop(self):
        self.isON = False
        for trader in self.traders:
            trader.join()
            print('\n[{}] .. and that\'s a wrap! Time to head home.\n'.format(trader.getName()))
        self.conn.shutdown()

    def _updater(self, _delay=0.1):

        while self.isON:

            try:
                # Acquire lock
                self.lock.acquire()

            finally:
                # Release lock
                self.lock.release()

            sleep(self.delay)

    def _trader(self):
        """
        TODO: use self.conn.make_request()
        """
        pass

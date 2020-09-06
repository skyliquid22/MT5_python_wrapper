"""
TODO: Use expert advisor to stream market data.
"""

from src.db.db_connection import DBConnector
from src.client.connector import Connector

from time import sleep
import datetime
from threading import Thread, Lock

import pandas as pd


class BaseStrategy(object):

    def __init__(self, name="Base Strategy", symbols=None, broker_tz_offset=0, verbose=True):
        self.name = name
        self.symbols = symbols
        self.broker_tz_offset = broker_tz_offset
        self.verbose = verbose

        self.conn = Connector()
        self.dbconn = DBConnector()
        # Strategy's ON/OFF switch
        self.isON = True
        self.trades = pd.DataFrame(columns=['orderid', 'timestamp', 'retcode', 'symbol', 'price', 'bid', 'ask',
                                            'comment', 'volume', 'dealid', 'tr_action', 'tr_volume', 'tr_price',
                                            'tr_stoplimit', 'tr_sl', 'tr_tp', 'tr_type', 'tr_type_filling',
                                            'tr_type_time', 'tr_expiration', 'tr_comment'])

        self.lock = Lock()

    def _save_order(self, result):
        """
        Save Successful orders to self.trades
        :param result: (obj) the return of send_command().
        """

        now = datetime.datetime.utcnow()

        result_dict = result._asdict()
        traderequest_dict = result_dict['request']._asdict()

        vals = tuple([
            result_dict['order'],  # Order ticket id
            now.strftime('%Y-%m-%d %H:%M:%S'),  # timestamp
            result_dict['retcode'],  # Return code of request
            traderequest_dict['symbol'],  # the symbol affecting
            result_dict['price'],
            result_dict['bid'],
            result_dict['ask'],
            result_dict['comment'],
            result_dict['volume'],
            result_dict['deal'],
            traderequest_dict['action'],
            traderequest_dict['volume'],
            traderequest_dict['price'],
            traderequest_dict['stoplimit'],
            traderequest_dict['sl'],
            traderequest_dict['tp'],
            traderequest_dict['type'],
            traderequest_dict['type_filling'],
            traderequest_dict['type_time'],
            traderequest_dict['expiration'],
            traderequest_dict['comment']

        ])
        # Update
        self.trades = self.trades.append(pd.concat([result_dict, traderequest_dict]), ignore_index=True)

        sql = """INSERT INTO order_history (
        orderid, timestamp, retcode, symbol, price, bid, ask, comment, volume, dealid, tr_action, tr_volume, tr_price,
        tr_stoplimit, tr_sl, tr_tp, tr_type, tr_type_filling, tr_type_time, tr_expiration, tr_comment
        ) VALUES {}""".format(vals)

        self.dbconn.execute_query(sql)


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

    def _trader(self, symbol, max_trades):
        """
        TODO: use self.conn.make_request()
        """
        self.conn.make_request()

        while self.isON:
            # Acquire lock
            self.lock.acquire()



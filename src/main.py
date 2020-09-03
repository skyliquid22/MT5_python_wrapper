import logging
from logging.handlers import TimedRotatingFileHandler

import pandas as pd
import datetime

import MetaTrader5 as mt5

from src.db.db_connection import DBConnector


def connect():
    if mt5.initialize():
        print('[CLIENT] Connected to server.')
    else:
        print('[CLIENT] Unable to Connect to server, error code: ', mt5.last_error())


class Connector:
    """
    account_info:
    login(int),trade_mode(int),leverage(int),limit_orders(int),
    margin_so_mode(int),trade_allowed(bool),trade_expert(bool),
    margin_mode(int),currency_digits(int),fifo_close(bool),
    balance(float),credit(float),profit(float),equity(float),
    margin(float),margin_free(float),margin_level(float),
    margin_so_call(float),margin_so_so(float),margin_initial(float),
    margin_maintenance(float),assets(float),liabilities(float),
    commission_blocked(float),name(str),server(str),currency(str),company(str)
    """

    def __init__(self):

        connect()
        if mt5.account_info() is not None:

            self.account_info = mt5.account_info()._asdict()
            # self.symbols = mt5.symbols_get(group="*,!*USD*,!*EUR*,!*JPY*,!*GBP*")
            self.all_symbols = mt5.symbols_total()
            self.account = mt5.account_info()
            # Symbols in the Market watch window
            self.selected = []

            # Log file for server warnings or errors.
            self.logger = logging.getLogger('my_logger')
            self.logger.setLevel(logging.DEBUG)
            handler = TimedRotatingFileHandler("logfile", when='midnight')
            handler.suffix = '%Y_%m_%d.log'
            self.logger.addHandler(handler)

        else:
            print('[CLIENT] Server Authorization failed, Quitting app')
            mt5.shutdown()

    def symbol_info(self, symbols):
        """

        :param symbols: (list of str) list of symbols
        :return: (DataFrame) a DataFrame of the complete symbols' description
        """
        # If selection was successful
        if self._select_symbol(symbols):
            info_list = []

            for symbol in symbols:
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is not None:
                    info_list.append(symbol_info._asdict())

            return pd.concat(info_list)
        else:
            print('[symbol_info] Unable to get info from unselected symbols')

    def get_balance(self):
        print('ACCOUNT BALANCE: {} {a}\nACCOUNT EQUITY: {} {a}'.format(self.account.balance,
                                                                       self.account.equity, a=self.account.currency))
        return self.account.balance

    @staticmethod
    def make_request(action=mt5.TRADE_ACTION_DEAL, symbol='EURUSD', volume=0.01,
                     type=mt5.ORDER_TYPE_BUY, market=False, sl_points=100, tp_points=100,
                     magic=123456, comment='MT5 Python'):
        """
        :param action: (int) trade action. example: mt5.TRADE_ACTION_DEAL
        :param symbol: (str) symbol
        :param volume: (float) trade volume
        :param type: (int) trade type. example: mt5.ORDER_TYPE_BUY
        :param market: (bool) True for market order. Default is False
        :param sl_points: (int) n# of point below ask price to close trade
        :param tp_points: (int) n# of point above ask price to close trade
        :param magic: (int) the magic number :)
        :param comment: (str) comment
        :return: (stack) [request, return-code]
        """

        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(symbol, "not found, can not call order_check()")

        # if the symbol is unavailable in MarketWatch, add it
        if not symbol_info.visible:
            print(symbol, "is not visible, trying to switch on")
            if not mt5.symbol_select(symbol, True):
                print("symbol_select({}}) failed, exit", symbol)

        # prepare the request
        point = mt5.symbol_info(symbol).point
        request = {
            "action": action,
            "symbol": symbol,
            "volume": volume,
            "type": type,
            "price": mt5.symbol_info_tick(symbol).ask,
            "sl": round(mt5.symbol_info_tick(symbol).ask - sl_points * point, 5),
            "tp": round(mt5.symbol_info_tick(symbol).ask + tp_points * point, 5),
            "deviation": 10,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,  # The order stays in the queue until it is manually canceled
            "type_filling": mt5.ORDER_FILLING_FOK,
            # https://www.mql5.com/en/docs/integration/python_metatrader5/mt5ordercheck_py
        }
        if market:
            request['price'] = 0.0
            request['type_filling'] = mt5.ORDER_FILLING_RETURN

        return request

    def check_request(self, request, verbose=False):
        """
        :return: The Structure of Results of a Trade Request Check
        """

        result = mt5.order_check(request)
        result_dict = result._asdict()
        if int(result_dict['retcode']) == 0:
            print('[MT5 SERVER] REQUEST VALID.')
        else:
            cont, description = self._return_code_dict(result_dict.retcode)
            print('[MT5 SERVER] Request Issue. Description: {}'.format(description))

        if verbose:
            for field in result_dict.keys():
                print("   {}={}".format(field, result_dict[field]))
                # if this is a trading request structure, display it element by element as well
                if field == "request":
                    traderequest_dict = result_dict[field]._asdict()
                    for tradereq_filed in traderequest_dict:
                        print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))

    def _save_order(self, r_dict):
        dbconn = DBConnector()
        now = datetime.datetime.utcnow()
        #cols = tuple("orderid timestamp retcode symbol".split(' '))
        vals = tuple([r_dict['order'], now.strftime('%Y-%m-%d %H:%M:%S'), r_dict['retcode'], 'EURUSD'])
        sql = """INSERT INTO order_history (orderid, timestamp, retcode, symbol) VALUES {}""".format(vals)
        dbconn.execute_query(sql)


    @staticmethod
    def _return_code_dict(ret_code):
        dbconn = DBConnector()
        df = dbconn.get_df_from_query("SELECT * FROM mt5_return_codes WHERE id={}".format(ret_code))

        return df['Constant'].values, df['Description'].values

    def send_command(self, request):
        """
        Send command to Mt5 Terminal
        """
        result = mt5.order_send(request)
        result_dict = result._asdict()
        # check the execution result
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            # log issue
            self.logger.debug(result)
            cont, description = self._return_code_dict(result_dict['retcode'])
            print('[MT5 SERVER] Order Issue. Description: {}'.format(description))

            for field in result_dict.keys():
                print("   {}={}".format(field, result_dict[field]))
                # if this is a trading request structure, display it element by element as well
                if field == "request":
                    traderequest_dict = result_dict[field]._asdict()
                    for tradereq_filed in traderequest_dict:
                        print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
            print("shutdown() and quit")
            mt5.shutdown()
        else:
            print("[MT5 SERVER] COMMAND EXECUTED SUCCESSFULLY!")
            print(result_dict)
            self._save_order(result_dict)
            # TODO: add order with assigned ticket to open orders in DB

    @staticmethod
    def get_orders_count():
        return mt5.orders_total()

    @staticmethod
    def get_orders(**kwargs):
        """
        symbol="Symbol"
        group="Group" i.e. group="*GBP*" > get the list of orders on symbols whose names contain "*GBP*"
        ticket="Ticket"
        """
        orders = mt5.orders_get(**kwargs)
        if orders is None:
            print("No orders found, error code={}".format(mt5.last_error()))
            return pd.DataFrame()
        else:
            df = pd.DataFrame(list(orders), columns=orders[0]._asdict().keys())
            df['time_setup'] = pd.to_datetime(df['time_setup'], unit='s')
            return df

    @staticmethod
    def get_rates(symbol, start=0, timeframe='TIMEFRAME_D1', count=270, end=None):
        """

        :param symbol: (str)
        :param timeframe: (str) the time interval, TIMEFRAME_M1: 1min, _H, _D, _W, _MN
        :param start: (str or int) the start of the data, can be date or bar index
        :param count: (int) number of bars to return
        :param end: (str) (optional) sets the end date instead of using count
        :return: (DateFrame)
        """
        # check if start is a bar index
        if isinstance(start, int):
            rates = pd.DataFrame(mt5.copy_rates_from_pos(symbol, timeframe, start, count))
            rates['time'] = pd.to_datetime(rates['time'], unit='s')
            return rates
        else:
            try:
                start_time = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S UTC')
                # create 'datetime' object in UTC time zone to avoid the implementation of a local time zone offset
                start_time.replace(tzinfo=datetime.timezone.utc)
                if end is not None:
                    end_time = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S UTC')
                    end_time.replace(tzinfo=datetime.timezone.utc)
                    rates = pd.DataFrame(mt5.copy_rates_range(symbol, timeframe, start_time, end_time))
                    rates['time'] = pd.to_datetime(rates['time'], unit='s')
                    return rates
                else:
                    rates = pd.DataFrame(mt5.copy_rates_from(symbol, timeframe, start_time, count))
                    rates['time'] = pd.to_datetime(rates['time'], unit='s')
                    return rates
            except TypeError:
                print('[get_rates] start type neither date nor bar index')

    @staticmethod
    def tick_info(symbols):
        """

        :param symbols: (list of str) list of symbols
        :return: (DataFrame) a DataFrame of the last symbols' tick data
        """
        tick_info_list = []
        for symbol in symbols:
            tick_info = mt5.symbol_info_tick(symbol)._asdict()
            if tick_info is not None:
                tick_info_list.append(tick_info)
        return pd.concat(tick_info_list)

    @staticmethod
    def _get_open_trades_count():
        """
        Returns the number of open positions
        """
        return mt5.positions_total()

    @staticmethod
    def _get_open_trades(**kwargs):
        """
        TODO : https://www.mql5.com/en/docs/integration/python_metatrader5/mt5positionsget_py
        """
        return mt5.positions_get(**kwargs)

    def _select_symbol(self, symbols):
        """
        Adds input symbols to mt5 market watch
        :param symbols: (list of str) list of symbols
        :return: (bool) True if all selected, False otherwise
        """
        # Remove all the symbols that are already selected
        symbols = [x for x in symbols if x not in self.selected]
        for symbol in symbols:
            if mt5.symbol_select(symbol, True):
                self.selected.append(symbol)
            else:
                print("Failed to select {}".format(symbol), mt5.last_error())

        if len(symbols) == len(self.selected):
            return True
        else:
            return False

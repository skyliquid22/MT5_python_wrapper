import pandas as pd

# module for working with time zone
import pytz

import MetaTrader5 as mt5


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

    def __init__(self, login='3000020370', password='f4DTmB1hlAT'):

        connect()
        if mt5.login(login, password) and mt5.account_info() is not None:

            self.account_info = mt5.account_info()._asdict()
            # self.symbols = mt5.symbols_get(group="*,!*USD*,!*EUR*,!*JPY*,!*GBP*")
            self.all_symbols = mt5.symbols_total()
            # Symbols in the Market watch window
            self.selected = []

        else:
            print('[CLIENT] Server Authorization failed, Quitting app')
            mt5.shutdown()
            quit()

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

    def get_rates(self, symbol, start, timeframe='TIMEFRAME_D1', count=270):
        """

        :param symbol: (str)
        :param timeframe: (str) the time interval, TIMEFRAME_M1: 1min, _H, _D, _W, _MN
        :param start: (date or int) the start of the data, can be date or bar index
        :param count: (int) number of bars to return
        :return: (DateFrame)
        """

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

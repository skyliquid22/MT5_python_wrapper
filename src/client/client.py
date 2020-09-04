import pandas as pd
from time import sleep

from src.client import ea_api


class Client:

    def __init__(self):
        self.conn = ea_api.EAConnector(client_id='ai_001')
        self.market_data = pd.DataFrame()

    def parse_market_data(self):
        """
        Returns a DataFrame object of the market_data_db variable which collects data from the Connector's subscribe socket
        :return: (DataFrame) Parsed BID/ASK market data for every symbol in multi-index columns
        """
        rawdata = self.conn.market_data_db
        df = pd.DataFrame(rawdata)

        # Flush market_data_db
        self.conn.market_data_db = {}

        for symbol in df.columns:
            new = pd.DataFrame()
            new['buy'] = df[symbol].apply(lambda x: x[0] if type(x) is tuple else x)
            new['sell'] = df[symbol].apply(lambda x: x[1] if type(x) is tuple else x)
            new.columns = pd.MultiIndex.from_arrays([[symbol, symbol], ['BUY', 'SELL']])
            self.market_data = pd.concat([self.market_data, new], axis=1)



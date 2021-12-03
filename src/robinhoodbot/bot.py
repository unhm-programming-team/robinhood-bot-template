import robin_stocks.robinhood as r
import pandas as pd
import numpy as np
import ta as ta
from pandas.plotting import register_matplotlib_converters
from ta import *
from .misc import *
from .tradingstats import *
from .config import *
import sys
import time
import csv
import traceback

""""with open('US_LIST_OF_SYMBOLS.csv') as f:
    reader = csv.reader(f)
    for row in reader:
        ticker_list.append(row[0])
"""


class RobinhoodBot:

    def __init__(self, username, password):
        """
            robin authentication and tickerlist initialization
            :param username: Robinhood email address. Type: String. Ex. John.Smith@gmail.com
            :param password: Robinhood password.

            """
        self.login = r.login(username, password)
        with open("filtered_stocks.txt") as stockfile:
            self.ticker_list = stockfile.read().split()

    def safe_division(self, numerator, denominator):
        """
        :return: Number: numerator divided by denominator unless denominator is 0, in which case return 0.
        """
        return numerator / denominator if denominator else 0

    @staticmethod
    def get_historicals(ticker, intervalArg='hour', spanArg='week', boundsArg='regular'):
        """
        :param ticker: String: Stock ticker. Ex: "APPL"
        :param intervalArg: interval to retrieve data for. Values are '5minute', '10minute', 'hour', 'day', 'week'. Default is 'hour'.
        :param spanArg: Sets the range of the data to be either 'day', 'week', 'month', '3month', 'year', or '5year'. Default is 'week'.
        :param boundsArg: Represents if graph will include extended trading hours or just regular trading hours. Values are 'extended', 'trading', or 'regular'. Default is 'regular'
        :return: [list] Returns a list of dictionaries where each dictionary is for a different time.
        If multiple stocks are provided \ the historical data is listed one after another.
        """
        history = r.get_stock_historicals(ticker, interval=intervalArg, span=spanArg, bounds=boundsArg)
        return history

    def get_ticker_list(self):
        """
        getter for self.ticker_list. Tickers from filtered_stocks.txt
        :return: List: list where each element is a string representing a ticker. Ex: ['ABNB', 'AAPL'...]
        """
        return self.ticker_list

    @staticmethod
    def get_portfolio_symbols():
        """
        Returns: the symbol for each stock in your portfolio as a list of strings. Ex" ['APPL', ...]
        """
        symbols = []
        holdings_data = r.get_open_stock_positions()
        for item in holdings_data:
            if not item:
                continue
            instrument_data = r.get_instrument_by_url(item.get('instrument'))
            symbol = instrument_data['symbol']
            symbols.append(symbol)
        return symbols

    @staticmethod
    def get_position_creation_date(symbol, holdings_data):
        """Returns the time at which we bought a certain stock in our portfolio

        Args:
            symbol(str): Symbol of the stock that we are trying to figure out when it was bought
            holdings_data(dict): dict returned by r.get_open_stock_positions()

        Returns:
            A string containing the date and time the stock was bought, or "Not found" otherwise
        """
        instrument = r.get_instruments_by_symbols(symbol)
        url = instrument[0].get('url')
        for holding in holdings_data:
            if holding.get('instrument') == url:
                return holding.get('created_at')
        return "Not found"

    @staticmethod
    def get_modified_holdings():
        """ Retrieves the same dictionary as r.build_holdings, but includes data about
            when the stock was purchased, which is useful for the read_trade_history() method
            in tradingstats.py

        Returns:
            the same dict from r.build_holdings, but with an extra key-value pair for each
            position you have, which is 'bought_at': (the time the stock was purchased)
        """
        holdings = r.build_holdings()
        holdings_data = r.get_open_stock_positions()
        for symbol, holding_info in holdings.items():
            bought_at = RobinhoodBot.get_position_creation_date(symbol, holdings_data)
            bought_at = str(pd.to_datetime(bought_at))
            holdings[symbol].update({'bought_at': bought_at})
        return holdings


    @staticmethod
    def five_year_check(stock_ticker):
        """Figure out if a stock has risen or been created within the last five years.

        Args:
            stock_ticker(str): Symbol of the stock we're querying

        Returns:
            True if the stock's current price is higher than it was five years ago, or the stock IPO'd within the last five years
            False otherwise
        """
        instrument = r.get_instruments_by_symbols(stock_ticker)

        if instrument is None or len(instrument) == 0:
            return True
        list_date = instrument[0].get("list_date")
        if (pd.Timestamp("now") - pd.to_datetime(list_date)) < pd.Timedelta("5 Y"):
            return True
        fiveyear = RobinhoodBot.get_historicals(stock_ticker, "day", "5year", "regular")
        if fiveyear is None or None in fiveyear:
            return True
        closing_prices = []
        for item in fiveyear:
            closing_prices.append(float(item['close_price']))
        recent_price = closing_prices[len(closing_prices) - 1]
        oldest_price = closing_prices[0]
        return recent_price > oldest_price

    @staticmethod
    def sell_holdings(symbol, holdings_data):
        """ Place an order to sell all holdings of a stock.

        Args:
            symbol(str): Symbol of the stock we want to sell
            holdings_data(dict): dict obtained from get_modified_holdings() method
        """
        shares_owned = round(float(holdings_data[symbol].get("quantity")), 6)
        if not debug:
            r.order_sell_market(symbol, shares_owned)
        print("####### Selling " + str(shares_owned) + " shares of " + symbol + " #######")


    @staticmethod
    def buy_holdings(buys, profile_data, holdings_data):
        """ Places orders to buy holdings of stocks. This method will try to order
            an appropriate amount of shares such that your holdings of the stock will
            roughly match the average for the rest of your portfoilio. If the share
            price is too high considering the rest of your holdings and the amount of
            buying power in your account, it will not order any shares.

        Args:
            buys(list): List of strings, the strings are the symbols of stocks we want to buy
            symbol(str): Symbol of the stock we want to sell
            holdings_data(dict): dict obtained from r.build_holdings() or get_modified_holdings() method
        """
        cash = float(profile_data.get('cash'))
        portfolio_value = float(profile_data.get('equity')) - cash
        ideal_position_size = (RobinhoodBot.safe_division(portfolio_value, len(holdings_data)) + cash / 5) / (2 * 5) # potentially change this
        prices = r.get_latest_price(buys)

        for stock in buys:
            index = buys.index(stock)
            stock_price = float(prices[index])
            if ideal_position_size < stock_price < ideal_position_size * 1.5:
                num_shares = ideal_position_size * 1.5 / stock_price
            elif ideal_position_size > 1:
                num_shares = ideal_position_size / stock_price
            else:
                print("####### Tried buying shares of " + stock
                     + ", but not enough buying power to do so#######")
                break
            print("####### Buying " + str(num_shares) + " shares of " + stock + " #######")
            if not debug:
                print(r.order_buy_market(stock, round(num_shares, 6), timeInForce="gfd"))

    def buy_strategy(self, symbol):
        """
        Here You can implement your buy strategy.
        :param symbol:
        :return:
        """
        pass

    def sell_strategy(self, symbol):
        """
        Here you can Implement your sell strategy
        :param symbol:
        :return:
        """

    def scan_stocks(self):
        """ The main method. Sells stocks in your portfolio if they meet your strategy. Buys a stock if it .

            ###############################################################################################
            WARNING: Comment out the sell_holdings and buy_holdings lines if you don't actually want to execute the trade.
            ###############################################################################################

            If you sell a stock, this updates tradehistory.txt with information about the position,
            how much you've earned/lost, etc.
        """
        if debug:
            print("----- DEBUG MODE -----\n")
        print("----- Starting scan... -----\n")
        register_matplotlib_converters()
        ticker_list = self.get_ticker_list()
        portfolio_symbols = self.get_portfolio_symbols()
        holdings_data = self.get_modified_holdings()
        potential_buys = []
        sells = []
        print("Current Portfolio: " + str(portfolio_symbols) + "\n")
        print("Current Watchlist: " + str(ticker_list) + "\n")
        print("----- Scanning portfolio for stocks to sell -----\n")
        for symbol in portfolio_symbols:
            """
            Your selling stategy here. accumulate into sells.
            """



        profile_data = r.build_user_profile()
        print("\n----- Scanning watchlist for stocks to buy -----\n")
        for symbol in ticker_list:
            """
            Your buying strategy here. Accumulate buys into 'potential_buys'.
            """

        if (len(potential_buys) > 0):
            self.buy_holdings(potential_buys, profile_data, holdings_data)
        if (len(sells) > 0):
            update_trade_history(sells, holdings_data, "tradehistory.txt")
        print("----- Scan over -----\n")
        if debug:
            print("----- DEBUG MODE -----\n")


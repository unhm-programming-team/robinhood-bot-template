"""
HistoricalsRetriever fetches from the API and gets saved information from the file system.

It is initialized with a base directory, which is relative from the current working directory, and that's where it
will save anything it fetches or loads anything already saved.

Historicals Retriever can fetch from 3 APIs: robinhood, alpha vantage, and polygon.

It saves information on each ticker to Instance.base_directory/TickerName.


It stores a meta_data.txt file in that directory regarding information about when it was last pulled.
"""

import os  # used for paths
import json  # used for formatting saved data

import requests
import robin_stocks  # robinhood API
from datetime import datetime  # for log time stamping
import pandas  # for getting pandas data frames

alpha_vantage_api_url = "https://www.alphavantage.co/query"
polygon_splits_url = "https://api.polygon.io/v2/reference/splits/"




class HistoricalsRetriever:
    def __init__(self, base_directory):
        """
        On initialization creates the directory to save data if it doesn't exist. If robin hood credentials are
        given, it also logs in to robinhood.

        :param base_directory: The output directory where data will be stored
        :type base_directory: str
        """
        current_working_directory = os.getcwd()
        self.logs = []
        self.directory = os.path.join(current_working_directory, base_directory)
        self.alpha_vantage_api_key = None
        self.polygon_api_key = None
        if not os.path.isdir(self.directory):
            os.mkdir(self.directory)
            self.log(f'created base directory {self.directory}')

    def load_api_keys(self, key_string, key):
        """
        Loads api key
        :param key_string: Which key to load. Either 'alpha_vantage' or 'polygon'
        :param key: the api key
        """
        if key_string == "alpha_vantage":
            self.alpha_vantage_api_key = key
            self.log('loaded alpha vantage API key')
        elif key_string == "polygon":
            self.polygon_api_key = key
            self.log('loaded polygon API key')

    def log(self, msg):
        """
        Logs a message to self.logs regarding operations performed on this class
        :param msg: a message to log
        :type msg: str
        """
        time = datetime.utcnow()
        hour_min_sec = time.strftime("%H:%M:%S:")
        milliseconds = int(time.microsecond / 1000)
        time_string = hour_min_sec + str(milliseconds)
        self.logs.append(f'{time_string} - {msg}')

    def _make_ticker_directory(self, ticker):
        """
        Creates a directory for a ticker if it doesn't exist,
        returns the directory either way.

        Should be called internally by retriever only.

        :param ticker: the ticker to make the directory for
        :return: the directory path
        """
        ticker_dir = os.path.join(self.directory, ticker)
        if not os.path.isdir(ticker_dir):
            os.mkdir(ticker_dir)
            self.log(f'created directory {ticker_dir}')
        return ticker_dir

    def get_loaded_tickers(self):
        """
        Gets a list of the current directories in data
        :return: list<str>
        """
        return os.listdir(self.directory)

    def _save_one(self, target, result):
        """
        Simply saves to a file.

        Should be called internally by retriever only.

        :param target: The file path to save
        :param result: The object to jsonify
        """
        file = open(target, "w")
        jsn = json.dumps(result)
        file.write(jsn)
        file.close()
        self.log(f'saved {target}')

    #  These technical fetchers/getters shouldn't really be used yet!
    #  The format of the return for different technicals varies.
    #  These functions will probably wind up being internal funcs
    #  Or there will have to be a reference dict for filenames and structures...

    def _fetch_alpha_vantage_technical(self, ticker, params):
        """
        Fetches alpha vantage technical data for a ticker and stores it on local storage
        :param ticker: The ticker to retrieve for
        :param params: A dictionary of parameters to send to alpha vantage api, varies based on what function is
        selected
        :type params: dict
        :return:
        """
        if "apikey" not in params.keys():
            if self.alpha_vantage_api_key is not None:
                params["apikey"] = self.alpha_vantage_api_key
        if "function" not in params.keys():
            self.log("A function is needed to retrieve an alpha vantage technical!")
            return False
        if "interval" not in params.keys():
            params["interval"] = "daily"
        params["symbol"] = ticker
        r = requests.get(alpha_vantage_api_url, params).json()
        ticker_dir = self._make_ticker_directory(ticker)
        file_name = ticker + "-AV-" + params["function"] + ".json"
        file_save = os.path.join(ticker_dir, file_name)
        self._save_one(file_save, r)
        self.log(f'fetched alpha vantage sma for {ticker}')

    def _get_alpha_vantage_technical(self, ticker, function_name):
        """
        Gets technical data stored on local file system as a series

        :param ticker: The ticker to get the info for
        :type ticker: str
        :param function_name: The name of the function
        :type function_name: str
        :return: The technical data
        :rtype: Pandas.Series
        """
        ticker_dir = self._make_ticker_directory(ticker)
        file_name = ticker + '-AV-' + function_name
        target_path = os.path.join(ticker_dir, file_name)
        try:
            file = open(target_path)
            data = json.load(file)
            tech_analysis = data[f"Technical Analysis: {function_name}"]
            series = pandas.Series(tech_analysis)
            series.index = pandas.to_datetime(series.index)
            for i in range(len(series)):
                series[i] = float(series[i][function_name])
            series = series.infer_objects()
            return series
        except FileNotFoundError:
            self.log(f"Error: No such file: {target_path}")
            return f"No such file {target_path}"

    def _get_alpha_vantage_technical_update_delta(self, ticker, function_name):
        """
        Gets the time delta between the most recent tech record and now
        :param ticker: the ticker to get
        :param function_name: The technical name. E.g: sma
        :return: datetime.delta
        """
        series = self._get_alpha_vantage_technical(ticker, function_name)
        now = datetime.now()
        return now - series.index.max()

    def fetch_alpha_vantage_prices(self, ticker):
        """
        Fetches daily price data from alpha vantage for a ticker, going back ~20 years
        :param ticker: The ticker to fetch
        :returns: Whether fetch was succesful
        :rtype: bool
        """
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": "full",
            "apikey": self.alpha_vantage_api_key
        }
        r = requests.get(alpha_vantage_api_url, params).json()
        if 'Error Message' in r.keys():
            self.log(f'error calling alpha vantage - probably a bad API key: {r["Error Message"]}')
            return False
        elif "Note" in r.keys():
            if r["Note"].startswith("Thank you"):
                self.log(f"error calling in alpha vantage, keys reached: {r['Note']}")
                return False
        else:
            if "Time Series (Daily)" in r.keys():
                ticker_dir = self._make_ticker_directory(ticker)
                file_name = ticker + '-AV-DAILY.json'
                file_save = os.path.join(ticker_dir, file_name)
                self._save_one(file_save, r)
                return True

    def get_alpha_vantage_prices(self, ticker):
        """
        Gets alpha vantage price data for a ticker from local storage.

        :param ticker: The ticker to get price data from.
        :return: A formatted and typed data frame representing open, high, low, close, and volume data for a ticker.
        :rtype: Pandas.DataFrame
        """
        ticker_dir = self._make_ticker_directory(ticker)
        file_name = ticker + '-AV-DAILY.json'
        target_path = os.path.join(ticker_dir, file_name)
        try:
            file = open(target_path)
            data = json.load(file)
            prices = data["Time Series (Daily)"]
            df = pandas.DataFrame.from_dict(data=prices, orient='index', dtype='float64')
            df.rename(
                columns={
                    "1. open": "open",
                    "2. high": "high",
                    "3. low": "low",
                    "4. close": "close",
                    "5. volume": "volume"
                },
                inplace=True
            )
            df.index = pandas.to_datetime(df.index)
            return df
        except FileNotFoundError:
            self.log(f"Error: No such file: {target_path}")
            return False

    def _get_alpha_vantage_prices_update_delta(self, ticker):
        """
        Gets the delta between the last price record and now

        :param ticker: ticker to check
        :return: the datetime delta
        """
        df = self.get_alpha_vantage_prices(ticker)
        now = datetime.now()
        return now - df.index.max()

    def fetch_polygon_splits(self, ticker):
        """
        Fetches splits data from polygon api and stores the .json locally.

        :param ticker: the ticker to get
        :return: whether fetch was succesful, True or False
        :rtype: bool
        """
        ticker_url = polygon_splits_url + ticker
        if self.polygon_api_key is None:
            self.log('Must have api key to call polygon')
            return False
        params = {
            "apiKey": self.polygon_api_key
        }
        r = requests.get(ticker_url, params).json()
        if r['status'] != 'ERROR':
            if(r['count'] <= 0):
                self.log(f"splits data for {ticker} was empty! Skipping save.")
                return False
            ticker_dir = self._make_ticker_directory(ticker)
            file_name = ticker + '-POL-SPLITS.json'
            file_save = os.path.join(ticker_dir, file_name)
            self._save_one(file_save, r)
            return True
        else:
            self.log(f'bad polygon call: {r["status"]}')
            return False

    def get_polygon_splits(self, ticker):
        """
        Gets a formatted data frame for the splits data on disc previously fetched from polygon.

        :param ticker: the ticker to get
        :return: splits DataFrame
        :rtype: pandas.DataFrame
        """
        ticker_dir = self._make_ticker_directory(ticker)
        file_name = ticker + '-POL-SPLITS.json'
        target_path = os.path.join(ticker_dir, file_name)
        try:
            file = open(target_path)
            data = json.load(file)
            splits = data["results"]
            df = pandas.DataFrame.from_records(splits,
                                               index='exDate'
                                               )
            df.index = pandas.to_datetime(df.index)
            if 'ticker' in df.keys():
                del df['ticker']
            if 'paymentDate' in df.keys():
                df['paymentDate'] = pandas.to_datetime(df['paymentDate'])
            if 'declaredDate' in df.keys():
                df['declaredDate'] = pandas.to_datetime(df['paymentDate'])
            return df
        except FileNotFoundError:
            self.log(f"Error: No such file: {target_path}")
            return f"No such file {target_path}"

    def _get_last_polygon_split_retrieve_date(self, ticker):
        """
        Gets the last date <ticker>-POL.SPLITS.json was modified.

        :param ticker: The ticker to look for
        :return: a datetime
        :rtype: datetime
        """
        ticker_dir = self._make_ticker_directory(ticker)
        file_name = ticker + '-POL-SPLITS.json'
        target_path = os.path.join(ticker_dir, file_name)
        stats = os.stat(target_path)
        return datetime.fromtimestamp(stats.st_mtime)

    def _get_polygon_split_data_update_delta(self, ticker):
        """
        Gets the delta between when the splits file was last updated and now.

        :param ticker: ticker to check
        :return:
        :rtype: datetime.delta
        """
        now = datetime.now()
        last_mod_date = self._get_last_polygon_split_retrieve_date(ticker)
        delta = now - last_mod_date
        return delta

    def get_available_data_for_ticker(self, ticker):
        """
        Checks what data is available for a ticker and when it was updated.

        :param ticker: The ticker to check
        :return: A dictionary
        :rtype: dict
        """
        target_path = os.path.join(self.directory, ticker)
        dic = {}
        raw_list = os.listdir(target_path)
        for each in raw_list:
            base = each.split('.')[0]
            parts = base.split('-')
            type = parts[2]
            value = "Unknown"
            if type == "DAILY":
                delta = self._get_alpha_vantage_prices_update_delta(ticker)
                if delta.days == 1:
                    day_text = "day"
                else:
                    day_text = "days"
                value = f"Updated {delta.days} {day_text} ago"
            elif type == "SPLITS":
                delta = self._get_polygon_split_data_update_delta(ticker)
                if delta.days == 1:
                    day_text = "day"
                else:
                    day_text = "days"
                value = f"Updated {delta.days} {day_text} ago"
            dic[type] = value
        return dic

    def report(self):
        """
        Reports logs
        """
        print('\n-------- Log report for HistoricalsRetriever -----------\n')
        print('h  m  s  ms')
        if len(self.logs) == 0:
            print('No logs to report!')
        else:
            for log in self.logs:
                print(log)
        print('\n--------------------------------------------------------\n')

    def report_to_string(self):
        """
        Gets the report, but as a string
        :return: the report
        :rtype: str
        """
        text = '\n-------- Log report for HistoricalsRetriever -----------\n\n'
        text += 'h  m  s  ms\n'
        if len(self.logs) == 0:
            text += 'No logs to report!\n'
        else:
            for log in self.logs:
                text += log + "\n"
        text += '\n\n--------------------------------------------------------\n'
        return text











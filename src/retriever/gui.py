from tkinter import *
from tkinter import ttk

from .retriever import HistoricalsRetriever

RETRIEVER = HistoricalsRetriever(base_directory="data")  # global retriever, initialized by the core gui frame,
# RetreiverGui

BASE_FONT = ("Times New Roman", 12)

SMALLER_FONT = (BASE_FONT[0], BASE_FONT[1] - 2)

LARGER_FONT = (BASE_FONT[0], BASE_FONT[1] + 2)

CROSS_UPDATE_FUNCS = []  # zero-parameter lambdas stored in this list which check retriever for updates


class RetrieverGui(Frame):
    """
    Holds the other components for the retriever gui
    """

    def __init__(self, base_directory="data", **kwargs):
        super().__init__(**kwargs)

        RETRIEVER.directory = base_directory
        title = Label(master=self,
                      pady=5,
                      text="Retriever GUI",
                      font=LARGER_FONT,
                      width=30,
                      borderwidth=3,
                      relief="ridge",
                      fg="#0d1012",
                      bg="#e9f0f0")
        title.grid(row=1, columnspan=3)

        api_keys_and_fetch_frame = Frame(master=self)
        api_keys_and_fetch_frame.grid(row=2, columnspan=3)
        api_keys_frame = Frame(master=api_keys_and_fetch_frame,
                               pady=12)
        api_keys_frame.pack(side="left")
        alpha_vantage_key_input = ApiKeyInput(master=api_keys_frame,
                                              api_name="alpha_vantage",
                                              text="Alpha Vantage Api Key")
        alpha_vantage_key_input.pack(side="top")
        polygon_key_input = ApiKeyInput(master=api_keys_frame,
                                        api_name="polygon",
                                        text="Polygon Api Key")
        polygon_key_input.pack(side="bottom")
        fetch_frame = Frame(master=api_keys_and_fetch_frame)
        fetch_frame.pack(side="right")
        fetch_box = FetchBox(master=fetch_frame,
                             text="fetch")
        fetch_box.pack(side="left")

        self.loaded_display = LoadedDisplay(master=self)
        self.loaded_display.grid(row=3, columnspan=3, sticky="NW")

        self.logger = Logger(master=self)
        self.logger.grid(row=4, sticky="NW")

        CROSS_UPDATE_FUNCS.append(lambda: self.loaded_display.refreshList())
        CROSS_UPDATE_FUNCS.append(lambda: self.logger.update_logs())


class ApiKeyInput(LabelFrame):
    """
    Inputs for API keys
    """

    def __init__(self, api_name, **kwargs):
        super().__init__(font=BASE_FONT, **kwargs)
        self.key_loaded = Label(master=self, text=" enter key:", font=BASE_FONT)
        self.key_loaded.pack(side="left")
        enter_frame = Frame(master=self, width=10)
        enter_frame.pack(side="left")
        self.key_var = StringVar()
        self.enter_key = Entry(master=enter_frame,
                               textvariable=self.key_var,
                               width=10,
                               show="*")
        self.enter_key.pack(side="left")
        self.button = Button(master=self,
                             text="load",
                             width=10,
                             command=lambda: self.on_load_click(),
                             font=BASE_FONT)
        self.button.pack(side="left")
        self.api_name = api_name

    def on_load_click(self):
        self.key_loaded.config(text="key loaded!")
        self.button.config(text="new key", command=lambda: self.new_key())
        RETRIEVER.load_api_keys(self.api_name, self.key_var.get())
        self.enter_key.pack_forget()
        for func in CROSS_UPDATE_FUNCS:
            func()

    def new_key(self):
        self.key_loaded.config(text="  enter key:")
        self.enter_key.pack(side="left")
        self.button.config(text="   load", command=lambda: self.on_load_click())


class FetchBox(LabelFrame):
    """
    Components for executing a fetch
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs, font=BASE_FONT)

        self.ticker_label = Label(master=self, text="  Ticker  ", font=BASE_FONT)
        self.ticker_label.grid(column=1, row=1, sticky="S")
        self.ticker_choice = StringVar()
        self.ticker_choice.trace('w', lambda a, b, c: self.entry_to_upper())
        self.ticker_entry = Entry(master=self,
                                  textvariable=self.ticker_choice,
                                  width=6,
                                  font=BASE_FONT)
        self.ticker_entry.grid(column=1, row=2, sticky="N")

        self.whether_to_get_dailys = BooleanVar()
        self.whether_to_get_splits = BooleanVar()
        self.choose_dailys = Checkbutton(master=self,
                                         text="Alpha Vantage Dailys?",
                                         font=BASE_FONT,
                                         variable=self.whether_to_get_dailys)
        self.choose_splits = Checkbutton(master=self,
                                         text="Polygon Splits?",
                                         font=BASE_FONT,
                                         variable=self.whether_to_get_splits
                                         )
        self.choose_dailys.grid(
            column=2,
            sticky="NW",
            row=1, )
        self.choose_splits.grid(
            column=2,
            sticky="NW",
            row=2)

        self.fetch_button = Button(master=self,
                                   text="Fetch 💹",
                                   font=BASE_FONT,
                                   command=lambda: self.fetch_click())
        self.fetch_button.grid(column=3,
                               row=1,
                               sticky="N")
        self.fetch_confirmer = Label(master=self,
                                     text="\nfetch!",
                                     font=(BASE_FONT[0], BASE_FONT[1] - 2)
                                     )
        self.fetch_confirmer.grid(column=3,
                                  row=2, sticky="N")

    def entry_to_upper(self):
        text = self.ticker_entry.get().upper()
        if len(text) > 5:
            text = text[1:6].lstrip().rstrip()
        self.ticker_choice.set(text)
        self.fetch_confirmer.config(text="\nfetch!")
        return True

    def fetch_click(self):
        ticker = self.ticker_choice.get().strip()
        res_text = ""
        if self.whether_to_get_splits.get():
            result1 = RETRIEVER.fetch_polygon_splits(ticker)
            if not result1:
                res_text += "polygon fail!\n"
        if self.whether_to_get_dailys.get():
            result2 = RETRIEVER.fetch_alpha_vantage_prices(ticker)
            if not result2:
                res_text += " av fail!"
        if len(res_text) == 0:
            res_text += f"{ticker}\nfetched!"
        self.ticker_choice.set('')

        self.fetch_confirmer.config(text=res_text)
        for func in CROSS_UPDATE_FUNCS:
            func()


class LoadedDisplay(LabelFrame):
    """
    Components for listing what is loaded on disc
    """

    def __init__(self, **kw):
        super().__init__(**kw, text="Available Data", font=BASE_FONT)
        self.ticker_choice = StringVar()
        self.ticker_choice.trace('w', lambda a, b, c: self.entry_to_upper())
        self.ticker_entry = Entry(master=self,
                                  textvariable=self.ticker_choice,
                                  width=6,
                                  font=BASE_FONT)
        self.ticker_entry.grid(row=1, column=1, columnspan=3, sticky="W")
        self.listvar = StringVar()
        self.listbox = Listbox(master=self,
                               listvariable=self.listvar,
                               relief="raised",
                               width=8,
                               font=BASE_FONT)
        self.listbox.grid(row=2, column=1, sticky="NS")
        self.listbox.bind("<<ListboxSelect>>", lambda x: self.list_box_select())
        yscroll = Scrollbar(master=self)
        yscroll.grid(row=2, column=3, sticky="NS")
        self.listbox.config(yscrollcommand=yscroll.set)
        yscroll['command'] = self.listbox.yview

        self.loaded_ticker = LoadedTicker(master=self)
        self.loaded_ticker.grid(column=4, row=1, rowspan=4, sticky="NW")

        self.refreshList()

    def refreshList(self):
        list_start = ' '.join(RETRIEVER.get_loaded_tickers())
        self.listvar.set(list_start)

    def entry_to_upper(self):
        text = self.ticker_entry.get().upper()
        if len(text) > 5:
            text = text[1:6].lstrip().rstrip()

        self.ticker_choice.set(text)
        tickers = RETRIEVER.get_loaded_tickers()
        filtered = [x for x in tickers if re.match(f"{text}.*", x)]
        self.listvar.set(' '.join(filtered))
        return True

    def list_box_select(self):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            data = self.listbox.get(index)
            self.loaded_ticker.load_ticker(data)
        else:
            self.loaded_ticker.unload()


class LoadedTicker(Frame):
    """
    Displays info about data last retrieval times
    """

    def __init__(self, **kw):
        super().__init__(**kw)
        self.ticker = ""
        name_label = Label(master=self, text="name", font=BASE_FONT)
        name_label.grid(row=1, column=1, sticky="E")
        self.name = Label(master=self, width=8, font=BASE_FONT)
        self.name.grid(row=1, column=2)
        self.facts_box = Frame(master=self)
        self.facts_box.grid(row=2, columnspan=3, rowspan=3)
        buttons_box = Frame(master=self)
        buttons_box.grid(row=6, columnspan=3)
        self.show_data_button = Button(master=buttons_box,
                                       text="Show Data",
                                       command=lambda: self.show_data(),
                                       font=BASE_FONT
                                       )

        self.data_frames = Frame(master=self)
        self.av_df_show = DataFrameShow(master=self.data_frames,
                                        data_frame_function=RETRIEVER.get_alpha_vantage_prices,
                                        name="AV Daily"
                                        )
        self.av_df_show.grid(row=1)
        self.poly_df_show = DataFrameShow(master=self.data_frames,
                                          data_frame_function=RETRIEVER.get_polygon_splits,
                                          name="Polygon Splits")
        self.poly_df_show.grid(row=2)

    def load_ticker(self, ticker):
        self.unload()
        self.ticker = ticker
        self.name.config(text=ticker)
        d = RETRIEVER.get_available_data_for_ticker(ticker)
        row = 0
        for k in d:
            label = Label(master=self.facts_box, text=k, font=BASE_FONT)
            label.grid(row=row, column=1)
            label2 = Label(master=self.facts_box, text=d[k], font=BASE_FONT)
            label2.grid(row=row, column=2)
            row += 1
        self.show_data_button.grid(row=1, column=2, sticky="EW")

    def unload(self):
        self.show_data_button.grid_remove()
        self.name.config(text="")
        self.facts_box.destroy()
        self.facts_box = Frame(master=self)
        self.facts_box.grid(row=2, columnspan=3, rowspan=3)
        self.data_frames.grid_remove()

    def show_data(self):
        self.data_frames.grid(column=4, row=1, rowspan=6, sticky="N")
        self.av_df_show.clear()
        self.poly_df_show.clear()
        avail = RETRIEVER.get_available_data_for_ticker(self.ticker)
        if 'DAILY' in avail.keys():
            self.av_df_show.load_data(self.ticker)
        if 'SPLITS' in avail.keys():
            self.poly_df_show.load_data(self.ticker)
        for func in CROSS_UPDATE_FUNCS:
            func()


class DataFrameShow(Frame):
    """
    Displays info about a DataFrame returned for a ticker
    """

    def __init__(self, data_frame_function=None, name="", **kw):
        super().__init__(**kw)
        self.name_label = Label(master=self, text="TCKR", font=LARGER_FONT)
        self.name_label.grid(row=1, column=2)
        self.type_label = Label(master=self, text="PANDAS", font=BASE_FONT)
        self.type_label.grid(row=2, column=2)
        self.dtypes_box = Frame(master=self, relief="groove", borderwidth=2)
        self.dtypes_box.grid(row=3, column=1, columnspan=3)

        self.data_frame_function = data_frame_function
        self.name = name

    def load_data(self, ticker):
        self.dtypes_box.grid(row=3, column=1, columnspan=3)
        self.name_label.config(text=ticker + " " + self.name)
        daily = self.data_frame_function(ticker)
        self.type_label.config(text=str(type(daily)))
        name_header = Label(master=self.dtypes_box, text="name", font=BASE_FONT)
        name_header.grid(row=1, column=1)
        type_header = Label(master=self.dtypes_box, text="dtype", font=BASE_FONT)
        type_header.grid(row=1, column=2)
        max_header = Label(master=self.dtypes_box, text="max", font=BASE_FONT)
        max_header.grid(row=1, column=3)
        min_header = Label(master=self.dtypes_box, text="min", font=BASE_FONT)
        min_header.grid(row=1, column=4)
        count_header = Label(master=self.dtypes_box, text="count", font=BASE_FONT)
        count_header.grid(row=1, column=5)
        self.make_row(daily.index, 'INDEX', 2)
        rownum = 3
        for key in daily.keys():
            series = daily[key]
            self.make_row(series, key, rownum)
            rownum += 1

    def clear(self):
        self.dtypes_box.destroy()
        self.dtypes_box = Frame(master=self, relief="groove", borderwidth=2)
        self.name_label.config(text="")
        self.type_label.config(text="")

    def short_date(self, dateindex):
        year = dateindex.year
        month = dateindex.month
        day = dateindex.day
        string = f"{year}-{month}-{day}"
        return string

    def make_row(self, series, name, row):
        name = Label(master=self.dtypes_box, text=name, font=SMALLER_FONT)
        name.grid(row=row, column=1)
        type = str(series.dtype)
        max = series.max()
        min = series.min()
        if type == 'datetime64[ns]':
            max = self.short_date(max)
            min = self.short_date(min)
        elif type == 'float64':
            max = round(max, 2)
            min = round(min, 2)
        type_label = Label(master=self.dtypes_box, text=type, font=SMALLER_FONT)
        type_label.grid(row=row, column=2)
        max_label = Label(master=self.dtypes_box, text=max, font=SMALLER_FONT)
        max_label.grid(row=row, column=3)
        min_label = Label(master=self.dtypes_box, text=min, font=SMALLER_FONT)
        min_label.grid(row=row, column=4)
        if hasattr(series, 'count'):
            count = series.count()
            count_label = Label(master=self.dtypes_box, text=str(count), font=SMALLER_FONT)
            count_label.grid(row=row, column=5)


class Logger(LabelFrame):
    def __init__(self, **kw):
        super().__init__(**kw, text="logs")
        self.clear_logs = Button(master=self,
                                 text="clear logs",
                                 font=SMALLER_FONT,
                                 width=7,
                                 command=lambda: self.clear_logs_click())
        self.clear_logs.grid(row=1, column=2)
        self.hide_logs = Button(master=self,
                                text="hide logs",
                                font=SMALLER_FONT,
                                width=7,
                                command=lambda: self.toggle_show_logs())
        self.hide_logs.grid(row=1, column=1)
        self.log_var = StringVar()
        self.log_var.set(RETRIEVER.report_to_string())
        self.log_text = Label(master=self, textvariable=self.log_var, font=BASE_FONT, justify="left")
        self.log_text.grid(row=2, columnspan=3)
        self.toggle_show_logs(force_hide=True)

    def update_logs(self):
        self.log_var.set(RETRIEVER.report_to_string())

    def clear_logs_click(self):
        RETRIEVER.logs = []
        self.update_logs()

    def toggle_show_logs(self, force_hide=False):
        if self.log_text.winfo_ismapped() or force_hide:
            self.log_text.grid_remove()
            self.clear_logs.grid_remove()
            self.hide_logs.config(text="show logs")
        else:
            self.log_text.grid()
            self.clear_logs.grid()
            self.hide_logs.config(text="hide logs")

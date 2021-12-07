
from tkinter import *

from src.retriever import gui

def begin_gui():
    window = Tk()
    window.title('Retriever GUI')

    # dimensions of the main window
    window.geometry("650x750")

    # start the retriever gui
    retriever_gui = gui.RetrieverGui(master=window, base_directory="data")
    retriever_gui.grid(row=1, column=1, sticky="NW")

    window.mainloop()


if __name__ == "__main__":
    begin_gui()
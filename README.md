# robinhood-bot-template
(soon to be) template for a Robinhood bot.
Contributers: Bryan, ...
Last updated: 11/5/21 by Bryan

You can use the "use template" button in the repo to create a new repo with this code as a starter.

It is highly encouraged to not only use this template as a template, but as well, clone the template repo, and create changes. Refinement of not only the code, but the README here will allow us to get a more
set in stone plan, and hopefully work out some of the details.

# Current State:

In it's current state all scripts are held in the directory "robinhoodbot"

# US_LIST_OF_SYMBOLS.csv
- a CSV file containing a comprehensive list of all stocks traded in the US. This includes not only large exchanges such as the NYSE or the NASDAQ, but as well small exchanges.
- This contains many tens of thousands of stocks which do not trade on robinhood

# filtered_stocks.txt
- a text file, where each line is a stock symbol. This is a subset of US_LIST_OF_SYMBOLS.csv. Each stock on this list should be tradeable on robinhood.

# main.py (tentative name)
- Contains the main RobinhoodBot class, it currently contains many useful methods for grabbing stock prices, buying stocks, selling stocks, and evaluating stock performance.
- IDEA: Rename (main.py -> robinhood_bot.py). Refactor the class to exclusively communicate with the robinhood api through robin_stocks. Some methods it may have:
  - Buying and Selling a stock. (We need to decide if ideal position size is determined in the method, or if the ideal position size is expected to be passed)
  - grabbing stock historical data and current price.
  
# IDEAS (very tentative):

## Currently Feasible
- create a 'strategy.py' module, in which a class is defined. This is where we will create our stategies:
- create a 'technicals.py' module, in which a class is defined. This class will have the functionality:
  - Given a specfic date and symbol. Methods which allow us to retrieve the latest technical indicators about a stock. (SMA, EMA, RSI, etc.)
- create a 'fundamentals.py' module, in which a class is defined. This class will have the functionality:
  - Various fundamental analysis of stocks. This could include sentiment analysis, or other ways of judging peoples feelings about a stock.
- some sort of backtesting functionality: (it may be worthwhile to avoid our own backtesting, and use another tool to design and backtest, this will limit future options though)
  - this could be in the form of a module with a backtesting class, giving us all the methods we need to backtest on historical data:
    - the backtesting module will most likely have some interplay with another script. 
    - this second script will most likely define things such as initial capital, buys, sells, as well as calculate profits.
    
## Currently less-feasible
- use some sort of machine learning to adjust parameters of strategies.
- use sentiment analysis on various stock discussion forums
- use machine learning to develop a strategy (I'm (bryan) thinking of Generative Adversarial Networks)
- stock options support? (options are a much more complex system than stocks, but allow for greater profit in exchange for greater risk)
    
# ROADMAP (very tentative):
  - Create a base template that allows easy creation of new strategies
  - Develop some of our own strategies
  - Test strategies using backtesting
  - Possible UI, perhaps allow users to import a strategy, or to design their own from within the Ui
  - Run it on a system, allow users to download and run on their systems. Allow users to 
  
 # RESOURCES
 - [basics of algorithmic trading](https://www.investopedia.com/articles/active-trading/101014/basics-algorithmic-trading-concepts-and-examples.asp)
 -  [Algorithmic trading strategies](https://www.youtube.com/watch?v=5iuF42s6zNo)
 - Soon I (Bryan) will have an untested but functional implementation of what I'm calling the "Golden Cross + RSI" strategy. This will be in another repo.
 

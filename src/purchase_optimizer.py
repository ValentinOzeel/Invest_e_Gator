from typing import str, int, List, Dict 
import pandas as pd

from secondary_module.yfinance_cache import session


class PurchaseOptimizer():
    def __init__(self, budget:int, ticker_list_ordered_priority:List, allocations:Dict, prices:dict, mode:str):
        # strict mode enables to buy the maximum amount of share one stock after the other (greedy approach) until the budget is exhausted.
        # progressive mode enable to buy 1 share per turn for each stock in priority order (round-robin approach) until the budget is exhausted.
        # rounds mode enables to attempt to buy a certain percentage of the allocated budget for each stock in each round (in ascending priority order)
        #             If the round_percentage is too small compared to the price of a share, it might prevent the purchase of any shares in that round. 
        #             To handle this, we can accumulate the budget allocated per stock over multiple rounds until it is sufficient to purchase at least one share.
        self.available_modes = ['strict', 'progressive', 'rounds']
        
        # Validate inputs
        self._verify_input(budget, ticker_list_ordered_priority, allocations, prices, mode)
        
        
        self.budget = budget
        self.ticker_priority = {ticker:priority_order+1 for priority_order, ticker in enumerate(ticker_list_ordered_priority)}
        self.allocations = allocations
        self.prices = prices
        self.mode = mode.lower() 

        self.ticker_yf_objects = {}

    ##########                      ##########
    ##########   INPUT VALIDATION   ##########
    ##########                      ##########
    
    def _validate_budget(self, budget):
        if budget <= 0:
            raise ValueError("'budget' attribute (args[0]) must be a positive value.")
        
    def _validate_allocations(self, allocations):
        if sum(allocations.values()) <= 0 or sum(allocations.values()) > 1:
            raise ValueError("The sum of ticker budget allocation proportions ('allocation' attribute, args[2]) must be comprised between 0 and 1.")
    
    def _validate_prices(self, prices):
        if any(price <= 0 for price in prices.values()):
            raise ValueError("All stock prices (dict's values) in the 'prices' attribute (args[3]) must be superior to 0.")
            
    def _validate_tickers_priority_and_allocations(self, ticker_list_priority, allocations, prices):
        # checks if all lists/dict keys contain the same unique elements
        
        allocations_keys=allocations.keys()
        price_keys=prices.keys() 

        if not set(ticker_list_priority) <= set(allocations_keys) and set(allocations_keys) <= set(ticker_list_priority):
            raise ValueError("The 'ticker_list_ordered_priority' attribute (args[1]) and the keys of 'allocations' attribute (args[2]) must contain the same unique ticker symbols.")

        if not set(ticker_list_priority) <= set(price_keys) and set(price_keys) <= set(ticker_list_priority):
            raise ValueError("The 'ticker_list_ordered_priority' attribute (args[1]) and the keys of 'prices' attribute (args[3]) must contain the same unique ticker symbols.")
        
        
    def _validate_mode(self, mode):
        if mode not in self.available_modes:
            raise ValueError(f"The 'mode' attribute (args[4]) value must be one of the following: {self.available_modes}")
        
    def _validate_tickers_exist_and_gather_yf_objects(self, tickers_list):
        for ticker in tickers_list:
            try:
                self.ticker_yf_objects[ticker] = yf.Ticker(ticker, session=session)
            except Exception as e:
                print(f"This ticker '{ticker}' either doesn't exist or isn't available via the yfinance API.\n{e}")
        
    def _verify_input(self, budget, ticker_list_priority, allocations, prices, mode):
        self._validate_budget(budget)
        self._validate_allocations(allocations)
        self._validate_prices(prices)
        self._validate_tickers_priority_and_allocations(ticker_list_priority, allocations, prices)
        self._validate_mode(mode)
        self._validate_tickers_exist_and_gather_yf_objects(ticker_list_priority)
        

    ##########             ##########
    ##########   BUILD DF  ##########
    ##########             ##########


    def _create_initial_df(self):
        # Convert inputs to a DataFrame for easy manipulation
        self.data = pd.DataFrame({
            'Ticker': self.ticker_priority.keys(),
            'Priority': self.ticker_priority.values(),
            'Allocation': self.allocation.values,
            'Price': self.prices.values,
        })  
         
    def _target_budget_per_stock(self):
        # Calculate target budget for each stock
        self.data['TargetBudget'] = self.data['Allocation'] * budget
    
    def _sort_by_priority(self):
        # Sort stocks by priority
        self.data = self.data.sort_values(by='Priority', ascending=False)

    def build_df(self, print_df=False):
        self._create_initial_df()
        self._target_budget_per_stock()
        if print_df:
            print(self.data)

    ##########                                      ##########
    ##########   PURCHASES OPTIMIZATION STRATEGIES  ##########
    ##########                                      ##########


       

        














# Example usage
ticker_prices = {'AAPL': 150, 'MSFT': 250, 'GOOGL': 2800}
budget = 10000
allocations = {'AAPL': 0.1, 'MSFT': 0.1, 'GOOGL': 0.1}
priorities = {'AAPL': 1, 'MSFT': 2, 'GOOGL': 3}

optimized_shares = optimize_stock_purchase(ticker_prices, budget, allocations, priorities)
print(optimized_shares)
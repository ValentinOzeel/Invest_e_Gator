from typing import List, Dict 
import pandas as pd
import copy

# If yfinance usage to get ticker price
#from secondary_modules.yfinance_cache import session




class PurchaseOptimizer():
    def __init__(self, budget:int, ticker_priority_order:List, allocations:Dict, prices:dict, mode:str='rounds'):
        
        # progressive mode enable to buy 1 share per turn for each stock in priority order (round-robin approach) until the budget is exhausted.
        # rounds mode enables to attempt to buy a certain percentage of the allocated budget for each stock in each round (in ascending priority order)
        #             If the round_percentage is too small compared to the price of a share, it might prevent the purchase of any shares in that round. 
        #             To handle this, we can accumulate the budget allocated per stock over multiple rounds until it is sufficient to purchase at least one share.
        self.available_modes = ['strict', 'progressive', 'rounds']
        
        ## yfinance doesn't provide real time price so let the user provide stocks prices
        #self.ticker_yf_objects = {}
        
        # Validate inputs
        self.validate_input(budget, ticker_priority_order, allocations, prices, mode)
        
        # Set attribute if inputs are valid
        self.budget = budget
        self.ticker_priority_order = ticker_priority_order
        self.allocations = allocations
        self.prices = prices
        self.mode = mode.lower() 
        
        
        # Build the data df
        self.build_df()



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
            raise ValueError("The 'ticker_priority_order' attribute (args[1]) and the keys of 'allocations' attribute (args[2]) must contain the same unique ticker symbols.")

        if not set(ticker_list_priority) <= set(price_keys) and set(price_keys) <= set(ticker_list_priority):
            raise ValueError("The 'ticker_priority_order' attribute (args[1]) and the keys of 'prices' attribute (args[3]) must contain the same unique ticker symbols.")
        
        
    def _validate_mode(self, mode):
        if mode not in self.available_modes:
            raise ValueError(f"The 'mode' attribute (args[4]) value must be one of the following: {self.available_modes}")
        
    ## yfinance doesn't provide real time price so let the user provide stocks prices
    #def _validate_tickers_exist_and_gather_yf_objects(self, tickers_list):
    #    for ticker in tickers_list:
    #        try:
    #            self.ticker_yf_objects[ticker] = yf.Ticker(ticker, session=session)
    #        except Exception as e:
    #            print(f"This ticker '{ticker}' either doesn't exist or isn't available via the yfinance API.\n{e}")
        
    def validate_input(self, budget, ticker_list_priority, allocations, prices, mode):
        self._validate_budget(budget)
        self._validate_allocations(allocations)
        self._validate_prices(prices)
        self._validate_tickers_priority_and_allocations(ticker_list_priority, allocations, prices)
        self._validate_mode(mode)
        #self._validate_tickers_exist_and_gather_yf_objects(ticker_list_priority)
        

    ##########             ##########
    ##########   BUILD DF  ##########
    ##########             ##########


    def _create_initial_df(self):
           
        # Build the df via a list of dict entries in the priority order
        self.data = pd.DataFrame([
            {
                'Ticker':ticker,
                'Priority': i+1,
                'Allocation': self.allocations[ticker],
                'Price': self.prices[ticker],
                'Shares': 0
            }
            for i, ticker in enumerate(self.ticker_priority_order)
        ])       
            
         
    def _target_budget_per_stock(self):
        # Calculate target budget for each stock
        self.data['TargetBudget'] = self.data['Allocation'] * self.budget
    
    def _sort_by_priority(self):
        # Sort stocks by priority
        self.data = self.data.sort_values(by='Priority', ascending=False)
    
    def _print_data_df(self, flag:bool=False):
        if flag: 
            print(self.data, '\n\n')

    def build_df(self, print_df=True):
        self._create_initial_df()
        self._target_budget_per_stock()
        #self._sort_by_priority()
        self._print_data_df(print_df)

    ##########                                      ##########
    ##########   PURCHASES OPTIMIZATION STRATEGIES  ##########
    ##########                                      ##########

    def _df_results(self, df, remaining_budget):
        df['FinalAllocation'] = round((df['Shares'] * df['Price']) / self.budget, 2)
        return df, remaining_budget
       
    def strict_optimizer(self, approved_alloc_surplus:float=0.05):
        '''
        strict mode enables to buy the maximum amount of shares to reach the Allocation +/- 'approved_alloc_surplus' % for each stock in order of priority (greedy approach) until the budget is exhausted. 
        '''
        remaining_budget = copy.deepcopy(self.budget)
        results = copy.deepcopy(self.data)
        
        # Iterate over ticker symbol
        for idx, row in self.data.iterrows():
            # Calculate the maximum_allowable_cost considering the 'approved_alloc_diff'
            max_allowable_cost = (row['Allocation'] + approved_alloc_surplus) * self.budget
            # Get maximum amount of shares to buy up to the max_allowable_cost and the associated cost
            max_shares = max_allowable_cost // row['Price']
            cost = max_shares * row['Price']
            # Buy the max amount of share if remaining budget >= cost
            if remaining_budget >= cost:
                results.at[idx, 'Shares'] = max_shares
                remaining_budget -= cost
            # If remaining budget < cost then allocate the max amount of shares with the remaining budget
            else:
                max_shares = remaining_budget // row['Price']
                results.at[idx, 'Shares'] = max_shares
                remaining_budget -= max_shares * row['Price']
        
        return self._df_results(results, remaining_budget)
            





# Example usage
budget = 10000
ticker_list = ['AAPL', 'MSFT', 'GOOGL']
ticker_allocations = {'AAPL': 0.5, 'MSFT': 0.1, 'GOOGL': 0.1}
ticker_prices = {'AAPL': 150, 'MSFT': 250, 'GOOGL': 1100}
mode = 'strict'


optim = PurchaseOptimizer(budget, ticker_list, ticker_allocations, ticker_prices, mode=mode)
results, remaining_budget = optim.strict_optimizer()
print(results, '\n\n', f'Initial budget: {budget}\n Remaining budget: {remaining_budget}')
#optimized_shares = optimize_stock_purchase(ticker_prices, budget, allocations, priorities)
#print(optimized_shares)
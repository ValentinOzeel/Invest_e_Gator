from typing import List, Dict 
import pandas as pd
import copy

from ticker import Ticker

class PurchaseOptimizer():
    def __init__(self, budget:int, ticker_priority_order:List, allocations:Dict, prices:dict=None, mode:str='rounds'):
        self.available_modes = ['strict', 'progressive', 'rounds']
        
        ## yfinance doesn't provide real time price so let the user provide stocks prices
        #self.ticker_yf_objects = {}
        
        # Set attribute if inputs are valid
        self.global_budget = budget
        self.ticker_priority_order = ticker_priority_order
        self.allocations = allocations
        self.prices = prices if prices else self.get_current_prices()
        self.mode = mode.lower() 
        
        # Validate inputs
        self.validate_input(self.global_budget, self.ticker_priority_order, self.allocations, self.prices, self.mode)
        
        
        # Build the data df
        self.build_df()



    ##########                      ##########
    ##########   INPUT VALIDATION   ##########
    ##########                      ##########
    
    def _validate_budget(self, budget):
        if budget <= 0:
            raise ValueError("'budget' attribute (args[0]) must be a positive value.")
        
    def _validate_allocations(self, allocations):
        if round(sum(allocations.values()), 1) <= 0 or round(sum(allocations.values()), 1) > 1:
            raise ValueError("The sum of ticker budget allocation proportions ('allocation' attribute, args[2]) must be comprised between 0 and 1.")
    
    def _validate_prices(self, prices):
        if not prices:
            pass
        elif any(price <= 0 for price in prices.values()):
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
        
    def get_current_prices(self):
        return {ticker:Ticker(ticker).current_price for ticker in self.ticker_priority_order}
    

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
        self.data['TargetBudget'] = self.data['Allocation'] * self.global_budget
    
    def _sort_by_priority(self):
        # Sort stocks by priority
        self.data = self.data.sort_values(by='Priority', ascending=False)
    
    def _print_data_df(self, flag:bool):
        if flag: 
            print(self.data, '\n\n')

    def build_df(self, flag_print_df=False):
        self._create_initial_df()
        self._target_budget_per_stock()
        #self._sort_by_priority()
        self._print_data_df(flag_print_df)

    ##########                                      ##########
    ##########   PURCHASES OPTIMIZATION STRATEGIES  ##########
    ##########                                      ##########

    def _df_results(self, df, remaining_budget):
        df['FinalBudget'] = round(df['Shares'] * df['Price'], 2)
        df['FinalAllocation'] = round(df['FinalBudget'] / self.global_budget, 2)
        return df, round(remaining_budget, 0)
    
    def _get_copy_budget_and_data(self):
        return copy.deepcopy(self.global_budget), copy.deepcopy(self.data)
    
    def _compute_max_allowable_cost(self, row, approved_alloc_surplus):
        # Calculate the maximum_allowable_cost considering the 'approved_alloc_diff'
        return round((row['Allocation'] + approved_alloc_surplus) * self.global_budget, 2)
    
    def _compute_max_shares_per_ticker(self, approved_alloc_surplus):
        # Compute max_allowable_cost considering approved surplus for each ticker
        max_allowable_costs = {row['Ticker'] : self._compute_max_allowable_cost(row, approved_alloc_surplus) for _, row in self.data.iterrows()}
        # Compute max shares according to max_allowable_costs
        max_shares = {row['Ticker'] : max_allowable_costs[row['Ticker']] // row['Price'] for _, row in self.data.iterrows()} 
        return max_shares
    
    def strict_optimizer(self, approved_alloc_surplus:float=0.05):
        '''
        strict mode enables to buy the maximum amount of shares to reach the Allocation +/- 'approved_alloc_surplus' % for each stock in order of priority (greedy approach) until the budget is exhausted. 
        '''
        remaining_budget, results = self._get_copy_budget_and_data()
        # For each ticker, compute max_allowable_cost and max_shares considering approved surplus
        max_shares_per_ticker = self._compute_max_shares_per_ticker(approved_alloc_surplus)
        
        # Iterate over ticker symbol
        for idx, row in self.data.iterrows():
            ticker = row['Ticker']
            cost = max_shares_per_ticker[ticker] * row['Price']
            # Buy the max amount of share if remaining budget >= cost
            if remaining_budget >= cost:
                results.at[idx, 'Shares'] = max_shares_per_ticker[ticker]
                remaining_budget -= cost
            # If remaining budget < cost then allocate the max amount of shares with the remaining budget
            else:
                max_shares = remaining_budget // row['Price']
                results.at[idx, 'Shares'] = max_shares
                remaining_budget -= max_shares * row['Price']
        return self._df_results(results, remaining_budget)
            

    def progressive_optimizer(self, approved_alloc_surplus:float=0.05):
        
        '''
        progressive mode enables to buy 1 share per turn for each stock in priority order (round-robin approach) considereng the max allocation until the budget is exhausted.
        '''
        
        remaining_budget, results = self._get_copy_budget_and_data()
        # For each ticker, compute max_allowable_cost and max_shares considering approved surplus
        max_shares = self._compute_max_shares_per_ticker(approved_alloc_surplus)
        # List of tickers that have reached max allocation
        reached_max_allocation = []
        
        # Progressive allocation using round-robin approach
        while remaining_budget >= self.data['Price'].min():
            for idx, row in self.data.iterrows():
                # Next ticker if haven't enough left to buy a share
                if row['Price'] > remaining_budget:
                    continue
                # Next ticker if max allocation have been reached
                if results.at[idx, 'Shares'] >= max_shares[row['Ticker']]:
                    if row['Ticker'] not in reached_max_allocation : reached_max_allocation.append(row['Ticker'])
                    continue
                # Implement a share and deduce price from remaining budget
                results.at[idx, 'Shares'] += 1
                remaining_budget -= row['Price']  
            # Break the loop if all tickers have reached max allocation even if there is some remaining budget left
            if all(ticker in reached_max_allocation for ticker in self.ticker_priority_order):
                break
            
        return self._df_results(results, remaining_budget)
            
    def rounds_optimizer(self, round_proportion:float, approved_alloc_surplus:float=0.05):
        '''
        Progressive Allocation in Rounds with Accumulated Budget. 
        In each round: 
        - Allocate a portion of the target budget (round_proportion) for each ticker. 
        - Accumulate this allocation until it's sufficient to buy at least one share. 
        - Once enough budget is accumulated for a ticker, buy as many shares as possible and deduct the cost from the accumulated budget.
        '''

        def _get_shares_to_buy_relative_to_remaining_budget(accumulated_amount, share_price, remaining_budg):
            # Start with share_to_buy, then try to decrement -1 share until cost of shares <= remaining_budget else return None
            shares_to_buy = accumulated_amount // share_price
            while shares_to_buy > 0:
                cost = shares_to_buy*share_price
                if cost <= remaining_budg:
                    return shares_to_buy 
                shares_to_buy -= 1
            return None
            
        remaining_budget, results = self._get_copy_budget_and_data()
        # For each ticker, compute max_allowable_cost and max_shares considering approved surplus
        max_shares = self._compute_max_shares_per_ticker(approved_alloc_surplus)
        # Store accumulated budget per ticker
        accumulated_budget = {ticker:0 for ticker in self.ticker_priority_order}
        # List of tickers that have reached max allocation
        reached_max_allocation = []
                
        # Perform rounds of purchases
        while remaining_budget >= self.data['Price'].min():
            done = []
            for idx, row in self.data.iterrows():
                ticker = row['Ticker']
                # Next ticker if in reacher_max_allocation or if haven't enough left to buy a share
                if (ticker in reached_max_allocation) or (row['Price'] > remaining_budget):
                    done.append(idx)
                    continue
                # Next ticker if max allocation have been reached
                if results.at[idx, 'Shares'] >= max_shares[ticker]:
                    if ticker not in reached_max_allocation : reached_max_allocation.append(ticker)
                    done.append(idx)
                    continue
                
                # Compute target budget with surplus
                target_budget_with_surplus = (row['Allocation'] + approved_alloc_surplus) * self.global_budget
                # Calculate the budget for the current round
                round_budget = target_budget_with_surplus * round_proportion
                # Accumulate the budget
                accumulated_budget[ticker] += round_budget   

                # Next ticker if we cannot buy a single share yet with the accumulated budget
                if accumulated_budget[ticker] <= row['Price']:
                    done.append(idx)
                    continue
                else:
                    # Determine the number of shares to buy with the accumulated budget
                    shares_to_buy = _get_shares_to_buy_relative_to_remaining_budget(accumulated_budget[ticker], row['Price'], remaining_budget)
                    if shares_to_buy:
                        # Calculate associated cost and pdate results/accumulated_budget/remaining_budget
                        cost = shares_to_buy * row['Price']
                        results.at[idx, 'Shares'] += shares_to_buy
                        accumulated_budget[ticker] -= cost
                        remaining_budget -= cost
                    # Otherwise add to reached_max_allocation list
                    elif ticker not in reached_max_allocation:
                        reached_max_allocation.append(ticker)
                        
            # Break the loop if all tickers have reached max allocation even if there is some remaining budget left
            if all(ticker in reached_max_allocation for ticker in self.ticker_priority_order):
                break
            
            # if all rows are done
            if pd.Index(done).equals(self.data.index):
                break  
        return self._df_results(results, remaining_budget)



        
        
if __name__ == "__main__":   
    # Example usage
    budget = 50000
    ticker_list = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'DNA']
    ticker_allocations = {'AAPL': 0.16, 'MSFT': 0.15, 'GOOGL': 0.12, 'NVDA': 0.25, 'TSLA': 0.22, 'DNA': 0.1}
    ticker_prices = {'AAPL': 150, 'MSFT': 250, 'GOOGL': 1000, 'NVDA': 133, 'TSLA': 188, 'DNA': 0.4}
    modes = ['strict', 'progressive', 'rounds']
    print('\n')

    optim = PurchaseOptimizer(budget, ticker_list, ticker_allocations, mode=modes[0])
    #optim = PurchaseOptimizer(budget, ticker_list, ticker_allocations, ticker_prices, mode=modes[0])
    strict_results, strict_remaining_budget = optim.strict_optimizer(approved_alloc_surplus=0.01)
    print('STRICT MODE:\n\n', strict_results, '\n\n', f'Initial budget: {budget}\n Remaining budget: {strict_remaining_budget}', '\n----------\n')

    optim = PurchaseOptimizer(budget, ticker_list, ticker_allocations, mode=modes[1])
    #optim = PurchaseOptimizer(budget, ticker_list, ticker_allocations, ticker_prices, mode=modes[1])
    progressive_results, progressive_remaining_budget = optim.progressive_optimizer(approved_alloc_surplus=0.01)
    print('PROGRESSIVE MODE:\n\n', progressive_results, '\n\n', f'Initial budget: {budget}\n Remaining budget: {progressive_remaining_budget}', '\n----------\n')

    optim = PurchaseOptimizer(budget, ticker_list, ticker_allocations, mode=modes[2])
    #optim = PurchaseOptimizer(budget, ticker_list, ticker_allocations, ticker_prices, mode=modes[2])
    round_results, round_remaining_budget = optim.rounds_optimizer(0.1, approved_alloc_surplus=0.01)
    print('ROUNDS MODE:\n\n', round_results, '\n\n', f'Initial budget: {budget}\n Remaining budget: {round_remaining_budget}', '\n----------\n')
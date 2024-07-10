from typing import List, Union
from datetime import datetime
import pandas as pd
import copy

from Invest_e_Gator.src.secondary_modules.currency_conversion import currency_conversion
from Invest_e_Gator.src.ticker import Ticker
from Invest_e_Gator.src.constants import available_metrics

class PortfolioMetrics():
    def __init__(self, transactions_df:pd.DataFrame, base_currency:str, start_date:datetime=None, end_date:datetime=None, today:bool=False):
        self.transactions_df = transactions_df
        self.base_currency = base_currency   
        self.today = today        
        # Get days range from start to end
        self.all_dates = self._get_all_dates(start_date, end_date) if not self.today else [datetime.now()]

        self.df_metrics = None
        
    def _get_all_dates(self, start_date:datetime, end_date:datetime):
        if start_date and end_date:
            return pd.date_range(start_date, start_date)
        else:
            # Create a date range from the first to the last transaction date
            start_d = self.transactions_df['date_hour'].min().date() + pd.Timedelta(days=1)
            end_d = self.transactions_df['date_hour'].max().date() + pd.Timedelta(days=1)
            return pd.date_range(start_d, end_d) 
        
    def compute_metrics(self, advanced_metrics:List=None):
                
        # Dict metric : bool_value
        metrics_activation = {}
            
        # build metrics_activation according to privided metrics in list_metrics
        if advanced_metrics:
            # Validate metrics
            if not all([metric in available_metrics for metric in advanced_metrics]):
                raise ValueError(f'All metrics provided as list should be found in the available metrics: {available_metrics}')
            
            metrics_activation = {metric:metric in advanced_metrics for metric in available_metrics}


                
        self.df_metrics = self._compute_general_metrics()
        return self.df_metrics
        
    def _compute_ticker_realized_loss(self, buys:pd.DataFrame, sales:pd.DataFrame):
        
        df_buys, df_sales = copy.deepcopy(buys), copy.deepcopy(sales)

        df_buys = df_buys[df_buys['transaction_action'] == 'real']
        df_sales = df_sales[df_sales['transaction_action'] == 'real']
        
        df_buys['remaining_shares'] = df_buys['n_shares']

        realized_gains_losses = []

        for _, sale in df_sales.iterrows():
            shares_sold = sale['n_shares']
            sale_price = sale['share_price_base_currency']

            remaining_shares_sold = shares_sold

            while remaining_shares_sold > 0 and not df_buys[df_buys['remaining_shares'] > 0].empty:
                # Find the oldest buy with remaining quantity
                for idx, buy in df_buys[df_buys['remaining_shares'] > 0].iterrows():
                    shares_bought = buy['remaining_shares']
                    buy_price = buy['share_price_base_currency']

                    if remaining_shares_sold <= shares_bought:
                        # All of the remaining sale quantity can be matched with this buy
                        realized = (sale_price - buy_price) * remaining_shares_sold
                        realized_gains_losses.append(realized)
                        df_buys.at[idx, 'remaining_shares'] -= remaining_shares_sold
                        remaining_shares_sold = 0
                    else:
                        # Only part of the sale quantity can be matched with this buy
                        realized = (sale_price - buy_price) * shares_bought
                        realized_gains_losses.append(realized)
                        df_buys.at[idx, 'remaining_shares'] = 0
                        remaining_shares_sold -= shares_bought

        return sum(realized_gains_losses)


    def _compute_returns(self, value, realized, invested):
        #print(f'({value} + {realized} - {invested}) / {invested} = {(value + realized - invested) / invested}')
        return (value + realized - invested) / invested
            
    def _compute_general_metrics(self):
        # Initialize a dict to store daily metrics
        daily_metrics = {}
        
        # Iterate over each date
        for selected_date in self.all_dates:
            # Filter out transaction after selected_date
            selected_transactions = self.transactions_df[self.transactions_df['date_hour'] <= selected_date]
            # Initialize dictionaries to store daily metrics
            position_held = {}                  # n financial object helg (exemple: n of shares held)
            position_values = {}                # Daily ticker position value
            position_total_invested = {}        # Daily ticker position invested
            position_realizeds_losses = {}      # Daily ticker realized gains/losses
            position_cost_average = {}          # Daily ticker cost average per share
            position_pl = {}                    # Daily position P/L
            position_ratio_invested = {}        # Daily ticker invested relative to total amount invested
            position_ratio_pf_value = {}        # Daily ticker position value relative to total pf value

            total_value = 0
            total_invested = 0
            total_realized = 0
            
            # Calculate total value and individual stock metrics
            for ticker in selected_transactions['ticker'].unique():
                # Get transactions corresponding to ticker
                ticker_transactions = selected_transactions[selected_transactions['ticker'] == ticker]
                # Get buys and sales transactions
                buys = ticker_transactions[ticker_transactions['transaction_type'] == 'buy']
                sales = ticker_transactions[ticker_transactions['transaction_type'] == 'sale']
                
                # Total share held at day
                quantity = ticker_transactions['quantity'].sum()
                # Total amount investment at day
                total_cost_base_currency = ticker_transactions['transact_amount_base_currency'].sum()
                # Create Ticker object
                ticker_obj = Ticker(ticker)
                print(f'CLOSING PRICE FOR TICKER {ticker}')
                
                # Total invested (check if real transaction)
                invested = ticker_transactions[ticker_transactions['transaction_action'] == 'real']['transact_amount_base_currency'].sum()
                #invested = ticker_transactions['transact_amount_base_currency'].sum()
                # Cost average per share
                cost_average = total_cost_base_currency / quantity if quantity else 0
                # Calculate realized gains/losses
                realized = self._compute_ticker_realized_loss(buys, sales)
                # Get day value in base currency
                print(f'QUANTITY HELD {ticker} = {quantity}')
                
                try:
                    day_value_base_currency = currency_conversion(
                        amount=ticker_obj.get_closing_price(selected_date), 
                        date_obj=selected_date, 
                        currency=ticker_obj.currency.lower(), 
                        target_currency=self.base_currency,
                        today=self.today
                    )
                    # Calculate day position value
                    position_value_base_currency = quantity * day_value_base_currency
                except Exception as e:
                    print(e)
                    print(f'{ticker} might have been delisted.')
                    position_value_base_currency = 0
                
                # Update dictionnaries
                position_held[ticker] = quantity
                position_values[ticker] = position_value_base_currency
                position_total_invested[ticker] = invested
                position_cost_average[ticker] = cost_average
                position_realizeds_losses[ticker] = realized
                # Update total_value, total_invested and total_realized
                total_value += position_value_base_currency
                total_invested += invested
                total_realized += realized

            # Calculate percentage portfolio value and percentage invested
            for ticker in position_values:
                #print(f'\n{ticker}')
                position_ratio_pf_value[ticker] = position_values[ticker] / total_value if total_value != 0 else 0
                position_ratio_invested[ticker] = position_total_invested[ticker] / total_invested if total_invested != 0 else 0
                position_pl[ticker] = self._compute_returns(position_values[ticker], position_realizeds_losses[ticker], position_total_invested[ticker])


            print(f'\n{selected_date} : positions {position_held}')
            daily_metrics[selected_date] = {
                'position_held': position_held, 
                'position_values': position_values, 
                'position_invested': position_total_invested,
                'position_cost_average': position_cost_average, 
                'position_realizeds_losses': position_realizeds_losses, 
                'position_pl': position_pl,
                'position_ratio_invested': position_ratio_invested, 
                'position_ratio_pf_value': position_ratio_pf_value, 
                'total_value': total_value,
                'total_invested': total_invested, 
                'total_realized': total_realized,
                'total_pl': self._compute_returns(total_value, total_realized, total_invested)
                }
            
        
        return pd.DataFrame.from_dict(daily_metrics, orient='index')
    

    

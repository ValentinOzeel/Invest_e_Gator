from typing import Union
from datetime import datetime
import pandas as pd

from Invest_e_Gator.src.secondary_modules.currency_conversion import currency_conversion
from Invest_e_Gator.src.ticker import Ticker

class PortfolioMetrics():
    def __init__(self, transactions_df:pd.DataFrame, base_currency:str, start_date:datetime=None, end_date:datetime=None):
        self.transactions_df = transactions_df
        self.base_currency = base_currency   
        
        # Get days range from start to end
        self.all_dates = self._get_all_dates(start_date, end_date)

        self.df_metrics = None
        
    def _get_all_dates(self, start_date:datetime, end_date:datetime):
        if start_date and end_date:
            return pd.date_range(start_date, start_date)
        else:
            # Create a date range from the first to the last transaction date
            start_d = self.transactions_df['date_hour'].min().date() + pd.Timedelta(days=1)
            end_d = self.transactions_df['date_hour'].max().date() + pd.Timedelta(days=1)
            return pd.date_range(start_d, end_d) 
        
    def compute_metrics(self):

        df = self._compute_invested_and_value()
        df = self._compute_returns(df)
        return df
        
    def _compute_ticker_realized_gain_loss(self, ticker_transactions):
        buys = ticker_transactions[ticker_transactions['transaction_type'] == 'buy']
        sales = ticker_transactions[ticker_transactions['transaction_type'] == 'sale']
        
        # Calculate realized gains/losses for sales
        realized = 0
        for _, sale in sales.iterrows():
            sale_quantity = sale['n_shares']
            sale_price = sale['share_price']
            # Calculate cost basis for the shares sold
            while sale_quantity > 0 and not buys.empty:
                first_buy = buys.iloc[0]
                buy_quantity = first_buy['n_shares']
                buy_price = first_buy['share_price']
                
                if buy_quantity <= sale_quantity:
                    realized += buy_quantity * (sale_price - buy_price)
                    sale_quantity -= buy_quantity
                    buys = buys.iloc[1:]  # Remove the processed buy transaction
                else:
                    realized += sale_quantity * (sale_price - buy_price)
                    buys.at[buys.index[0], 'n_shares'] -= sale_quantity
                    sale_quantity = 0
        return realized

    def _compute_invested_and_value(self):
        # Initialize a dict to store daily metrics
        daily_metrics = {}

        # Iterate over each date
        for selected_date in self.all_dates:
            # Filter out transaction after selected_date
            selected_transactions = self.transactions_df[self.transactions_df['date_hour'] <= selected_date]
            # Initialize dictionaries to store daily metrics
            position_values = {}                # Daily ticker position value
            position_invested = {}              # Daily ticker position invested
            position_cost_average = {}          # Daily ticker cost average per share
            position_ratio_invested = {}        # Daily ticker invested relative to total amount invested
            position_ratio_pf_value = {}        # Daily ticker position value relative to total pf value
            position_realized_gains_losses = {} # Daily ticker realized gains/losses

            total_value = 0
            total_invested = 0
            total_realized = 0
            
            # Calculate total value and individual stock metrics
            for ticker in selected_transactions['ticker'].unique():
                # Get transactions corresponding to ticker
                ticker_transactions = selected_transactions[selected_transactions['ticker'] == ticker]
                # Total share held at day
                quantity = ticker_transactions['quantity'].sum()
                # Total cost investment at day
                total_cost_base_currency = ticker_transactions['transact_cost_base_currency'].sum()
                # Create Ticker object
                ticker_obj = Ticker(ticker)
                # Get day value in base currency
                day_value_base_currency = currency_conversion(
                    amount=ticker_obj.get_closing_price(selected_date), 
                    date_obj=selected_date, 
                    currency=ticker_obj.currency.lower(), 
                    target_currency=self.base_currency
                )
                
                # Cost average per share
                cost_average = total_cost_base_currency / quantity if quantity else 0
                # Calculate realized gains/losses
                realized = self._compute_ticker_realized_gain_loss(ticker_transactions)
                # Calculate day position value
                position_value_base_currency = quantity * day_value_base_currency
                # Update dictionnaries
                position_values[ticker] = position_value_base_currency
                position_invested[ticker] = total_cost_base_currency
                position_cost_average[ticker] = cost_average
                position_realized_gains_losses[ticker] = realized
                # Update total_value, total_invested and total_realized
                total_value += position_value_base_currency
                total_invested += total_cost_base_currency
                total_realized += realized

            # Calculate percentage portfolio value and percentage invested
            for ticker in position_values:
                position_ratio_pf_value[ticker] = position_values[ticker] / total_value if total_value != 0 else 0
                position_ratio_invested[ticker] = position_invested[ticker] / total_invested if total_invested != 0 else 0
                
                
                COMPUTE PL POSITION HERE
                position_pl = (position_values[ticker] + position_realized_gains_losses[ticker] - 
                
                 (self.total_portfolio_value + self.total_realized_gains_losses - self.total_portfolio_invested) / self.total_portfolio_invested

            daily_metrics[selected_date] = {
                'position_values': position_values,
                'position_invested': position_invested,
                'position_cost_average': position_cost_average,
                'position_realized_gains_losses': position_realized_gains_losses,
                'position_ratio_invested': position_ratio_invested,
                'position_ratio_pf_value': position_ratio_pf_value,
                'total_value': total_value,
                'total_invested': total_invested,
                'total_realized': total_realized
                }
            
        
        return pd.DataFrame.from_dict(daily_metrics, orient='index')
    

    def _compute_returns(self, df):
        df['pl'] = (df['total_value'] - df['total_invested'])/df['total_invested']
        return df
    
    def compute_returns(self):
        Portfolio Return=Total Portfolio InvestedTotal Portfolio Value+Total Realized Gains/Losses−Total Portfolio Invested​
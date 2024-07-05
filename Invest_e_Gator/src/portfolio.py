from typing import Dict, List, Union
import pandas as pd
from forex_python.converter import CurrencyRates
from datetime import datetime

from Invest_e_Gator.src.secondary_modules.pydantic_valids import validate_load_csv, validate_tags_dict
from Invest_e_Gator.src.transactions import Transaction
from Invest_e_Gator.src.ticker import Ticker

class Portfolio:
    def __init__(self, base_currency: str = 'usd'):
        self.base_currency = base_currency.lower()
        self.currency_conversion = CurrencyRates()
        
        self.transactions_df = pd.DataFrame(columns=['date_hour', 
                                                     'transaction_type',  
                                                     'ticker', 'name', 
                                                     'share_currency', 'share_price', 'quantity'
                                                     'fee',
                                                     'transact_cost_share_currency', 'transact_cost_expense_currency', 'transact_cost_base_currency'])

    def _currency_conversion(self, amount:float, date_obj:datetime, currency:str, target_currency:str):
        return amount if currency == self.base_currency else amount * self.currency_conversion.get_rate(currency, target_currency, date_obj)
        
    def _get_ticker_tags(self, ticker:str, tags_dict:Dict[str, List]):
        if not tags_dict:
            return None
        return tags_dict[ticker] if tags_dict.get(ticker) else None
            
        
    def add_transaction(self, transaction: Transaction, tags_dict:Dict[str, List]=None):
        if not isinstance(transaction, Transaction): raise ValueError('In add_transaction, transaction parameters should be a Transaction object.')
        validate_tags_dict(tags_dict=tags_dict)
        
        # Validate ticker_symbol and get long name
        ticker_obj = Ticker(ticker_name=transaction.ticker)
        ticker_long_name = ticker_obj.name
        ticker_tags = self._get_ticker_tags(transaction.ticker, tags_dict)
        
        # Check if exepense currency == base currency, otherwise make conversion
        if transaction.expense_currency != self.base_currency:
            cr = CurrencyRates()
            transact_cost_base_currency = transaction.transaction_cost_expense_currency * cr.get_rate(transaction.expense_currency, 
                                                                                                      self.base_currency, 
                                                                                                      transaction.date_hour)
        
        # Add transaction in dataframe (convert currency + add name + add n_shares_price)
        self.transactions_df = self.transactions_df._append({
            'date_hour': transaction.date_hour,
            'transaction_type': transaction.transaction_type,
            'ticker': transaction.ticker,
            'name': ticker_long_name,
            'tags': ticker_tags,
            'share_currency': transaction.share_currency,
            'share_price': transaction.share_price,
            'quantity': transaction.quantity,
            #'expense_currency': transaction.expense_currency,
            'fee': transaction.fee,
            #'transact_cost_share_currency': transaction.transaction_cost_share_currency,
            #'transact_cost_expense_currency': transaction.transaction_cost_expense_currency,
            'transact_cost_base_currency': transact_cost_base_currency if transact_cost_base_currency else transaction.transaction_cost_expense_currency
        }, ignore_index=True)
        
    def load_transactions_from_csv(self, file_path: str, tags_dict:Dict[str, List]=None):
        validate_load_csv(file_path=file_path, tags_dict=tags_dict)
        # Read csv
        transactions_df = pd.read_csv(file_path, parse_dates=['date_hour'])
        # Transaform rows as Transaction obj
        for _, row in transactions_df.iterrows():
            self.add_transaction(Transaction(
                date_hour=row['date_hour'],
                transaction_type=row['transaction_type'],
                ticker=row['ticker'],
                n_shares=row['n_shares'],
                share_price=row['share_price'],
                share_currency=row['share_currency'],
                expense_currency=row['expense_currency'],
                fee=row['fee']
                ), 
                tags_dict
            )

        
    def process_transactions(self):
        # Create a date range from the first to the last transaction date
        start_date = self.transactions_df['date_hour'].min().date()
        end_date = self.transactions_df['date_hour'].max().date()
        all_dates = pd.date_range(start_date, end_date)
        
        # Initialize a list to store daily metrics
        daily_metrics = []

        # Iterate over each date
        for current_date in all_dates:
            current_transactions = self.transactions_df[self.transactions_df['date_hour'] <= current_date]

            # Initialize dictionaries to store daily metrics
            security_values = {}                # Daily ticker position value
            security_invested = {}              # Daily ticker position invested
            security_cost_average = {}          # Daily ticker cost average per share
            security_percentages_invested = {}  # Daily ticker invested relative to total amount invested
            security_percentages_pf_value = {}  # Daily ticker position value relative to total pf value

            total_value = 0
            total_invested = 0
            
            # Calculate total value and individual stock metrics
            for ticker in current_transactions['ticker'].unique():
                ticker_transactions = current_transactions[current_transactions['ticker'] == ticker]

                # Total share held at day
                quantity = ticker_transactions['quantity'].sum()
                # Total cost investment at day
                total_cost_base_currency = ticker_transactions['transact_cost_base_currency'].sum()
                # Cost average per share
                cost_average = total_cost_base_currency / quantity
                
                ticker_obj = Ticker(ticker)
                # Get day value in base currency
                day_value_base_currency = self._currency_conversion(
                    amount=ticker_obj.get_closing_price(current_date), 
                    date_obj=current_date, 
                    currency=ticker_obj.currency, 
                    target_currency=self.base_currency
                )
                # Calculate day position value
                position_value_base_currency = quantity * day_value_base_currency
                # Update dictionnaries
                security_values[ticker] = position_value_base_currency
                security_invested[ticker] = total_cost_base_currency
                security_cost_average[ticker] = cost_average
                # Update total_value and total_invested
                total_value += position_value_base_currency
                total_invested += total_cost_base_currency



            # Calculate percentage portfolio value and percentage invested
            for ticker in security_values:
                security_percentages_pf_value[ticker] = security_values[ticker] / total_value if total_value != 0 else 0
                security_percentages_invested[ticker] = security_invested[ticker] / total_invested if total_invested != 0 else 0


            
            
        create portfolio_df
        
        Holdingds, holding_pct, holding_value, holdings_invested
        
        iterate over df_transaction rows inverted:
            at the time of the date, gathe all stock held, their % of all holdings, their value at the time and the amount invested


    def get_portfolio_value(self, date: Union[str, datetime] = datetime.now()) -> float:
        total_value = 0.0
        for ticker, quantity in self.holdings.items():
            ticker_obj = Ticker(ticker)
            price = ticker_obj.data_history(interval='1d', start=date, end=date)['Close'].iloc[0]
            total_value += quantity * price
        return total_value

    def get_total_cost(self) -> float:
        total_cost = sum(self.currency_conversion(transaction.transaction_cost, transaction.currency, self.base_currency, transaction.date_hour) for transaction in self.transactions)
        return total_cost

    def get_portfolio_return(self, date: Union[str, datetime] = datetime.now()) -> float:
        initial_value = self.get_total_cost()
        current_value = self.get_portfolio_value(date)
        return (current_value - initial_value) / initial_value * 100 if initial_value else 0

    def calculate_metrics(self, benchmark_ticker: str = '^GSPC'):
        # This method will calculate all the requested metrics and plot them
        # Placeholder for now; full implementation will follow with each specific calculation
        pass

    def plot_metrics(self):
        # This method will generate the required plots
        # Placeholder for now; full implementation will follow with each specific plot
        pass

        
if __name__ == "__main__":
    portfolio = Portfolio()
    portfolio.load_transactions_from_csv(r'C:\Users\V.ozeel\Documents\Perso\Coding\Python\Projects\Finances\Invest_e_Gator\Invest_e_Gator\src\transactions.csv')
    print(portfolio.transactions_df)
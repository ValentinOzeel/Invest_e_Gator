from typing import Dict, List, Union
import pandas as pd
from forex_python.converter import CurrencyRates
from datetime import datetime

from transactions import Transaction
from ticker import Ticker

class Portfolio:
    def __init__(self, base_currency: str = 'usd'):
        self.base_currency = base_currency.lower()
        self.currency_conversion = CurrencyRates()
        
        self.transactions_df = pd.DataFrame(columns=['date_hour', 
                                                     'transaction_type', 'share_currency', 
                                                     'ticker', 'name', 
                                                     'n_shares', 'share_price', 
                                                     'fee'])

    def _currency_conversion(self, amount:float, date_obj:datetime, currency:str, target_currency:str):
        return amount if currency == self.base_currency else amount * self.currency_conversion.get_rate(currency, target_currency, date_obj)
        
    def add_transaction(self, transaction: Transaction):
        # Validate ticker_symbol and get long name
        ticker_obj = Ticker(ticker_name=transaction.ticker)
        ticker_long_name = ticker_obj.name
        
        EACH TRANSACTION WE HAVE ACCESS TO PROPERTY SUCH AS COST TRANSACTION ALREADY SO ADD THEM
        
        # Add transaction in dataframe (convert currency + add name + add n_shares_price)
        self.transactions_df = self.transactions_df.append({
            'date_hour': transaction.date_hour,
            'transaction_type': transaction.transaction_type,
            'share_currency': transaction.share_currency,
            'ticker': transaction.ticker,
            'name': ticker_long_name,
            'n_shares': transaction.n_shares,
            'share_price': transaction.share_price,
            'fee': transaction.fee
        }, ignore_index=True)

    def load_transactions_from_csv(self, file_path: str):
        transactions_df = pd.read_csv(file_path, parse_dates=['date_hour'])
        for _, row in transactions_df.iterrows():
            self.add_transaction(Transaction(
                date_hour=row['date_hour'],
                transaction_type=row['transaction_type'],
                share_currency=row['share_currency'],
                ticker=row['ticker'],
                n_shares=row['n_shares'],
                share_price=row['share_price'],
                fee=row['fee']
            ))

    def process_transactions(self):
        # Sort the DataFrame by the 'date_hour' column
        self.transactions_df = self.transactions_df.sort_values(by='date_hour').reset_index(drop=True)
        
        self.transactions_df['share_price'] = self._currency_conversion(self.transactions_df['share_price'], 
                                                                        self.transactions_df['date_hour'], 
                                                                        self.transactions_df['share_currency'])
        
        
        
        
        
        
        
        
        self.transactions_df['currency'] = self.base_currency
        self.transactions_df['n_shares_price'] = self.transactions_df['share_price']
        'n_shares_price'
        
        
        # Add transaction in dataframe (convert currency + add name + add n_shares_price)
        self.transactions_df = self.transactions_df.append({
            'date_hour': transaction.date_hour,
            'transaction_type': transaction.transaction_type,
            'currency': self.base_currency,
            'ticker': transaction.ticker,
            'name': ticker_long_name,
            'n_shares': transaction.n_shares,
            'share_price': self._currency_conversion(transaction.share_price, transaction.date_hour, transaction.currency),
            'n_shares_price': self._currency_conversion(transaction.share_price * transaction.n_shares, transaction.date_hour, transaction.currency),
            'fee': transaction.fee
        }, ignore_index=True)
        


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


class Portfolio():
    def __init__(self):

        self.transaction_obj = []
        self.transaction_csv = None
        
        

    
    def _df_metrics:
        
        ADD TAGS IN TRANSACTIONS !!!!!!
        
        
        stocks hold at a date
        cumulative investement (money you spent)
        
        Metrics computed via yfinance (ticker daily/weekly/etc prices) + df (positions held at that time):

        daily portfolio value (Net Asset Value)
        daily net_pl (Net Asset Value - investment)
        daily net_pl specific TAGS (sectors)
        
        cumulative Net Asset Value
        cumulative net_pl 
        cumulative net_pl  specific TAGS (sectors)
        
        annual returns CAGR 
        annual volatility 
        
        sharpe ratio 
        sortino ratio
        
        max drawdown 
        max drawdown date 
        



        
        portfolio drawdown     
        last Net Asset Value (current portfolio value)

        
from typing import Dict, List, Union
import pandas as pd

from Invest_e_Gator.src.secondary_modules.pydantic_valids import validate_load_csv, validate_tags_dict
from Invest_e_Gator.src.secondary_modules.currency_conversion import currency_conversion
from Invest_e_Gator.src.transactions import Transaction
from Invest_e_Gator.src.ticker import Ticker
from Invest_e_Gator.src.portfolio_metrics import PortfolioMetrics

class Portfolio:
    def __init__(self, 
                 #cash_position:Union[int, float], 
                 base_currency: str = 'usd'):
        #self.cash_position = cash_position
        self.base_currency = base_currency.lower()
        self.transactions_df = pd.DataFrame()

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
        transact_amount_base_currency = currency_conversion(
            amount=transaction.transaction_amount_transact_currency, 
            date_obj=transaction.date_hour, 
            currency=transaction.transact_currency, 
            target_currency=self.base_currency
        )
        
        # Add transaction in dataframe (convert currency + add name + add n_shares_price)
        self.transactions_df = self.transactions_df._append({
            'date_hour': transaction.date_hour,
            'transaction_type': transaction.transaction_type,
            'ticker': transaction.ticker,
            'name': ticker_long_name,
            'tags': ticker_tags,
            'n_shares': transaction.n_shares, # n shares sold or bought (positive number)
            'quantity': transaction.quantity, # actual number (negative or positive)
            'share_price_base_currency': currency_conversion(
                                            amount=transaction.share_price_transact_currency, 
                                            date_obj=transaction.date_hour, 
                                            currency=transaction.transact_currency, 
                                            target_currency=self.base_currency
                                        ),
            #'transact_currency': transaction.transact_currency,
            'fee_transact_currency': transaction.fee,
            'transact_amount_base_currency': transact_amount_base_currency if transact_amount_base_currency else transaction.transaction_amount_transact_currency
        }, ignore_index=True)
        
        self.transactions_df.sort_values(by='date_hour', ascending = True, inplace = True)
        
    def load_transactions_from_csv(self, file_path: str, tags_dict:Dict[str, List]=None):
        validate_load_csv(file_path=file_path)
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
                transact_currency=row['transact_currency'],
                fee=row['fee']
                ), 
                tags_dict
            )

        
    def compute_portfolio_metrics(self):
        pf_metrics = PortfolioMetrics(self.transactions_df, self.base_currency)
        results = pf_metrics.compute_metrics()

        return results



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
    metrics = portfolio.compute_portfolio_metrics()
    #for date in metrics:
    #    print(metrics[date], '\n')
    print(metrics)
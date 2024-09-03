from datetime import datetime
from typing import Dict, List, Union
import pandas as pd
import numpy as np

from Invest_e_Gator.src.secondary_modules.pydantic_valids import validate_load_csv, validate_tags_dict
from Invest_e_Gator.src.secondary_modules.currency_conversion import currency_conversion
from Invest_e_Gator.src.transactions import Transaction
from Invest_e_Gator.src.ticker import Ticker
from Invest_e_Gator.src.portfolio_metrics import PortfolioMetrics, plot_allocations
from Invest_e_Gator.src.degiro_csv_processing import SQLiteManagment


class Portfolio:
    def __init__(self, 
                 user_id:str,
                 #cash_position:Union[int, float], 
                 base_currency: str = 'usd'):
        
        self.user_id = user_id
        #self.cash_position = cash_position
        self.base_currency = base_currency.lower()
        self.transactions_df = pd.DataFrame()
        
        self.ticker_full_names = {}

    def _get_ticker_tags(self, ticker:str, tags_dict:Dict[str, List]):
        if not tags_dict:
            return None
        return tags_dict[ticker] if tags_dict.get(ticker) else None
            
    def add_transaction(self, transaction: Transaction, tags_dict:Dict[str, List]=None):
        if not isinstance(transaction, Transaction): raise ValueError('In add_transaction, transaction parameters should be a Transaction object.')
        validate_tags_dict(tags_dict=tags_dict)
        
        # Validate ticker_symbol and get long name
        ticker_obj = Ticker(ticker_symbol=transaction.ticker_symbol)
        # Get ticker's full name
        if not self.ticker_full_names.get(transaction.ticker_symbol):
            ticker_long_name = ticker_obj.name 
            self.ticker_full_names[transaction.ticker_symbol] = ticker_long_name
        else:
            ticker_long_name = self.ticker_full_names[transaction.ticker_symbol]

        # Get potential tags  
        ticker_tags = self._get_ticker_tags(transaction.ticker_symbol, tags_dict)
        
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
            'transaction_action': transaction.transaction_action,
            'ticker_symbol': transaction.ticker_symbol,
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
            'transact_currency': transaction.transact_currency,
            'fee_transact_currency': transaction.fee,
            'transact_amount_base_currency': transact_amount_base_currency if transact_amount_base_currency else transaction.transaction_amount_transact_currency
        }, ignore_index=True)
        
        self.transactions_df.sort_values(by='date_hour', ascending = True, inplace = True)
        
    def load_transactions_from_sqlite(self, table_name:str, tags_dict:Dict[str, List]=None):

        transactions_df = SQLiteManagment.retrieve_dataframe_from_sqlite(self.user_id, table_name)
        
        print(transactions_df)
        print(transactions_df.columns)
        
        
        transactions = [
            Transaction(
                date_hour=pd.to_datetime(row['date_hour']),
                transaction_type=row['transaction_type'],
                ticker_symbol=row['ticker_symbol'],
                n_shares=row['n_shares'],
                share_price=row['share_price'],
                share_currency=row['share_currency'],
                transact_currency=row['transact_currency'],
                fee=row['fee'],
                transaction_action=row['transaction_action']
            )
            for _, row in transactions_df.iterrows()
        ]

        for i, transaction in enumerate(transactions):
            self.add_transaction(transaction, tags_dict)
            print(f'Loaded {i+1} / {len(transactions)} transactions')

    
    def tags_allocation(self, ticker_tags:Dict[str,Dict], alloc_tags:Dict, other_tags:Dict[str,Dict]=None):
        '''
        alloc_tags ahould be as {
                                    'main_tag_1': {
                                                'weight': 0.3, 
                                                'subtags': {
                                                    'subtag_1': weight, 
                                                    'subtag_2': weight, 
                                                    ...
                                                    }
                                                }
                                    ...
                                }
        '''
        
        if not ticker_tags or not alloc_tags:
            return
        
        cv_per_tag = {}         
        
        # GET CURRENT VALUES
        total_value_pf = self.current_metrics['total_value']
        position_values = self.current_metrics['position_values']
        
        # Calculate actual allocations per tag
        for ticker, tags in ticker_tags.items():
            
            for main_tag, mt_dict in tags.items():
                
                cv_per_tag[main_tag] = {'value': (cv_per_tag.get(main_tag, {}).get('value', 0) + mt_dict['weight'] * position_values[ticker]) / total_value_pf, 
                                        'subtags': {}}

                for subtag, weight in mt_dict['subtags'].items():
                   cv_per_tag[main_tag]['subtags'][subtag] = (cv_per_tag.get(main_tag, {}).get('subtags', {}).get(subtag, 0) + weight * position_values[ticker]) / total_value_pf
                    
        
        main_tags = list(cv_per_tag.keys())
        # Extracting main tags and their values
        main_tags_df = pd.DataFrame.from_dict(
            {
                'MAIN_TAGS' : main_tags, 
                'ALLOCATIONS': [cv_per_tag[tag]['value'] for tag in main_tags]
                }
            ).sort_values(by='ALLOCATIONS')
        
        plot_allocations(f"main_tags_allocations", main_tags_df)
        
        # Extracting sub tags and their values
        sub_tags_dict = {}
        
        for main_tag in main_tags:
            sub_tags_dict[main_tag] = {'subtags':[], 'allocations': []}
            for sub_tag in cv_per_tag[main_tag]['subtags'].keys():
                sub_tags_dict[main_tag]['subtags'].append(sub_tag)
                sub_tags_dict[main_tag]['allocations'].append(cv_per_tag[main_tag]['subtags'][sub_tag])

            sub_tags_df = pd.DataFrame.from_dict(
            {
                'SUB_TAGS' : sub_tags_dict[main_tag]['subtags'], 
                'ALLOCATIONS': sub_tags_dict[main_tag]['allocations']
                }
            )
        
        
            plot_allocations(str(main_tag), sub_tags_df, tag_col_name='SUB_TAGS')
        
        


    
    
    
    
    def compute_portfolio_metrics(self, 
                                  #start_date:datetime=None, end_date:datetime=None, 
                                  today:bool=True, plot_current:bool=True,
                                  ticker_tags=None, alloc_tags=None):
        
        pf_metrics = PortfolioMetrics(self.transactions_df, self.base_currency, 
                                      #start_date=start_date, end_date=end_date, 
                                      today=today)
        
        self.metrics = pf_metrics.compute_metrics()
        # Identify the closest key to today's date
        today = pd.Timestamp.now()
        self.closest_date = self.metrics.index[np.abs(self.metrics.index - today).argmin()]
        # Access the element at column 'pl_value' for the identified closest date
        self.current_metrics = self.metrics.loc[self.closest_date]
        
        
        if plot_current:
            pf_metrics._plot_current_metrics(self.metrics)
            self.tags_allocation(ticker_tags, alloc_tags)
            
        return self.metrics


    def calculate_metrics(self, benchmark_ticker: str = '^GSPC'):
        # This method will calculate all the requested metrics and plot them
        # Placeholder for now; full implementation will follow with each specific calculation
        pass

    def plot_metrics(self):
        # This method will generate the required plots
        # Placeholder for now; full implementation will follow with each specific plot
        pass

        
if __name__ == "__main__":
    import matplotlib
    #%matplotlib inline
    import quantstats as qs

    # extend pandas functionality with metrics, etc.
    qs.extend_pandas()
    
    
    
    portfolio = Portfolio(user_id='Valola')
    portfolio.load_transactions_from_sqlite(table_name='Valola_cleaned_transactions')
#

    alloc_tags = {
                    'AI': {
                                'weight': 0.4, 'subtags': {'SOFTWARE': 0.7, 'INFRA': 0.3}
                                },
                    'ENERGY': {
                                'weight': 0.13, 'subtags': {'BATTERY': 0.7, 'SOLAR': 0.3}
                                }
                }

    ticker_tags =  {
                     'pltr': {
                                'AI': {
                                        'weight': 0.7, 'subtags': {'SOFTWARE':0.8, 'INFRA': 0.2}
                                       }
                                },
                     'enph': {
                                'ENERGY': {
                                        'weight': 0.7, 'subtags': {'SOLAR':0.8, 'INVERTOR':0.2}
                                       }
                                },
                     'nee': {
                                'ENERGY': {
                                        'weight': 0.7, 'subtags': {'SOLAR':1}
                                       }
                                },
                     'nvda': {
                                'BLABLA': {
                                        'weight': 0.7, 'subtags': {'BUBU':1}
                                       }
                                },
                     'asml': {
                                'BIBIBI': {
                                        'weight': 0.7, 'subtags': {'SOLAR':1}
                                       }
                                },
                     'ionq': {
                                'QUANTUM': {
                                        'weight': 0.7, 'subtags': {'SOLAR':1}
                                       }
                                },
                     'crwd': {
                                'CYBERSEC': {
                                        'weight': 0.7, 'subtags': {'SOLAR':1}
                                       }
                                },
                     'tsla': {
                                'ROBOTS': {
                                        'weight': 0.7, 'subtags': {'SOLAR':1}
                                       }
                                },
                     'dna': {
                                'SYNBIO': {
                                        'weight': 0.7, 'subtags': {'SOLAR':1}
                                       }
                                },
                    }
    
    metrics = portfolio.compute_portfolio_metrics(today=True, ticker_tags=ticker_tags, alloc_tags=alloc_tags)
    

            

    print(metrics)
    
    for i, col in enumerate(metrics.columns):
        print(col.upper())
        
        element = metrics.iat[0, i]
        
        if isinstance(element, Dict):
            for key, value in sorted(element.items(), key=lambda x:x[1]):
                print(f'{key} : {value}')
        else:
            print(element)
        print('\n\n\n')
    

   # pf = []
#
   # # Get today's date normalized to midnight (00:00:00)
   # today = pd.Timestamp.now().normalize()
#
   # # Filter rows where the date part of the index matches today's date
   # metrics = metrics[metrics.index.normalize() == today]
#
   # print(metrics)
#
   # for key, value in sorted(metrics.iat[0, 7].items(), key=lambda x:x[1]):
   #     print(f'{key.upper()} : {value}')
   #     if key not in ['pltr', 'nvda', 'tsla', 'crwd']: continue
   #     try:
   #         stock = qs.utils.download_returns(key.upper())
#
   #         pf.append(value * stock)
   #     except Exception as e:
   #         print(f'COULDNT DO {key},    {e}')
   #         continue

    #pf = sum(pf)
    ## show sharpe ratio
    #qs.stats.sharpe(pf)
    #pf_plot = qs.plots.snapshot(pf, title='Test Performance', show=True, savefig='pf')
    #test = qs.reports.html(pf, "SPY", output=True)
    #test = qs.reports.full(pf, title='Test Performance', show=True, savefig='stock1')
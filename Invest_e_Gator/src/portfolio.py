from datetime import datetime
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
                 base_currency: str = 'eur'):
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
        ticker_obj = Ticker(ticker_name=transaction.ticker)
        # Get ticker's full name
        if not self.ticker_full_names.get(transaction.ticker):
            ticker_long_name = ticker_obj.name 
            self.ticker_full_names[transaction.ticker] = ticker_long_name
        else:
            ticker_long_name = self.ticker_full_names[transaction.ticker]
        # Get potential tags  
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
            'transaction_action': transaction.transaction_action,
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
            'transact_currency': transaction.transact_currency,
            'fee_transact_currency': transaction.fee,
            'transact_amount_base_currency': transact_amount_base_currency if transact_amount_base_currency else transaction.transaction_amount_transact_currency
        }, ignore_index=True)
        
        self.transactions_df.sort_values(by='date_hour', ascending = True, inplace = True)
        
    def load_transactions_from_csv(self, file_path: str, degiro:bool = True, tags_dict:Dict[str, List]=None):
        validate_load_csv(file_path=file_path)
        # Read csv
        transactions_df = pd.read_csv(file_path, parse_dates=['date_hour']) if not degiro else self._load_degiro_transactions(file_path)
        
        n_transactions = transactions_df.shape[0]
        # Transaform rows as Transaction obj
        for i, (_, row) in enumerate(transactions_df.iterrows()):
            self.add_transaction(Transaction(
                date_hour=pd.to_datetime(row['date_hour']),
                transaction_type=row['transaction_type'],
                ticker=row['ticker'],
                n_shares=row['n_shares'],
                share_price=row['share_price'],
                share_currency=row['share_currency'],
                transact_currency=row['transact_currency'],
                fee=row['fee'],
                transaction_action=row['transaction_action'] # 'real' (deliberate transaction) vs 'non_real' (stock split, reverse split etc...)
                ), 
                tags_dict
            )
            print(f'Loaded {i+1} / {n_transactions} transactions')

        
    def _load_degiro_transactions(self, file_path: str):
        df = pd.read_csv(file_path)
        # Select some columns
        df = df[['Datetime', 'Quantity', 'Ticker_symbol', 'Share_price', 'Currency_SP', 'Currency_TPIMC', 'Fee', 'transaction_action']]
        # Get transaction_type and n_shares
        df['transaction_type'] = df['Quantity'].apply(lambda x: 'buy' if x > 0 else 'sale')
        df['n_shares'] = df['Quantity'].apply(lambda x: abs(x))
        df = df.drop(columns=['Quantity'])
        # Rename some columns
        df = df.rename(columns={"Datetime": "date_hour", 
                           "Ticker_symbol": "ticker",
                           "Share_price": "share_price",
                           "Currency_SP": "share_currency",
                           "Currency_TPIMC": "transact_currency",
                           "Fee": "fee",
                           "Transaction_action": "transaction_action"
                            }
                  )
        return df
    
    
    

    
    def tags_allocation(self, ticker_tags:Dict[str:Dict], alloc_tags:Dict, alloc_subtags:Dict[str:Dict]):
        def stacked_radial_chart_plot(ax, title: str, data: Dict[str, Dict[str, float]]):
            main_tags = list(data.keys())
            main_tag_values = [data[tag]['value'] for tag in main_tags]
            subtags = {tag: {k: v for k, v in data[tag].items() if k != 'value'} for tag in main_tags}

            max_value_full_ring = max(main_tag_values)
            ring_colours = ['#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600']
            data_len = len(main_tags)

            # Ensure the radial chart fits within the subplot's dimensions
            rect = ax.get_position()
            ax_polar_bg = plt.subplot(projection='polar', position=[rect.x0, rect.y0, rect.width, rect.height])
            ax_polar_bg.set_theta_zero_location('N')
            ax_polar_bg.set_theta_direction(1)

            # Plot background grey bars
            for i in range(data_len):
                ax_polar_bg.barh(i, max_value_full_ring * 1.5 * np.pi / max_value_full_ring, color='grey', alpha=0.1)
            ax_polar_bg.axis('off')

            ax_polar = plt.subplot(projection='polar', position=[rect.x0, rect.y0, rect.width, rect.height])
            ax_polar.set_theta_zero_location('N')
            ax_polar.set_theta_direction(1)

            # Plot data bars with stacked sub-bars
            for i, main_tag in enumerate(main_tags):
                start_angle = 0
                for j, (subtag, subvalue) in enumerate(subtags[main_tag].items()):
                    bar = ax_polar.barh(i, subvalue * 1.5 * np.pi / max_value_full_ring, left=start_angle, color=ring_colours[j % len(ring_colours)])
                    start_angle += subvalue * 1.5 * np.pi / max_value_full_ring

                    # Annotate subtags
                    angle = (start_angle - subvalue * 1.5 * np.pi / (2 * max_value_full_ring))
                    ax_polar.text(angle, i, subtag, ha='center', va='center', fontsize=8, color='black')

            # Annotate main tags on the radial chart
            for i, main_tag in enumerate(main_tags):
                angle = i * (2 * np.pi / data_len)
                ax_polar.text(angle, max_value_full_ring + 0.1, main_tag, ha='center', va='center', fontsize=10, color='black')

            ax_polar.grid(False)
            ax_polar.tick_params(axis='both', left=False, bottom=False, labelbottom=False, labelleft=False)
            ax_polar.set_title(title, fontsize=14, color='black', loc='center', pad=20)

        '''
        alloc_tags ahould bew as {
                                    'main_tag_1': {
                                                'weight': 0.3, 'subtags': {'subtag_1': weight, 'subtag_2': weight, ...}
                                                }
                                    ...
                                }
        '''
        if sum(alloc_tags.values()) > 1:
            raise ValueError('The sum of alloc_tags values should be <= 1.')
        
        cv_per_tag = {}         
        tags_actual_alloc = sum(self.current_value.values())
        
        
        # GET CURRENT VALUES
        total_value_pf = self.metrics['total_pl']
        position_values = self.current_metrics['position_values']
        
        # Calculate actual allocations per tag
        for ticker, tags in ticker_tags.items():
            
            for main_tag, mt_dict in tags.items():
                cv_per_tag[main_tag] = {'value': (cv_per_tag.get(main_tag, 0) + mt_dict['weight'] * position_values[ticker]) / total_value_pf}
                
                for subtag, weight in mt_dict['subtags'].items():
                   cv_per_tag[main_tag][subtag] = (cv_per_tag.get(subtag, 0) + weight * position_values[ticker]) / total_value_pf
        # Store the results
        self.tags_actual_alloc = tags_actual_alloc
    
    # self.tags_actual_alloc
       # {'maintag_1': {'value': 0.25, 
       #                'subtag_1': 0.3, 
       #                'subtag2':0.7},
       #  
       #  'maintag_2': ['value': 0.75]
       #  }
        
    def compute_portfolio_metrics(self, 
                                  #start_date:datetime=None, end_date:datetime=None, 
                                  today:bool=True, plot_current:bool=True):
        
        pf_metrics = PortfolioMetrics(self.transactions_df, self.base_currency, 
                                      #start_date=start_date, end_date=end_date, 
                                      today=today)
        
        self.metrics = pf_metrics.compute_metrics()
        # Identify the closest key to today's date
        today = pd.Timestamp.now()
        closest_date = self.metrics.index[np.abs(self.metrics.index - today).argmin()]
        # Access the element at column 'pl_value' for the identified closest date
        self.current_metrics = self.metrics.loc[closest_date,:]
        
        if plot_current:
            pf_metrics._plot_current_metrics(self.metrics)
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
    
    
    
    portfolio = Portfolio()
    portfolio.load_transactions_from_csv(file_path=r'C:\Users\V.ozeel\Documents\Perso\Coding\Python\Projects\Finances\Invest_e_Gator\Invest_e_Gator\data\degiro_transactions\Valola\cleaned_transactions.csv',
                                         degiro=True)
#


    metrics = portfolio.compute_portfolio_metrics(today=True)

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
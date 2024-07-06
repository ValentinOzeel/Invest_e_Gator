from typing import Union
from datetime import datetime
import pandas as pd

class PortfolioMetrics():
    def __init__(self, df:pd.DataFrame, start_date:datetime=None, end_date:datetime=None):
        self.initial_df = df
        
        
        self.df = None
        
    def compute_metrics(self, date:datetime):
        # Filter df rows to get all transactions prior to date
        self.df = self.initial_df[self.initial_df['date_hour'] <= date]
        
        self._compute_total_investment()
        
        
        self._compute_returns()
    
    def _compute_total_investment(self):
        self.df['total_investment_base_currency'] = self.df['transact_cost_base_currency'].cumsum

    def _compute_nav(self, df):
        pass 
    
    def _compute_returns(self, df):
        pass
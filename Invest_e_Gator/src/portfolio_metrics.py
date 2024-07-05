from typing import Union
from datetime import datetime
import pandas as pd

class PortfolioMetrics():
    def __init__(self, df:pd.DataFrame):
        self.df = df
        
    def compute_metrics(self, date:datetime):
        # Filter df rows to get all transactions prior to date
        filtered_df = self.df[self.df['date_hour'] <= date]
        
        self._compute_returns(filtered_df)
    
    def _compute_investment(self, df:pd.DataFrame):
        return df['transact_cost_base_currency'].cumsum
        
    def _compute_nav(self, df):
        pass 
    
    def _compute_returns(self, df):
        pass
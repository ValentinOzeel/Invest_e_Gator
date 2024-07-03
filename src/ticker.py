import inspect
import yfinance as yf


from secondary_modules.yfinance_cache import session
from secondary_modules.pydantic_valids import validate_data_history, validate_financials
from constants import yfinance_info_attributes

class Ticker():
    def __init__(self, ticker_name):
        self.ticker_name = ticker_name 
        self.session = session
        self._ticker = self.get_yfinance_ticker()
        # Create property methods to easily access yfinance.Ticker.info values
        self.create_property_info_methods()
        
    def get_yfinance_ticker(self):
        try:
            return yf.Ticker(self.ticker_name, session=self.session)
        except Exception as e:
            print(f"This ticker '{self.ticker_name}' either doesn't exist or isn't available via the yfinance API.\n{e}")


    ### Create property methods corresponding to elements yfinance.Ticker.info dict.
    ### Relevant elements considered are gathered in 'yfinance_info_attributes'.
    def _get_info_value(self, key):
        return self._ticker.info.get(key, None)
    
    def _create_property_method(self, info_key):
        # Function to create the dynamic property methods
        def property_method(self):
            return self._get_info_value(info_key)
        # Wraps method with property
        return property(property_method)
    
    def create_property_info_methods(self):
        # Dynamically create methods and add them to the class
        for attr_name, info_key in yfinance_info_attributes.items():
            setattr(self.__class__, attr_name, self._create_property_method(info_key))
            
    @property
    def info(self):
        return self._ticker.info
    
    def data_history(self, interval:str='1d', period='max', start=None, end=None, repair=True, keepna=False, include_divs_splits=False, history_metadata=False):
        """
        Fetch historical market data for the ticker.

        Parameters:
        - interval (str): Data interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo').
        - period (str): Data period (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max', None).
        - start (str): Start date for fetching data (YYYY-MM-DD format or datatime objet).
        - end (str): End date for fetching data (YYYY-MM-DD format or datatime objet).
        - repair (bool): Whether to repair missing data.
        - keepna (bool): Whether to keep NaN values in the data.
        - include_divs_splits (bool): Whether to include dividends and stock splits.
        - history_metadata (bool): Whether to include history metadata.

        Returns:
        - DataFrame or Tuple[DataFrame, dict]: Historical data and optionally history_metadata.
        """
        # Validate data_history parameters input through pydantic model
        validate_data_history(interval=interval, period=period, start=start, end=end, 
                              repair=repair, keepna=keepna, include_divs_splits=include_divs_splits)
        # Call yfinance.Ticker.history method
        history_df = self._ticker.history(interval=interval, period=period, start=start, end=end, 
                                          repair=repair, keepna=keepna, actions=include_divs_splits)
        # Return df or tuple(df, metadata)
        return history_df if not history_metadata else (history_df, self._ticker.history_metadata) 


    def financials(self, income_stmt:bool=True, balance_sheet:bool=False, cash_flow:bool=False, quarterly:bool=False, pretty:bool=False):
        """
        Fetch financial statements for the ticker.

        Parameters:
        - income_stmt (bool): Fetch income statement if True.
        - balance_sheet (bool): Fetch balance sheet if True.
        - cash_flow (bool): Fetch cash flow statement if True.
        - quarterly (bool): Fetch quarterly data if True, otherwise yearly data.
        - pretty (bool): Fetch data in a pretty row name format if True.

        Returns:
        - dict: Dictionary containing the requested financial statements.
        """
        validate_financials(income_stmt=income_stmt, balance_sheet=balance_sheet, cash_flow=cash_flow, quarterly=quarterly, pretty=pretty)\
            
        results = {}
        params = {'freq': 'yearly' if not quarterly else 'quarterly', 'pretty': pretty}
        
        if income_stmt: results['income_stmt'] = self._ticker.get_income_stmt(**params)
        if balance_sheet: results['balance_sheet'] = self._ticker.get_balance_sheet(**params)
        if cash_flow: results['cash_flow'] = self._ticker.get_cash_flow(**params)
        return results
    
if __name__ == "__main__":
    
    msft_obj = Ticker('MSFT')
    
    
    #print(msft_obj.forward_pe, '\n')
    #print(msft_obj.data_history(period='5d'), '\n')
    #print(msft_obj.financials(income_stmt=True, balance_sheet=True, cash_flow=True, quarterly=False, pretty=False), '\n')
    print(msft_obj._ticker.news)
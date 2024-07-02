import yfinance as yf

from secondary_modules.yfinance_cache import session
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
    
    @property
    def data_history(self, interval:str='1d', period='max', start=None, end=None, repair=True):
        return self._ticker.history(interval=interval, period=period, start=start, end=end, repair=repair)
    
    PROPERTY HISTORY DATA 
    
    
    
    
if __name__ == "__main__":
    
    msft_obj = Ticker('MSFT')
    
    print(msft_obj.forward_pe)
from typing import Any, Literal
from datetime import datetime
import re
from pydantic import BaseModel, field_validator, ValidationInfo, ValidationError

from constants import yfinance_history_interval_period_choices
from checks import verify_datetime_format




def _verify_date_str_format(field_name, value, regex_pattern:str, common_date_format:str, datetime_format, return_as_datetime=False):
    # Check if the date_str matches the pattern
    if not re.match(regex_pattern, value):
        raise ValueError(f"Input {field_name} -- {value} -- should follow the {common_date_format}.")
    # Try to parse the date_str to a datetime object to check if it is a valid date
    try:
        datetime.strptime(value, datetime_format)
    except ValueError:
        raise ValueError(f"Input {field_name} -- {value} -- is not a valid date.")
        
    return value if not return_as_datetime else datetime.strptime(value, datetime_format)

def _verify_datetime_format(dt_obj:datetime, expected_format:str = '%Y-%m-%d %H:%M:%S') -> bool:
    try:
        # Convert the datetime object to a string using the expected format
        dt_str = dt_obj.strftime(expected_format)
        # Parse the string back to a datetime object using the expected format
        parsed_dt = datetime.strptime(dt_str, expected_format)
        # Compare the parsed datetime object with the original
        return dt_obj == parsed_dt
    except ValueError:
        return False
    
    
    
############# Ticker: data_history #############
          
class DataHistoryPydantic(BaseModel):
    interval: str
    period: str 
    start: Any
    end: Any
    include_divs_splits: bool
    repair: bool
    keepna: bool

    @field_validator('interval')
    @classmethod
    def validate_interval(cls, value, info: ValidationInfo):
        if value not in yfinance_history_interval_period_choices["interval"]:
            raise ValueError(f"Input {info.field_name} -- {value} -- is not a valid interval. It should be assigned to one of the following {str} value: {yfinance_history_interval_period_choices['interval']}.")
        return value
    
    @field_validator('period')
    @classmethod
    def validate_period(cls, value, info: ValidationInfo):
        if value not in yfinance_history_interval_period_choices["period"]:
            raise ValueError(f"Input {info.field_name} -- {value} -- is not a valid period. It should be assigned to one of the following {str} value: {yfinance_history_interval_period_choices['period']}.")
        return value
    
    @field_validator('start', 'end')
    @classmethod
    def validate_start_end(cls, value, info: ValidationInfo):
        # Return value if is None
        if value is None:
            return value
        # Check if value is either str or datetime
        if not any([isinstance(value, str), isinstance(value, datetime)]):
            raise ValueError(f"Input {info.field_name} -- {value} -- is not an instance of {str} nor {datetime}.")
        # If value is str, check if valid str
        if isinstance(value, str):
            # Define the regular expression pattern for YYYY-MM-DD
            re_pattern = r'^\d{4}-\d{2}-\d{2}$'
            # Date format
            str_format = 'YYYY-MM-DD'
            datetime_format = '%Y-%m-%d'

            value = _verify_date_str_format(info.field_name, value, re_pattern, str_format, datetime_format, return_as_datetime=False)
        
        if isinstance(value, datetime):
            if not verify_datetime_format(value, datetime_format):
                raise ValueError(f"Input {info.field_name} -- {value} -- should follow the {datetime_format}.")
            
        return value
    
    @field_validator('include_divs_splits', 'repair', 'keepna')
    @classmethod
    def validate_divs_repair_keepna(cls, value, info: ValidationInfo):
        # Return value if is None
        if value is None:
            return value
        # Check if value is bool
        if not isinstance(value, bool):
            raise ValueError(f"Input {info.field_name} -- {value} -- is not an instance of {bool}.")
        return value
  
  
def validate_data_history(**kwargs):  
    # Validate data_history parameters input through pydantic model
    try:
        DataHistoryPydantic(**kwargs)
    except ValidationError as e:
        raise ValueError(f'Invalid data_history parameters:\n{e}')





############# Ticker: financials #############

class FinancialsPydantic(BaseModel):
    income_stmt: bool
    balance_sheet: bool 
    cash_flow: bool
    quarterly: bool
    pretty: bool

    @field_validator('income_stmt', 'balance_sheet', 'cash_flow', 'quarterly', 'pretty')
    @classmethod
    def validate_interval(cls, value, info: ValidationInfo):
        if not isinstance(value, bool):
            raise ValueError(f"Input {info.field_name} -- {value} -- is not a {bool} instance.")
        return value
    
def validate_financials(**kwargs):  
    # Validate data_history parameters input through pydantic model
    try:
        FinancialsPydantic(**kwargs)
    except ValidationError as e:
        raise ValueError(f'Invalid financials parameters:\n{e}')
    
    
    
    
############# Transaction: add #############
       
class TransactionPydantic(BaseModel):
    date_hour: datetime
    transaction_type: Literal['buy', 'sale']
    currency: Literal['usd', 'eur', 'jpy', 'gbp', 'cnh', 'aud', 'cad', 'chf']
    ticker: str
    n_shares: float
    share_price: float
    fee: float

    @field_validator('date_hour')
    @classmethod
    def validate_date_hour(cls, value, info: ValidationInfo):
        # Check if value is either str or datetime
        if not any([isinstance(value, str), isinstance(value, datetime)]):
            raise ValueError(f"Input {info.field_name} -- {value} -- is not an instance of {str} nor {datetime}.")
        
        # If value is str, check if valid str
        if isinstance(value, str):
            # Define the regular expression pattern YYYY-MM-DD HH:MM:SS
            re_pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
            # Define format
            str_format = 'YYYY-MM-DD HH:MM:SS'
            datetime_format = '%Y-%m-%d %H:%M:%S'
            
            value = _verify_date_str_format(info.field_name, value, re_pattern, str_format, datetime_format, return_as_datetime=True)
            
        if isinstance(value, datetime):
            if not verify_datetime_format(value, '%Y-%m-%d %H:%M:%S'):
                raise ValueError(f"Input {info.field_name} -- {value} -- should follow the '%Y-%m-%d %H:%M:%S'.")
            
        return value
    

    @field_validator('transaction_type')
    @classmethod
    def validate_transaction_type(cls, value, info: ValidationInfo):
        if not value in ['buy', 'sale']:
            raise ValueError(f"Input {info.field_name} -- {value} -- should be one of the following {str} value: ['buy', 'sale'].")   
        return value
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, value, info: ValidationInfo):
        if not value in ['usd', 'eur', 'jpy', 'gbp', 'cnh', 'aud', 'cad', 'chf']:
            raise ValueError(f"Input {info.field_name} -- {value} -- should be one of the following {str} value: ['usd', 'eur', 'jpy', 'gbp', 'cnh', 'aud', 'cad', 'chf'].")   
        return value
    
    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, value, info: ValidationInfo):
        if not isinstance(value, str):
            raise ValueError(f"Input {info.field_name} -- {value} -- is not an instance of {str}.")  
        
    @field_validator('n_shares', 'share_price', 'fee')
    @classmethod
    def validate_ticker(cls, value, info: ValidationInfo):
        if info.field_name == 'fee' and value is None:
            return value 
        
        if not isinstance(value, float) and not isinstance(value, int):
            raise ValueError(f"Input {info.field_name} -- {value} -- is not an {int}/{float} instance.")  
        return value


def validate_transaction(**kwargs):  
    # Validate data_history parameters input through pydantic model
    try:
        TransactionPydantic(**kwargs)
    except ValidationError as e:
        raise ValueError(f'Invalid Transaction class parameters:\n{e}')
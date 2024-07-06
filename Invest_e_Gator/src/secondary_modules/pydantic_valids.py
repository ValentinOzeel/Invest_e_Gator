from typing import Union, Any, Literal, Dict, List
from datetime import datetime
import re
from pydantic import BaseModel, field_validator, ValidationInfo, ValidationError

from Invest_e_Gator.src.constants import available_currencies, yfinance_history_interval_period_choices
#from Invest_e_Gator.src.transactions import Transaction



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
    
    
def _check_tags_dict(tags_dict, info):    
    if not isinstance(tags_dict, Dict):
        raise ValueError(f"Input {info.field_name} -- {tags_dict} -- is not an instance of {Dict}.")
    
    if not all([isinstance(key, str) for key in tags_dict.keys()]):
        raise ValueError(f"Input {info.field_name} -- {tags_dict} -- all keys should be of type {str}.")
    
    if not all([isinstance(value, List) for value in tags_dict.values()]):
        raise ValueError(f"Input {info.field_name} -- {tags_dict} -- all values should be of type {List}.")
    
    if not all([isinstance(tag, str) for value in tags_dict.values() for tag in value]):
        raise ValueError(f"Input {info.field_name} -- {tags_dict} -- all elements in List (Dict values) should be of type {str}.")
    
    
    
    
    
    
    
############# Ticker: data_history #############
          
class DataHistoryPydantic(BaseModel):
    interval: str
    period: Union[str, None] 
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
        
        # Date format
        str_format = 'YYYY-MM-DD'
        datetime_format = '%Y-%m-%d' 
            
        # If value is str, check if valid str
        if isinstance(value, str):
            # Define the regular expression pattern for YYYY-MM-DD
            re_pattern = r'^\d{4}-\d{2}-\d{2}$'
            value = _verify_date_str_format(info.field_name, value, re_pattern, str_format, datetime_format, return_as_datetime=False)
        
        if isinstance(value, datetime):
            if not _verify_datetime_format(value, datetime_format):
                raise ValueError(f"Input {info.field_name} -- {value} -- should follow the {datetime_format}.")
            
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
    
def validate_financials(**kwargs):  
    # Validate data_history parameters input through pydantic model
    try:
        FinancialsPydantic(**kwargs)
    except ValidationError as e:
        raise ValueError(f'Invalid financials parameters:\n{e}')
    
    
    
    
############# Transaction: add #############
       
class TransactionPydantic(BaseModel):
    date_hour: Union[str, datetime]
    transaction_type: Literal['buy', 'sale']
    ticker: str
    n_shares: Union[float, int]
    share_price: Union[float, int]
    share_currency: str
    expense_currency: str
    fee: Union[float, None]

    @field_validator('date_hour')
    @classmethod
    def validate_date_hour(cls, value, info: ValidationInfo):        
        # If value is str, check if valid str
        if isinstance(value, str):
            # Define the regular expression pattern YYYY-MM-DD HH:MM:SS
            re_pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
            # Define format
            str_format = 'YYYY-MM-DD HH:MM:SS'
            datetime_format = '%Y-%m-%d %H:%M:%S'
            
            value = _verify_date_str_format(info.field_name, value, re_pattern, str_format, datetime_format, return_as_datetime=True)
            
        if isinstance(value, datetime):
            if not _verify_datetime_format(value, '%Y-%m-%d %H:%M:%S'):
                raise ValueError(f"Input {info.field_name} -- {value} -- should follow the '%Y-%m-%d %H:%M:%S'.")
            
        return value
 

    @field_validator('share_currency', 'expense_currency')
    @classmethod
    def validate_share_currency(cls, value, info: ValidationInfo):        
        if not value in available_currencies:
            raise ValueError(f"Input {info.field_name} -- {value} -- should be one of the following {str} value: {available_currencies}.")   
        return value

def validate_transaction(**kwargs):  
    # Validate data_history parameters input through pydantic model
    try:
        TransactionPydantic(**kwargs)
    except ValidationError as e:
        raise ValueError(f'Invalid Transaction class parameters:\n{e}')
    
    
    
    

############# Portfolio: load_transactions_from_csv #############

class PortfolioLoadCsvPydantic(BaseModel):
    file_path: str
        
    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, value, info: ValidationInfo):
        if '.csv' not in value:
            raise ValueError(f"Input {info.field_name} -- {value} -- should point towards a '.csv' file.")   
        return value
    
def validate_load_csv(**kwargs):  
    # Validate data_history parameters input through pydantic model
    try:
        PortfolioLoadCsvPydantic(**kwargs)
    except ValidationError as e:
        raise ValueError(f'Invalid load_transactions_from_csv parameters:\n{e}')
    
    
############# Portfolio: add_transaction #############

class PortfolioTagsDictPydantic(BaseModel):
    #transaction: Transaction
    tags_dict: Union[Dict[str, List], None]
        
    @field_validator('tags_dict')
    @classmethod
    def validate_tags_dict(cls, value, info: ValidationInfo):
        if value is None:
            return value 
        _check_tags_dict(value, info)
        return value
    
def validate_tags_dict(**kwargs):  
    # Validate data_history parameters input through pydantic model
    try:
        PortfolioTagsDictPydantic(**kwargs)
    except ValidationError as e:
        raise ValueError(f'Invalid add_transaction parameters:\n{e}')
    
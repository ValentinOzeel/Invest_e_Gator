import os
from typing import List, Tuple, Union

import pandas as pd
import numpy as np
import sqlite3
from contextlib import contextmanager

import finnhub
from ratelimit import limits, sleep_and_retry
import time

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file


from Invest_e_Gator.src.secondary_modules.pydantic_valids import validate_load_csv

# Assuming we are in src\degiro_csv_processing.py
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SQLITE_DATABASE_PATH = os.path.join(ROOT_PATH, 'conf', 'sqlite', 'data_sqlite.db')





class SQLiteManagment:
    '''SQLite DATABASE MANAGEMENT'''

    @staticmethod
    @contextmanager
    def get_db_connection():
        """Get a connection to the SQLite database and close it when context ends (after user action)."""
        conn = sqlite3.connect(SQLITE_DATABASE_PATH)
        try:
            yield conn
        finally:
            conn.close()

    @staticmethod
    def store_dataframe_in_sqlite(user_id, df, table_name):
        # Add a user_id column to the DataFrame
        df['user_id'] = user_id

        with SQLiteManagment.get_db_connection() as conn:
            # Store the DataFrame in the SQLite database table
            df.to_sql(table_name, conn, if_exists='replace', index=False)

    @staticmethod
    def retrieve_dataframe_from_sqlite(user_id, table_name):
        try:
            with SQLiteManagment.get_db_connection() as conn:
                # Query the database and retrieve the table as a DataFrame
                query = f"SELECT * FROM {table_name} WHERE user_id = ?"
                df = pd.read_sql_query(query, conn, params=(user_id,))
                # Remove the user_id column
                df = df.drop(columns=['user_id']) if not df.empty else pd.DataFrame()
                return df
        except Exception as e:
            print(f'Error retrieving dataframe from db for user {user_id} and table {table_name}: {e}')
            return pd.DataFrame()  # Return empty DataFrame instead of None

    @staticmethod
    def get_user_table_names(user_id):
        """Return a list of all existing table names for the given user."""
        try:
            with SQLiteManagment.get_db_connection() as conn:
                query = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?"
                tables = pd.read_sql_query(query, conn, params=(f'{user_id}_%',))
                return tables['name'].tolist() if not tables.empty else []
        except Exception as e:
            print(f'Error retrieving table names for user {user_id}: {e}')
            return []  # Return an empty list in case of error

        
        
class CSVMerger:
    def __init__(self, user_id, pf_paths:Union[str, List[str]], pf_name:str):
        self.user_id = user_id
        self.pf_paths  = pf_paths
        self.pf_name = pf_name
            
        self.all_transactions = SQLiteManagment.retrieve_dataframe_from_sqlite(self.user_id, table_name=self.pf_name)
        self.process_files()
        self.write_to_sqlite()

    def process_files(self): 
        # iterate over the files in the specified directory
        for file_path in self.pf_paths:
            # check if the file is a CSV and if it has not been processed before
            if file_path.endswith('.csv'):
                # read the CSV file into a DataFrame
                df = pd.read_csv(file_path)
                #Reverse rows (transactions) order + reset index
                df = df.loc[::-1].reset_index(drop=True)
                # drop rows that have no date, romve some bugs in data export of degiro
                df = df.dropna(subset=['Date'])       
                # append the data from the CSV file to the all_transactions DataFrame
                self.all_transactions = pd.concat([self.all_transactions, df], ignore_index=True)
                # Necessary drop duplicates (some lines with NaN value are not droped with classical .drop_duplicates() when we retrieve preexisting data)
                                 # Date, Hour, Product, ISIN code, Brokerage fee, Negociated price, Order ID
                column_indices = [0, 1, 2, 3, 14, 16, 18]
                self.all_transactions = self.all_transactions.drop_duplicates(subset=self.all_transactions.columns[column_indices], keep='first')

    def write_to_sqlite(self):
        # Store the DataFrame in the SQLite database table
        SQLiteManagment.store_dataframe_in_sqlite(self.user_id, self.all_transactions, table_name=self.pf_name)


     
         

               
class DataProcess:
    
    def __init__(self, 
                 user_id:str,
                 df:pd.DataFrame, 
                 mapper_df:pd.DataFrame,
                 pf_name:str
                 ):
        
        self.user_id = user_id
        self.df = df
        self.mapper_df = mapper_df
        self.pf_name = pf_name
        
        self.degiro_Date_Hour_format = '%d-%m-%Y %H:%M'
        
        # Clean the dataframe (add columns names, drop duplicates etc)
        self.process_data()
        # Write final transaction files cleaned
        self.write_to_sqlite()
  
    def _check_tickersymbol_column(self):
        # Access rows without value in the 'Ticker Symbol' column
        rows_wo_tick = self.df[self.df['ticker_symbol'].isna()]
        # isin for which we didnt retrieve ticker symbol
        not_found_isin = rows_wo_tick['ISIN_code'].unique().tolist()
        
        if not_found_isin:
            raise ValueError(f"Couldn't find ticker symbol for the following isin codes: {not_found_isin}. Please provide them via the mapper csv file.")
    
    def _get_ticker_symbol_from_isin_via_finnhub(self, ISIN_codes:List[str], CALLS=50, ONE_MINUTE=60):
        
        def get_finnhub_client():
            # Get API key
            FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
            if FINNHUB_API_KEY is None:
                raise ValueError("No API key found. Set the FINNHUB_API_KEY environment variable.")
            # Get finnhub client
            return finnhub.Client(api_key=FINNHUB_API_KEY)

        
        @sleep_and_retry
        @limits(calls=CALLS, period=ONE_MINUTE)
        # 60 api calls max per minute
        def finnhub_api_call_symbl_lookup(finnhub_client, isin) -> Tuple[str, str]:
            output = finnhub_client.symbol_lookup(isin)
            # {'count': 1, 'result': [{'description': 'Tomra Systems ASA', 'displaySymbol': 'TOM.OL', 'symbol': 'TOM.OL', 'type': 'Common Stock'}]}
            return (output['result'][0]['symbol'], output['result'][0]['type']) if len(output['result']) > 0 else (None, None)
        
        def _add_ticker_symbol(row, ISIN_results, ticker_key):
            return ISIN_results[row['ISIN_code']][ticker_key]
        
        def _add_product_type(row, ISIN_results, type_key):
            return ISIN_results[row['ISIN_code']][type_key]
        

        finnhub_c = get_finnhub_client()
        ISIN_results = {}
        
        if ISIN_codes:
            print(f'We will perform 60 API calls per minute to finnhub. Total calls to carry out: {len(ISIN_codes)}. ISIN to fetch: {ISIN_codes}')
            ticker_key, type_key = 'ticker_symbol', 'type'
            
            for isin in ISIN_codes:
                ticker_symbol, product_type = finnhub_api_call_symbl_lookup(finnhub_c, isin)
                ISIN_results[isin] = {ticker_key : ticker_symbol, type_key : product_type}

            # Apply the function to the 'ISIN_code' column and create a new 'ticker_symbol' and 'product_type' column
            self.df['ticker_symbol'] = self.df.apply(lambda row: _add_ticker_symbol(row, ISIN_results, ticker_key)
                                                     if row['ISIN_code'] in ISIN_codes else row['ticker_symbol'], axis=1)
            
            self.df['product_type'] = self.df.apply(lambda row: _add_product_type(row, ISIN_results, type_key)
                                                    if row['ISIN_code'] in ISIN_codes else row['product_type'],axis=1)
        

    def _add_ticker_symbol(self):
        try:
            # Open csv and remove duplicates
            self.mapper_df = self.mapper_df.drop_duplicates()        
            self.mapper_df = self.mapper_df.drop_duplicates(subset="ISIN_code")
            
            # Map 'Ticker Symbol' values (present in file ticker_list) in self.df according to 'Product' 
            self.df['ticker_symbol'] = self.df["ISIN_code"].map(self.mapper_df.set_index("ISIN_code")['ticker_symbol'])
            self.df['product_type'] = self.df["ISIN_code"].map(self.mapper_df.set_index("ISIN_code")['product_type'])   
            
        except Exception as e:
            print(f'{e}')
            # Fallback to this method to get ticker symbols
            #self._get_ticker_symbol_from_isin_via_finnhub()

        if 'ticker_symbol' in self.df.columns:
            wo_ticker_symbol_value = self.df[self.df['ticker_symbol'].isnull()]
            ISIN_codes = wo_ticker_symbol_value['ISIN_code'].unique().tolist()
        else:
            ISIN_codes = self.df['ISIN_code'].unique().tolist()
            
        # If there are lacking tickers/product_type -> get them via finnhub
        self._get_ticker_symbol_from_isin_via_finnhub(ISIN_codes)
            
        self._check_tickersymbol_column()
    


    def process_data(self):
        # Define expected column names
        expected_columns = [
            'date', 'hour', 'product', 'ISIN_code', 'exchange', 'venue', 'quantity', 
            'share_price', 'share_currency', 'total_price', 'currency_TP', 
            'total_price_in_my_currency', 'transact_currency', 'change_rate', 
            'fee', 'currency_fee', 'total_paid', 'currency_paid', 'ID_order'
        ]

        # Validate DataFrame structure
        if self.df.shape[1] != len(expected_columns):
            raise ValueError(f"There should be {len(expected_columns)} columns in the df. We got:\n{self.df.columns}")

        # Rename columns if necessary
        self.df.columns = expected_columns if not all(self.df.columns == expected_columns) else self.df.columns

        # Data cleaning steps
        self.df = self.df.dropna(subset=['date'])
        self.df = self.df.drop_duplicates()
        # Drop row that contains 'NON TRADEABLE' in their product name
        self.df = self.df[~self.df["product"].str.contains("NON TRADEABLE", na=False)]

        # Combine 'date' and 'hour' into a single 'date_hour' column
        self.df['date_hour'] = pd.to_datetime(self.df['date'] + ' ' + self.df['hour'], format=self.degiro_Date_Hour_format)
        self.df = self.df.drop(columns=['date', 'hour'])

        # Format 'date_hour' to string
        self.df['date_hour'] = self.df['date_hour'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # Determine transaction action
        self.df['transaction_action'] = self.df['ID_order'].apply(lambda x: 'real' if isinstance(x, str) and x else 'non_real')

        # Add ticker symbols
        self._add_ticker_symbol()

        # Select relevant columns and derive additional fields
        self.df = self.df[['date_hour', 'quantity', 'ticker_symbol', 'share_price', 'share_currency', 'transact_currency', 'fee', 'transaction_action']]
        self.df['transaction_type'] = self.df['quantity'].apply(lambda x: 'buy' if x > 0 else 'sale')
        self.df['n_shares'] = self.df['quantity'].abs()
        self.df = self.df.drop(columns=['quantity'])



    def write_to_sqlite(self):
        # Store the DataFrame in the SQLite database table
        SQLiteManagment.store_dataframe_in_sqlite(self.user_id, self.df, table_name=self.pf_name)
        
    def get_processed_df(self):
        return(self.df)
    
    
    
    
class CsvProcessor:
    def __init__(self, user_id:str, mapper_file_path:str):
        self.user_id = user_id
        self.sqlite_path = f'Invest_e_Gator\conf\sqlite\{user_id}.db'

        self.mapper_file_path = mapper_file_path  
        
        self.all_transactions_df = pd.DataFrame()
    
    def _validate_csv_paths(self, csv_paths:List[str]):
        # Validate all paths are csv
        for path in csv_paths:
            validate_load_csv(file_path=path)
            
    def _paths_to_list(self, paths:Union[str, List[str]]):
        # If only one path is provided, convert it to a list
        return paths if isinstance(paths, List) else [paths]
            
    def degiro_process_and_store(self, pf_name:str, degiro_csv_paths:Union[str, List[str]]):
        # If only one path is provided, convert it to a list
        degiro_csv_paths = self._paths_to_list(degiro_csv_paths)
        # Validate all paths are csv
        self._validate_csv_paths(degiro_csv_paths)
        
        self._run_csv_processing(pf_name, degiro_csv_paths)
        self._run_data_cleaning(pf_name)
        
    def _run_csv_processing(self, pf_name:str, degiro_csv_paths:Union[str, List[str]]):      
        sqlite_table_name = '_'.join([pf_name, 'all_transactions'])   
        CSVMerger(self.user_id, degiro_csv_paths, sqlite_table_name)
        self.all_transactions_df = SQLiteManagment.retrieve_dataframe_from_sqlite(self.user_id, sqlite_table_name)
        
    def _run_data_cleaning(self, pf_name:str):
        # Init DataProcess object
        DataProcess(
            self.user_id,
            self.all_transactions_df, 
            pd.read_csv(self.mapper_file_path),
            '_'.join([pf_name, 'cleaned_transactions'])
        )

    def csv_process_and_clean(self, pf_name:str, classical_csv_paths:Union[str, List[str]]):
        # If only one path is provided, convert it to a list
        classical_csv_paths = self._paths_to_list(classical_csv_paths)
        # Validate all paths are csv
        self._validate_csv_paths(classical_csv_paths)
        needed_columns = ['date_hour', 'transaction_type', 'ticker_symbol', 'n_shares', 'share_price', 'share_currency', 'transact_currency', 'fee', 'transaction_action']
        
        for path in classical_csv_paths:
            df = pd.read_csv(path, parse_dates=['date_hour'])
        
            for column in needed_columns:
                if column not in df.columns:
                    raise ValueError(f"Column {column} not found in the dataframe.")
            
        # Store the DataFrame in the SQLite database table
        SQLiteManagment.store_dataframe_in_sqlite(self.user_id, df, table_name=pf_name)
        
    def get_cleaned_transactions(self, pf_name:str):
        # Retrieve the portfolio from the sqlite database
        clean_df = SQLiteManagment.retrieve_dataframe_from_sqlite(self.user_id, '_'.join([pf_name, 'cleaned_transactions']))
        # Sort by datetime
        clean_df['date_hour'] = pd.to_datetime(clean_df['date_hour'], format='%Y-%m-%d %H:%M:%S')

        return clean_df.sort_values(by='date_hour')

    
    def merge_cleaned_transactions(self, pfs_names:List[str]):
        fusion_df = pd.DataFrame()
        
        for pf_name in pfs_names:
            # Get cleaned df
            cleaned_df = SQLiteManagment.retrieve_dataframe_from_sqlite(self.user_id, '_'.join([pf_name, 'cleaned_transactions']))
            # Concatenate and remove duplicates
            fusion_df = pd.concat([fusion_df, cleaned_df], ignore_index=True).drop_duplicates()
        
        # Sort by Datetime
        fusion_df['date_hour'] = pd.to_datetime(fusion_df['date_hour'], format='%Y-%m-%d %H:%M:%S')
        fusion_df = fusion_df.sort_values(by='date_hour')

        return fusion_df
    

        
        
        
        
        
        
        
        
    ## LOAD CLASSICAL CSV NON DEGIRO FILE (NEED SOME PREDIFINED COLUMNS)
    ## LOAD CLASSICAL CSV NON DEGIRO FILE (NEED SOME PREDIFINED COLUMNS)
    ## LOAD CLASSICAL CSV NON DEGIRO FILE (NEED SOME PREDIFINED COLUMNS)
    
    ## FUSE PF CLEANED DF ACCORDING TO SOME SELECTED USER'S PF NAMES
    ## FUSE PF CLEANED DF ACCORDING TO SOME SELECTED USER'S PF NAMES
    ## FUSE PF CLEANED DF ACCORDING TO SOME SELECTED USER'S PF NAMES
    ## FUSE PF CLEANED DF ACCORDING TO SOME SELECTED USER'S PF NAMES
    
    ## THEN IN THE PORTFOLIO CLASS JUST SELECT THE PF WE WANT TO ANALYSE
    

    
    



if __name__ == "__main__":
    pf_name='Valola'
    
    degiro_csv_paths=[
        r'C:\Users\V.ozeel\Documents\Perso\Coding\Python\Projects\Finances\Invest_e_Gator\Invest_e_Gator\data\degiro_transactions\Val\transactions\07-09-2024.csv',
        r'C:\Users\V.ozeel\Documents\Perso\Coding\Python\Projects\Finances\Invest_e_Gator\Invest_e_Gator\data\degiro_transactions\Lola\transactions\07-09-2024.csv'
    ]
        
    csv_process = CsvProcessor(
        user_id='Valola',
        mapper_file_path=r'C:\Users\V.ozeel\Documents\Perso\Coding\Python\Projects\Finances\Invest_e_Gator\Invest_e_Gator\data\degiro_transactions\mapper_file.csv'
        )
    
    csv_process.degiro_process_and_store(
        pf_name=pf_name,
        degiro_csv_paths=degiro_csv_paths)
    
    df = csv_process.get_cleaned_transactions(pf_name)
    print(df)
    

    
    
    







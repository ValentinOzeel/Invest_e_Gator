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
                return df if not df.empty else pd.DataFrame()  # Return empty DataFrame instead of None
        except Exception as e:
            print(f'Error retrieving dataframe from db for user {user_id} and table {table_name}: {e}')
            return pd.DataFrame()  # Return empty DataFrame instead of None

        
        
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
        rows_wo_tick = self.df[self.df['Ticker_symbol'].isna()]
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
            ticker_key, type_key = 'ticker', 'type'
            
            for isin in ISIN_codes:
                ticker_symbol, product_type = finnhub_api_call_symbl_lookup(finnhub_c, isin)
                ISIN_results[isin] = {ticker_key : ticker_symbol, type_key : product_type}

            # Apply the function to the 'ISIN_code' column and create a new 'Ticker_symbol' and 'Product_type' column
            self.df['Ticker_symbol'] = self.df.apply(lambda row: _add_ticker_symbol(row, ISIN_results, ticker_key)
                                                     if row['ISIN_code'] in ISIN_codes else row['Ticker_symbol'], axis=1)
            
            self.df['Product_type'] = self.df.apply(lambda row: _add_product_type(row, ISIN_results, type_key)
                                                    if row['ISIN_code'] in ISIN_codes else row['Product_type'],axis=1)
        

    def _add_ticker_symbol(self):
        try:
            # Open csv and remove duplicates
            self.mapper_df = self.mapper_df.drop_duplicates()        
            self.mapper_df = self.mapper_df.drop_duplicates(subset="ISIN_code")
            
            # Map 'Ticker Symbol' values (present in file ticker_list) in self.df according to 'Product' 
            self.df["Ticker_symbol"] = self.df["ISIN_code"].map(self.mapper_df.set_index("ISIN_code")["Ticker_symbol"])
            self.df["Product_type"] = self.df["ISIN_code"].map(self.mapper_df.set_index("ISIN_code")["Product_type"])   
            
        except Exception as e:
            print(f'{e}')
            # Fallback to this method to get ticker symbols
            #self._get_ticker_symbol_from_isin_via_finnhub()

        if 'Ticker_symbol' in self.df.columns:
            wo_ticker_symbol_value = self.df[self.df['Ticker_symbol'].isnull()]
            ISIN_codes = wo_ticker_symbol_value['ISIN_code'].unique().tolist()
        else:
            ISIN_codes = self.df['ISIN_code'].unique().tolist()
            
        # If there are lacking tickers/product_type -> get them via finnhub
        self._get_ticker_symbol_from_isin_via_finnhub(ISIN_codes)
            
        self._check_tickersymbol_column()
    


    def process_data(self):

        # Perform data cleaning and manipulation with the row appended csv file
        #Check if columns are in english 
        column_names = ['Date', 'Hour', 'Product', 'ISIN_code', 'Exchange', 'Venue', 'Quantity', 
                        'Share_price', 'Currency_SP', 'Total_price', 'Currency_TP', 'Total_price_in_my_currency', 
                        'Currency_TPIMC', 'Change_rate', 'Fee', 'Currency_fee', 'Total_paid', 'Currency_paid', 'ID_order', 'user_id']
        # if number columns = number elements in column_names 
        if len(self.df.axes[1]) == len(column_names) :
            #Change column names of the dataframe if df's column names != column_names
            result = all(col1 == col2 for col1, col2 in zip(self.df.columns, column_names))
            if not result:
                self.df.rename(columns=dict(zip(self.df.columns, column_names)), inplace=True) 
        else:
            raise ValueError(f"There should be 20 columns in the df. We got:\n{self.df.columns}")      
            
        # remove rows without date
        self.df.dropna(subset = ['Date'], inplace= True)
        # remove duplicate rows from the all_transactions DataFrame
        self.df = self.df.drop_duplicates().reset_index(drop=True)
        # Drop row that contains 'NON TRADEABLE' in their product name
        self.df = self.df[self.df["Product"].str.contains("NON TRADEABLE") == False]
        # Combine 'date' and 'hour' columns and convert to datetime
        self.df['Datetime'] = pd.to_datetime(self.df['Date'] + ' ' + self.df['Hour'], format=self.degiro_Date_Hour_format)
        self.df = self.df.drop(columns=['Date', 'Hour'])
        ## Convert the datetime to the desired format (american datetime) as string
        self.df['Datetime'] = self.df['Datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        # add detail about transaction: 'real' = deliberate transaction, 'non_real' = transaction due to stok split, reverse split etc...
        self.df['Transaction_action'] = self.df['ID_order'].apply(lambda x: 'real' if isinstance(x, str) and x else 'non_real')
        # Based on the mapper file or morningstar wrapper, add ticker
        self._add_ticker_symbol()

    def write_to_sqlite(self):
        # Store the DataFrame in the SQLite database table
        SQLiteManagment.store_dataframe_in_sqlite(self.user_id, self.df, table_name=self.pf_name)
        
    def get_processed_df(self):
        return(self.df)
    
    
    
    
class DegiroCsvProcess:
    def __init__(self, user_id:str, pf_name:str, degiro_csv_paths:Union[str, List[str]], mapper_file_path:str):
        self.user_id = user_id
        self.pf_name = pf_name
        self.sqlite_path = f'Invest_e_Gator\conf\sqlite\{user_id}.db'
        
        self.degiro_csv_paths = degiro_csv_paths if isinstance(degiro_csv_paths, List) else [degiro_csv_paths]
        self.mapper_file_path = mapper_file_path  
        
        self.all_transactions_df = pd.DataFrame()
        
    def process_and_clean(self):
        self.run_csv_processing()
        self.run_data_cleaning()
        
    def run_csv_processing(self):      
        sqlite_table_name = '_'.join([self.pf_name, 'all_transactions'])   
        CSVMerger(self.user_id, self.degiro_csv_paths, sqlite_table_name)
        self.all_transactions_df = SQLiteManagment.retrieve_dataframe_from_sqlite(self.user_id, sqlite_table_name)
        
    def run_data_cleaning(self):
        # Init DataProcess object
        DataProcess(
            self.user_id,
            self.all_transactions_df, 
            pd.read_csv(self.mapper_file_path),
            '_'.join([self.pf_name, 'cleaned_transactions'])
        )

    def get_cleaned_transactions(self):
        # Retrieve the portfolio from the sqlite database
        clean_df = SQLiteManagment.retrieve_dataframe_from_sqlite(self.user_id, '_'.join([self.pf_name, 'cleaned_transactions']))
        # Sort by datetime
        clean_df['Datetime'] = pd.to_datetime(clean_df['Datetime'], format='%Y-%m-%d %H:%M:%S')

        return clean_df.sort_values(by='Datetime')

        


if __name__ == "__main__":

    degiro_process = DegiroCsvProcess(
        user_id='Valola',
        pf_name='Valola',
        degiro_csv_paths=[
            r'C:\Users\V.ozeel\Documents\Perso\Coding\Python\Projects\Finances\Invest_e_Gator\Invest_e_Gator\data\degiro_transactions\Val\transactions\07-09-2024.csv',
            r'C:\Users\V.ozeel\Documents\Perso\Coding\Python\Projects\Finances\Invest_e_Gator\Invest_e_Gator\data\degiro_transactions\Lola\transactions\07-09-2024.csv'
        ],
        mapper_file_path=r'C:\Users\V.ozeel\Documents\Perso\Coding\Python\Projects\Finances\Invest_e_Gator\Invest_e_Gator\data\degiro_transactions\mapper_file.csv'
        )
    degiro_process.process_and_clean()
    df = degiro_process.get_cleaned_transactions()
    print(df)
    

    
    
    







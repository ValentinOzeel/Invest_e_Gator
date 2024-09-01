import sys
import os

# Now import your modules
from taipy import Gui
from taipy.gui import navigate, notify
import taipy.gui.builder as tgb

import pandas as pd
import json
from Invest_e_Gator.src.portfolio import Portfolio
from Invest_e_Gator.src.degiro_csv_processing import DegiroCsvProcess
from Invest_e_Gator.src.purchase_optimizer import PurchaseOptimizer
from Invest_e_Gator.src.constants import available_currencies

# Initialize global variables
portfolio = Portfolio()
degiro_processor = DegiroCsvProcess()
optimizer = None

# Define data nodes
transactions_data = pd.DataFrame()
portfolio_metrics = pd.DataFrame()
optimization_results = pd.DataFrame()

# Pages variables
root = None
portfolio_page = None
optimization_page = None
transactions_page = None

# Callbacks
def on_load_transactions(state):
    try:
        degiro_processor.process_and_clean(state.file_path)
        state.transactions_data = degiro_processor.processed_dfs.get('Val', pd.DataFrame())
        portfolio.load_transactions_from_csv(state.file_path, degiro=True)
        notify(state, "success", "Transactions loaded successfully!")
    except Exception as e:
        notify(state, "error", f"Error loading transactions: {str(e)}")

def on_compute_metrics(state):
    try:
        portfolio.base_currency = state.base_currency
        metrics = portfolio.compute_portfolio_metrics(today=True)
        state.portfolio_metrics = metrics
        notify(state, "success", "Portfolio metrics computed successfully!")
    except Exception as e:
        notify(state, "error", f"Error computing metrics: {str(e)}")

def on_optimize_purchases(state):
    try:
        global optimizer
        ticker_list = [t.strip() for t in state.ticker_priority.split(',')]
        alloc_dict = json.loads(state.allocations)
        price_dict = json.loads(state.prices)
        
        optimizer = PurchaseOptimizer(state.budget, ticker_list, alloc_dict, price_dict, mode=state.optimization_mode)
        
        if state.optimization_mode == 'strict':
            results, remaining_budget = optimizer.strict_optimizer()
        elif state.optimization_mode == 'progressive':
            results, remaining_budget = optimizer.progressive_optimizer()
        else:  # rounds
            results, remaining_budget = optimizer.rounds_optimizer(0.1)
        
        state.optimization_results = results
        notify(state, "success", f"Optimization completed. Remaining budget: {remaining_budget}")
    except Exception as e:
        notify(state, "error", f"Error in purchase optimization: {str(e)}")


# Define Taipy pages
with tgb.Page() as root:
    tgb.navbar(lov=[
        ('/root', '---'),
        ('/portfolio_page', 'Portofolio page'),
        ('/optimization_page', 'Purchase optimization'), 
        ('/transactions_page', 'Transactions')
        ]
    )
    with tgb.layout("1 1 1"):
        tgb.text('\n')
        tgb.text("## Welcome! Please choose a task", mode="md")
        
# Portfolio Management Page
with tgb.Page() as portfolio_page:
    with tgb.layout("1"):
        tgb.text('## Invest e Gator - Portfolio Management', mode="md")
    with tgb.layout("1 1 1"):
        tgb.file_selector("{file_path}", label='Select CSV file', extensions='.csv', multiple=True, on_change=on_load_transactions)
        tgb.selector("{base_currency}", lov="{available_currencies}", dropdown=True, label='Base Currency')
        tgb.button("Compute Metrics", on_action=on_compute_metrics)

    with tgb.layout("1"):
        tgb.text('\n\n\n')
    with tgb.layout("1"):
        tgb.text('## Results', mode="md")
    with tgb.layout("1"):
        tgb.table("{portfolio_metrics}", label='Portfolio Metrics')
        
# Purchase Optimization Page
with tgb.Page() as optimization_page:
    with tgb.layout("1 1 1 1 1 1 1"):
        tgb.text('## Invest e Gator - Purchase Optimization', mode="md")
        tgb.number("{budget}", label='Budget')
        tgb.input("{ticker_priority}", label='Ticker Priority (comma-separated)')
        tgb.input("{allocations}", label='Allocations (JSON)')
        tgb.input("{prices}", label='Prices (JSON)')
        tgb.selector("{optimization_mode}", lov='strict;progressive;rounds', label='Optimization Mode')
        tgb.button("Optimize Purchases", on_action=on_optimize_purchases)
    with tgb.layout("1 1"):
        tgb.text('## Results', mode="md")
        tgb.table("{optimization_results}", label='Optimization Results')
        
# Transactions Results Page
with tgb.Page() as transactions_page:
    with tgb.layout("1 1"):
        tgb.text('## Invest e Gator - Transactions', mode="md")
        tgb.table("{transactions_data}", label='Transactions')


'''
MAKE PAGE FOR INDICATING EVENT BEARISH OR BULLISH PER TICKER
e.g : UltraBearishEvent, BearishEvent, NeutralEvent, BullishEvent, UltraBullishEvent
Add count of event per ticker followed (+ potential indication of the vent)
'''
# Initialize variables
file_path = ""
base_currency = "USD"
budget = 10000
ticker_priority = ""
allocations = "{}"
prices = "{}"
optimization_mode = "strict"


pages = {"root": root, "portfolio_page": portfolio_page, "optimization_page": optimization_page, "transactions_page": transactions_page}
# Create and run the Taipy app
Gui(pages=pages).run()
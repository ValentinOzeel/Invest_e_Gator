from typing import List, Dict, Union
from datetime import datetime
import numpy as np
import pandas as pd
import copy
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.patches import PathPatch
import matplotlib.path as mpath
import matplotlib.ticker as mtick

from Invest_e_Gator.src.secondary_modules.currency_conversion import currency_conversion
from Invest_e_Gator.src.ticker import Ticker
from Invest_e_Gator.src.constants import available_metrics

class PortfolioMetrics():
    def __init__(self, transactions_df:pd.DataFrame, base_currency:str, start_date:datetime=None, end_date:datetime=None, today:bool=False):
        self.transactions_df = transactions_df
        self.base_currency = base_currency   
        self.today = today        
        # Get days range from start to end
        self.all_dates = self._get_all_dates(start_date, end_date) if not self.today else [datetime.now()]

        self.df_metrics = None
        
    def _get_all_dates(self, start_date:datetime, end_date:datetime):
        if start_date and end_date:
            return pd.date_range(start_date, start_date)
        else:
            # Create a date range from the first to the last transaction date
            start_d = self.transactions_df['date_hour'].min().date() + pd.Timedelta(days=1)
            end_d = self.transactions_df['date_hour'].max().date() + pd.Timedelta(days=1)
            return pd.date_range(start_d, end_d) 
        
    def compute_metrics(self, advanced_metrics:List=None):
                
        # Dict metric : bool_value
        metrics_activation = {}
            
        # build metrics_activation according to privided metrics in list_metrics
        if advanced_metrics:
            # Validate metrics
            if not all([metric in available_metrics for metric in advanced_metrics]):
                raise ValueError(f'All metrics provided as list should be found in the available metrics: {available_metrics}')
            
            metrics_activation = {metric:metric in advanced_metrics for metric in available_metrics}


                
        self.df_metrics = self._compute_general_metrics()
        return self.df_metrics
        
    def _compute_ticker_realized_loss(self, buys:pd.DataFrame, sales:pd.DataFrame):
        
        df_buys, df_sales = copy.deepcopy(buys), copy.deepcopy(sales)

        df_buys = df_buys[df_buys['transaction_action'] == 'real']
        df_sales = df_sales[df_sales['transaction_action'] == 'real']
        
        df_buys['remaining_shares'] = df_buys['n_shares']

        realized_gains_losses = []

        for _, sale in df_sales.iterrows():
            shares_sold = sale['n_shares']
            sale_price = sale['share_price_base_currency']

            remaining_shares_sold = shares_sold

            while remaining_shares_sold > 0 and not df_buys[df_buys['remaining_shares'] > 0].empty:
                # Find the oldest buy with remaining quantity
                for idx, buy in df_buys[df_buys['remaining_shares'] > 0].iterrows():
                    shares_bought = buy['remaining_shares']
                    buy_price = buy['share_price_base_currency']

                    if remaining_shares_sold <= shares_bought:
                        # All of the remaining sale quantity can be matched with this buy
                        realized = (sale_price - buy_price) * remaining_shares_sold
                        realized_gains_losses.append(realized)
                        df_buys.at[idx, 'remaining_shares'] -= remaining_shares_sold
                        remaining_shares_sold = 0
                    else:
                        # Only part of the sale quantity can be matched with this buy
                        realized = (sale_price - buy_price) * shares_bought
                        realized_gains_losses.append(realized)
                        df_buys.at[idx, 'remaining_shares'] = 0
                        remaining_shares_sold -= shares_bought

        return sum(realized_gains_losses)


    def _compute_returns(self, value, realized, invested):
        #print(f'({value} + {realized} - {invested}) / {invested} = {(value + realized - invested) / invested}')
        return (value + realized - invested) / invested
            
    def _compute_general_metrics(self):
        # Initialize a dict to store daily metrics
        daily_metrics = {}
        
        # Iterate over each date
        for selected_date in self.all_dates:
            # Filter out transaction after selected_date
            selected_transactions = self.transactions_df[self.transactions_df['date_hour'] <= selected_date]
            # Initialize dictionaries to store daily metrics
            position_held = {}                  # n financial object helg (exemple: n of shares held)
            position_values = {}                # Daily ticker position value
            position_total_invested = {}        # Daily ticker position invested
            position_realizeds_losses = {}      # Daily ticker realized gains/losses
            position_cost_average = {}          # Daily ticker cost average per share
            position_pl = {}                    # Daily position P/L
            position_ratio_invested = {}        # Daily ticker invested relative to total amount invested
            position_ratio_pf_value = {}        # Daily ticker position value relative to total pf value

            total_value = 0
            total_invested = 0
            total_realized = 0
            
            # Calculate total value and individual stock metrics
            for ticker in selected_transactions['ticker'].unique():
                # Get transactions corresponding to ticker
                ticker_transactions = selected_transactions[selected_transactions['ticker'] == ticker]
                # Get buys and sales transactions
                buys = ticker_transactions[ticker_transactions['transaction_type'] == 'buy']
                sales = ticker_transactions[ticker_transactions['transaction_type'] == 'sale']
                
                # Total share held at day
                quantity = ticker_transactions['quantity'].sum()
                # Total amount investment at day
                total_cost_base_currency = ticker_transactions['transact_amount_base_currency'].sum()
                # Create Ticker object
                ticker_obj = Ticker(ticker)
                
                # Total invested (check if real transaction)
                invested = ticker_transactions[ticker_transactions['transaction_action'] == 'real']['transact_amount_base_currency'].sum()
                #invested = ticker_transactions['transact_amount_base_currency'].sum()
                # Cost average per share
                cost_average = total_cost_base_currency / quantity if quantity else 0
                # Calculate realized gains/losses
                realized = self._compute_ticker_realized_loss(buys, sales)
                # Get day value in base currency
                
                try:
                    day_value_base_currency = currency_conversion(
                        amount=ticker_obj.get_closing_price(selected_date), 
                        date_obj=selected_date, 
                        currency=ticker_obj.currency.lower(), 
                        target_currency=self.base_currency,
                        today=self.today
                    )
                    # Calculate day position value
                    position_value_base_currency = quantity * day_value_base_currency
                except Exception as e:
                    print(e)
                    print(f'{ticker} might have been delisted.')
                    position_value_base_currency = 0
                
                
                # Update dictionnaries
                position_held[ticker] = quantity
                position_values[ticker] = position_value_base_currency
                position_total_invested[ticker] = invested
                position_cost_average[ticker] = cost_average
                position_realizeds_losses[ticker] = realized
                # Update total_value, total_invested and total_realized
                total_value += position_value_base_currency
                total_invested += invested
                total_realized += realized

            # Calculate percentage portfolio value and percentage invested
            for ticker in position_values:
                #print(f'\n{ticker}')
                position_ratio_pf_value[ticker] = position_values[ticker] / total_value if total_value != 0 else 0
                position_ratio_invested[ticker] = position_total_invested[ticker] / total_invested if total_invested != 0 else 0
                position_pl[ticker] = self._compute_returns(position_values[ticker], position_realizeds_losses[ticker], position_total_invested[ticker])


            daily_metrics[selected_date] = {
                'position_held': position_held, 
                'position_values': position_values, 
                'position_invested': position_total_invested,
                'position_cost_average': position_cost_average, 
                'position_realized_gains_losses': position_realizeds_losses, 
                'position_pl': position_pl,
                'position_ratio_invested': position_ratio_invested, 
                'position_ratio_pf_value': position_ratio_pf_value, 
                'total_value': total_value,
                'total_invested': total_invested, 
                'total_realized': total_realized,
                'total_pl': self._compute_returns(total_value, total_realized, total_invested)
                }
            
        
        df = pd.DataFrame.from_dict(daily_metrics, orient='index')
        # Convert index to DateTimeIndex (if not already)
        df.index = pd.to_datetime(df.index)
        return df

    def _plot_current_metrics(self, metrics: pd.DataFrame):
        def get_current_metrics_as_series(df):
            df.index = pd.to_datetime(df.index)
            today = datetime.now()
            df['diff'] = np.abs(df.index - today)
            closest_date_index = df['diff'].idxmin()
            df = df.drop(columns=['diff'])
            closest_row = df.loc[closest_date_index]
            return closest_row

        def create_gradient_bar(ax, x, y, width, height, cmap, norm):
            verts = [(x, 0), (x, height), (x + width, height), (x + width, 0), (x, 0)]
            codes = [mpath.Path.MOVETO, mpath.Path.LINETO, mpath.Path.LINETO, mpath.Path.LINETO, mpath.Path.CLOSEPOLY]
            path = mpath.Path(verts, codes)
            patch = PathPatch(path, facecolor='none', edgecolor='none')
            ax.add_patch(patch)
            gradient = np.linspace(norm(0), norm(height), 256)
            ax.imshow(np.atleast_2d(gradient).T, extent=(x, x + width, 0, height), origin='lower', aspect='auto', cmap=cmap)

        def bar_plot(ax, title, keys, values):
            cmap = cm.get_cmap('viridis')
            norm = plt.Normalize(min(values), max(values))
            for i, key in enumerate(keys):
                create_gradient_bar(ax, i - 0.4, 0, 0.8, values[i], cmap, norm)
            
            ax.set_xticks(range(len(keys)))
            ax.set_xticklabels(keys, rotation=60)
            ax.set_title(title, fontsize=20)
            ax.grid(axis='y', color='black', linestyle='--', alpha=0.5)
            ax.grid(False, axis='x')
            ax.set_axisbelow(True)
            
            if '/' in title:
                ax.yaxis.set_major_formatter(mtick.PercentFormatter(1, 0))
                for i, value in enumerate(values):
                    ax.text(i, value, f'{value*100:.1f}', ha='center', va='bottom', fontsize=6, weight='bold')
            else:
                ax.set_yscale('log')
                for i, value in enumerate(values):
                    ax.text(i, value, f'{value:.0f}', ha='center', va='bottom', fontsize=6, weight='bold')





        def stacked_bars_plot(ax, title, keys, values, stack_values):
            ax.bar(keys, values, color='#5e0000', alpha=0.9)
            ax.bar(keys, stack_values, bottom=0, color='#0d850d', alpha=0.7)
            ax.set_title(title, fontsize=20)
            ax.tick_params(axis='x', rotation=60)
            ax.set_yscale('log')
            ax.grid(axis='y', color='black', linestyle='--', alpha=0.5)
            ax.grid(False, axis='x')
            splits = title.split(' vs ')
            ax.legend(splits)


        def scatter_plot(ax, title, keys, values):
            colors= ['#fde725', '#7ad151', '#22a884', '#2a788e', '#414487', '#440154']
            i, c = 0, []
            for key in keys:
                c.append(colors[i])
                i += 1
                if i == 6: i = 0
            ax.scatter(keys, values, c=c, alpha=0.7)
            ax.set_title(title, fontsize=14)
            ax.tick_params(axis='x', rotation=60)
            ax.grid(axis='y', color='black', linestyle='--', alpha=0.5)
            ax.grid(False, axis='x')


        def radial_chart_plot(ax, title, keys, values):
            max_value_full_ring = max(values)
            ring_colours = ['#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600']  # Adjust colors as needed
            ring_labels = [f'{x} ({v})' for x, v in zip(keys, values)]
            data_len = len(keys)
        
            rect = [0.1, 0.1, 0.3, 0.3]
            ax_polar_bg = fig.add_axes(rect, polar=True, frameon=False)
            ax_polar_bg.set_theta_zero_location('N')
            ax_polar_bg.set_theta_direction(1)
        
            for i in range(data_len):
                ax_polar_bg.barh(i, max_value_full_ring * 1.5 * np.pi / max_value_full_ring, color='grey', alpha=0.1)
            ax_polar_bg.axis('off')
        
            ax_polar = fig.add_axes(rect, polar=True, frameon=False)
            ax_polar.set_theta_zero_location('N')
            ax_polar.set_theta_direction(1)
            ax_polar.set_rgrids(np.linspace(0, max_value_full_ring, data_len), labels=ring_labels, angle=0, fontsize=14, fontweight='bold', color='white', verticalalignment='center')
        
            for i in range(data_len):
                ax_polar.barh(i, values[i] * 1.5 * np.pi / max_value_full_ring, color=ring_colours[i % len(ring_colours)])
        
            ax_polar.grid(False)
            ax_polar.tick_params(axis='both', left=False, bottom=False, labelbottom=False, labelleft=True)
            ax_polar.set_title(title, fontsize=14, color='white')
            
        def pie_plot(ax, title, keys, values):
            wedges, texts, autotexts = ax.pie(values, labels=keys, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired(np.arange(len(keys))))
            ax.set_title(title, fontsize=14)
            for text in texts + autotexts:
                text.set_fontsize(12)

        def text_plot(ax, titles_values):
            to_display = '\n'.join([f'{title} = {value:.2f}' for title, value in titles_values.items()])
            ax.text(0.5, 0.5, to_display, horizontalalignment='center', verticalalignment='center', fontsize=20, transform=ax.transAxes)
            ax.grid(False)
            ax.set_xticks([])
            ax.set_yticks([])

        metrics = get_current_metrics_as_series(metrics)
        fig, axes = plt.subplots(7, 1, figsize=(25, 35))


        plot_instructions = {
            'position_values': [axes[0], 'Position Current Values', bar_plot],
            'position_invested': [axes[1], 'Total Invested', bar_plot],
            'position_ratio_invested': [axes[2], 'Amount Invested / Total Invested', bar_plot],
            'position_ratio_pf_value': [axes[3], 'Position Value / Total Portfolio Value', bar_plot],
            'position_cost_average': [axes[4], 'Cost Average per Share vs Current Share Price', stacked_bars_plot],
            'position_pl': [axes[5], 'P/L', scatter_plot],
            'total_value': [axes[6], 'Portfolio Value', text_plot],
            'total_invested': [axes[6], 'Total Amount Invested', text_plot],
            'total_realized': [axes[6], 'Portfolio Realized Gains/Losses', text_plot],
            'total_pl': [axes[6], 'Portfolio P/L', text_plot],
        }

        single_text_plot = ['total_value', 'total_invested', 'total_realized', 'total_pl']
        to_text_plot = {}

        for metric in metrics.index:
            if metric not in plot_instructions.keys():
                continue
            
            metric_value = metrics.at[metric]
            
            if isinstance(metric_value, Dict):
                metric_value = dict(sorted(metric_value.items(), key=lambda x: x[1]))

            if metric == 'position_cost_average':
                sorting = dict(sorted(metrics.at['position_values'].items(), key=lambda x: x[1]))
                metric_value = dict(sorted(metric_value.items(), key=lambda item: sorting[item[0]]))
                
                current_prices = {ticker: Ticker(ticker).get_closing_price(datetime.now()) for ticker in list(metric_value.keys())}
                current_prices = {key: (value if value is not None else 0) for key, value in current_prices.items()}
                current_prices = dict(sorted(current_prices.items(), key=lambda item: sorting[item[0]]))
                
                stacked_bars_plot(plot_instructions[metric][0], plot_instructions[metric][1], list(metric_value.keys()), list(metric_value.values()), list(current_prices.values()))

            elif metric in single_text_plot:
                to_text_plot[plot_instructions[metric][1]] = metric_value
            
            else:
                plot_instructions[metric][2](
                    ax=plot_instructions[metric][0],
                    title=plot_instructions[metric][1],
                    keys=list(metric_value.keys()),
                    values=list(metric_value.values())
                )

        text_plot(axes[6], to_text_plot)
        
        fig.subplots_adjust(hspace=0.5, top=0.95, bottom=0.05, left=0.05, right=0.95)  # Customize these values as needed

        plt.savefig('enhanced_metrics_plot.png')

        plt.show()

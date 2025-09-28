import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from flask import Flask, render_template
from io import BytesIO
import base64

app = Flask(__name__)

DATA_FILE = '/app/data/nasdaq100_data.csv'
MIN_DD_FILE = '/app/data/min_dd_per_section.csv'
STATIC_IMG_DIR = '/app/static/images'

# Ensure static dir exists
os.makedirs(STATIC_IMG_DIR, exist_ok=True)

@app.route('/')
def dashboard():
    # Load data
    if not os.path.exists(DATA_FILE):
        return "Data file not found. Run initial script first.", 404
    
    data = pd.read_csv(DATA_FILE, index_col='Date', parse_dates=True)
    if os.path.exists(MIN_DD_FILE):
        min_dd = pd.read_csv(MIN_DD_FILE, index_col='Section')
    else:
        min_dd = pd.DataFrame()

    # Calculate daily change rate and current drawdown
    daily_change = 'N/A'
    current_drawdown = 'N/A'

    if len(data) >= 2:
        latest_close = data['Close'].iloc[-1]
        previous_close = data['Close'].iloc[-2]
        daily_change = ((latest_close - previous_close) / previous_close) * 100
        current_drawdown = data['Drawdown'].iloc[-1]
    elif len(data) >= 1:
        current_drawdown = data['Drawdown'].iloc[-1]

    # Calculate statistics for the board, excluding Min-DD == 0
    stats = {
        'daily_change': daily_change,
        'current_drawdown': current_drawdown
    }

    if not min_dd.empty:
        min_dd_series = min_dd['Drawdown']
        # Filter out Min-DD values equal to 0
        filtered_min_dd = min_dd_series[min_dd_series != 0]
        if not filtered_min_dd.empty:
            stats['percentile_1'] = np.percentile(filtered_min_dd, 1)
            stats['percentile_10'] = np.percentile(filtered_min_dd, 10)
            stats['last_min_dd'] = min_dd_series.iloc[-1]  # Last section's Min-DD
            # Calculate percentile of last section's Min-DD, excluding 0s
            stats['last_percentile'] = (np.sum(filtered_min_dd <= stats['last_min_dd']) / len(filtered_min_dd) * 100) if len(filtered_min_dd) > 0 else 100
        else:
            stats.update({'percentile_1': 'N/A', 'percentile_10': 'N/A', 'last_min_dd': min_dd_series.iloc[-1], 'last_percentile': 'N/A'})
    else:
        stats.update({'percentile_1': 'N/A', 'percentile_10': 'N/A', 'last_min_dd': 'N/A', 'last_percentile': 'N/A'})

    # Generate plots
    nasdaq_plot = generate_nasdaq_plot(data)
    dd_plot = generate_drawdown_plot(data, stats.get('percentile_10', 0), stats.get('percentile_1', 0))

    # Convert plots to base64 for embedding
    nasdaq_b64 = plot_to_base64(nasdaq_plot)
    dd_b64 = plot_to_base64(dd_plot)

    return render_template('dashboard.html',
                          nasdaq_plot=nasdaq_b64,
                          dd_plot=dd_b64,
                          stats=stats)

def generate_nasdaq_plot(data):
    fig = Figure(figsize=(10, 5))
    ax = fig.add_subplot(111)
    ax.plot(data.index, data['Close'], label='Nasdaq-100 Close')
    ax.set_title('Nasdaq-100 Index Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('Close Price')
    ax.legend()
    ax.tick_params(axis='x', rotation=45)
    return fig

def generate_drawdown_plot(data, percentile_10, percentile_1):
    fig = Figure(figsize=(10, 5))
    ax = fig.add_subplot(111)
    ax.plot(data.index, data['Drawdown'], label='Drawdown %', color='red')

    # Add horizontal line for 10th percentile
    if isinstance(percentile_10, (int, float)):
        ax.axhline(y=percentile_10, color='green', linestyle='--', label=f'10th Percentile ({percentile_10:.2f}%)')

    # Add horizontal line for 1st percentile
    if isinstance(percentile_1, (int, float)):
        ax.axhline(y=percentile_1, color='orange', linestyle=':', label=f'1st Percentile ({percentile_1:.2f}%)')

    ax.set_title('Drawdown Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('Drawdown (%)')
    ax.legend()
    ax.tick_params(axis='x', rotation=45)
    return fig


def plot_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)  # Prevent memory leak
    return img_base64

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
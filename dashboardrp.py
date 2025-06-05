import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(layout="wide", page_title="Trading Dashboard")

# Add custom CSS for dark theme
st.markdown("""
    <style>
    .stApp {
        background-color: #1a1a1a;
        color: white;
    }
    .metric-container {
        background-color: #2d3035;
        padding: 20px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Function to load and prepare data
def load_data():
    # Replace 'trading_data.csv' with your CSV file path
    # Expected columns: Date, Ticker, Quantity, Price, Value, Cost_Basis
    df = pd.read_csv('newdata.csv')
    df['Date'] = pd.to_datetime(df['Date'], format='mixed')
    return df

# Function to calculate portfolio metrics
def calculate_metrics(df):
    if df is None or df.empty:
        return {
            'total_value': 0,
            'total_return': 0,
            'return_percentage': 0,
            'var_amount': 0,
            'var_percentage': 0,
            'sharpe_ratio': 0
        }
    
    try:
        total_value = df['Value'].sum()
        total_cost = df['Cost_Basis'].sum()
        total_return = total_value - total_cost
        return_percentage = (total_return / total_cost) * 100 if total_cost != 0 else 0
        
        # Calculate VaR (Value at Risk) using historical method
        daily_values = df.groupby('Date')['Value'].sum()
        if len(daily_values) > 1:
            daily_returns = daily_values.pct_change().dropna()
            if not daily_returns.empty:
                var_95 = np.percentile(daily_returns, 5)
                var_amount = total_value * var_95
            else:
                var_95, var_amount = 0, 0
        else:
            var_95, var_amount = 0, 0
        
        # Calculate Sharpe Ratio (assuming risk-free rate of 2%)
        if len(daily_values) > 1:
            daily_returns = daily_values.pct_change().dropna()
            if not daily_returns.empty:
                rf_rate = 0.02
                excess_returns = daily_returns - (rf_rate / 252)  # Daily risk-free rate
                std_dev = excess_returns.std()
                if std_dev > 0:
                    sharpe_ratio = np.sqrt(252) * (excess_returns.mean() / std_dev)
                else:
                    sharpe_ratio = 0  # Set to 0 if there's no variation in returns
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_value': total_value,
            'total_return': total_return,
            'return_percentage': return_percentage,
            'var_amount': var_amount,
            'var_percentage': var_95 * 100,
            'sharpe_ratio': sharpe_ratio
        }
    except Exception as e:
        st.error(f'Error calculating metrics: {str(e)}')
        return {
            'total_value': 0,
            'total_return': 0,
            'return_percentage': 0,
            'var_amount': 0,
            'var_percentage': 0,
            'sharpe_ratio': 0
        }

def main():
    st.title('Trading Portfolio Dashboard')
    
    # Load data
    try:
        df = load_data()
    except FileNotFoundError:
        st.error('Please ensure trading_data.csv exists in the same directory')
        return
    
    metrics = calculate_metrics(df)
    
    # Create layout with columns
    col1, col2, col3 = st.columns(3)
    
    # Portfolio Value
    with col1:
        st.metric(
            "Portfolio Value",
            f"${metrics['total_value']:,.2f}",
            f"{metrics['return_percentage']:,.1f}%"
        )
    
    # Value at Risk
    with col2:
        st.metric(
            "Value at Risk (95%)",
            f"${abs(metrics['var_amount']):,.2f}",
            f"{metrics['var_percentage']:,.1f}%"
        )
    
    # Sharpe Ratio
    with col3:
        st.metric(
            "Sharpe Ratio",
            f"{metrics['sharpe_ratio']:.2f}"
        )
    
    # Create charts
    st.subheader('Portfolio Performance')
    
    # Portfolio Value Chart
    daily_value = df.groupby('Date')['Value'].sum().reset_index()
    if not daily_value.empty:
        fig_value = go.Figure()
        fig_value.add_trace(go.Scatter(
            x=daily_value['Date'],
            y=daily_value['Value'],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#3366CC')
        ))
        fig_value.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            margin=dict(l=0, r=0, t=0, b=0),
            yaxis_title='Value ($)',
            height=300
        )
        st.plotly_chart(fig_value, use_container_width=True)
    else:
        st.warning('No time series data available for the portfolio value chart.')
    
    # Growth Comparison Chart
    st.subheader('Growth Rate Comparison')
    
    # Calculate growth rates
    if not daily_value.empty:
        initial_value = daily_value['Value'].iloc[0]
        
        comparison_data = []
        for index, row in daily_value.iterrows():
            days_passed = (row['Date'] - daily_value['Date'].iloc[0]).days
            current_value = row['Value']
            
            # Calculate growth rates
            portfolio_growth = ((current_value - initial_value) / initial_value) * 100
            treasury_growth = (pow(1.045, days_passed/365) - 1) * 100  # 4.5% annual
            spy_growth = ((pow(1.10, days_passed/365) - 1) * 100)  # 10% annual
            
            comparison_data.append({
                'Date': row['Date'],
                'Portfolio': portfolio_growth,
                'Treasury': treasury_growth,
                'SPY': spy_growth
            })
            
        fig_comparison = go.Figure()
        
        # Add traces for each line
        fig_comparison.add_trace(go.Scatter(
            x=[d['Date'] for d in comparison_data],
            y=[d['Portfolio'] for d in comparison_data],
            mode='lines',
            name='Portfolio',
            line=dict(color='#4ade80', width=2)
        ))
        
        fig_comparison.add_trace(go.Scatter(
            x=[d['Date'] for d in comparison_data],
            y=[d['Treasury'] for d in comparison_data],
            mode='lines',
            name='Treasury',
            line=dict(color='#60a5fa', width=2)
        ))
        
        fig_comparison.add_trace(go.Scatter(
            x=[d['Date'] for d in comparison_data],
            y=[d['SPY'] for d in comparison_data],
            mode='lines',
            name='SPY',
            line=dict(color='#f87171', width=2)
        ))
        
        fig_comparison.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            margin=dict(l=0, r=0, t=0, b=0),
            yaxis_title='Growth Rate (%)',
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)
    else:
        st.warning('No data available for growth comparison chart.')

    # Position Stats Table
    st.subheader('Position Stats')
    if not df.empty:
        position_stats = df.groupby('Ticker').agg({
            'Quantity': 'sum',
            'Value': 'sum',
            'Cost_Basis': 'sum'
        }).reset_index()
        
        position_stats['Gain'] = position_stats['Value'] - position_stats['Cost_Basis']
        position_stats['Gain_Percentage'] = (position_stats['Gain'] / position_stats['Cost_Basis']) * 100
        position_stats['Portfolio_Percentage'] = (position_stats['Value'] / position_stats['Value'].sum()) * 100
        
        st.dataframe(
            position_stats.style.format({
                'Value': '${:,.2f}',
                'Cost_Basis': '${:,.2f}',
                'Gain': '${:,.2f}',
                'Gain_Percentage': '{:,.1f}%',
                'Portfolio_Percentage': '{:,.1f}%'
            }),
            hide_index=True
        )
    else:
        st.warning('No position data available for the statistics table.')

if __name__ == '__main__':
    main()
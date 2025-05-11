import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- App Config ---
st.set_page_config(layout="wide", page_title="Product Performance Hub")

# --- Cached Data Generation Function (from your Version 1) ---
@st.cache_data
def generate_initial_data():
    product_names = ["Aurora Buds", "Nova Mug", "Zenith Mat", "Lumos Lamp", "Terra SSD", "Helios Charger", "Orion Mousepad"]
    product_categories_map = {
        "Aurora Buds": "Electronics", "Nova Mug": "Home Goods", "Zenith Mat": "Wellness",
        "Lumos Lamp": "Office", "Terra SSD": "Electronics", "Helios Charger": "Electronics", "Orion Mousepad": "Office"
    }
    channels = ["Organic", "Paid Social", "Email", "Affiliate"]
    num_months = 12
    products_data = []
    for i, name in enumerate(product_names):
        rev_trend = np.clip(np.random.randint(300,1500) + np.cumsum(np.random.randint(-100,150,size=num_months)), 50, None)
        units_trend = np.clip(np.random.randint(10,80) + np.cumsum(np.random.randint(-10,20,size=num_months)), 5, None)
        chan_dist = np.random.dirichlet(np.ones(len(channels)),size=1)[0]*100
        products_data.append({
            "ID": f"P{i+201}", "Name": name, "Category": product_categories_map[name],
            "YTD Revenue": int(np.sum(rev_trend[-3:])), # Original YTD from last 3 months
            "YTD Units": int(np.sum(units_trend[-3:])), # Original YTD from last 3 months
            "Revenue Trend": rev_trend.tolist(),
            "Units Trend": units_trend.tolist(),
            "Rating": round(random.uniform(3.5,4.9),1), "Stock": random.choice(["In Stock","Low","Out"]),
            "Channels %": {ch:round(d,1) for ch,d in zip(channels,chan_dist)},
            "Target Met %": random.randint(60,125)
        })
    df = pd.DataFrame(products_data).set_index("ID")
    return df

df_products = generate_initial_data()

# --- Sidebar for Parameters ---
with st.sidebar:
    st.header("⚙️ Dashboard Parameters")

    st.subheader("Comparison View Settings")
    sort_by_options = {"YTD Revenue": "YTD Revenue", "Rating": "Rating", "YTD Units Sold": "YTD Units"}
    selected_sort_by_display = st.selectbox("Sort products by:", list(sort_by_options.keys()), index=0)
    sort_column = sort_by_options[selected_sort_by_display]
    sort_ascending = st.checkbox("Sort Ascending?", False)
    num_comparison_cols = st.slider("Number of columns for product comparison:", min_value=1, max_value=7, value=3)

    st.subheader("Target Performance Colors")
    target_good_threshold = st.number_input("Good 'Target Met %' if >= :", min_value=0, max_value=200, value=100, step=5)
    target_warning_threshold = st.number_input("Warning 'Target Met %' if >= :", min_value=0, max_value=target_good_threshold-1, value=80, step=5)

# Minimal CSS for basic font (Here I used AI only)
st.markdown("""
<style>
    body { font-family: 'Arial', sans-serif; }
</style>""", unsafe_allow_html=True)

# --- Main Dashboard ---
st.title("📈 Comprehensive Product Insights Hub")
st.markdown("Explore detailed sales performance, uncover trends, and analyze channel & category contributions to drive strategic decisions.")
st.markdown("---")

# --- Overall KPIs ---
st.header("Overall Business Health (YTD)")
kpi_cols = st.columns(3)
kpi_cols[0].metric(label="Total Revenue", value=f"${df_products['YTD Revenue'].sum():,}")
kpi_cols[1].metric(label="Total Units Sold", value=f"{df_products['YTD Units'].sum():,}")
kpi_cols[2].metric(label="Avg. Product Rating", value=f"{df_products['Rating'].mean():.1f} ⭐")
st.markdown("---")

# --- Product Deep Dive ---
st.header("📊 Product Deep Dive")
selected_name = st.selectbox("Select Product:", df_products["Name"].tolist(), label_visibility="collapsed", key="product_deep_dive_select")
product = df_products[df_products["Name"] == selected_name].iloc[0]

with st.expander(f"Details for: {product['Name']}", expanded=True):
    main_cols = st.columns([0.4, 0.6])
    with main_cols[0]:
        st.subheader("Product Info")
        stock_level_product = product['Stock']
        stock_color_product = {"In Stock":"green", "Low":"orange", "Out":"red"}.get(stock_level_product, "grey")
        st.markdown(f"**Category:** {product['Category']}")
        st.markdown(f"**YTD Revenue:** ${product['YTD Revenue']:,}")
        st.markdown(f"**YTD Units:** {product['YTD Units']:,}")
        st.markdown(f"**Rating:** {product['Rating']:.1f} ⭐")
        st.markdown(f"**Stock:** <span style='color:{stock_color_product}; font-weight:bold;'>{stock_level_product}</span>", unsafe_allow_html=True)

        st.subheader("Channel Revenue Share")
        if product['Channels %']:
            channel_df = pd.DataFrame(list(product['Channels %'].items()), columns=['Channel', 'Share'])
            fig_donut = go.Figure(data=[go.Pie(labels=channel_df['Channel'],
                                               values=channel_df['Share'],
                                               hole=.5,
                                               marker_colors=px.colors.qualitative.Pastel1,
                                               textinfo='label+percent',
                                               pull=[0.02]*len(channel_df),
                                               insidetextorientation='radial' # Helps with label fitting
                                               )])
            fig_donut.update_layout(
                margin=dict(t=5,b=5,l=5,r=5),
                height=220,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)', # Transparent paper
                plot_bgcolor='rgba(0,0,0,0)'  # Transparent plot area
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.write("No channel data available.")

    with main_cols[1]:
        st.subheader("Monthly Sales Trends")
        trend_df = pd.DataFrame({'Month': pd.to_datetime([f"2023-{m:02d}-01" for m in range(1,13)]),
                                'Revenue ($)': product['Revenue Trend'], 'Units Sold': product['Units Trend']})

        fig_dual_axis = make_subplots(specs=[[{"secondary_y": True}]])
        fig_dual_axis.add_trace(go.Scatter(x=trend_df['Month'], y=trend_df['Revenue ($)'], name='Revenue ($)',
                                        mode='lines', line=dict(color='#007bff', width=2.5)), secondary_y=False)
        fig_dual_axis.add_trace(go.Scatter(x=trend_df['Month'], y=trend_df['Units Sold'], name='Units Sold',
                                        mode='lines', line=dict(color='#28a745', width=2.5)), secondary_y=True)
        fig_dual_axis.update_layout(
            height=300,
            margin=dict(t=20,b=20,l=0,r=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, linecolor='rgba(0,0,0,0.2)', mirror=True), # Subtle axis line, no grid
            yaxis=dict(showgrid=True, gridcolor='rgba(233, 236, 239, 0.6)', zeroline=False, title_text="Revenue ($)", tickprefix="$", linecolor='rgba(0,0,0,0.2)', mirror=True), # Lighter grid for primary
            yaxis2=dict(showgrid=False, zeroline=False, title_text="Units Sold", linecolor='rgba(0,0,0,0.2)', mirror=True) # No grid for secondary, subtle axis line
        )
        st.plotly_chart(fig_dual_axis, use_container_width=True)
st.markdown("---")

# --- Comparative Product Snapshot ---
st.header("🚀 All Products at a Glance")
sorted_products_df = df_products.sort_values(by=sort_column, ascending=sort_ascending)
comp_cols = st.columns(num_comparison_cols)

for i, (idx, prod_data) in enumerate(sorted_products_df.iterrows()):
    col_idx = i % num_comparison_cols
    with comp_cols[col_idx]:
        with st.expander(f"{prod_data['Name']}"):
            st.caption(f"Category: {prod_data['Category']}")
            st.metric("Revenue", f"${prod_data['YTD Revenue']:,}")
            st.metric("Units", f"{prod_data['YTD Units']:,}")

            stock_level_comp = prod_data['Stock']
            stock_color_comp = {"In Stock":"green", "Low":"orange", "Out":"red"}.get(stock_level_comp, "grey")
            st.markdown(f"**Rating:** {prod_data['Rating']:.1f}⭐ | **Stock:** <span style='color:{stock_color_comp}; font-weight:bold;'>{stock_level_comp}</span>", unsafe_allow_html=True)

            target_met_val = prod_data['Target Met %']
            st.markdown(f"**Target Met:** {target_met_val}%")
            st.progress(min(target_met_val, 100) / 100)

            if target_met_val >= target_good_threshold: status_emoji = "✅ Good"
            elif target_met_val >= target_warning_threshold: status_emoji = "⚠️ Warning"
            else: status_emoji = "❌ Needs Improvement"
            st.markdown(f"**Target Status:** {status_emoji}")

st.markdown("---")

# --- Category Performance Section ---
st.header("🗂️ Category Performance (YTD Revenue)")
category_performance = df_products.groupby("Category")["YTD Revenue"].sum().sort_values(ascending=True)
if not category_performance.empty:
    fig_cat_perf = px.bar(category_performance, x=category_performance.values, y=category_performance.index,
                          orientation='h', labels={'y': 'Category', 'x': 'YTD Revenue ($)'},
                          text=category_performance.values)
    fig_cat_perf.update_traces(texttemplate='$%{text:,.0f}', textposition='outside', marker_color=px.colors.qualitative.Plotly)
    fig_cat_perf.update_layout(
        height=max(200, len(category_performance) * 40 + 50),
        yaxis_title=None, # Let px.bar handle from 'labels' or remove if not desired
        xaxis_title=None, # Let px.bar handle from 'labels' or remove if not desired
        yaxis=dict(
            categoryorder='total ascending',
            linecolor='rgba(0,0,0,0.2)',
            mirror=True
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            linecolor='rgba(0,0,0,0.2)',
            mirror=True
        ),
        margin=dict(t=20, b=20, l=100, r=10), # Increased left margin for category labels
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_cat_perf, use_container_width=True)
else:
    st.write("No category data to display.")

# --- Footer ---
st.markdown("---")
st.caption(
    "**Purpose:** Data Visualization and Decision-Making. "
    "This dashboard utilizes randomly generated data solely for the "
    "Interactive Application Development II assignment."
)
st.caption("**Author**: Antonio Karl Lamúa Gómez")

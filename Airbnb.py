import pandas as pd
from pymongo import MongoClient
import streamlit as st
import folium
from streamlit_folium import folium_static
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

# MongoDB Connection and Data Retrieval
def connect_to_mongodb():
    client = MongoClient('your_connection_string')  # Replace with your connection string
    db = client['sample_airbnb']
    listings = db['listingsAndReviews']
    df = pd.DataFrame(list(listings.find()))
    return df

def clean_data(df):
    # Handle missing values
    df.fillna(method='ffill', inplace=True)
    
    # Remove duplicates
    df.drop_duplicates(inplace=True)
    
    # Convert data types
    df['price'] = df['price'].replace('[\$,]', '', regex=True).astype(float)
    df['availability.start_date'] = pd.to_datetime(df['availability.start_date'])
    df['availability.end_date'] = pd.to_datetime(df['availability.end_date'])
    return df

# Geospatial Visualization with Streamlit
def create_map(df):
    map_center = [df['location.coordinates'].apply(lambda x: x[1]).mean(), df['location.coordinates'].apply(lambda x: x[0]).mean()]
    map = folium.Map(location=map_center, zoom_start=12)

    for _, row in df.iterrows():
        folium.Marker(
            location=[row['location.coordinates'][1], row['location.coordinates'][0]],
            popup=row['name'],
            tooltip=f"Price: ${row['price']}"
        ).add_to(map)

    return map

def streamlit_app(df):
    st.title('Airbnb Listings Visualization')

    map = create_map(df)
    folium_static(map)

    st.write("### Listings Overview")
    st.dataframe(df[['name', 'price', 'neighbourhood', 'location.coordinates']])

    st.write("### Price Distribution by Neighbourhood")
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='neighbourhood', y='price', data=df)
    plt.xticks(rotation=90)
    plt.title('Price Variation by Neighbourhood')
    st.pyplot()

    st.write("### Availability by Season")
    df['month'] = df['availability.start_date'].dt.month
    df['season'] = df['month'].apply(lambda x: 'Winter' if x in [12, 1, 2] else 'Spring' if x in [3, 4, 5] else 'Summer' if x in [6, 7, 8] else 'Fall')
    availability_by_season = df.groupby('season')['availability.start_date'].count()
    plt.figure(figsize=(10, 6))
    sns.lineplot(x=availability_by_season.index, y=availability_by_season.values)
    plt.title('Availability by Season')
    st.pyplot()

    st.write("### Interactive Price Map")
    fig = px.scatter_mapbox(df, lat=df['location.coordinates'].apply(lambda x: x[1]), lon=df['location.coordinates'].apply(lambda x: x[0]),
                             hover_name="name", hover_data=["price", "neighbourhood"],
                             color="price", size_max=15, zoom=10)
    fig.update_layout(mapbox_style="carto-positron")
    st.plotly_chart(fig)

    st.write("### Location-Based Insights")
    region = st.selectbox('Select Region', df['neighbourhood'].unique())
    region_df = df[df['neighbourhood'] == region]
    region_map = folium.Map(location=[region_df['location.coordinates'].apply(lambda x: x[1]).mean(), region_df['location.coordinates'].apply(lambda x: x[0]).mean()], zoom_start=12)
    
    for _, row in region_df.iterrows():
        folium.Marker(
            location=[row['location.coordinates'][1], row['location.coordinates'][0]],
            popup=row['name'],
            tooltip=f"Price: ${row['price']}"
        ).add_to(region_map)
    folium_static(region_map)

def main():
    st.sidebar.title('Airbnb Analysis')
    st.sidebar.write('Select an option:')
    choice = st.sidebar.radio('Navigation', ['Home', 'Data Visualization'])

    if choice == 'Home':
        st.write("# Welcome to the Airbnb Analysis Project")
        st.write("This project visualizes and analyzes Airbnb listings data from MongoDB.")
        st.write("Use the sidebar to navigate through the application.")

    elif choice == 'Data Visualization':
        st.write("# Data Visualization")
        df = connect_to_mongodb()
        df = clean_data(df)
        streamlit_app(df)

if __name__ == "__main__":
    main()

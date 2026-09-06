# Action Plan – Avocado Prices Interactive Dashboard

## Project Goal

The goal of this project is to build an interactive dashboard for exploring avocado prices and sales volume using the Avocado Prices 2020 dataset.

The dashboard will be developed using Python, pandas, Plotly, and Dash, and deployed as a web application using Render.

## Dataset

The project uses the Avocado Prices 2020 dataset.

The dataset contains information including:

- Date
- Average avocado price
- Total volume
- Avocado type
- Geography
- PLU sales volume
- Bag sizes

## Dashboard Features

The dashboard will include interactive controls for:

- Date range
- Avocado type (Conventional / Organic)
- Geography level
- Region selection

## Key Performance Indicators

The dashboard will display:

- Average Price
- Total Volume
- Total Bags
- Price Change

## Visualisations

The dashboard will include:

1. Price Trends
   - Weekly price trends
   - Monthly price trends

2. Regional Comparison
   - Average price by region
   - Price versus sales volume

3. Volume and Bag Mix
   - PLU sales volume
   - Bag size distribution

4. Raw Data
   - Filtered dataset displayed in tabular form

## Technical Approach

The application will use:

- Python for application development
- pandas for data processing and analysis
- Plotly for interactive visualisations
- Dash for the dashboard interface and callbacks
- Gunicorn as the production server
- Render.com for web deployment

The existing analytical logic will be preserved where possible while the user interface is implemented using Dash components and callbacks.

## Deployment Plan

The completed project will be stored in a GitHub repository.

Render will connect to the GitHub repository and deploy the Dash application as a web service.

The application will use:

Build command:

`pip install -r requirements.txt`

Start command:

`gunicorn app:server`

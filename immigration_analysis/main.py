# Import all necessary libraries
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

# Load the data
dataset_austria = pd.read_csv('data/DatasetAustria.csv', delimiter=';')
dataset_countries = pd.read_csv('data/DatasetCountries.csv', delimiter=';')

# Merge the datasets and rename columns
dataset_austria = pd.merge(dataset_austria, dataset_countries[['code', 'name']], left_on='C-GHZLAND-0', right_on='code')
dataset_austria = dataset_austria.drop(columns=['code', 'C-GHZLAND-0'])
dataset_austria = dataset_austria.rename(columns={'name': 'country'})

# Only European countries
european_countries = [
    'Albanien', 'Andorra', 'Belgien', 'Bosnien und Herzegowina', 'Bulgarien', 'Dänemark', 'Deutschland',
    'Estland', 'Finnland', 'Frankreich', 'Griechenland', 'Irland', 'Island', 'Italien', 'Kroatien',
    'Lettland', 'Liechtenstein', 'Litauen', 'Luxemburg', 'Malta', 'Moldau', 'Monaco', 'Montenegro',
    'Niederlande', 'Nordmazedonien', 'Norwegen', 'Polen', 'Portugal', 'Rumänien', 'San Marino',
    'Schweden', 'Schweiz', 'Serbien', 'Slowakei', 'Slowenien', 'Spanien', 'Tschechische Republik', 'Ukraine', 'Ungarn',
    'Vatikan', 'Vereinigtes Königreich', 'Belarus'
]
dataset_austria = dataset_austria[dataset_austria['country'].isin(european_countries)]

# Rename columns
dataset_austria = dataset_austria.rename(columns={
    'C-A10-0': 'year',
    'C-STAATEN_DICHOTOM-0': 'nationality',
    'C-GALT5J100-0': 'age_group',
    'F-ZUZUEGE': 'moved_to',
    'F-WEGZUEGE': 'moved_away'
})

# Cut off unwanted words
dataset_austria['age_group_numeric'] = dataset_austria['age_group'].str.extract('(\d+)$').astype(int)
dataset_austria['year_numeric'] = dataset_austria['year'].str.extract('(\d+)$').astype(int)

# Replace German country names with English names
country_mapping = {
    'Albanien': 'Albania',
    'Andorra': 'Andorra',
    'Belgien': 'Belgium',
    'Bosnien und Herzegowina': 'Bosnia and Herzegovina',
    'Bulgarien': 'Bulgaria',
    'Dänemark': 'Denmark',
    'Deutschland': 'Germany',
    'Estland': 'Estonia',
    'Finnland': 'Finland',
    'Frankreich': 'France',
    'Griechenland': 'Greece',
    'Irland': 'Ireland',
    'Island': 'Iceland',
    'Italien': 'Italy',
    'Kroatien': 'Croatia',
    'Lettland': 'Latvia',
    'Liechtenstein': 'Liechtenstein',
    'Litauen': 'Lithuania',
    'Luxemburg': 'Luxembourg',
    'Malta': 'Malta',
    'Moldau': 'Moldova',
    'Monaco': 'Monaco',
    'Montenegro': 'Montenegro',
    'Niederlande': 'Netherlands',
    'Nordmazedonien': 'North Macedonia',
    'Norwegen': 'Norway',
    'Polen': 'Poland',
    'Portugal': 'Portugal',
    'Rumänien': 'Romania',
    'San Marino': 'San Marino',
    'Schweden': 'Sweden',
    'Schweiz': 'Switzerland',
    'Serbien': 'Serbia',
    'Slowakei': 'Slovakia',
    'Slowenien': 'Slovenia',
    'Spanien': 'Spain',
    'Tschechische Republik': 'Czech Republic',
    'Ukraine': 'Ukraine',
    'Ungarn': 'Hungary',
    'Vatikan': 'Vatican',
    'Vereinigtes Königreich': 'United Kingdom',
    'Belarus': 'Belarus'
}

dataset_austria['country'] = dataset_austria['country'].replace(country_mapping)

# Change age groups to ten year range
def pair_age_groups(age_group):
    if age_group in [1, 2]:
        return '0-9'
    elif age_group in [3, 4]:
        return '10-19'
    elif age_group in [5, 6]:
        return '20-29'
    elif age_group in [7, 8]:
        return '31-39'
    elif age_group in [9, 10]:
        return '40-49'
    elif age_group in [11, 12]:
        return '50-59'
    elif age_group in [13, 14]:
        return '60-69'
    elif age_group in [15, 16]:
        return '70-79'
    elif age_group in [17, 18]:
        return '80-89'
    else:
        return'90+'
dataset_austria['paired_age_group'] = dataset_austria['age_group_numeric'].apply(pair_age_groups)

# Build the different datasets
country_balance_total = dataset_austria.groupby('country').agg({
    'moved_to': 'sum',
    'moved_away': 'sum'
}).reset_index()
country_balance_total['balance'] = country_balance_total['moved_to'] - country_balance_total['moved_away']

country_yearly = dataset_austria.groupby(['country', 'year_numeric']).agg({
    'moved_to': 'sum',
    'moved_away': 'sum'
}).reset_index()

country_agegroup_paired = dataset_austria.groupby(['country', 'paired_age_group']).agg({
    'moved_to': 'sum',
    'moved_away': 'sum'
}).reset_index()

# Dash-App
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True
app.layout = html.Div([
    html.H1("Migration Trends Austria since 2002", style={'font-family': 'Arial', 'font-size': '18px', 'text-align': 'center'}),
    html.Div([
        dcc.Graph(id='choropleth-map')
    ], style={'width': '50%', 'float': 'left', 'margin-top': '30px'}),
    html.Div([
            dcc.Dropdown(
                id='country-dropdown',
                options=[{'label': country, 'value': country} for country in country_mapping.values()],
                value='Germany',  # Default value
                clearable=False
            ),
            dcc.Graph(id='line-plot'),
        ], style={'width': '50%', 'float': 'right'}),
        html.Div([
            dcc.Graph(id='bar-chart')
        ], style={'width': '100%', 'margin-top': '450px'})

])

# Choropleth-map
@app.callback(
    Output('choropleth-map', 'figure'),
    Input('choropleth-map', 'clickData')
)
def update_map(clickData):
    fig = px.choropleth(country_balance_total, locations='country', locationmode='country names',
                        color='balance', hover_name='country',
                        color_continuous_scale=px.colors.sequential.Plasma,
                        title='Migration Balance in Europe',
                        scope='europe')
    fig.update_geos(
        projection_scale=2,
        center={"lat": 50, "lon": 10}
    )
    return fig
# Linechart
@app.callback(
    Output('line-plot', 'figure'),
    Input('country-dropdown', 'value')
)
def update_line_plot(selected_country):
    country_data = country_yearly[country_yearly['country'] == selected_country]
    fig = px.line(
        country_data,
        x='year_numeric',
        y=['moved_to', 'moved_away'],
        title=f'Migration Trends for {selected_country}',
        labels={'year_numeric': 'Year', 'value': 'Number of People'}
    )
    fig.update_traces(hovertemplate='%{y}<extra></extra>')
    fig.update_layout(
        height=400,  # Set a suitable height
        margin=dict(l=40, r=40, t=40, b=60),  # Adjust margins
        xaxis_title='Year',
        yaxis_title='Number of People',
        legend_title_text='',
        xaxis=dict(
            tickmode='linear',
            tick0=country_data['year_numeric'].min(),
            dtick=1,
            tickangle=45
        )
    )
    fig.for_each_trace(
        lambda t: t.update(name=t.name.replace('moved_to', 'Moved to').replace('moved_away', 'Moved away')))
    return fig


# Bar Chart
@app.callback(
    Output('bar-chart', 'figure'),
    Input('country-dropdown', 'value')
)
def update_bar_chart(selected_country):
    country_data = country_agegroup_paired[country_agegroup_paired['country'] == selected_country]
    fig = px.bar(country_data, x='paired_age_group', y=['moved_to', 'moved_away'],
                 title=f'Migration by Age Group for {selected_country}',
                 barmode='group',
                 labels={'value': 'Number of People', 'variable': '', 'paired_age_group': 'Age Group'})  # Remove variable label
    fig.for_each_trace(
        lambda t: t.update(name=t.name.replace('moved_to', 'Moved to').replace('moved_away', 'Moved away')))
    fig.update_layout(legend_title_text='')
    fig.update_traces(
        hovertemplate='Number of People: %{y}<extra></extra>')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

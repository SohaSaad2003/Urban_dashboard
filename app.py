from flask import Flask, render_template, request, redirect, url_for, flash
import os
import geopandas as gpd
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Setup upload folder (for reading pre-existing files)
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load and process GeoJSON files
def load_geojson(file_path):
    try:
        gdf = gpd.read_file(file_path)
        required_cols = ['name:ar', 'name:en', 'amenity', 'addr:street']
        for col in required_cols:
            if col not in gdf.columns:
                gdf[col] = None
        return gdf
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def classify_districts(gdf):
    # Handle missing addr:street by setting district to "غير معروف"
    gdf['district'] = gdf['addr:street'].apply(
        lambda x: x.split()[0] if pd.notnull(x) and len(str(x).split()) > 0 else 'غير معروف'
    )
    return gdf

def analyze_data(gdf, region_name):
    # Filter homes and services
    homes = gdf[gdf['amenity'] == 'residential'] if 'amenity' in gdf.columns else pd.DataFrame()

    services = gdf[gdf['amenity'] != 'residential'] if 'amenity' in gdf.columns else gdf

    total_homes = len(homes)
    total_services = len(services)

    if total_homes == 0:
        print(f"Warning: No residential data found for {region_name}")
    if total_services == 0:
        print(f"Warning: No services data found for {region_name}")

    # Analyze services by type
    services_by_type = services['amenity'].value_counts().reset_index()
    services_by_type.columns = ['Service Type', 'Count']

    # Top streets for services and homes
    top_service_streets = services['addr:street'].value_counts().head(5).reset_index()
    top_service_streets.columns = ['Street', 'Service Count']
    top_service_streets['Street'] = top_service_streets['Street'].fillna('غير معروف')

    top_home_streets = homes['addr:street'].value_counts().head(5).reset_index()
    top_home_streets.columns = ['Street', 'Home Count']
    top_home_streets['Street'] = top_home_streets['Street'].fillna('غير معروف')

    # Prepare map data
    map_data = services[['geometry', 'amenity', 'name:en', 'district']].copy()
    if 'geometry' in map_data.columns and map_data.geometry.notnull().any():
        map_data['lon'] = map_data.geometry.apply(lambda x: x.x if x else None)
        map_data['lat'] = map_data.geometry.apply(lambda x: x.y if x else None)
    else:
        map_data['lon'] = None
        map_data['lat'] = None
        print(f"Warning: No valid geometry data for {region_name} map")

    return {
        'total_homes': total_homes,
        'total_services': total_services,
        'services_by_type': services_by_type.to_dict('records'),
        'top_service_streets': top_service_streets.to_dict('records'),
        'top_home_streets': top_home_streets.to_dict('records'),
        'services': services,
        'homes': homes,
        'map_data': map_data.to_dict('records')
    }

# Define regions using the provided paths
regions = {
    "Madinaty": os.path.join(UPLOAD_FOLDER, "madinaty.geojson"),
    "10th of Ramadan": os.path.join(UPLOAD_FOLDER, "10_of_ramdan_restored2.geojson"),
    "6th of October": os.path.join(UPLOAD_FOLDER, "6_october.geojson")
}

# Load data on startup
data = {}
for region_name, file_path in regions.items():
    if os.path.exists(file_path):
        gdf = load_geojson(file_path)
        if gdf is not None:
            gdf = classify_districts(gdf)
            data[region_name] = analyze_data(gdf, region_name)
        else:
            print(f"Failed to load data for {region_name}")
    else:
        print(f"File not found: {file_path}")

@app.route('/')
def index():
    cities_data = []
    pie_data = {'labels': [], 'data_values': []}
    bar_data = {'labels': [], 'data_values': []}

    # Define the desired order of cities
    ordered_cities = ["10th of Ramadan", "6th of October", "Madinaty"]

    for city_name in ordered_cities:
        file_path = regions.get(city_name)
        if not file_path or not os.path.exists(file_path):
            continue

        gdf = gpd.read_file(file_path)
        if gdf.empty:
            continue

        total_homes = len(gdf[gdf['amenity'] == 'residential']) if 'amenity' in gdf.columns else 0
        total_services = len(gdf[gdf['amenity'] != 'residential']) if 'amenity' in gdf.columns else 0

        cities_data.append({
            'name': city_name,
            'total_homes': total_homes,
            'total_services': total_services
        })

        pie_data['labels'].append(city_name)
        pie_data['data_values'].append(total_homes)
        bar_data['labels'].append(city_name)
        bar_data['data_values'].append(total_services)

    return render_template('index.html', cities_data=cities_data, pie_data=pie_data, bar_data=bar_data)


@app.route('/city/<city_name>', methods=['GET'])
def city_details(city_name):
    region_file = regions.get(city_name)
    if not region_file or not os.path.exists(region_file):
        return render_template('city.html', city_name=city_name, no_data=True)

    gdf = gpd.read_file(region_file)
    if gdf.empty:
        return render_template('city.html', city_name=city_name, no_data=True)

    selected_service = request.args.get('service_type', 'all')
    selected_street = request.args.get('street', 'all')

    service_types = gdf['amenity'].dropna().unique().tolist() if 'amenity' in gdf.columns else []
    streets = gdf['addr:street'].dropna().unique().tolist() if 'addr:street' in gdf.columns else []

    # === Filtered data for table and map ===
    filtered_gdf = gdf.copy()
    if selected_street != 'all':
        filtered_gdf = filtered_gdf[filtered_gdf['addr:street'] == selected_street]
    if selected_service != 'all':
        filtered_gdf = filtered_gdf[filtered_gdf['amenity'] == selected_service]

    no_data = filtered_gdf.empty
    no_homes = len(filtered_gdf[filtered_gdf['amenity'] == 'residential']) == 0 if 'amenity' in filtered_gdf.columns else True

    # === Unfiltered data for charting ===
    chart_gdf = gdf.copy()
    if selected_street != 'all':
        chart_gdf = chart_gdf[chart_gdf['addr:street'] == selected_street]
    services_only = chart_gdf[chart_gdf['amenity'] != 'residential']

    # === Chart logic ===
    if selected_service == 'all':
        # Pie: homes vs services
        total_homes = chart_gdf[chart_gdf['amenity'] == 'residential'].shape[0]
        total_services = services_only.shape[0]
        pie_data = {
            'labels': ['بيوت', 'خدمات'],
            'values': [total_homes, total_services]
        }

        # Bar: all service types
        service_counts = services_only['amenity'].value_counts().to_dict()
        bar_data = {
            'labels': list(service_counts.keys()),
            'values': list(service_counts.values())
        }
    else:
        # Pie & Bar: selected vs other services
        selected_count_val = services_only[services_only['amenity'] == selected_service].shape[0]
        other_count_val = services_only[services_only['amenity'] != selected_service].shape[0]

        pie_data = {
            'labels': [selected_service, 'خدمات أخرى'],
            'values': [selected_count_val, other_count_val]
        }

        bar_data = {
            'labels': [selected_service, 'Other Services'],
            'values': [selected_count_val, other_count_val]
        }

    # === Area chart: top 5 streets ===
    street_counts = filtered_gdf['addr:street'].value_counts().head(5).to_dict() if 'addr:street' in filtered_gdf.columns else {}
    area_data = {
        'labels': list(street_counts.keys()),
        'values': list(street_counts.values())
    }

    # === Map data ===
    map_data = []
    for _, row in filtered_gdf[filtered_gdf['geometry'].notnull()].iterrows():
        if row['geometry'] is not None and not row['geometry'].is_empty and hasattr(row['geometry'], 'x') and hasattr(row['geometry'], 'y'):
            map_data.append({
                'coordinates': [row['geometry'].x, row['geometry'].y],
                'amenity': row['amenity'] if 'amenity' in gdf.columns and pd.notnull(row['amenity']) else 'غير متوفر',
                'name:en': row['name:en'] if 'name:en' in gdf.columns and pd.notnull(row['name:en']) else 'غير متوفر',
                'name:ar': row['name:ar'] if 'name:ar' in gdf.columns and pd.notnull(row['name:ar']) else 'غير متوفر'
            })

    # === Table data ===
    table_columns = ['name:en', 'name:ar', 'amenity', 'addr:street']
    table_columns = [col for col in gdf.columns if col in table_columns]
    table_data = filtered_gdf[table_columns].to_dict('records') if table_columns else []
    table_data = [{k: v if pd.notnull(v) else 'غير متوفر' for k, v in record.items()} for record in table_data]

    if selected_service == 'all':
        card1_title = "إجمالي البيوت"
        card1_value = len(filtered_gdf[filtered_gdf['amenity'] == 'residential'])
        card2_title = "إجمالي الخدمات"
        card2_value = len(filtered_gdf[filtered_gdf['amenity'] != 'residential'])
    else:
        selected_count = len(services_only[services_only['amenity'] == selected_service])
        other_count = len(services_only[services_only['amenity'] != selected_service])
        card1_title = selected_service
        card1_value = selected_count
        card2_title = "باقي الخدمات"
        card2_value = other_count

    return render_template(
        'city.html',
        city_name=city_name,
        card1_title=card1_title,
        card1_value=card1_value,
        card2_title=card2_title,
        card2_value=card2_value,
        total_homes=len(filtered_gdf[filtered_gdf['amenity'] == 'residential']),
        total_services=len(filtered_gdf[filtered_gdf['amenity'] != 'residential']),
        service_types=['all'] + service_types,
        streets=['all'] + streets,
        selected_service=selected_service,
        selected_street=selected_street,
        pie_data=pie_data,
        bar_data=bar_data,
        area_data=area_data,
        map_data=map_data,
        table_data=table_data,
        no_data=no_data,
        no_homes=no_homes
    )






def filter_data_by_street(data, street):
    return [item for item in data if item['street'] == street]

def prepare_pie_chart_data(data):
        # Handle missing data
        return []

if __name__ == '__main__':
    app.run(port=8080,debug=True)
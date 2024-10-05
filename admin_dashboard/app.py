import base64
import io
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
import snowflake.connector
import datetime
import pandas as pd
import ast
import requests
from geopy.distance import geodesic
import googlemaps
from sklearn.neighbors import NearestNeighbors
import numpy as np
import time
import polyline
import os
import folium
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt

app = Flask(__name__, static_url_path='/static')

# MongoDB connection
uri ="mongodb+srv://sam10:sam@cluster0.o3wv5.mongodb.net/"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['mail_send']
collection = db['data']

# Snowflake connection credentials
SNOWFLAKE_USER = 'srikanth'
SNOWFLAKE_PASSWORD = 'Srik@2005'
SNOWFLAKE_ACCOUNT = 'mvzaemy-ha30008'
SNOWFLAKE_WAREHOUSE = 'COMPUTE_WH'
SNOWFLAKE_DATABASE = 'WASTE_MANGE'
SNOWFLAKE_SCHEMA = 'DATA'
SNOWFLAKE_ROLE = 'ACCOUNTADMIN'

if not os.path.exists('static/vehicle_maps'):
    os.makedirs('static/vehicle_maps')

BIN_DATA_FILE = 'garbage_data_check2.csv'
df1 = pd.read_csv('your_predictions_file.csv')

# Function to create density plot for a given location
def create_density_plot(location):
    specific_data = df1[df1['Location'] == location]
    
    plt.figure(figsize=(10, 5))
    sns.kdeplot(data=specific_data, x='Predicted Fill Level (%)', fill=True, color='blue', alpha=0.5)
    plt.title(f'Density Plot of Predicted Fill Level for {location}')
    plt.xlabel('Predicted Fill Level (%)')
    plt.ylabel('Density')
    plt.grid()

    # Save plot to a PNG in memory
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

# Modify the function to create a static overall main graph
def create_static_main_graph():
    plt.figure(figsize=(10, 5))
    overall_avg = df1.groupby('Day')['Predicted Fill Level (%)'].mean()  # Calculate average for all locations
    plt.plot(overall_avg.index, overall_avg.values, marker='o', color='green', label='Overall Average Fill Level (%)')
    plt.title('Overall Garbage Fill Level')
    plt.xlabel('Days')
    plt.ylabel('Predicted Fill Level (%)')
    plt.xticks(rotation=45)
    plt.grid()
    plt.legend()

    # Save plot to a PNG in memory
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

def get_top_locations(file_path, top_n=5):
    """Loads CSV, filters today's data, and returns the top locations by weight."""
    # Load CSV data
    df = pd.read_csv(BIN_DATA_FILE)
    
    # Get today's date in the same format as the 'Timestamp' in the CSV
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Filter the data for today's entries based on 'Timestamp'
    today_data = df[df['Timestamp'].str.startswith(today)]
    
    # Get the top N weights by location for today
    top_locations = today_data.groupby('Location').agg({
        'Weight (kg)': 'sum',
        'Fill Level (%)': 'sum',
        'Latitude': 'first',
        'Longitude': 'first'
    }).nlargest(top_n, 'Weight (kg)').reset_index()
    
    # Return top locations as a list of dictionaries
    return top_locations.to_dict(orient='records')

# Google Maps API Key
API_KEY = 'YOUR_API_KEY'  # Replace with your actual API key
gmaps = googlemaps.Client(key=API_KEY)

# Function to get coordinates for a district using Google Maps API
def get_coordinates(district_name):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={district_name}&key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get('results')
        if results:
            location = results[0]['geometry']['location']
            return location['lat'], location['lng']
    return None

# Function to create munxap map for a vehicle
def create_munxap(vehicle_name, checkpoints, district_coordinates):
    start_point = "No.35, Third Floor, Apoorva Louis Apartment, Reddiarpalayam, Puducherry, 605010"
    end_point = "WQM6+XWX Kurumbapet Dumpyard, VIP's Residential Area, Marie Oulgaret, Puducherry, 605111"
    
    waypoints = '|'.join(checkpoints)
    directions_url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_point}&destination={end_point}&waypoints={waypoints}&key={API_KEY}"
    response = requests.get(directions_url)
    
    if response.status_code == 200:
        polyline_points = response.json().get('routes')[0]['overview_polyline']['points']
        decoded_points = polyline.decode(polyline_points)
        
        start_coords = get_coordinates("Reddiarpalayam, Puducherry")
        m = folium.Map(location=start_coords, zoom_start=13)
        
        folium.PolyLine(decoded_points, color="blue", weight=2.5, opacity=1).add_to(m)
        folium.Marker(start_coords, tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
        for checkpoint in checkpoints:
            folium.Marker(district_coordinates[checkpoint], tooltip=checkpoint).add_to(m)
        
        end_coords = get_coordinates("Kurumbapet Dumpyard, Puducherry")
        folium.Marker(end_coords, tooltip="End", icon=folium.Icon(color="red")).add_to(m)

        map_filename = os.path.join('static', 'vehicle_maps', f"{vehicle_name}_munxap.html")
        m.save(map_filename)
        print(f"Munxap map for {vehicle_name} saved as {map_filename}")
        return map_filename

# Load district names from location.txt and fetch coordinates
def load_districts(file_path):
    with open(file_path, 'r') as file:
        districts = ast.literal_eval(file.read().strip())
    
    district_coordinates = {}
    for district in districts:
        coords = get_coordinates(district)
        if coords:
            district_coordinates[district] = coords
        else:
            print(f"Could not fetch coordinates for {district}.")
        time.sleep(1)  # To avoid hitting the API rate limit

    return districts, district_coordinates

# Load bin data from a CSV file
def load_bin_data(file_path):
    return pd.read_csv(file_path)

# Function to calculate weights for each district based on the selected date
def calculate_weights(bin_data, districts, selected_date):
    weights = {}
    filtered_data = bin_data[bin_data['Timestamp'].str.startswith(selected_date)]

    for district in districts:
        total_weight = filtered_data[filtered_data['Location'] == district]['Weight (kg)'].sum()
        weights[district] = total_weight

    return weights

# Function to perform KNN clustering
def perform_knn_clustering(district_coordinates):
    coords = np.array(list(district_coordinates.values()))
    nbrs = NearestNeighbors(n_neighbors=7).fit(coords)  # Adjust n_neighbors as necessary
    distances, indices = nbrs.kneighbors(coords)
    
    clusters = {}
    districts = list(district_coordinates.keys())
    for idx, district in enumerate(districts):
        nearby_districts = [districts[i] for i in indices[idx] if i != idx]
        clusters[district] = nearby_districts
    
    return clusters

# Function to calculate the distance between two districts
def calculate_distance(district1, district2, district_coordinates):
    coords1 = district_coordinates[district1]
    coords2 = district_coordinates[district2]
    return geodesic(coords1, coords2).km

# Function to allocate vehicles
def allocate_vehicles(weights, clusters, district_coordinates):
    vehicle_capacity = 300  # in kg
    vehicle_allocations = {}
    total_vehicle_count = 0
    assigned_districts = set()  # To track already assigned districts

    sorted_districts = sorted(weights.items(), key=lambda x: x[1], reverse=True)

    while sorted_districts:  # Continue until no districts are left to process
        district, weight = sorted_districts.pop(0)

        if weight <= 0 or district in assigned_districts:
            continue

        remaining_weight = weight
        vehicle_allocation = [district]
        assigned_districts.add(district)

        # Try to combine with nearby districts
        for nearby_district in clusters[district]:
            if nearby_district not in assigned_districts and weights[nearby_district] > 0:
                combined_weight = remaining_weight + weights[nearby_district]
                if combined_weight <= vehicle_capacity and calculate_distance(district, nearby_district, district_coordinates) <= 10:
                    vehicle_allocation.append(nearby_district)
                    assigned_districts.add(nearby_district)
                    remaining_weight += weights[nearby_district]
                    weights[nearby_district] = 0

        vehicle_allocations[f"Vehicle {total_vehicle_count + 1}"] = vehicle_allocation
        total_vehicle_count += 1

    return vehicle_allocations


@app.route('/', methods=['GET', 'POST'])
def index():
    # MongoDB functionality
    events_data = list(collection.find())
    event_details = None
    if request.method == 'POST':
        event_id = request.form.get('event_id')
        event_details = collection.find_one({'_id': ObjectId(event_id)})
    top_locations = get_top_locations('garbage_data_check2.csv', top_n=5)
    locations = df1['Location'].unique()
    # Create the static main graph for overall fill level
    static_main_graph = create_static_main_graph()
    density_graph = create_density_plot(locations[0])  # Default density graph for the first location
    return render_template('index1.html', events=events_data, event_details=event_details,top_locations=top_locations, locations=locations, main_graph=static_main_graph, density_graph=density_graph, default_location=locations[0])

@app.route('/update/<location>')
def update(location):
    density_graph = create_density_plot(location)
    return jsonify({'density_graph': density_graph})

@app.route('/run_allocation', methods=['POST'])
def run_allocation():
    try:
        selected_date = request.form.get('selected_date_unique')
        
        if not selected_date:
            return jsonify({"error": "No date provided"}), 400

        # Load data
        districts, district_coordinates = load_districts('data/location.txt')
        bin_data = load_bin_data('data/garbage_data_check2.csv')

        # Calculate weights
        weights = calculate_weights(bin_data, districts, selected_date)

        # Perform clustering
        clusters = perform_knn_clustering(district_coordinates)

        # Allocate vehicles
        vehicle_allocations = allocate_vehicles(weights, clusters, district_coordinates)

        # Prepare data for frontend
        vehicles_data = []
        for vehicle, allocated_districts in vehicle_allocations.items():
            # Generate the munxap map
            map_filename = create_munxap(vehicle, allocated_districts, district_coordinates)

            vehicles_data.append({
                "vehicle_id": vehicle,
                "assigned_districts": allocated_districts,
                "map_url": map_filename  # Include map URL in the response
            })

        return jsonify(vehicles_data)
    
    except Exception as e:
        print(f"Error during allocation: {e}")
        return jsonify({"error": "An error occurred during allocation."}), 500

# Snowflake functionality for calendar
@app.route('/get_default_upcoming_events', methods=['GET'])
def get_default_upcoming_events():
    today = datetime.date.today()
    conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        role=SNOWFLAKE_ROLE
    )
    cursor = conn.cursor()

    query = f"""
    SELECT EVENT_NAME, LATITUDE, LONGITUDE, VEHICLES_NEEDED, PERSONNEL_NEEDED 
    FROM EVENT_WASTE_ESTIMATION 
    WHERE EVENT_DATE >= '{today}' 
    ORDER BY EVENT_DATE
    """
    cursor.execute(query)
    events = cursor.fetchall()
    cursor.close()
    conn.close()

    events_list = []
    for event in events:
        event_name, latitude, longitude, vehicles_needed, personnel_needed = event
        map_link = f"https://www.google.com/maps?q={latitude},{longitude}"
        events_list.append({
            'event_name': event_name,
            'location': map_link,
            'vehicles_needed': vehicles_needed,
            'personnel_needed': personnel_needed
        })

    return jsonify(events_list)

@app.route('/get_events', methods=['GET'])
def get_events():
    date = request.args.get('date')
    conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        role=SNOWFLAKE_ROLE
    )
    
    cursor = conn.cursor()
    query = f"""
    SELECT EVENT_NAME, LATITUDE, LONGITUDE, VEHICLES_NEEDED, PERSONNEL_NEEDED 
    FROM EVENT_WASTE_ESTIMATION 
    WHERE EVENT_DATE = '{date}'
    """
    cursor.execute(query)
    events = cursor.fetchall()
    cursor.close()
    conn.close()

    events_list = []
    for event in events:
        event_name, latitude, longitude, vehicles_needed, personnel_needed = event
        map_link = f"https://www.google.com/maps?q={latitude},{longitude}"
        events_list.append({
            'event_name': event_name,
            'location': map_link,
            'vehicles_needed': vehicles_needed,
            'personnel_needed': personnel_needed
        })

    return jsonify(events_list)

@app.route('/get_event_counts', methods=['GET'])
def get_event_counts():
    month = request.args.get('month')
    year = request.args.get('year')

    conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        role=SNOWFLAKE_ROLE
    )

    cursor = conn.cursor()
    query = f"""
    SELECT DAY(EVENT_DATE) AS day, COUNT(*) AS event_count 
    FROM EVENT_WASTE_ESTIMATION
    WHERE MONTH(EVENT_DATE) = {month} AND YEAR(EVENT_DATE) = {year} 
    GROUP BY DAY(EVENT_DATE);
    """
    
    cursor.execute(query)
    counts = cursor.fetchall()
    cursor.close()
    conn.close()

    event_counts = {str(day[0]): day[1] for day in counts}
    return jsonify(event_counts)


if __name__ == '__main__':
    app.run(debug=True)

## This file utilizes indexmap.html & map.html
## Input: This code alows the user to upload an excel file on the web interface and also enter desired city
## Output: It will display companies in that desired city within a 20 mile radius in a list and on a map

from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import GoogleV3
import folium
import random
import re

app = Flask(__name__)

# Function to geocode an address
def geocode_address(address):
    try:
        geolocator = GoogleV3(api_key="AIzaSyDifzVsXzyw-6-NZJIYNOQAUcRCBa7W5RI")
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        else:
            print("Geocodng failed for address: {address}")
    except Exception as e:
        print(f"Error occured during geocoding: {e}")
    return None

# Normalize Phone Numbers
def normalize_phone_number(phone_number):
    if pd.isna(phone_number):
        return None
    # Ensure phone_number is a string
    phone_number = str(phone_number)
    # Remove all non-numeric characters
    cleaned_number = re.sub(r'\D', '', phone_number)
    # Format to a consistent format, e.g., (123) 456-7890
    if len(cleaned_number) == 10:
        return f"({cleaned_number[:3]}) {cleaned_number[3:6]}-{cleaned_number[6:]}"
    elif len(cleaned_number) == 11 and cleaned_number[0] == '1':
        return f"({cleaned_number[1:4]}) {cleaned_number[4:7]}-{cleaned_number[7:]}"
    else:
        return phone_number  # Return as is if it doesn’t match expected lengths


# Function to find nearby companies within a radius
def find_nearby_companies(df, city, radius=20):
    print("Phone numbers before normalization:")
    print(df['Phone Number'].head())
    
    df['Phone Number'] = df['Phone Number'].apply(normalize_phone_number)
    city_location = geocode_address(city)
    if not city_location:
        return None
    df['Coordinates'] = df['Address'].apply(geocode_address)
    df['Distance'] = df['Coordinates'].apply(lambda x: geodesic(city_location, x).miles if x else None)
    nearby_companies = df[df['Distance'] <= radius]

    # Group by both 'Company Name' and 'Address' to count students accurately
    nearby_companies['Student Count'] = nearby_companies.groupby(['Company Name', 'Address'])['Address'].transform('count')
    
    # Drop duplicate rows to avoid placing multiple markers on the same location
    nearby_companies = nearby_companies.drop_duplicates(subset=['Company Name', 'Address'])

    
    # Count how many students (rows) are associated with each company location
    #nearby_companies['Student Count'] = nearby_companies.groupby('Address')['Address'].transform('count')
    
    # Drop duplicate rows to avoid placing multiple markers on the same location
    #nearby_companies = nearby_companies.drop_duplicates(subset=['Address'])

    return nearby_companies

# Function to slightly offset coordinates for visibility
def offset_coordinates(coords, index, total_count):
    if coords:
        offset_lat = 0.001 * (index % 10)  # Offset latitude slightly
        offset_lon = 0.001 * (index // 10)  # Offset longitude slightly
        return (coords[0] + offset_lat, coords[1] + offset_lon)
    return coords

# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        city = request.form['city']
        
        if file and city:
            df = pd.read_excel(file)
            df = df.dropna(subset=['Address'])
            print(df.head())
            nearby_companies = find_nearby_companies(df, city)
            
            if nearby_companies is not None:
                map = folium.Map(location=geocode_address(city), zoom_start=12)
                
                #total_count = len(nearby_companies)
                for index, row in nearby_companies.iterrows():
                    coords = offset_coordinates(row['Coordinates'], index, len(nearby_companies))
                    if coords:
                        popup_html = f"""
                        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
                            <b style="font-size: 16px;">{row['Company Name']}</b><br>
                            <span style="color: #555;">{row['Address']}</span><br>
                            <span>Students Employed: <b>{row['Student Count']}</b></span><br>
                            <span style="color: #666;">Phone: {row['Phone Number']}</span>
                        </div>
                        """
                        folium.Marker(
                            location=coords,
                            popup=folium.Popup(popup_html, max_width=300),
                            icon=folium.Icon(color='blue', icon='info-sign')
                        ).add_to(map)
                    #if coords:
                        #folium.Marker(location=coords, 
                                  #popup=row['Company Name']).add_to(map)
                                  
                                  #popup=f"<b>{row['Company Name']}</b><br><br>Students Employed: {row['Student Count']}<br>Phone: {row['Phone Number']}").add_to(map)
                
                map.save('templates/map.html')
                # Sort by 'Company Name' alphabetically
                nearby_companies_sorted = nearby_companies.sort_values(by='Company Name')
                
                # Convert nearby companies to a list of dictionaries for easier handling in the template
                company_list = nearby_companies_sorted.to_dict(orient='records')
                
                return render_template('indexmap.html', company_list=company_list)

                #return redirect(url_for('show_map'))
            else:
                return "City not found"
    return render_template('indexmap.html')

# Route to display the map
@app.route('/map')
def show_map():
    return render_template('map.html')

if __name__ == '__main__':
    app.run(debug=True)
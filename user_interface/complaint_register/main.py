from flask import Flask, request, render_template, redirect, url_for, flash
from PIL import Image, ExifTags
import os
import smtplib
import uuid
import subprocess
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pymongo import MongoClient
from bson.objectid import ObjectId
from pymongo.server_api import ServerApi

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB setup
uri = "mongodb+srv://sam10:sam@cluster0.o3wv5.mongodb.net/"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['mail_send']  # Replace with your database name
email_collection = db['data']

# Function to extract GPS coordinates from the image
def extract_gps(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        gps_info = {}
        if exif_data:
            for tag, value in exif_data.items():
                decoded_tag = ExifTags.TAGS.get(tag)
                if decoded_tag == 'GPSInfo':
                    for t, val in value.items():
                        gps_tag = ExifTags.GPSTAGS.get(t)
                        gps_info[gps_tag] = val
        gps_latitude = gps_info.get('GPSLatitude')
        gps_latitude_ref = gps_info.get('GPSLatitudeRef')
        gps_longitude = gps_info.get('GPSLongitude')
        gps_longitude_ref = gps_info.get('GPSLongitudeRef')
        if gps_latitude and gps_longitude:
            latitude = convert_to_degrees(gps_latitude)
            if gps_latitude_ref != 'N':
                latitude = -latitude
            longitude = convert_to_degrees(gps_longitude)
            if gps_longitude_ref != 'E':
                longitude = -longitude
            return latitude, longitude
        else:
            return None, None
    except Exception as e:
        print(f"Error extracting GPS data: {e}")
        return None, None

# Convert GPS coordinates to degrees
def convert_to_degrees(value):
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)

# Function to send confirmation email
def send_confirmation_email(to_email, complaint_id, lat, lon, photo_path, name, description):
    subject = "Complaint Filed Successfully"
    body = f"Dear {name},\n\nYour complaint has been filed successfully.\n\nComplaint ID: {complaint_id}\nLocation: https://maps.google.com/?q={lat},{lon}\n\nDescription:\n{description}\n\nThank you for your submission."
    
    sender_email = "sendhaaneilamourougou@gmail.com"  # Replace with your sender email
    password = "taqb sauf yytw rlid"  # Use environment variables for production

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with open(photo_path, 'rb') as img:
            img_attachment = MIMEImage(img.read())
            img_attachment.add_header('Content-Disposition', f'attachment; filename={os.path.basename(photo_path)}')
            msg.attach(img_attachment)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)

        # Store data in MongoDB
        email_collection.insert_one({
            "complaint_id": complaint_id,
            "name": name,
            "email": to_email,
            "description": description,
            "latitude": lat,
            "longitude": lon,
            "photo_path": photo_path,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")  # Store current time
        })

        return True
    except Exception as e:
        print(f"Error sending email or storing data in MongoDB: {e}")
        return False

# Route for the main page
@app.route('/')
def index():
    return render_template('main.html')

# Route for uploading the photo
@app.route('/upload', methods=['GET', 'POST'])
def upload_photo():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        description = request.form['description']
        photo = request.files['photo']

        if photo:
            # Create 'uploads' directory if it doesn't exist
            os.makedirs('uploads', exist_ok=True)

            # Save the image and extract GPS data
            photo_path = os.path.join('uploads', photo.filename)
            photo.save(photo_path)
            latitude, longitude = extract_gps(photo_path)

            if latitude and longitude:
                # Generate a unique complaint ID
                complaint_id = str(uuid.uuid4())

                # Send confirmation email with the image attached and include name & description
                email_sent = send_confirmation_email(email, complaint_id, latitude, longitude, photo_path, name, description)
                if email_sent:
                    flash(f"Complaint filed successfully! Your Complaint ID is: {complaint_id}", 'success')
                else:
                    flash("Complaint filed, but failed to send email notification.", 'warning')
            else:
                flash("No GPS data found in the image. Please provide a geotagged image.", 'danger')
            return redirect(url_for('upload_photo'))

    return render_template('upload.html')

# Route for capturing the photo
@app.route('/capture', methods=['GET', 'POST'])
def capture_photo():
    if request.method == 'POST':
        email = request.form['email']
        description = request.form['description']

        device_id = '10BD9M1G8000050'  # Replace with your actual device ID from adb
        
        # Step 1: Get the previous (latest) photo before opening the camera
        previous_photo_path = get_previous_photo(device_id)
        
        # Step 2: Open the camera and wait for the user to take a photo
        open_camera(device_id)
        time.sleep(10)  # Wait for a moment to allow the user to take a photo

        # Step 3: Get the new (latest) photo after the camera is closed
        latest_photo_path = get_latest_photo(device_id)
        
        # Step 4: Compare previous and latest photos
        if latest_photo_path and latest_photo_path != previous_photo_path:
            # New photo is different from the previous one
            file_name = f'static/photo_{uuid.uuid4()}.jpg'  # Save to static folder
            
            # Pull the latest photo from the device
            if pull_photo(device_id, latest_photo_path, file_name):
                # Extract GPS data from the new photo
                latitude, longitude = extract_gps(file_name)

                if latitude and longitude:
                    # Step 5: Send the email with the latest photo and GPS data
                    complaint_id = str(uuid.uuid4())
                    email_sent = send_confirmation_email(email, complaint_id, latitude, longitude, file_name, "User", description)
                    
                    if email_sent:
                        flash(f"Complaint filed successfully! Your Complaint ID is: {complaint_id}", 'success')
                    else:
                        flash("Complaint filed, but failed to send email notification.", 'warning')
                else:
                    flash("No GPS data found in the image. Please provide a geotagged image.", 'danger')
            else:
                flash("Failed to pull photo from device.", 'danger')
        else:
            flash("No new photo found. Please take a photo.", 'danger')

    return render_template('capture.html')

# Route for sending the email
@app.route('/send_email', methods=['POST'])
def send_email():
    email = request.form['email']
    description = request.form['description']
    latitude = request.form['latitude']
    longitude = request.form['longitude']
    image_path = request.form['image_path']

    # Generate a unique complaint ID
    complaint_id = str(uuid.uuid4())

    # Send confirmation email with the image attached
    email_sent = send_confirmation_email(email, complaint_id, latitude, longitude, image_path, "User", description)
    if email_sent:
        flash(f"Email sent successfully! Complaint ID is: {complaint_id}", 'success')
    else:
        flash("Failed to send email notification.", 'danger')

    return redirect(url_for('capture_photo'))

# Function to open camera
def open_camera(device_id):
    """Open the camera app on the device."""
    try:
        launch_camera_command = f"adb -s {device_id} shell am start -a android.media.action.STILL_IMAGE_CAMERA"
        subprocess.run(launch_camera_command, shell=True, check=True)
        print("Camera opened. Please take a photo.")
    except subprocess.CalledProcessError as e:
        print(f"Error opening camera: {e}")

# Function to get the previous photo
def get_previous_photo(device_id):
    """Retrieve the previous photo taken by the user."""
    try:
        list_photos_command = f"adb -s {device_id} shell ls -t /storage/emulated/0/DCIM/Camera/*.jpg"
        result = subprocess.run(list_photos_command, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            photos = result.stdout.strip().split('\n')
            if photos:
                return photos[0].strip()  # Return the most recent photo path
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error getting previous photo: {e}")
        return None

# Function to get the latest photo
def get_latest_photo(device_id):
    """Retrieve the latest photo taken by the user."""
    try:
        list_photos_command = f"adb -s {device_id} shell ls -t /storage/emulated/0/DCIM/Camera/*.jpg"
        result = subprocess.run(list_photos_command, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            photos = result.stdout.strip().split('\n')
            if photos:
                return photos[0].strip()  # Return the most recent photo path
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error getting latest photo: {e}")
        return None

# Function to pull the latest photo from the device
def pull_photo(device_id, photo_path, destination):
    """Pull the photo from the device to the server."""
    try:
        pull_command = f"adb -s {device_id} pull {photo_path} {destination}"
        subprocess.run(pull_command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error pulling photo: {e}")
        return False

if __name__ == '__main__':
    app.run(debug=True)

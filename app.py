import os
from flask import Flask, request, render_template, redirect
from dotenv import load_dotenv
import psycopg2
import datetime

load_dotenv()  # Load variables from .env file

app = Flask(__name__)

# Read DB connection info from .env ,Stores sensor data persistently 
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

#Fetches the latest sensor reading from PostgreSQL.Renders an HTML template (index.html) to display the data.Why?Provides a real-time dashboard for users to monitor temperature/humidity.
@app.route('/')
def index():
    cur = conn.cursor()
    cur.execute("SELECT timestamp, temperature, humidity FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
    row = cur.fetchone()
    return render_template('index.html', data=row)

#Data Ingestion (/data) :Accepts POST requests from the ESP8266,Inserts the data into the sensor_data table with a timestamp.Why? Acts as the API endpoint for your ESP8266 to send sensor data.Returns HTTP status 204 (No Content) to acknowledge receipt without cluttering the response.
@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sensor_data (timestamp, temperature, humidity) VALUES (%s, %s, %s)",
        (datetime.datetime.now(), data['temperature'], data['humidity'])
    )
    conn.commit()
    return ('', 204)


#When you click a button (e.g., "Turn ON") on the dashboard, it triggers this route (e.g., /control/on).Forwards the command to the ESP8266 ,Why?Lets you control hardware (e.g., an LED/relay) from the dashboard.Uses requests.post() to send commands to the ESP8266 (which you’ll program to handle these requests).
@app.route('/control/<action>')
def control(action):
    esp_url = os.getenv("ESP_CONTROL_URL")
    if esp_url:
        import requests
        try:
            requests.post(f"{esp_url}/{action}")
        except Exception as e:
            print(f"Error contacting ESP: {e}")
    return redirect('/')

if __name__ == '__main__':
    app.run(host=os.getenv("FLASK_HOST"), port=int(os.getenv("FLASK_PORT")))


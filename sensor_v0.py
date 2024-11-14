import time
import board
import adafruit_dht
import psycopg2
import RPi.GPIO as GPIO
from datetime import datetime
import pytz
import tkinter as tk
from tkinter import messagebox

# Initialize the DHT22 sensor with the data pin connected to GPIO4 (D4)
dhtDevice = adafruit_dht.DHT22(board.D4)

# GPIO setup for the 4 relays
GPIO.setmode(GPIO.BCM)
reles = [18, 23, 24, 12]  # Updated GPIO pins connected to the relays
for rele in reles:
    GPIO.setup(rele, GPIO.OUT)

# Database connection parameters
db_config = {
    'dbname': 'sensor',
    'user': 'postgres',
    'password': 'postgres',
    'host': '127.0.0.1',
    'port': '5432'
}

# Function to save data to PostgreSQL
def save_to_postgresql(temperature_c, humidity, timestamp):
    try:
        # Connect to PostgreSQL
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        # Create the table if it doesn't exist
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id SERIAL PRIMARY KEY,
            temperature_c FLOAT NOT NULL,
            humidity FLOAT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL
        );
        '''
        cursor.execute(create_table_query)
        connection.commit()

        # Insert temperature, humidity, and timestamp into the database
        insert_query = '''
        INSERT INTO sensor_data (temperature_c, humidity, timestamp) 
        VALUES (%s, %s, %s);
        '''
        cursor.execute(insert_query, (temperature_c, humidity, timestamp))
        connection.commit()

    except Exception as e:
        print(f"Database error: {e}")

    finally:
        # Close connection
        if connection:
            cursor.close()
            connection.close()

# Set local timezone
local_timezone = pytz.timezone('America/Sao_Paulo')  # Replace with your local timezone

# Default thresholds (initial values)
min_temperature = 5.0  # Minimum temperature (in Celsius)
max_temperature = 50.0  # Maximum temperature (in Celsius)
min_humidity = 20.0     # Minimum humidity (in percentage)
max_humidity = 100.0     # Maximum humidity (in percentage)

# Hysteresis variables
last_temp = 0.0
last_humidity = 0.0

# Function to control the relays based on temperature and humidity
def control_reles(temperature_c, humidity):
    global last_temp, last_humidity
    temp_threshold_low = min_temperature - 0.5
    temp_threshold_high = max_temperature + 0.5

    if (temperature_c < temp_threshold_low or humidity < min_humidity) and last_temp >= temp_threshold_low:
        # Activate all relays (all contactors on)
        for rele in reles:
            GPIO.output(rele, GPIO.HIGH)
        print("All relays ON: Heating activated")
    elif (temperature_c > temp_threshold_high or humidity > max_humidity) and last_temp <= temp_threshold_high:
        # Deactivate all relays (all contactors off)
        for rele in reles:
            GPIO.output(rele, GPIO.LOW)
        print("All relays OFF: Heating deactivated")
    else:
        # Control specific relays depending on the range
        if temperature_c < 25.0:
            GPIO.output(reles[0], GPIO.HIGH)
            GPIO.output(reles[1], GPIO.HIGH)
            GPIO.output(reles[2], GPIO.LOW)
            GPIO.output(reles[3], GPIO.LOW)
            print("Half relays ON: Moderate heating")
        else:
            GPIO.output(reles[0], GPIO.LOW)
            GPIO.output(reles[1], GPIO.LOW)
            GPIO.output(reles[2], GPIO.HIGH)
            GPIO.output(reles[3], GPIO.HIGH)
            print("Other half relays ON: Lower heating")
    
    last_temp = temperature_c
    last_humidity = humidity

# Function to update thresholds from the GUI
def update_parameters():
    global min_temperature, max_temperature, min_humidity, max_humidity
    try:
        min_temperature = float(entry_min_temp.get())
        max_temperature = float(entry_max_temp.get())
        min_humidity = float(entry_min_hum.get())
        max_humidity = float(entry_max_hum.get())
        messagebox.showinfo("Success", "Parameters updated successfully!")
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numbers.")

# Function to display current sensor data in the GUI
def update_sensor_data():
    try:
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity
        timestamp = datetime.now(local_timezone)

        # Update labels with sensor values and change color based on thresholds
        label_temperature_value.config(text=f"{temperature_c:.1f} °C")
        label_humidity_value.config(text=f"{humidity:.1f} %")

        if temperature_c < min_temperature or temperature_c > max_temperature:
            label_temperature_value.config(fg="red")
        else:
            label_temperature_value.config(fg="green")
        
        if humidity < min_humidity or humidity > max_humidity:
            label_humidity_value.config(fg="red")
        else:
            label_humidity_value.config(fg="green")

        # Control the relays
        control_reles(temperature_c, humidity)

        # Save data to PostgreSQL
        save_to_postgresql(temperature_c, humidity, timestamp)

    except RuntimeError as error:
        print(f"Sensor error: {error.args[0]}")
    except Exception as error:
        dhtDevice.exit()
        GPIO.cleanup()
        raise error

    # Schedule next update in 60 seconds
    root.after(60000, update_sensor_data)


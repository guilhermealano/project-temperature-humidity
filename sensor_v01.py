import time
import adafruit_dht
import board
import RPi.GPIO as GPIO
# import tkinter as tk
# from tkinter import messagebox
import psycopg2
from datetime import datetime, timedelta
# import pytz

# Configurações do GPIO
RELAY_CHANNELS = {
    "temp_on": 18,  # Canal para ligar resistência de temperatura
    "temp_off": 23, # Canal para desligar resistência de temperatura
    "humidity_on": 24,  # Canal para ligar resistência de umidade
    "humidity_off": 25, # Canal para desligar resistência de umidade
}

# Configura o GPIO
GPIO.setmode(GPIO.BCM)
for channel in RELAY_CHANNELS.values():
    GPIO.setup(channel, GPIO.OUT)

# Configura o sensor
dht_sensor = adafruit_dht.DHT22(board.D4)

# Variáveis globais para metas
desired_temperature = 25.0  # Temperatura desejada inicial
desired_humidity = 50.0     # Umidade desejada inicial

# Database connection parameters
db_config = {
    'dbname': 'services',
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
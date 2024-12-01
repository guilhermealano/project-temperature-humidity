#!/usr/bin/python3
import time
import adafruit_dht
import board
import RPi.GPIO as GPIO
import tkinter as tk
from tkinter import messagebox
import psycopg2
from datetime import datetime, timedelta

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

# Função para conectar ao banco de dados
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname="services",
            user="postgres",
            password="postgres",
            host="localhost"
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Função para registrar leituras no banco de dados
def log_reading(temperature, humidity):
    conn = connect_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sensor_data (temperature_c, humidity, timestamp) VALUES (%s, %s, %s)",
                (temperature, humidity)
            )
            conn.commit()
        conn.close()

# Inicia a interface
try:
    connect_db()
finally:
    dht_sensor.exit()
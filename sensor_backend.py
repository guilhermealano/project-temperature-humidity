#!/usr/bin/python3
import time
import adafruit_dht
import board
import RPi.GPIO as GPIO
import psycopg2
from datetime import datetime
import pytz
from dotenv import load_dotenv
import requests
import os

# Carregar variáveis do arquivo .env
load_dotenv()

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

# Initialize the DHT22 sensor with the data pin connected to GPIO4 (D4)
dhtDevice = adafruit_dht.DHT22(board.D4, use_pulseio=True)

# Variáveis globais para metas
desired_temperature = 2.0  # Temperatura desejada inicial
desired_humidity = 20.0     # Umidade desejada inicial

# URLs da API Fastify
FASTIFY_API_GET_PARAMS = os.getenv("FASTIFY_API_GET_PARAMS", "http://localhost:3000/api/v1/sensor/get_data_sensor")
FASTIFY_API_POST_DATA = os.getenv("FASTIFY_API_POST_DATA", "http://localhost:3000/api/v1/sensor/senddata")

# Função para obter parâmetros da API Fastify
def get_sensor_params():
    try:
        response = requests.get(FASTIFY_API_GET_PARAMS)
        response.raise_for_status()
        data = response.json()
        if data.get("parameters") and len(data["parameters"]) > 0:
            param = data["parameters"][0]
            return {
                "desired_temperature": param[0],
                "desired_temp_min": param[1],
                "desired_temp_max": param[2],
                "desired_humidity": param[3],
                "desired_humi_min": param[4],
                "desired_humi_max": param[5],
            }
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter parâmetros da API: {e}")
    
    return None

# Função para enviar os dados para a API Fastify
def log_reading(temperature_c, humidity):
    timestamp = datetime.now().isoformat()
    
    payload = {
        "temperature_c": temperature_c,
        "humidity": humidity,
        "timestamp": timestamp
    }
    
    try:
        response = requests.post(FASTIFY_API_POST_DATA, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar dados para API: {e}")
        return None

# Função para ler o sensor
def read_sensor():
    global desired_temperature, desired_humidity

    try:
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity

        # Obter o horário atual
        timestamp = datetime.now()

        # Exibir valores no console
        print(f"Temp: {temperature_c:.1f} C  Humidity: {humidity}%  Timestamp: {timestamp}")

        if temperature_c is not None and humidity is not None:
            # Log das leituras no banco de dados
            log_reading(temperature_c, humidity, timestamp)

            # Controla as resistências com base nas metas
            if temperature_c < desired_temperature:
                GPIO.output(RELAY_CHANNELS["temp_on"], GPIO.HIGH)
                GPIO.output(RELAY_CHANNELS["temp_off"], GPIO.LOW)
            else:
                GPIO.output(RELAY_CHANNELS["temp_on"], GPIO.LOW)
                GPIO.output(RELAY_CHANNELS["temp_off"], GPIO.HIGH)

            if humidity < desired_humidity:
                GPIO.output(RELAY_CHANNELS["humidity_on"], GPIO.HIGH)
                GPIO.output(RELAY_CHANNELS["humidity_off"], GPIO.LOW)
            else:
                GPIO.output(RELAY_CHANNELS["humidity_on"], GPIO.LOW)
                GPIO.output(RELAY_CHANNELS["humidity_off"], GPIO.HIGH)

    except RuntimeError as error:
        print(f"Erro do sensor: {error.args[0]}")
    except Exception as error:
        dhtDevice.exit()
        raise error

# Loop principal para executar a leitura do sensor a cada 60 segundos
try:
    while True:
        read_sensor()
        time.sleep(60)  # Aguardar 60 segundos antes da próxima execução
except KeyboardInterrupt:
    print("Encerrando o programa.")
    GPIO.cleanup()

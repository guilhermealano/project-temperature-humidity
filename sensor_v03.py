#!/usr/bin/python3
import time
import adafruit_dht
import board
import RPi.GPIO as GPIO
import psycopg2
from datetime import datetime
import pytz

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
def log_reading(temperature_c, humidity):
    timezone = pytz.timezone('America/Sao_Paulo')
    timestamp = datetime.now(timezone)

    conn = connect_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sensor_data (temperature_c, humidity, timestamp) VALUES (%s, %s, %s)",
                (temperature_c, humidity, timestamp)
            )
            conn.commit()
        conn.close()

# Set local timezone
local_timezone = pytz.timezone('America/Sao_Paulo')  # Substitua pelo seu fuso horário local

# Função para ler o sensor
def read_sensor():
    global desired_temperature, desired_humidity
    try:
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity

        # Obter o horário atual com o fuso horário local
        timestamp = datetime.now(local_timezone)

        # Exibir os valores no console
        print(
            "Temp: {:.1f} C  Humidity: {}%  Timestamp: {}".format(
                temperature_c, humidity, timestamp
            )
        )

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

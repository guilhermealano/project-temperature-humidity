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
            dbname="varmengo",
            user="usuario_real",
            password="palnomengo",
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
                "INSERT INTO leituras (temperatura, umidade) VALUES (%s, %s)",
                (temperature, humidity)
            )
            conn.commit()
        conn.close()

# Função para ler o sensor
def read_sensor():
    global desired_temperature, desired_humidity
    try:
        temperature = dht_sensor.temperature
        humidity = dht_sensor.humidity

        if temperature is not None and humidity is not None:
            temp_label.config(text=f"Temperatura: {temperature:.2f} C")
            humidity_label.config(text=f"Umidade: {humidity:.2f}%")

            # Log das leituras no banco de dados
            log_reading(temperature, humidity)

            # Controla as resistências com base nas metas
            if temperature < desired_temperature:
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
                
        else:
            temp_label.config(text="Falha ao obter dados do sensor")
        
    except RuntimeError as e:
        temp_label.config(text=f"Erro de execução: {e}")
    
    # Atualiza a interface a cada 60 segundos
    window.after(60000, read_sensor)

# Funções para aumentar e diminuir a temperatura desejada
def increase_temperature():
    global desired_temperature
    desired_temperature += 0.5
    update_labels()

def decrease_temperature():
    global desired_temperature
    desired_temperature -= 0.5
    update_labels()

# Funções para aumentar e diminuir a umidade desejada
def increase_humidity():
    global desired_humidity
    desired_humidity += 1
    update_labels()

def decrease_humidity():
    global desired_humidity
    desired_humidity -= 1
    update_labels()

# Atualiza os rótulos da interface com os valores desejados
def update_labels():
    temp_setpoint_label.config(text=f"Temperatura Desejada: {desired_temperature:.1f} C")
    humidity_setpoint_label.config(text=f"Umidade Desejada: {desired_humidity:.1f}%")

# Função para mostrar histórico de leituras
def show_history():
    conn = connect_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM leituras ORDER BY data_hora DESC LIMIT 15")
            rows = cursor.fetchall()
            conn.close()

        if rows:
            history_text = "Histórico de Leituras:\n"
            for row in rows:
                history_text += f"ID: {row[0]}, Temp: {row[1]} C, Umidade: {row[2]}%, Data/Hora: {row[3]}\n"
            messagebox.showinfo("Histórico", history_text)
        else:
            messagebox.showinfo("Histórico", "Nenhuma leitura encontrada.")
    else:
        messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")

# Configura a interface gráfica
window = tk.Tk()
window.title("Controle de Temperatura e Umidade")

# Labels
temp_label = tk.Label(window, text="Temperatura: ", font=("Arial", 16))
temp_label.pack(pady=10)

humidity_label = tk.Label(window, text="Umidade: ", font=("Arial", 16))
humidity_label.pack(pady=10)

temp_setpoint_label = tk.Label(window, text=f"Temperatura Desejada: {desired_temperature:.1f} C", font=("Arial", 16))
temp_setpoint_label.pack(pady=10)

humidity_setpoint_label = tk.Label(window, text=f"Umidade Desejada: {desired_humidity:.1f}%", font=("Arial", 16))
humidity_setpoint_label.pack(pady=10)

# Botões para ajustar a temperatura
increase_temp_button = tk.Button(window, text="Aumentar Temperatura", command=increase_temperature, font=("Arial", 14))
increase_temp_button.pack(pady=5)

decrease_temp_button = tk.Button(window, text="Diminuir Temperatura", command=decrease_temperature, font=("Arial", 14))
decrease_temp_button.pack(pady=5)

# Botões para ajustar a umidade
increase_humidity_button = tk.Button(window, text="Aumentar Umidade", command=increase_humidity, font=("Arial", 14))
increase_humidity_button.pack(pady=5)

decrease_humidity_button = tk.Button(window, text="Diminuir Umidade", command=decrease_humidity, font=("Arial", 14))
decrease_humidity_button.pack(pady=5)

# Botão para acessar o histórico
history_button = tk.Button(window, text="Mostrar Histórico", command=show_history, font=("Arial", 14))
history_button.pack(pady=10)

# Inicia a leitura do sensor
read_sensor()

# Inicia a interface
try:
    window.mainloop()
finally:
    dht_sensor.exit()
    GPIO.cleanup()

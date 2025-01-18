from flask import Flask, render_template, request, redirect
import psycopg2
from datetime import datetime
import pytz

app = Flask(__name__)

# Banco de dados
DB_CONFIG = {
    "dbname": "services",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
}

local_timezone = pytz.timezone('America/Sao_Paulo')

# Conectar ao banco de dados
def connect_db():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Rota principal
@app.route('/')
def index():
    conn = connect_db()
    temperature, humidity, parameters = None, None, []
    if conn:
        with conn.cursor() as cursor:
            # Obter os dados mais recentes de sensor_data
            cursor.execute("SELECT temperature_c, humidity, timestamp FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
            data = cursor.fetchone()
            if data:
                temperature, humidity = data[0], data[1]

            # Obter os parâmetros mais recentes de sensor_param
            cursor.execute("SELECT desired_temperature, desired_temp_min, desired_temp_max, desired_humidity, desired_humi_min, desired_humi_max, TO_CHAR(timestamp AT TIME ZONE 'America/Sao_Paulo', 'YYYY-MM-DD HH24:MI:SS') AS localized_timestamp FROM sensor_param ORDER BY timestamp DESC LIMIT 1")
            parameters = cursor.fetchall()
        conn.close()

    return render_template('index.html', temperature=temperature, humidity=humidity, parameters=parameters)

# Rota para definir novos valores
@app.route('/set_params', methods=['POST'])
def set_params():
    new_temp = request.form['temperature']
    new_temp_min = request.form['temp_min']
    new_temp_max = request.form['temp_max']
    new_humidity = request.form['humidity']
    new_humi_min = request.form['humi_min']
    new_humi_max = request.form['humi_max']
    conn = connect_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sensor_param (desired_temperature, desired_humidity, desired_temp_min, desired_temp_max, desired_humi_min, desired_humi_max, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (new_temp, new_humidity, new_temp_min, new_temp_max, new_humi_min, new_humi_max, datetime.now(local_timezone)),
            )
            conn.commit()
        conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

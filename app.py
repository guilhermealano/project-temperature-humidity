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
    if conn:
        with conn.cursor() as cursor:
            # Obter os dados mais recentes
            cursor.execute("SELECT temperature_c, humidity, timestamp FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
            data = cursor.fetchone()
            temperature = data[0] if data else None
            humidity = data[1] if data else None
        conn.close()
    else:
        temperature, humidity = None, None
    return render_template('index.html', temperature=temperature, humidity=humidity)

# Rota para definir novos valores
@app.route('/set_params', methods=['POST'])
def set_params():
    new_temp = request.form['temperature']
    new_humidity = request.form['humidity']
    conn = connect_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sensor_param (desired_temperature, desired_humidity, timestamp) VALUES (%s, %s, %s)",
                (new_temp, new_humidity, datetime.now(local_timezone)),
            )
            conn.commit()
        conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
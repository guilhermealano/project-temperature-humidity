from flask import Flask, jsonify, request, render_template
import psycopg2
from datetime import datetime
import pytz

app = Flask(__name__)

# Configuração de conexão ao banco de dados
DB_CONFIG = {
    "dbname": "services",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost"
}

local_timezone = pytz.timezone('America/Sao_Paulo')  # Substitua pelo seu fuso horário local


# Função para conectar ao banco de dados
def connect_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


# Rota para obter os dados mais recentes do sensor
@app.route("/api/sensor", methods=["GET"])
def get_latest_sensor_data():
    conn = connect_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT temperature_c, humidity, timestamp FROM sensor_data ORDER BY timestamp DESC LIMIT 1"
            )
            result = cursor.fetchone()
            if result:
                data = {
                    "temperature": result[0],
                    "humidity": result[1],
                    "timestamp": result[2].astimezone(local_timezone).strftime("%Y-%m-%d %H:%M:%S")
                }
                conn.close()
                return jsonify(data)
    return jsonify({"error": "No data found"}), 500


# Rota para definir novos parâmetros
@app.route("/api/parameters", methods=["POST"])
def set_parameters():
    try:
        data = request.json
        desired_temperature = data.get("temperature")
        desired_humidity = data.get("humidity")
        timestamp = datetime.now(local_timezone)

        if desired_temperature is None or desired_humidity is None:
            return jsonify({"error": "Invalid input"}), 400

        conn = connect_db()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO sensor_param (desired_temperature, desired_humidity, timestamp) VALUES (%s, %s, %s)",
                    (desired_temperature, desired_humidity, timestamp)
                )
                conn.commit()
                conn.close()
                return jsonify({"message": "Parameters updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Rota para servir o frontend
@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
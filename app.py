from flask import Flask, render_template, request, jsonify
import psycopg2

app = Flask(__name__)

# Conexão com o banco de dados
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

# Função para buscar os dados mais recentes
def get_latest_data():
    conn = connect_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT temperature_c, humidity, timestamp FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
            result = cursor.fetchone()
        conn.close()
        return result
    return None

# Rota principal para renderizar a página
@app.route("/")
def index():
    data = get_latest_data()
    if data:
        temperature, humidity, timestamp = data
    else:
        temperature, humidity, timestamp = "N/A", "N/A", "N/A"
    return render_template("index.html", temperature=temperature, humidity=humidity, timestamp=timestamp)

# Rota para atualizar os valores desejados
@app.route("/update", methods=["POST"])
def update_desired_values():
    global desired_temperature, desired_humidity
    data = request.json
    desired_temperature = data.get("temperature", desired_temperature)
    desired_humidity = data.get("humidity", desired_humidity)
    return jsonify({"success": True, "temperature": desired_temperature, "humidity": desired_humidity})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
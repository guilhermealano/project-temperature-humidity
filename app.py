from flask import Flask, render_template
import psycopg2

app = Flask(__name__)

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

# Função para obter os dados mais recentes
def get_latest_data():
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT temperature_c, humidity, timestamp FROM sensor_data ORDER BY timestamp DESC LIMIT 1"
                )
                data = cursor.fetchone()
                return data  # Retorna uma tupla (temperature_c, humidity, timestamp)
        except Exception as e:
            print(f"Erro ao consultar dados: {e}")
        finally:
            conn.close()
    return None

@app.route('/')
def index():
    # Busca os dados mais recentes
    data = get_latest_data()
    if data:
        temperature, humidity, timestamp = data
        return render_template(
            'index.html',
            temperature=temperature,
            humidity=humidity,
            timestamp=timestamp
        )
    else:
        return render_template(
            'index.html',
            error="Nenhum dado disponível."
        )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
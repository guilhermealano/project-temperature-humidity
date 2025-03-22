from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import psycopg2

app = FastAPI()

# Modelo de entrada
class Reading(BaseModel):
    temperature_c: float
    humidity: float

# Função para conectar ao banco de dados
def connect_db():
    return psycopg2.connect(
        dbname="seu_banco",
        user="seu_usuario",
        password="sua_senha",
        host="seu_host",
        port="5432"
    )

@app.post("/api/v1/sensor/senddata/")
async def log_reading(reading: Reading):
    timestamp = datetime.now()
    
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sensor_data (temperature_c, humidity, timestamp) VALUES (%s, %s, %s)",
                (reading.temperature_c, reading.humidity, timestamp)
            )
            conn.commit()
        conn.close()
        return {"message": "Reading logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/v1/sensor/get_data_sensor/")
async def get_data_sensor():
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, temperature_c, humidity, timestamp FROM sensor_data ORDER BY timestamp DESC")
            data = cursor.fetchall()
        conn.close()
        
        return [
            {"id": row[0], "temperature_c": row[1], "humidity": row[2], "timestamp": row[3].isoformat()} 
            for row in data
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
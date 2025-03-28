from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel
from datetime import datetime
import psycopg2
import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

app = FastAPI()

# Modelo de entrada
class Reading(BaseModel):
    temperature_c: float
    humidity: float

class SensorParams(BaseModel):
    desired_temperature: float
    desired_temp_min: float
    desired_temp_max: float
    desired_humidity: float
    desired_humi_min: float
    desired_humi_max: float

# Função para conectar ao banco de dados
def connect_db():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432")
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

@app.get("/api/v1/sensor/get_data_old/")
async def get_data_old():
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

@app.get("/api/v1/sensor/get_data_sensor/")
async def get_data_sensor():
    try:
        conn = connect_db()
        temperature, humidity, parameters = None, None, []
        
        with conn.cursor() as cursor:
            # Obter os dados mais recentes de sensor_data
            cursor.execute("SELECT temperature_c, humidity, timestamp FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
            data = cursor.fetchone()
            if data:
                temperature, humidity = data[0], data[1]

            # Obter os parâmetros mais recentes de sensor_param
            cursor.execute("""
                SELECT desired_temperature, desired_temp_min, desired_temp_max, 
                       desired_humidity, desired_humi_min, desired_humi_max, 
                       TO_CHAR(timestamp AT TIME ZONE 'America/Sao_Paulo', 'YYYY-MM-DD HH24:MI:SS') 
                FROM sensor_param ORDER BY timestamp DESC LIMIT 1
            """)
            parameters = cursor.fetchall()
        conn.close()
        
        return {"temperature": temperature, "humidity": humidity, "parameters": parameters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/v1/sensor/set_params/")
async def set_params(
    desired_temperature: float = Form(...),
    desired_temp_min: float = Form(...),
    desired_temp_max: float = Form(...),
    desired_humidity: float = Form(...),
    desired_humi_min: float = Form(...),
    desired_humi_max: float = Form(...),
):
    try:
        conn = connect_db()
        timestamp = datetime.now()
        
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sensor_param (desired_temperature, desired_humidity, desired_temp_min, desired_temp_max, desired_humi_min, desired_humi_max, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (desired_temperature, desired_humidity, desired_temp_min, desired_temp_max, desired_humi_min, desired_humi_max, timestamp),
            )
            conn.commit()
        conn.close()
        
        return {"message": "Parameters updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
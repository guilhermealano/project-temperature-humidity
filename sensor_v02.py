import time
import board
import adafruit_dht
import psycopg2
from datetime import datetime
import pytz

# Initialize the DHT22 sensor with the data pin connected to GPIO4 (D4)
dhtDevice = adafruit_dht.DHT22(board.D4)

# Database connection parameters
db_config = {
    'dbname': 'services',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

# Function to save data to PostgreSQL
def save_to_postgresql(temperature_c, humidity, timestamp):
    try:
        # Connect to PostgreSQL
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        # Create the table if it doesn't exist
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id SERIAL PRIMARY KEY,
            temperature_c FLOAT NOT NULL,
            humidity FLOAT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL
        );
        '''
        cursor.execute(create_table_query)
        connection.commit()

        # Insert temperature, humidity, and timestamp into the database
        insert_query = '''
        INSERT INTO sensor_data (temperature_c, humidity, timestamp) 
        VALUES (%s, %s, %s);
        '''
        cursor.execute(insert_query, (temperature_c, humidity, timestamp))
        connection.commit()

    except Exception as e:
        print(f"Database error: {e}")

    finally:
        # Close connection
        if connection:
            cursor.close()
            connection.close()

# Set local timezone
local_timezone = pytz.timezone('Your/Timezone')  # Replace with your local timezone, e.g., 'America/New_York'

# Main loop for capturing sensor data and saving it to PostgreSQL
while True:
    try:
        # Read temperature and humidity from the DHT22 sensor
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity

        # Get the current time with local timezone
        timestamp = datetime.now(local_timezone)

        # Print the values to the serial port (console)
        print(
            "Temp: {:.1f} C  Humidity: {}%  Timestamp: {}".format(
                temperature_c, humidity, timestamp
            )
        )

        # Save the data to PostgreSQL
        save_to_postgresql(temperature_c, humidity, timestamp)

    except RuntimeError as error:
        # Handle errors from the DHT22 sensor (expected occasional errors)
        print(f"Sensor error: {error.args[0]}")
        time.sleep(2.0)
        continue

    except Exception as error:
        # Exit the program and close the DHT device on any unexpected errors
        dhtDevice.exit()
        raise error

    # Wait for 2 seconds before capturing the next data
    time.sleep(2.0)
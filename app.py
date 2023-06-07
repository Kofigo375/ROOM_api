import os # used to read environment variables from .env file
import psycopg2
from dotenv import load_dotenv
from datetime  import datetime, timezone
from flask import Flask, request



load_dotenv()  # take environment variables from .env
def create_app():
    app = Flask(__name__)
    url = os.getenv('DATABASE_URL')
    connection = psycopg2.connect(url)

    CREATE_ROOMS_TABLE = (
        "CREATE TABLE IF NOT EXISTS rooms (id SERIAL PRIMARY KEY, name TEXT);"
    )
    CREATE_TEMPS_TABLE = """CREATE TABLE IF NOT EXISTS temperatures (room_id INTEGER, temperature REAL, 
                            date TIMESTAMP, FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE CASCADE);"""

    INSERT_ROOM_RETURN_ID = "INSERT INTO rooms (name) VALUES (%s) RETURNING id;"
    INSERT_TEMP = (
        "INSERT INTO temperatures (room_id, temperature, date) VALUES (%s, %s, %s);"
    )

    GLOBAL_NUMBER_OF_DAYS = (
        """SELECT COUNT(DISTINCT DATE(date)) AS days FROM temperatures;"""
    )
    GLOBAL_AVG = """SELECT AVG(temperature) as average FROM temperatures;"""



    # adding a room to the database
    @app.post("/api/rooms")
    def create_room():
        data = request.get_json()  # takes the string and turns it into a dictionary
        name = data["name"]
        with connection:           # starting a connection with the database 
            with connection.cursor() as cursor:   # cursor is an object that allows insertion and iteration in the database
                cursor.execute(CREATE_ROOMS_TABLE)  # creating the table if it doesn't exist    
                cursor.execute(INSERT_ROOM_RETURN_ID, (name,) )
                room_id = cursor.fetchone()[0]  # fetchone() returns the first row of the query
        return {"id": room_id, "message": f"Room {name} created"}, 201      


    # adding a temperature to the room in the database
    @app.post("/api/temperature")
    def add_temp():
        data = request.get_json()
        temperature = data["temperature"]
        room_id = data["room"]
        try:
            date = datetime.strptime(data["date"], "%m-%d-%Y %H:%M:%S.%f")
        except KeyError:
            date = datetime.now(timezone.utc)

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(CREATE_TEMPS_TABLE)
                cursor.execute(INSERT_TEMP, (room_id, temperature, date))
        return {"message": f"Temperature {temperature} added successfully"}, 201  

    @app.get("/api/average")
    def get_global_avg():
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(GLOBAL_AVG)
                average = cursor.fetchone()[0]
                cursor.execute(GLOBAL_NUMBER_OF_DAYS)
                days = cursor.fetchone()[0]
        return {"average": round(average), "days": days}, 200

    return app
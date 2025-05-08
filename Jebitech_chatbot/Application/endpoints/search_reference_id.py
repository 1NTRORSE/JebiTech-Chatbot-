import pymysql
import asyncio
import concurrent.futures
from dotenv import load_dotenv
import os

load_dotenv()
host = os.getenv("client_host")
user = os.getenv("client_user")
password = os.getenv("client_password")
database = os.getenv("client_database")
port = int(os.getenv("client_port"))

db_configs = [

    {"host": host, "port": port, "user": user, "password": password, "database": database, "table":"BREEZEAWAY_RESERVATIONS"},
    {"host": host, "port": port, "user": user, "password": password, "database": database, "table": "GUESTY_RESERVATIONS_FULL"},
    {"host": host, "port": port, "user": user, "password": password, "database": database, "table": "GUESTY_RESERVATIONS"},

]

executor = concurrent.futures.ThreadPoolExecutor()

def search_reference_in_db_sync(db_config, reference_id):
    try:
        conn = pymysql.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )
        cursor = conn.cursor()
        
        check_reservation_query = f"SELECT 1 FROM {db_config['table']} WHERE reservation_id = %s LIMIT 1"
        cursor.execute(check_reservation_query, (reference_id,))
        reservation_exists = cursor.fetchone()

        if not reservation_exists:
            conn.close()
            return None

        if db_config["table"] == "BREEZEAWAY_RESERVATIONS":
            get_property_query = f"SELECT reference_external_property_id FROM {db_config['table']} WHERE reservation_id = %s LIMIT 1"
        elif db_config["table"] == "GUESTY_RESERVATIONS_FULL":
            get_property_query = f"SELECT listing_id FROM {db_config['table']} WHERE reservation_id = %s LIMIT 1"
        else:
            get_property_query = f"SELECT reservation_listing_id FROM {db_config['table']} WHERE reservation_id = %s LIMIT 1"

        cursor.execute(get_property_query, (reference_id,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None
    except Exception as e:
        print(f"Database Error: {e}")
        return None

async def search_reference_in_db(db_config, reference_id):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, search_reference_in_db_sync, db_config, reference_id)

async def find_reference_id(reference_id: str) -> str:
    tasks = [search_reference_in_db(db, reference_id) for db in db_configs]
    results = await asyncio.gather(*tasks)

    for result in results:
        if result:
            return result

    return -1

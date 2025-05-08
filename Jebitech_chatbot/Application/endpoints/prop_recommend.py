import pymysql
from dotenv import load_dotenv
#from Application.endpoints.prompt_generator import recommendation_prompt
from Application.endpoints.prompt_supplier import recommendation_prompt
import os
import google.generativeai as genai
import json

load_dotenv()

user=os.getenv('our_user')
password=os.getenv('our_password')
host=os.getenv('our_host')
database=os.getenv('our_database')
print("PORT NUMBER->",os.getenv('our_port'))
port=int(os.getenv('our_port'))
#port=3306

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

async def get_reference():    
    try:
        conn=pymysql.connect(
        host=host,
        user=user,
        password=password,  
        database=database,
        port=port)
    
        cursor=conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("select property_building,property_address1,address_state,address_country,nick_name,address_full,property_type,bedrooms from property_data_live")
        results=cursor.fetchall()
        results_json=json.dumps(results,indent=4)
    
        return results_json
    
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL for Property Recommendation: {e}")
    finally:
        if conn:
            conn.close()
############
# {'property_building': None, 'property_address1': None, 'address_state': 'Tennessee', 'address_country': 'United States', 'nick_name': "Parson's Retreat", 'address_full': '107 Parsons Pl, Franklin, TN 37064, USA', 'property_type': 'House', 'bedrooms': '4'}
# {'property_building': 'Grandview Resort', 'property_address1': '690 Stockton Dr', 'address_state': None, 'address_country': None, 'nick_name': None, 'address_full': None, 'property_type': None, 'bedrooms': None}

def recommend(user_input,book):
    """Recommends properties based on user input."""
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
        system_instruction=recommendation_prompt
    )

    chat_session = model.start_chat()

    modified_input=f"User Asked:{user_input},Your Property reference: {book}"
    response = chat_session.send_message(modified_input)
    return response.text

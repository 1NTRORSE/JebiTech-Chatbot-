from fastapi import HTTPException
from dotenv import load_dotenv
import logging
import google.generativeai as genai
import os
import asyncio
import pymysql
import re

from Application.endpoints.prompt_supplier import guest_prompt
                                                                     
load_dotenv()


our_host = os.getenv("our_host")
our_user = os.getenv("our_user")
our_password = os.getenv("our_password")
our_database = os.getenv("our_database")


GEMINI_API_KEY = os.getenv("GEMINI_KEY")
if not GEMINI_API_KEY:
    logging.error("GEMINI_API_KEY environment variable is missing!")
    raise ValueError("GEMINI_KEY is not set in environment variables")

genai.configure(api_key=GEMINI_API_KEY)


generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}





async def clean_user_input(user_input):
    """Extracts potential property names from user input using regex."""
    words = re.findall(r"[A-Za-z\s\-]+", user_input)
    return " ".join(words).strip()


def clean_sql_query(sql_query):
    """Cleans SQL query formatting."""
    return " ".join(sql_query.replace("```sql", "").replace("```", "").strip().split())


def execute_sql(sql_query):
    try:
        cleaned_query = clean_sql_query(sql_query)
        connection = pymysql.connect(
    host=our_host,
    user=our_user,  
    password=our_password,  
    database=our_database  
)       
        cursor = connection.cursor()
 
        cursor.execute(cleaned_query)
        results = cursor.fetchall()

        if results:
            formatted_results = "\n".join([str(row) for row in results])
 
            return formatted_results
        else:
            return "Query executed successfully, but no results were found."
            
    except pymysql.MySQLError as e:
    
        raise HTTPException( f"MySQL Error: {e}")


def get_property_names():
    """Fetches property names from the database, considering both property_name and nick_name."""
    property_names = set()
    try:
        
        connection = pymysql.connect(
    host=our_host,
    user=our_user,  
    password=our_password,  
    database=our_database  
)       
        cursor = connection.cursor()
        query = "SELECT property_building, nick_name FROM property_data_live"
        
        cursor.execute(query)

        results = cursor.fetchall()

        for row in results:
            if row[0]:
                property_names.add(row[0])  
            if row[1] and row[1] not in property_names:
                property_names.add(row[1])
        cursor.close()
        connection.close()

    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return property_names

async def property_name_identifier(user_input, property_list):
    """Identifies property names in user input using Gemini AI."""
    system_prompt="You are an AI assistant that identifies 1 property name from user input IF user is asking question referencing to any property from a given list of property." \
    " You have access to a predefined list of property names  {property_list}. If a user refers to a property name, even with typos, match it to the closest valid property name. If no property name is detected, respond with 'No matching property found.'" \
    "please correctly identify property name while assisngning  from given list.{property_list}" \
    "eg:1 if user is asking 'I want to know about zen lodge' and if the list contains 'Zen Lodge', you should identify it as 'Zen Lodge'.(observation:Here in user question, property name is correctly mentioned if we not concider lower or upper case)" \
    "eg:2 if user is asking 'I want to know about zen loj' and if the list contains  'Zen Lodge', you should identify it as 'Zen Lodge'.(observation:Here although 2 words are'nt same but they seem to be Homophone thus you will choose 'Zen Lodge' )" \



    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
        system_instruction=system_prompt,
    )

    chat_session = model.start_chat()
    modified_input = f"User Asked: {user_input}. Property List: {property_list}. Identify the property name."
    
    value = await asyncio.to_thread(chat_session.send_message, modified_input)
    
    return value.text


async def final_answer(new_input):
    """Generates final response using Gemini AI."""
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
        system_instruction=guest_prompt,
    )

    chat_session = model.start_chat()
    
    value = await asyncio.to_thread(chat_session.send_message, new_input)
    
    return value.text


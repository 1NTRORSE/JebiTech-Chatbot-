from pydantic import BaseModel, Field
from typing import Dict
#class database_config(BaseModel):
    # our_username: str
    # our_password: str 
    # our_host: str 
    # our_port: int 
    # our_db_name: str 
    # client_username: str
    # client_password: str 
    # client_host: str 
    # client_port: int 
    # client_db_name: str 
class DBCredentials(BaseModel):
    host: str
    user: str
    password: str
    database: str
    port: int



class MappingPayload(BaseModel):
    our_db: DBCredentials
    client_db: DBCredentials
    our_table: str
    mappings: Dict[str, Dict[str, str]] 

from fastapi import APIRouter, HTTPException,Depends,Request,Response
from sqlalchemy.orm import Session, aliased
from sqlalchemy import desc, distinct, func, and_
from datetime import datetime
import logging
import asyncio
from typing import List, Union, Optional
from Application.endpoints.prop_recommend import get_reference,recommend
from dotenv import load_dotenv
import google.generativeai as genai
from Application.database import get_db, Session_Table, Chat, ChatTransfer, SessionLocal, AgentID
from Application.endpoints.search_reference_id import find_reference_id
from Application.endpoints.prompt_supplier import guest_prompt
from Application.sql_response import execute_sql,get_property_names,clean_user_input,final_answer,property_name_identifier
from Application.endpoints.chat_transfer import transfer_to_customer_care
from pydantic import BaseModel
from datetime import datetime, timedelta
import pymysql
import uuid
import os
import re
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("guest_user.log", mode="a"), logging.StreamHandler()],
)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_KEY")
#GEMINI_API_KEY=""
if not GEMINI_API_KEY:
    logging.error("GEMINI_API_KEY environment variable is missing!")
    raise ValueError("GEMINI_KEY is not set in environment variables")

genai.configure(api_key=GEMINI_API_KEY)


guest_router = APIRouter()

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}


property_reference_list="empty"

async def initial():

    global property_reference_list

    property_reference_list = await get_reference()
    #print(property_reference_list)



def property_recommendation() -> str:
     print("Property Recommendation Function Called")

def customer_assist():
    """Execute this funtion when user explicitly demands to connect customer assistance team. """
    return "Wait a moment....Call connected successfully."


def extract_user_id(text: str) -> str:
    """Extracts a user ID from a given text."""
    pattern = r"\b(?:[0-9a-f]{24}|\d{8})\b"
    match = re.search(pattern, text, re.IGNORECASE)

    return match.group(0) if match else "None"

model2 = genai.GenerativeModel(
    model_name="gemini-2.0-flash", #"gemini-2.5-pro-exp-03-25",#"gemini-2.0-flash",  
    generation_config=generation_config,
    system_instruction=guest_prompt,
    tools=[extract_user_id,property_recommendation,customer_assist]
)
chat_session = model2.start_chat()


async def ensure_guest_session(db: Session, request: Request, response: Response):
   

    session_id = request.cookies.get("session_id")  
  

    if not session_id:  
        session_id = str(uuid.uuid4())

        new_session = Session_Table(
            session_id=session_id,
            #user_id=user_id,
            user_type="guest",
            status="active",
            started_at=datetime.utcnow(),
        )

        db.add(new_session)
        db.commit()

        response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=7200)  
       
    return session_id#, user_id

    


property_list=list(get_property_names())        
@guest_router.post("/Guest_user/chat/guest")
async def chat_with_bot( user_input: str,request: Request, response: Response, db: Session = Depends(get_db)):
    """Takes Guest/Registered user's input, generates LLM response, and appends conversation in DB."""
    s=time.time()
    
    #print(property_list)
    session_id =await ensure_guest_session(db, request, response)#session_id, user_id
    user = db.query(Session_Table).filter_by(session_id=session_id).first()
    record_search = db.query(Chat).filter_by(session_id=session_id).first()
    flag=0
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid session ID")
        
        
    
 
    result =await property_name_identifier(user_input, property_list)
    #print(result)
    if result not in [None, "No matching property found."]:  
        property_name= result  

    else:
        property_name="No matching property found."


    modified_input = f"User asked:{user_input},property_name:{property_name}"     
    #print(modified_input)
    try:
        response = chat_session.send_message(modified_input)
        #print(response)
    except Exception as e:
        raise HTTPException(status_code=404,detail="kindly resend your question,facing some network issue.")
    for part in response.candidates[0].content.parts:
        if hasattr(part, "function_call") and part.function_call is not None and part.function_call.name == "extract_user_id":
            id = extract_user_id(user_input)
            #print(id)
            if id != None:
                referenced_property_id=await find_reference_id(id)
                if referenced_property_id !=0 and referenced_property_id!=-1:
                    referenced_property_id = referenced_property_id.replace("'", "''")
                    generated_sql = f"select summary from property_data_live where listing_id ='{referenced_property_id}' "
                    

                    query_result = execute_sql(generated_sql)
                    #print(query_result)
                    new_input=f"User asked:{user_input}. The query result is: {query_result}.(He is verified user) Format it for user understanding in natural language professionaly."
           
                    final_response=await final_answer(new_input)
         
                    generated_sql = final_response
                if referenced_property_id==0:
                     generated_sql="Reservation ID provided by you is expired thus no property is associated with you"
                if referenced_property_id==-1:
                     generated_sql="Invalid Reservation ID is provided kindly double check your Reservation ID !!!"
                user.ended_at = datetime.utcnow()
                message_container=f"\n USER-> {user_input}\n RESPONSE-> {generated_sql}"
                print("message_container",message_container)

                
                if not record_search:
                    first_chat = Chat(
            session_id=session_id,
            sender="user",
            message=message_container,
            sent_at=datetime.utcnow(),
            status="read"
        )
                    
                    
                    db.add(first_chat)
                    record_search = first_chat
                    
                else :
                    record_search.message = str((record_search.message or "") + message_container)
                    record_search.sent_at = datetime.utcnow()
                    db.add(record_search)
                    
                if user.started_at:
                    user.Duration = (user.ended_at - user.started_at).total_seconds() 
                
                    

            
                db.commit()
                db.refresh(user)
              
                print({"session_id": session_id,
            "User: ":user_input,
            "AI Response: ":generated_sql})
                return {"session_id": session_id,
            "User: ":user_input,
            "AI Response: ":generated_sql}

            else:
                final_string="Please enter valid Reservation ID as no User found with this ID"
            
                user.ended_at = datetime.utcnow()
                message_container=f"\n USER-> {user_input}\n RESPONSE->{final_string}."
                
                if user.started_at:
                    user.Duration = (user.ended_at - user.started_at).total_seconds() 
                if not record_search:
                        

                    first_chat = Chat(
            session_id=session_id,
            sender="user",
            message=message_container,
            sent_at=datetime.utcnow(),
            status="read"
        )
                        
                    
                    
                    db.add(first_chat)
                    record_search=first_chat
                else :
                 
                           
                    record_search.message = str((record_search.message or "") + message_container)
                    record_search.sent_at = datetime.utcnow()
                    db.add(record_search)

                
                db.commit()
                db.refresh(user)
                db.refresh(record_search)
                print({"session_id": session_id,
             "User: ":user_input,
             "AI Response: ":"Please enter valid Reservation ID as no user found with this ID."})
                return {"session_id": session_id,
             "User: ":user_input,
             "AI Response: ":"Please enter valid Reservation ID as no user found with this ID."}


        if hasattr(part, "function_call") and part.function_call is not None and part.function_call.name == "property_recommendation":
            try:
                recommendation=recommend(user_input,property_reference_list)
                print("recommendation",recommendation)
            #print(recommendation)
                user.ended_at = datetime.utcnow()
                message_container=f"\n USER-> {user_input}\n RESPONSE-> {recommendation}"
                if user.started_at:
                    user.Duration = (user.ended_at - user.started_at).total_seconds() 
                if not record_search:

                    first_chat = Chat(
            session_id=session_id,
            sender="user",
            message=message_container,
            sent_at=datetime.utcnow(),
            status="read"
        )
                    db.add(first_chat)
                else:
                    record_search.message = str((record_search.message or "") + message_container)
                    record_search.sent_at = datetime.utcnow()
    #  "Execution Time: ":e-s
                db.add(user)
                db.commit()
                db.refresh(user)
                e=time.time()
                print( {"session_id": session_id,
             "User: ":user_input,

             "AI Response: ":recommendation,
            
           
             })
                return {"session_id": session_id,
             "User: ":user_input,

             "AI Response: ":recommendation,
            
           
             }
            except Exception as e:
                raise HTTPException(status_code=501,detail="Facing some network delay,resend your question.")
            #return recommendation 
        if hasattr(part, "function_call") and part.function_call is not None and part.function_call.name == "customer_assist":


            session = db.query(Session_Table).filter_by(session_id=session_id).first()
            if session:
                session.status = "unassigned"
                db.add(session)
                db.commit()
            fun = customer_assist()
            return  fun





    generated_sql = response.text
    print("AI RESPONSE->",generated_sql)
    try:        
        if  "property_data_live" in generated_sql :


            logging.info("SQL query detected in response")
        
            query_result =execute_sql(generated_sql)
            print(generated_sql)
            #final_response=await asyncio.to_thread(chat_session.send_message,f"User asked: '{user_input}'. The query result is: {query_result}.(He is not verified user thus NEVER provide any sensitive information if{user_input} contains.) Format it for user understanding in natural language professionaly but if they seek any information from (Not allowed )field then professionally say no to user.Also answer only  what is asked please.No Unnecessary information.")
            final_response=await asyncio.to_thread(chat_session.send_message,f"User asked: '{user_input}'. The query result is: {query_result}.(He is not verified user thus NEVER provide any sensitive information if{user_input} contains.) Format it for user understanding in natural language professionaly but if they seek any information from (Not allowed )field then professionally say no to user.Also answer only  what is asked please.No Unnecessary information.")
            response_text = final_response.candidates[0].content.parts[0].text
            generated_sql=response_text

    
        else:
            print(generated_sql)
            logging.info("Non-SQL response detected")
        
    except Exception as e:
        raise HTTPException(status_code=405,detail=f"Kindly resend your question facing some network issue {e}")
    
    user.ended_at = datetime.utcnow()
    message_container=f"\n USER-> {user_input}\n RESPONSE-> {generated_sql}"
    if user.started_at:
        user.Duration = (user.ended_at - user.started_at).total_seconds() 
    if not record_search:
        first_chat = Chat(
            session_id=session_id,
            sender="user",
            message=message_container,
            sent_at=datetime.utcnow(),
            status="read"
        )
        db.add(first_chat)
    else:
        record_search.message = str((record_search.message or "") + message_container)
        record_search.sent_at = datetime.utcnow()
    #  "Execution Time: ":e-s
    db.add(user)
    db.commit()
    db.refresh(user)
    e=time.time()
    print({"session_id": session_id,
             "User: ":user_input,

             "AI Response: ":generated_sql,
            
           
             })
    return {"session_id": session_id,
             "User: ":user_input,

             "AI Response: ":generated_sql,
            
           
             }


@guest_router.get("/Get_session_chat/")
def get_session_chat(session_id: str, db: Session = Depends(get_db)):
    """Fetches conversation history for a given session ID."""
    record_search = db.query(Chat).filter_by(session_id=session_id).all()
    if not record_search:
        raise HTTPException(status_code=400, detail="Please enter a valid session ID")
    
    formatted_history = []
    
    for record in record_search:
        lines = record.message.strip().split('\n')
        for line in lines:
            clean_line = line.strip()
            if clean_line:  
                formatted_history.append(clean_line)
    
    return {
        "Session ID": session_id,
        "Conversation History": formatted_history
    }

############



@guest_router.get("/Get_all_session_chat/")
async def get_all_session_chat( db: Session = Depends(get_db)):
    """Admin can walthrough all the sessions from here"""
    sessions = db.query(Session_Table).all()
    if not sessions:
        raise HTTPException(status_code=404, detail="No sessions found")

    response_data = []

    for session in sessions:
        chat_history = db.query(Chat).filter_by(session_id=session.session_id).all()
        if not chat_history:
            continue
        else:
            session_info={
            "session_id": session.session_id,
            "Started At":session.started_at,
            "Ended At":session.ended_at
        }
        response_data.append(session_info)

    if not response_data:
        raise HTTPException(status_code=404, detail="No chat history found for any session")

    return response_data

############
@guest_router.post("/create_user/")
async def create_user(db:Session=Depends(get_db)):
    """"Creates New user Session"""
   
    

    new_session = Session_Table(
       
        
        user_type="user",
        status="active",
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
        Duration=0
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {
        "message": "New user created successfully!",
        "user_id": new_session.user_id,
        "session_id": new_session.session_id
    }
#####
@guest_router.put("/Change-to-Admin/")
async def update_admin(user_id:str,db:Session=Depends(get_db)):
    """"Updates User to Admin"""
    user=db.query(Session_Table).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.user_type="admin"
    db.commit()
    db.refresh(user)

    return {
        "message": "User type updated to admin successfully!",
        "user_id": user.user_id,
        
    }
#####
class TransferRequest(BaseModel):
    transfer_reason: Optional[str] = ""
    agent_id: str
    session_id: str

@guest_router.post("/transfer")
async def transfer_to_customer_care(
        request: TransferRequest,
        db: Session = Depends(get_db),
        http_req: Request = None,
        http_res: Response = None,
):
    # Validate session_id from request
    session = db.query(Session_Table).filter_by(session_id=request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="No session found for the given session_id.")

    # Check if a transfer record already exists for this session_id
    existing_transfer = db.query(ChatTransfer).filter_by(session_id=request.session_id).first()
    if existing_transfer:
        return {"message": "Request already created"}

    # Validate agent_id from request
    agent = db.query(AgentID).filter_by(agent_id=request.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Invalid agent_id provided.")

    # Update session status to 'assigned'
    session.status = "assigned"

    # Notify Gemini model (assuming it's a pre-existing function)
    gemini_response = chat_session.send_message(f"User is being transferred. Reason: {request.transfer_reason}")
    gemini_text = gemini_response.text

    # Extract user ID from the response (assuming extract_user_id is a pre-existing function)
    extracted_user_id = extract_user_id(gemini_text)
    user_id = extracted_user_id if extracted_user_id != "None" else session.user_id

    # Save transfer record to ChatTransfer table
    transfer_record = ChatTransfer(
        transfer_id=str(uuid.uuid4()),
        session_id=session.session_id,
        transferred_by= "Admin",
        transfer_reason=request.transfer_reason or "",
        agent_id=request.agent_id
    )

    db.add(transfer_record)
    db.commit()
    db.refresh(transfer_record)

    # Return the response with transfer details and agent info
    return {
        "message": "Customer transferred successfully",
        "transfer_id": transfer_record.transfer_id,
        "session_id": session.session_id,
        "user_id": user_id,
        "transferred_by": "Admin",
        "transfer_reason": request.transfer_reason or "",
        "agent_name": agent.agent_name,
        "agent_id": request.agent_id,
        "agent_phone": agent.agent_phone,
        "agent_mail": agent.agent_mail
    }

#########
class UnassignedUser(BaseModel):
    user_id: Union[int, str]
    session_id: Union[int, str]
    status: str

@guest_router.get("/unassigned-users", response_model=List[UnassignedUser])
def get_unassigned_users(db: Session = Depends(get_db)):
    unassigned_sessions = db.query(Session_Table).filter_by(status="unassigned").all()

    return [
        {
            "user_id": session.user_id,
            "session_id": session.session_id,
            "status": session.status
        }
        for session in unassigned_sessions
    ]

#########
class AssignedUser(BaseModel):
    user_id: Union[int, str]
    session_id: Union[int, str]
    transfer_id: Union[int, str]
    agent_id: Union[int, str]
    agent_name: str
    status: str

@guest_router.get("/assigned_users", response_model=List[AssignedUser])
def get_assigned_users(db: Session = Depends(get_db)):
    # Subquery to get the latest transfer per session
    subquery = (
        db.query(
            ChatTransfer.session_id,
            func.max(ChatTransfer.transferred_at).label("latest_transfer_time")
        )
        .group_by(ChatTransfer.session_id)
        .subquery()
    )

    # Join Session_Table with ChatTransfer using the subquery
    assigned_sessions = (
        db.query(
            Session_Table.user_id,
            Session_Table.session_id,
            Session_Table.status,
            ChatTransfer.transfer_id,
            ChatTransfer.agent_id,
            AgentID.agent_name,
        )
        .join(ChatTransfer, ChatTransfer.session_id == Session_Table.session_id)
        .join(subquery, and_(
            ChatTransfer.session_id == subquery.c.session_id,
            ChatTransfer.transferred_at == subquery.c.latest_transfer_time
        ))
        .filter(Session_Table.status == "assigned")
        .all()
    )

    return [
        {
            "user_id": row.user_id,
            "session_id": row.session_id,
            "transfer_id": row.transfer_id,
            "agent_id": row.agent_id,
            "agent_name": row.agent_name,
            "status": row.status
        }
        for row in assigned_sessions
    ]


class AgentsFetch(BaseModel):
    agent_name: str
    agent_id: Union[int, str]
    agent_phone: int
    agent_mail:Union[int, str]

@guest_router.get("/agent_info", response_model= List[AgentsFetch])
def get_all_agents(db: Session = Depends(get_db)):
    agents = db.query(AgentID).all()

    return[
        {
            "agent_name": agent.agent_name,
            "agent_id": agent.agent_id,
            "agent_phone": agent.agent_phone,
            "agent_mail": agent.agent_mail
        }
        for agent in agents
    ]



##################### live updation.py code is below.(for your reference)

# import pymysql
# import schedule
# import time
# import logging
# import os
# from dotenv import load_dotenv

# load_dotenv()


# our_host=os.getenv("our_host")
# our_user=os.getenv("our_user")
# our_password=os.getenv("our_password")
# our_database=os.getenv("our_database")
# our_port=int(os.getenv("our_port"))
# COLUMN_MAPPING={

#  "GUESTY_LISTINGS": {
#     "id": "property_id",
#     "listing_id": "listing_id",
#     "saas_auto_renew": "saas_auto_renew",
#     "cleaning_fee_id": "cleaning_fee_id",
#     "cleaning_fee_value_type": "cleaning_fee_value_type",
#     "cleaning_fee_formula": "cleaning_fee_formula",
#     "cleaning_fee_multiplier": "cleaning_fee_multiplier",
#     "channel_commission_use_account_settings": "channel_commission_use_account_settings",
#     "channel_commission_id": "channel_commission_id",
#     "channel_commission_created_at": "channel_commission_created_at",
#     "channel_commission_updated_at": "channel_commission_updated_at",
#     "cleaning_status": "cleaning_status",
#     "picture_caption": "picture_caption",
#     "picture_thumbnail": "picture_thumbnail",
#     "minimum_nights": "minimum_nights",
#     "maximum_nights": "maximum_nights",
#     "monthly_price_factor": "monthly_price_factor",
#     "weekly_price_factor": "weekly_price_factor",
#     "base_price": "base_price",
#     "weekend_base_price": "weekend_base_price",
#     "currency": "currency",
#     "cleaning_fee": "cleaning_fee",
#     "confirmed_before_checkin_delay_minutes": "confirmed_before_checkin_delay_minutes",
#     "confirmed_day_of_checkin_delay_minutes": "confirmed_day_of_checkin_delay_minutes",
#     "confirmed_day_of_checkout_delay_minutes": "confirmed_day_of_checkout_delay_minutes",
#     "confirmed_during_stay_delay_minutes": "confirmed_during_stay_delay_minutes",
#     "confirmed_after_checkout_delay_minutes": "confirmed_after_checkout_delay_minutes",
#     "unconfirmed_first_message_delay_minutes": "unconfirmed_first_message_delay_minutes",
#     "unconfirmed_subsequent_message_delay_minutes": "unconfirmed_subsequent_message_delay_minutes",
#     "answeing_machine_is_active": "answeing_machine_is_active",
#     "auto_reviews_status": "auto_reviews_status",
#     "auto_payments_time_relation_names": "auto_payments_time_relation_names",
#     "auto_payments_time_relation_units": "auto_payments_time_relation_units",
#     "auto_payments_time_relation_amounts": "auto_payments_time_relation_amounts",
#     "pms_cleaning_status": "pms_cleaning_status",
#     "calendar_rules_default_availability": "calendar_rules_default_availability",
#     "bookingcom_cut_off_hours_enabled": "bookingcom_cut_off_hours_enabled",
#     "expedia_cut_off_hours_enabled": "expedia_cut_off_hours_enabled",
#     "airbnb_cut_off_hours_enabled": "airbnb_cut_off_hours_enabled",
#     "directbookings_cut_off_hours_enabled": "directbookings_cut_off_hours_enabled",
#     "calendar_rules_default_hours": "calendar_rules_default_hours",
#     "calendar_rules_allow_request_to_book": "calendar_rules_allow_request_to_book",
#     "calendar_rules_advance_notice_updated_at": "calendar_rules_advance_notice_updated_at",
#     "calendar_rules_advance_notice_updated_by": "calendar_rules_advance_notice_updated_by",
#     "booking_window_default_days": "booking_window_default_days",
#     "booking_window_updated_at": "booking_window_updated_at",
#     "preparation_time_updated_at": "preparation_time_updated_at",
#     "dynamic_checkin_updated_at": "dynamic_checkin_updated_at",
#     "rental_periods_request_to_book": "rental_periods_request_to_book",
#     "rental_periods_ids": "rental_periods_ids",
#     "rental_periods_from": "rental_periods_from",
#     "default_availability_updated_at": "default_availability_updated_at",
#     "default_availability_updated_by": "default_availability_updated_by",
#     "listing_type": "listing_type",
#     "owners_list": "owners_list",
#     "amenities_list": "amenities_list",
#     "amenities_not_included_list": "amenities_not_included_list",
#     "use_account_revenue_share": "use_account_revenue_share",
#     "use_account_taxes": "use_account_taxes",
#     "use_account_markups": "use_account_markups",
#     "use_account_additional_fees": "use_account_additional_fees",
#     "is_active": "is_active",
#     "net_income_formula": "net_income_formula",
#     "commission_formula": "commission_formula",
#     "owner_revenue_formula": "owner_revenue_formula",
#     "tax_ids": "tax_ids",
#     "tax_types": "tax_types",
#     "tax_amounts": "tax_amounts",
#     "tax_names": "tax_names",
#     "tax_units": "tax_units",
#     "tax_quantifiers": "tax_quantifiers",
#     "taxes_applied_to_all_fees": "taxes_applied_to_all_fees",
#     "taxes_applied_on_fees": "taxes_applied_on_fees",
#     "taxes_are_applied_by_default": "taxes_are_applied_by_default",
#     "tax_conditional_overrides_view_types": "tax_conditional_overrides_view_types",
#     "tax_conditional_overrides_max_nights": "tax_conditional_overrides_max_nights",
#     "pre_bookings_list": "pre_bookings_list",
#     "origin_id": "origin_id",
#     "nick_name": "nick_name",
#     "minimum_age": "minimum_age",
#     "address_full": "address_full",
#     "address_street": "address_street",
#     "address_city": "address_city",
#     "address_country": "address_country",
#     "address_latitude": "address_latitude",
#     "address_longitude": "address_longitude",
#     "address_zip_code": "address_zip_code",
#     "address_state": "address_state",
#     "address_county": "address_county",
#     "room_type": "room_type",
#     "property_type": "property_type",
#     "ota_room_type": "ota_room_type",
#     "accommodates": "accommodates",
#     "bathrooms": "bathrooms",
#     "bedrooms": "bedrooms",
#     "beds_count": "beds_count",
#     "listing_status": "listing_status",
#     "host_name": "host_name",
#     "wifi_name": "wifi_name",
#     "wifi_password": "wifi_password",
#     "area_in_square_feet": "area_in_square_feet",
#     "trash_collection_day": "trash_collection_day",
#     "parking_instructions": "parking_instructions",
#     "created_at": "created_at",
#     "origin": "origin",
#     "default_check_in_time": "default_check_in_time",
#     "default_check_out_time": "default_check_out_time",
#     "check_in_instructions": "check_in_instructions",
#     "check_out_instructions": "check_out_instructions",
#     "picture_ids": "picture_ids",
#     "picture_captions": "picture_captions",
#     "picture_originals": "picture_originals",
#     "picture_heights": "picture_heights",
#     "picture_widths": "picture_widths",
#     "picture_thumbnails": "picture_thumbnails",
  
#     "account_id": "account_id",
#     "time_zone": "time_zone",
#     "last_updated_at": "last_updated_at",
#     "integration_ids": "integration_ids",
#     "integration_platforms": "integration_platforms",
#     "booking_com_initial_complex_listings": "booking_com_initial_complex_listings",
#     "booking_com_publish_company_logos": "booking_com_publish_company_logos",
#     "booking_com_is_published_company_logos": "booking_com_is_published_company_logos",
#     "booking_com_publish_company_infos": "booking_com_publish_company_infos",
#     "booking_com_is_published_company_infos": "booking_com_is_published_company_infos",
#     "vacayhome_currencies": "vacayhome_currencies",
#     "vacayhome_statuses": "vacayhome_statuses",
#     "vacayhome_cancellation_policies": "vacayhome_cancellation_policies",
#     "vacayhome_cancellation_penalties": "vacayhome_cancellation_penalties",
#     "vacayhome_creation_times": "vacayhome_creation_times",
#     "listing_room_ids": "listing_room_ids",
#     "listing_room_numbers": "listing_room_numbers",
#     "listing_room_bed_ids": "listing_room_bed_ids",
#     "listing_room_bed_types": "listing_room_bed_types",
#     "listing_room_bed_quantities": "listing_room_bed_quantities",
#     "custom_field_ids": "custom_field_ids",
#     "custom_field_field_ids": "custom_field_field_ids",
#     "custom_field_values": "custom_field_values",
#     "import_time": "import_time",
#     "date_of_first_scrape": "date_of_first_scrape",
#     "date_of_last_update": "date_of_last_update",
#     "date_of_last_scrape": "date_of_last_scrape"
# },

#     "BREEZEAWAY_PROPERTIES_GW": {
#     "property_address1": "property_address1",
#     "property_address2": "property_address2",
#     "property_building": "property_building",
#     "property_id": "property_id",
#     "property_notes_access": "property_notes_access",
#     "property_notes_general": "property_notes_general",
#     "property_notes_guest_access": "property_notes_guest_access",
#     "property_photos_url": "property_photos_url",
#     "property_state": "property_state",
#     "property_status": "property_status"
# }


# }


# LOG_FILE = "sync_log.txt"

# logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")

# try:
#     CLIENT_DB_CONFIG = {
#     "host":os.getenv("client_host"),
#    "user":os.getenv("client_user"),
#    "password":os.getenv("client_password"),
#     "database":os.getenv("client_database"),
#     "port":int(os.getenv("client_port")),
  
#     } 
    
# except Exception as e:

#     raise f"Exception occured while connecting to client DB:{e} " 

# try:
#     YOUR_DB_CONFIG = {
#     "host":our_host,
#     "user":our_user,
#     "password":our_password,
#     "database":our_database,
#     "port":our_port,

#     }
   
# except Exception as e:
#     raise f"Exception occured while connecting to my DB:{e} "

# CLIENT_TABLE_1 = "GUESTY_LISTINGS " 
# CLIENT_TABLE_2 = "BREEZEAWAY_PROPERTIES_GW"
# YOUR_TABLE= "property_data_live"




# def fetch_client_data():
#     """Fetch data from both client tables"""
#     try:
#         client_conn = pymysql.connect(**CLIENT_DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
#         print("Connection made to client DB successfully!")
#         client_cursor = client_conn.cursor()

        
#         client_cursor.execute(f"SELECT {', '.join(COLUMN_MAPPING['GUESTY_LISTINGS'].keys())} FROM {CLIENT_TABLE_1}")
#         table1_data = client_cursor.fetchall()
#         print(f"Fetched {len(table1_data)} records from {CLIENT_TABLE_1}")

       
#         client_cursor.execute(f"SELECT {', '.join(COLUMN_MAPPING['BREEZEAWAY_PROPERTIES_GW'].keys())} FROM {CLIENT_TABLE_2}")
#         table2_data = client_cursor.fetchall()
#         print(f"Fetched {len(table2_data)} records from {CLIENT_TABLE_2}")

#         client_conn.close()
#         return table1_data, table2_data
#     except Exception as e:
#         logging.error(f"Error fetching client data: {e}")
#         return [], []

# def sync_data():
#     """Sync client data to your database using defined column mapping for each client table."""
#     table1_data, table2_data = fetch_client_data()  

#     if not table1_data and not table2_data:
#         logging.warning("No new data fetched from client tables.")
#         return

#     try:
#         your_conn = pymysql.connect(**YOUR_DB_CONFIG)
#         your_cursor = your_conn.cursor()
#         print("Connection made to our DB successfully!")
        
     
#         guesty_records = []
   
#         guesty_columns = list(COLUMN_MAPPING["GUESTY_LISTINGS"].values()) + ["summary","organisation_name","organisation_id"]
#         for row in table1_data:
       
#             mapped_row = {dest_col: row[src_col] for src_col, dest_col in COLUMN_MAPPING["GUESTY_LISTINGS"].items()}
#             mapped_row["summary"] = ", ".join([f"{col}: {val}" for col, val in mapped_row.items() if val])
#             mapped_row["organisation_name"]="Guesty"
#             mapped_row["organisation_id"]="Guesty_CL1"
#             guesty_records.append(mapped_row)

#         if guesty_records:
#             placeholders = ", ".join(["%s"] * len(guesty_columns))
#             sql = f"""
#             INSERT INTO {YOUR_TABLE} ({', '.join(guesty_columns)})
#             VALUES ({placeholders})
#             ON DUPLICATE KEY UPDATE
#             {', '.join([f'{col}=VALUES({col})' for col in guesty_columns])}
#             """
#             data_to_insert = [[row[col] for col in guesty_columns] for row in guesty_records]
#             your_cursor.executemany(sql, data_to_insert)
#             your_conn.commit()
#             print(f"Inserted/updated {len(guesty_records)} records from GUESTY_LISTINGS.")

       
#         breezeaway_records = []
       
#         breezeaway_columns = list(COLUMN_MAPPING["BREEZEAWAY_PROPERTIES_GW"].values()) + ["summary","organisation_name","organisation_id"]
#         for row in table2_data:
#             mapped_row = {dest_col: row[src_col] for src_col, dest_col in COLUMN_MAPPING["BREEZEAWAY_PROPERTIES_GW"].items()}
#             mapped_row["summary"] = ", ".join([f"{col}: {val}" for col, val in mapped_row.items() if val])
#             mapped_row["organisation_name"]="Breezeaway"
#             mapped_row["organisation_id"]="Breezeaway_CL1"
#             breezeaway_records.append(mapped_row)

#         if breezeaway_records:
#             placeholders = ", ".join(["%s"] * len(breezeaway_columns))
#             sql = f"""
#             INSERT INTO {YOUR_TABLE} ({', '.join(breezeaway_columns)})
#             VALUES ({placeholders})
#             ON DUPLICATE KEY UPDATE
#             {', '.join([f'{col}=VALUES({col})' for col in breezeaway_columns])}
#             """
#             data_to_insert = [[row[col] for col in breezeaway_columns] for row in breezeaway_records]
#             your_cursor.executemany(sql, data_to_insert)
#             your_conn.commit()
#             print(f"Inserted/updated {len(breezeaway_records)} records from BREEZEAWAY_PROPERTIES_GW.")
        
        
#         print("Sync successfull!")
#         logging.info("Sync successful!")
#         your_conn.close()
#     except Exception as e:
#         logging.error(f"Error syncing data: {e}")
#         print(f"Error syncing data: {e}")


# while True:
#     sync_data()
#     time.sleep(7200)


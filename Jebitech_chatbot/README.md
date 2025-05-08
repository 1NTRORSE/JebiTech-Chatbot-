![image](https://github.com/user-attachments/assets/724b50b9-5646-415b-8592-8ca0f63bdd08)
# Jebitech Chatbot

A sophisticated FastAPI-based chatbot application that leverages Google's Gemini AI for intelligent property-related conversations and database management.
So far chat API is designed for Guest User & Registered User.Guest User can ask any question about property by providing property name,ask ai to recommend property by entering 3 requirements i.e. Location(Texas,California,etc... states of US) ,Property type and no of bedroom,along with this if user explicitly write to connect with customer team then specified function will get called.If User asks for some property-reserved information like wifi password,master code,...(In system propmpt I've marked such fields as **Not Allow**
then they will be asked for reservation ID followed by question.If its correct means user is registered user thus user will be assisted with information ONLY with respect to property associated with reservation ID. 

## Features

- 🤖 **AI-Powered Chat**: Utilizes Google's Gemini AI for natural language processing specifically Gemini 2.0 flash.via google-generativeai library.
- 🏠 **Property Management**: Intelligent property recommendations and information retrieval
- 🔐 **User Management**: Guest and registered user support with session management
- 💾 **Database Integration**: Seamless database onboarding and synchronization
- 🔄 **Real-time Chat**: Asynchronous chat processing with session history
- 🛡️ **Security**: Secure session management and API key handling

## Tech Stack

- **Backend**: FastAPI
- **AI**: Google Gemini AI
- **Database**: MySQL
- **ORM**: SQLAlchemy
- **Authentication**: Session-based with UUID
- **API Documentation**: FastAPI's built-in Swagger UI
- **Function Calling**:In following situations Function call executes

  1.When User enters there reservation ID along with question(extract_user_id function)

  2.When user enters 3 requirement which is a. Property type,b.property location c.No. of bedroom(property_recommendation function)

  3.When user enters texts like ""Connect me with customer support team. (customer_assist function)

## Prerequisites

- Python 3.12+
- MySQL Server
- Google Gemini API Key
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Aryakumarjaiswal/Jebitech_chatbot.git
cd jebitech-chatbot
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with:
```
GEMINI_KEY= #your gemini key without ""
client_host=db-mysql-sfo3-49744-do-user-15692128-0.c.db.ondigitalocean.com
client_user=neovis_ai_user
client_password="t@ngrino1"
client_database=guesty_db
client_port=25060
our_host=localhost
our_user=root
our_password="#your_db_password"
our_database=chatbot_db #keep it as it ,else you would have to change in prop_recommend.py
our_port=3306
```



## Project Structure

```
Jebitech_chatbot/
├── Application/
│   ├── endpoints/
│   │   ├── app.py              # Main FastAPI application
│   │   ├── user_endpoints.py   # contains all APIs marked under Guest/Regisgtered User Tag
│   │   └── db_onboarding.py    # Consists Database on-boarding API code
|       └── prompt_supplier.py  #Consists System prompt for property name identification model (property_name_prompt),chat model (guest_prompt) &       
                                #property recommendation model prop_recommend.py (recommendation_prompt)
|       └── prop_recommend.py   # Based on user's requirement recommends property(default 3 property)
|       └── schemas.py          #contains pydentic schemas which is used in db-onboarding API
|       └── search_reference_id.py #Searchs for listing ID associated with reservation ID in 3 clients table BREEZEAWAY_RESERVATIONS,GUESTY_RESERVATIONS_FULL &                                    #GUESTY_RESERVATIONS.
│   ├── database                # Database models and configurations
│   └── sql_response.py         # contains function to format sql query,ececute sql command to fetch summary column database(property_data_live) and get                                         # property name.
├── requirements.txt
├── .env
└── README.md
```

## API Endpoints

### User Endpoints (`/user`)
- `POST /chat/guest`: Chat with the bot
- `GET /Get_session_chat/`: Retrieve chat history for a session ID
- `GET /Get_all_session_chat/`: Get all chat sessions summary
- `POST /create_user/`: Create a new user 
- `PUT /Change-to-Admin/`: Update user to admin role

### Database Endpoints
- `POST /db-onboarding`: Handle database synchronization and mapping

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn Application.endpoints.app:app
```

2. Access the API documentation at:
```
http://localhost:8000/docs
```

3.In swagger,at db-onboarding just copy paste below and execute.
```plaintext
{
  "our_db": {
    "host": "localhost",
    "user": "root",
    "password": "",#put your db password
    "database": "chatbot_db",
    "port": 3306
  },
  "client_db": {
    "host": "db-mysql-sfo3-49744-do-user-15692128-0.c.db.ondigitalocean.com",
    "user": "neovis_ai_user",
    "password":"t@ngrino1",
    "database": "guesty_db",
    "port": 25060
  },
  "our_table": "property_data_live",
  "mappings": {
    "GUESTY_LISTINGS": {
    "id": "property_id",
    "listing_id": "listing_id",
    "saas_auto_renew": "saas_auto_renew",
    "cleaning_fee_id": "cleaning_fee_id",
    "cleaning_fee_value_type": "cleaning_fee_value_type",
    "cleaning_fee_formula": "cleaning_fee_formula",
    "cleaning_fee_multiplier": "cleaning_fee_multiplier",
    "channel_commission_use_account_settings": "channel_commission_use_account_settings",
    "channel_commission_id": "channel_commission_id",
    "channel_commission_created_at": "channel_commission_created_at",
    "channel_commission_updated_at": "channel_commission_updated_at",
    "cleaning_status": "cleaning_status",
    "picture_caption": "picture_caption",
    "picture_thumbnail": "picture_thumbnail",
    "minimum_nights": "minimum_nights",
    "maximum_nights": "maximum_nights",
    "monthly_price_factor": "monthly_price_factor",
    "weekly_price_factor": "weekly_price_factor",
    "base_price": "base_price",
    "weekend_base_price": "weekend_base_price",
    "currency": "currency",
    "cleaning_fee": "cleaning_fee",
    "confirmed_before_checkin_delay_minutes": "confirmed_before_checkin_delay_minutes",
    "confirmed_day_of_checkin_delay_minutes": "confirmed_day_of_checkin_delay_minutes",
    "confirmed_day_of_checkout_delay_minutes": "confirmed_day_of_checkout_delay_minutes",
    "confirmed_during_stay_delay_minutes": "confirmed_during_stay_delay_minutes",
    "confirmed_after_checkout_delay_minutes": "confirmed_after_checkout_delay_minutes",
    "unconfirmed_first_message_delay_minutes": "unconfirmed_first_message_delay_minutes",
    "unconfirmed_subsequent_message_delay_minutes": "unconfirmed_subsequent_message_delay_minutes",
    "answeing_machine_is_active": "answeing_machine_is_active",
    "auto_reviews_status": "auto_reviews_status",
    "auto_payments_time_relation_names": "auto_payments_time_relation_names",
    "auto_payments_time_relation_units": "auto_payments_time_relation_units",
    "auto_payments_time_relation_amounts": "auto_payments_time_relation_amounts",
    "pms_cleaning_status": "pms_cleaning_status",
    "calendar_rules_default_availability": "calendar_rules_default_availability",
    "bookingcom_cut_off_hours_enabled": "bookingcom_cut_off_hours_enabled",
    "expedia_cut_off_hours_enabled": "expedia_cut_off_hours_enabled",
    "airbnb_cut_off_hours_enabled": "airbnb_cut_off_hours_enabled",
    "directbookings_cut_off_hours_enabled": "directbookings_cut_off_hours_enabled",
    "calendar_rules_default_hours": "calendar_rules_default_hours",
    "calendar_rules_allow_request_to_book": "calendar_rules_allow_request_to_book",
    "calendar_rules_advance_notice_updated_at": "calendar_rules_advance_notice_updated_at",
    "calendar_rules_advance_notice_updated_by": "calendar_rules_advance_notice_updated_by",
    "booking_window_default_days": "booking_window_default_days",
    "booking_window_updated_at": "booking_window_updated_at",
    "preparation_time_updated_at": "preparation_time_updated_at",
    "dynamic_checkin_updated_at": "dynamic_checkin_updated_at",
    "rental_periods_request_to_book": "rental_periods_request_to_book",
    "rental_periods_ids": "rental_periods_ids",
    "rental_periods_from": "rental_periods_from",
    "default_availability_updated_at": "default_availability_updated_at",
    "default_availability_updated_by": "default_availability_updated_by",
    "listing_type": "listing_type",
    "owners_list": "owners_list",
    "amenities_list": "amenities_list",
    "amenities_not_included_list": "amenities_not_included_list",
    "use_account_revenue_share": "use_account_revenue_share",
    "use_account_taxes": "use_account_taxes",
    "use_account_markups": "use_account_markups",
    "use_account_additional_fees": "use_account_additional_fees",
    "is_active": "is_active",
    "net_income_formula": "net_income_formula",
    "commission_formula": "commission_formula",
    "owner_revenue_formula": "owner_revenue_formula",
    "tax_ids": "tax_ids",
    "tax_types": "tax_types",
    "tax_amounts": "tax_amounts",
    "tax_names": "tax_names",
    "tax_units": "tax_units",
    "tax_quantifiers": "tax_quantifiers",
    "taxes_applied_to_all_fees": "taxes_applied_to_all_fees",
    "taxes_applied_on_fees": "taxes_applied_on_fees",
    "taxes_are_applied_by_default": "taxes_are_applied_by_default",
    "tax_conditional_overrides_view_types": "tax_conditional_overrides_view_types",
    "tax_conditional_overrides_max_nights": "tax_conditional_overrides_max_nights",
    "pre_bookings_list": "pre_bookings_list",
    "origin_id": "origin_id",
    "nick_name": "nick_name",
    "minimum_age": "minimum_age",
    "address_full": "address_full",
    "address_street": "address_street",
    "address_city": "address_city",
    "address_country": "address_country",
    "address_latitude": "address_latitude",
    "address_longitude": "address_longitude",
    "address_zip_code": "address_zip_code",
    "address_state": "address_state",
    "address_county": "address_county",
    "room_type": "room_type",
    "property_type": "property_type",
    "ota_room_type": "ota_room_type",
    "accommodates": "accommodates",
    "bathrooms": "bathrooms",
    "bedrooms": "bedrooms",
    "beds_count": "beds_count",
    "listing_status": "listing_status",
    "host_name": "host_name",
    "wifi_name": "wifi_name",
    "wifi_password": "wifi_password",
    "area_in_square_feet": "area_in_square_feet",
    "trash_collection_day": "trash_collection_day",
    "parking_instructions": "parking_instructions",
    "created_at": "created_at",
    "origin": "origin",
    "default_check_in_time": "default_check_in_time",
    "default_check_out_time": "default_check_out_time",
    "check_in_instructions": "check_in_instructions",
    "check_out_instructions": "check_out_instructions",
    "picture_ids": "picture_ids",
    "picture_captions": "picture_captions",
    "picture_originals": "picture_originals",
    "picture_heights": "picture_heights",
    "picture_widths": "picture_widths",
    "picture_thumbnails": "picture_thumbnails",
  
    "account_id": "account_id",
    "time_zone": "time_zone",
    "last_updated_at": "last_updated_at",
    "integration_ids": "integration_ids",
    "integration_platforms": "integration_platforms",
    "booking_com_initial_complex_listings": "booking_com_initial_complex_listings",
    "booking_com_publish_company_logos": "booking_com_publish_company_logos",
    "booking_com_is_published_company_logos": "booking_com_is_published_company_logos",
    "booking_com_publish_company_infos": "booking_com_publish_company_infos",
    "booking_com_is_published_company_infos": "booking_com_is_published_company_infos",
    "vacayhome_currencies": "vacayhome_currencies",
    "vacayhome_statuses": "vacayhome_statuses",
    "vacayhome_cancellation_policies": "vacayhome_cancellation_policies",
    "vacayhome_cancellation_penalties": "vacayhome_cancellation_penalties",
    "vacayhome_creation_times": "vacayhome_creation_times",
    "listing_room_ids": "listing_room_ids",
    "listing_room_numbers": "listing_room_numbers",
    "listing_room_bed_ids": "listing_room_bed_ids",
    "listing_room_bed_types": "listing_room_bed_types",
    "listing_room_bed_quantities": "listing_room_bed_quantities",
    "custom_field_ids": "custom_field_ids",
    "custom_field_field_ids": "custom_field_field_ids",
    "custom_field_values": "custom_field_values",
    "import_time": "import_time",
    "date_of_first_scrape": "date_of_first_scrape",
    "date_of_last_update": "date_of_last_update",
    "date_of_last_scrape": "date_of_last_scrape"
},

    "BREEZEAWAY_PROPERTIES_GW": {
    "property_address1": "property_address1",
    "property_address2": "property_address2",
    "property_building": "property_building",
    "property_id": "property_id",
    "property_notes_access": "property_notes_access",
    "property_notes_general": "property_notes_general",
    "property_notes_guest_access": "property_notes_guest_access",
    "property_photos_url": "property_photos_url",
    "property_state": "property_state",
    "property_status": "property_status"
}
  }
}


4.After successful execution of step 3,now user can start chat from "user/chat/guest" API.


```
## Security Considerations

- API keys are stored in environment variables
- Session management uses secure UUIDs
- CORS is configured for specific origins
- Database credentials are securely managed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the development team.

## Acknowledgments

- Google Gemini AI for the language model
- FastAPI team for the web framework
- SQLAlchemy for database ORM

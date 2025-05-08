from fastapi import APIRouter,HTTPException
import pymysql
from Application.endpoints.schemas import MappingPayload
from typing import Dict
import time
db_router = APIRouter()


@db_router.post("/db-onboarding")
async def get_credentials(payload: MappingPayload):
    """Enter user & client's DB Credentials, followed by mapper dictionary {"client_column":"our_column"}"""
    
    # Extract credentials
    s=time.time()
    our_db_config = payload.our_db
    client_db_config = payload.client_db
    column_mapping = payload.mappings
    destination_table = payload.our_table


    COLUMN_MAPPING = {}
    for k, ele in column_mapping.items():
        COLUMN_MAPPING[k] = ele
        print(f"Table Name: {k}")


    try:
        YOUR_DB_CONFIG = {
            "host": our_db_config.host,
            "user": our_db_config.user,
            "password": our_db_config.password,
            "database": our_db_config.database,
            "port": our_db_config.port,
        }
        your_conn = pymysql.connect(**YOUR_DB_CONFIG)
        your_cursor = your_conn.cursor()
        print("Connection made to our DB successfully!") 
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Exception occurred while connecting to our DB: {e}")
    

    try:
        CLIENT_DB_CONFIG = {
            "host": client_db_config.host,
            "user": client_db_config.user,
            "password": client_db_config.password,
            "database": client_db_config.database,
            "port": client_db_config.port,
        }
        client_conn = pymysql.connect(**CLIENT_DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
        client_cursor = client_conn.cursor()
        print("Connection made to client DB successfully!")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Exception occurred while connecting to client DB: {e}")
    
    # Fetch data
    l1 = []
    table_names = []
    for table_name, columns in column_mapping.items():
        try:
            client_cursor.execute(f"SELECT {', '.join(COLUMN_MAPPING[table_name].keys())} FROM {table_name}")
            table_data = client_cursor.fetchall()
            l1.append(table_data)
            table_names.append(table_name)
            print(f"Fetched {len(table_data)} records from {table_name}")
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Exception occurred while fetching data from {table_name}: {e}")

    
    try:
        for table_data, table_name in zip(l1, table_names):
            our_records = []
            our_columns = list(COLUMN_MAPPING[table_name].values()) + ["summary", "organisation_name", "organisation_id"]

            for row in table_data:
                mapped_row = {
                    dest_col: row[src_col]
                    for src_col, dest_col in COLUMN_MAPPING[table_name].items()
                }
                mapped_row["summary"] = ", ".join([f"{col}: {val}" for col, val in mapped_row.items() if val])
                mapped_row["organisation_name"] = table_name.split("_")[0].capitalize()
                mapped_row["organisation_id"] = f"{table_name}_CL1"
                our_records.append(mapped_row)

            if our_records:
                placeholders = ", ".join(["%s"] * len(our_columns))
                sql = f"""
                INSERT INTO {destination_table} ({', '.join(our_columns)})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE
                {', '.join([f'{col}=VALUES({col})' for col in our_columns])}
                """
                data_to_insert = [[row[col] for col in our_columns] for row in our_records]
                your_cursor.executemany(sql, data_to_insert)
                your_conn.commit()
                print(f"Inserted/updated {len(our_records)} records from {table_name}.")

        client_conn.close()
        your_conn.close()
        e=time.time()

    except Exception as e:       
        raise HTTPException(status_code=500, detail=f"Kindly ensure columns you've added in mapping are present in their respective table.{e-s} ")

    return {
        "message": f"Data fetched and synced successfully from {table_names},{e-s}",
    }

############################################################################################################
{
  "our_db": {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "chatbot_db",
    "port": 3306
  },
  "client_db": {
    "host": "",
    "user": "",
    "password":"",
    "database": "",
    "port":""
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

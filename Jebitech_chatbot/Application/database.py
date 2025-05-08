from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import bcrypt
from sqlalchemy import (
    Column, String, Integer, Enum, ForeignKey, Text, TIMESTAMP, func, CHAR, VARCHAR
)
import uuid

from dotenv import load_dotenv
import os


load_dotenv()


DB_PASSWORD= os.getenv("our_password") 
USERNAME=os.getenv("our_user")
HOST=os.getenv("our_host")
PORT=int(os.getenv("our_port"))
DB=os.getenv("our_database")

DATABASE_URL = f"mysql+pymysql://{USERNAME}:{DB_PASSWORD}@{HOST}:{PORT}/{DB}"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Session_Table(Base):
    __tablename__ = "Session_table"

    user_id = Column(Integer, primary_key=True, autoincrement=True, index=True)  # Auto-incrementing
    session_id = Column(CHAR(36), default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=False)
    user_type = Column(String(50), nullable=False, default="user")
    status = Column(Enum("active", "closed", "unassigned", "transferred", "assigned"), nullable=False, default="active")
    started_at = Column(TIMESTAMP, server_default=func.now(), nullable=True)
    ended_at = Column(TIMESTAMP, nullable=True)
    Duration = Column(Integer, nullable=True)

    chats = relationship("Chat", back_populates="session")
    chat_transfers = relationship("ChatTransfer", back_populates="session")


class Chat(Base):
    __tablename__ = "Chat_table"

    chat_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(CHAR(36), ForeignKey("Session_table.session_id"))
    sender = Column(Enum("user", "bot", "agent"), nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(TIMESTAMP, server_default=func.now(), nullable=True)
    status = Column(Enum("unread", "read"), default="read")
    session = relationship("Session_Table", back_populates="chats")


class AgentID(Base):
    __tablename__ = "agent_id_table"

    agent_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    agent_phone = Column(VARCHAR(15), nullable=False)
    agent_mail = Column(VARCHAR(36), nullable=False)
    agent_name = Column(CHAR(50), nullable=False)


class ChatTransfer(Base):
    __tablename__ = "chat_transfer_table"

    transfer_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(CHAR(36), ForeignKey("Session_table.session_id"))
    transferred_by = Column(String(50))
    transfer_reason = Column(Text, nullable=True)
    transferred_at = Column(TIMESTAMP, server_default=func.now(), nullable=True)
    agent_id = Column(CHAR(36), default=lambda: str(uuid.uuid4()), index=True)
    session = relationship("Session_Table", back_populates="chat_transfers")


class PropertyTable(Base):
    __tablename__="property_data_live"
    property_id =Column(CHAR(32),primary_key=True)
    property_status=Column(CHAR(24))
    property_address1=Column(Text) 
    property_address2=Column(Text)
    property_state=Column(CHAR(40))
    property_building=Column(CHAR(128))
    property_notes_access=Column(Text)
    property_notes_general=Column(Text)
    property_notes_guest_access=Column(Text)
    property_photos_url=Column(Text)
    listing_id=Column(CHAR(32))
    saas_auto_renew=Column(CHAR(8))
    cleaning_fee_id=Column(CHAR(32))
    cleaning_fee_value_type=Column(CHAR(16))
    cleaning_fee_formula=Column(CHAR(8))
    cleaning_fee_multiplier=Column(CHAR(24))
    channel_commission_use_account_settings=Column(CHAR(8))
    channel_commission_id=Column(CHAR(32))
    channel_commission_created_at=Column(CHAR(32))
    channel_commission_updated_at=Column(CHAR(32))
    cleaning_status=Column(CHAR(32))
    picture_caption=Column(Text)
    picture_thumbnail=Column(Text)
    minimum_nights=Column(CHAR(4))
    maximum_nights=Column(CHAR(8))
    monthly_price_factor =Column(CHAR(8))
    weekly_price_factor=Column(CHAR(8))
    base_price=Column(CHAR(8))
    weekend_base_price=Column(CHAR(8) )
    currency=Column(CHAR(8))
    cleaning_fee=Column(CHAR(8))
    confirmed_before_checkin_delay_minutes=Column(CHAR(8))
    confirmed_day_of_checkin_delay_minutes=Column(CHAR(8))
    confirmed_day_of_checkout_delay_minutes=Column(CHAR(8))
    confirmed_during_stay_delay_minutes=Column(CHAR(8) )
    confirmed_after_checkout_delay_minutes=Column(CHAR(8))
    unconfirmed_first_message_delay_minutes=Column(CHAR(8))
    unconfirmed_subsequent_message_delay_minutes=Column( CHAR(8))
    answeing_machine_is_active=Column(CHAR(8))
    auto_reviews_status=Column(CHAR(8))
    auto_payments_time_relation_names = Column(Text)
    auto_payments_time_relation_units = Column(Text)
    auto_payments_time_relation_amounts = Column(Text)
    pms_cleaning_status = Column(String(8))
    calendar_rules_default_availability = Column(String(16))
    bookingcom_cut_off_hours_enabled = Column(String(8))
    expedia_cut_off_hours_enabled = Column(String(8))
    airbnb_cut_off_hours_enabled = Column(String(8))
    directbookings_cut_off_hours_enabled = Column(String(8))
    calendar_rules_default_hours = Column(String(8))
    calendar_rules_allow_request_to_book = Column(String(8))
    calendar_rules_advance_notice_updated_at = Column(String(32))
    calendar_rules_advance_notice_updated_by = Column(String(32))
    booking_window_default_days = Column(String(8))
    booking_window_updated_at = Column(String(32))
    preparation_time_updated_at = Column(String(32))
    dynamic_checkin_updated_at = Column(String(32))
    rental_periods_request_to_book = Column(Text)
    rental_periods_ids = Column(Text)
    rental_periods_from = Column(Text)
    default_availability_updated_at = Column(String(32))
    default_availability_updated_by = Column(String(32))
    listing_type = Column(String(32))
    owners_list = Column(Text)
    amenities_list = Column(Text)
    amenities_not_included_list = Column(Text)
    use_account_revenue_share = Column(String(8))
    use_account_taxes = Column(Text)
    use_account_markups = Column(String(32))
    use_account_additional_fees = Column(String(8))
    is_active = Column(String(8))
    net_income_formula = Column(String(64))
    commission_formula = Column(String(64))
    owner_revenue_formula = Column(String(64))
    tax_ids = Column(Text)
    tax_types = Column(Text)
    tax_amounts = Column(Text)
    tax_names = Column(Text)
    tax_units = Column(Text)
    tax_quantifiers = Column(Text)
    taxes_applied_to_all_fees = Column(Text)
    taxes_applied_on_fees = Column(Text)
    taxes_are_applied_by_default = Column(Text)
    tax_conditional_overrides_view_types = Column(Text)
    tax_conditional_overrides_max_nights = Column(Text)
    tax___vs = Column(Text)
    pre_bookings_list = Column(Text)
    origin_id = Column(String(32))
    nick_name = Column(String(64))
    minimum_age = Column(String(8))
    address_full = Column(String(256))
    address_street = Column(String(256))
    address_city = Column(String(64))
    address_country = Column(String(64))
    address_latitude = Column(String(32))
    address_longitude = Column(String(32))
    address_zip_code = Column(String(12))
    address_state = Column(String(32))
    address_county = Column(String(40))
    room_type = Column(String(64))
    property_type = Column(String(64))
    ota_room_type = Column(String(64))
    accommodates = Column(String(4))
    bathrooms = Column(String(4))
    bedrooms = Column(String(4))
    beds_count = Column(String(4))
    listing_status = Column(String(8))
    host_name = Column(String(80))
    wifi_name = Column(String(64))
    wifi_password = Column(String(64))
    area_in_square_feet = Column(String(8))
    trash_collection_day = Column(Text)
    parking_instructions = Column(Text)
    created_at = Column(String(32))
    origin = Column(String(32))
    default_check_in_time = Column(String(16))
    default_check_out_time = Column(String(16))
    check_in_instructions = Column(Text)
    check_out_instructions = Column(Text)
    picture_ids = Column(Text)
    picture_captions = Column(Text)
    picture_originals = Column(Text)
    picture_heights = Column(Text)
    picture_widths = Column(Text)
    picture_thumbnails = Column(Text)
    account_id = Column(String(32))
    time_zone = Column(String(64))
    last_updated_at = Column(String(32))
    integration_ids = Column(Text)
    integration_platforms = Column(Text)
    booking_com_initial_complex_listings = Column(Text)
    booking_com_publish_company_logos = Column(Text)
    booking_com_is_published_company_logos = Column(Text)
    booking_com_publish_company_infos = Column(Text)
    booking_com_is_published_company_infos = Column(Text) 
    vacayhome_currencies=Column(Text )
    vacayhome_statuses=Column(Text )
    vacayhome_cancellation_policies=Column(Text )
    vacayhome_cancellation_penalties =Column(Text )
    vacayhome_creation_times =Column(Text )
    listing_room_ids=Column(Text )
    listing_room_numbers =Column(Text )
    listing_room_bed_ids =Column(Text )
    listing_room_bed_types=Column(Text )
    listing_room_bed_quantities=Column(Text) 
    custom_field_ids =Column(Text)
    custom_field_field_ids=Column(Text )
    custom_field_values=Column(Text )
    import_time =Column(CHAR(32) )
    date_of_first_scrape=Column(TIMESTAMP) 
    date_of_last_update =Column(TIMESTAMP) 
    date_of_last_scrape =Column(TIMESTAMP)
    organisation_id=Column(CHAR(32))
    organisation_name =Column(String(64) )
    summary=Column(Text)


print("Tables to be created:")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

##################################### BACKUP TABLE DEFINATION COMMAND #########################################################
# create table property_data_live
# (
# property_id varchar(32) primary key, 
# property_status varchar(24) ,
# property_address1 varchar(512) ,
# property_address2 varchar(512) ,
# property_state varchar(40) ,
# property_building varchar(128) ,
# property_notes_access text ,
# property_notes_general text ,
# property_notes_guest_access text ,
# property_photos_url text ,
# listing_id varchar(32) ,
# saas_auto_renew varchar(8) ,
# cleaning_fee_id varchar(32) ,
# cleaning_fee_value_type varchar(16) ,
# cleaning_fee_formula varchar(8) ,
# cleaning_fee_multiplier varchar(24) ,
# channel_commission_use_account_settings varchar(8) ,
# channel_commission_id varchar(32) ,
# channel_commission_created_at varchar(32) ,
# channel_commission_updated_at varchar(32) ,
# cleaning_status varchar(32) ,
# picture_caption varchar(256) ,
# picture_thumbnail varchar(512), 
# minimum_nights varchar(4) ,
# maximum_nights varchar(8) ,
# monthly_price_factor varchar(8) ,
# weekly_price_factor varchar(8) ,
# base_price varchar(8) ,
# weekend_base_price varchar(8) ,
# currency varchar(8) ,
# cleaning_fee varchar(8) ,
# confirmed_before_checkin_delay_minutes varchar(8) ,
# confirmed_day_of_checkin_delay_minutes varchar(8) ,
# confirmed_day_of_checkout_delay_minutes varchar(8) ,
# confirmed_during_stay_delay_minutes varchar(8) ,
# confirmed_after_checkout_delay_minutes varchar(8) ,
# unconfirmed_first_message_delay_minutes varchar(8) ,
# unconfirmed_subsequent_message_delay_minutes varchar(8) ,
# answeing_machine_is_active varchar(8) ,
# auto_reviews_status varchar(8) ,
# auto_payments_time_relation_names text ,
# auto_payments_time_relation_units text ,
# auto_payments_time_relation_amounts text, 
# pms_cleaning_status varchar(8) ,
# calendar_rules_default_availability varchar(16) ,
# bookingcom_cut_off_hours_enabled varchar(8) ,
# expedia_cut_off_hours_enabled varchar(8) ,
# airbnb_cut_off_hours_enabled varchar(8) ,
# directbookings_cut_off_hours_enabled varchar(8) ,
# calendar_rules_default_hours varchar(8) ,
# calendar_rules_allow_request_to_book varchar(8) ,
# calendar_rules_advance_notice_updated_at varchar(32) ,
# calendar_rules_advance_notice_updated_by varchar(32) ,
# booking_window_default_days varchar(8) ,
# booking_window_updated_at varchar(32) ,
# preparation_time_updated_at varchar(32) ,
# dynamic_checkin_updated_at varchar(32) ,
# rental_periods_request_to_book text ,
# rental_periods_ids text ,
# rental_periods_from text ,
# default_availability_updated_at varchar(32) ,
# default_availability_updated_by varchar(32) ,
# listing_type varchar(32) ,
# owners_list text ,
# amenities_list text ,
# amenities_not_included_list text ,
# use_account_revenue_share varchar(8) ,
# use_account_taxes text ,
# use_account_markups varchar(32) ,
# use_account_additional_fees varchar(8) ,
# is_active varchar(8) ,
# net_income_formula varchar(64) ,
# commission_formula varchar(64) ,
# owner_revenue_formula varchar(64) ,
# tax_ids text ,
# tax_types text ,
# tax_amounts text ,
# tax_names text ,
# tax_units text ,
# tax_quantifiers text ,
# taxes_applied_to_all_fees text ,
# taxes_applied_on_fees text ,
# taxes_are_applied_by_default text ,
# tax_conditional_overrides_view_types text ,
# tax_conditional_overrides_max_nights text ,
# tax___vs text ,
# pre_bookings_list text ,
# origin_id varchar(32) ,
# nick_name varchar(64) ,
# minimum_age varchar(8) ,
# address_full varchar(256) ,
# address_street varchar(256) ,
# address_city varchar(64) ,
# address_country varchar(64) ,
# address_latitude varchar(32) ,
# address_longitude varchar(32) ,
# address_zip_code varchar(12) ,
# address_state varchar(32) ,
# address_county varchar(40) ,
# room_type varchar(64) ,
# property_type varchar(64) ,
# ota_room_type varchar(64) ,
# accommodates varchar(4) ,
# bathrooms varchar(4) ,
# bedrooms varchar(4) ,
# beds_count varchar(4) ,
# listing_status varchar(8) ,
# host_name varchar(80) ,
# wifi_name varchar(64) ,
# wifi_password varchar(64) ,
# area_in_square_feet varchar(8) ,
# trash_collection_day text ,
# parking_instructions text ,
# created_at varchar(32) ,
# origin varchar(32) ,
# default_check_in_time varchar(16) ,
# default_check_out_time varchar(16) ,
# check_in_instructions text ,
# check_out_instructions text ,
# picture_ids text ,
# picture_captions text ,
# picture_originals text ,
# picture_heights text ,
# picture_widths text ,
# picture_thumbnails text ,
# account_id varchar(32) ,
# time_zone varchar(64) ,
# last_updated_at varchar(32) ,
# integration_ids text ,
# integration_platforms text ,
# booking_com_initial_complex_listings text ,
# booking_com_publish_company_logos text ,
# booking_com_is_published_company_logos text ,
# booking_com_publish_company_infos text ,
# booking_com_is_published_company_infos text ,
# vacayhome_currencies text ,
# vacayhome_statuses text ,
# vacayhome_cancellation_policies text ,
# vacayhome_cancellation_penalties text ,
# vacayhome_creation_times text ,
# listing_room_ids text ,
# listing_room_numbers text ,
# listing_room_bed_ids text ,
# listing_room_bed_types text ,
# listing_room_bed_quantities text ,
# custom_field_ids text ,
# custom_field_field_ids text ,
# custom_field_values text ,
# import_time varchar(32) ,
# date_of_first_scrape timestamp ,
# date_of_last_update timestamp ,
# date_of_last_scrape timestamp ,
# organisation_id varchar(32),
# organisation_name varchar(64) ,
# summary text);

"""SQLAlchemy models for all KrishiLink AI entities."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=True)
    phone = Column(String(32), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(String(32), nullable=False, default="farmer")
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    farmer_profile = relationship("FarmerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    buyer_profile = relationship("BuyerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    farms = relationship("Farm", back_populates="farmer", cascade="all, delete-orphan")
    produce_listings = relationship("ProduceListing", back_populates="farmer", cascade="all, delete-orphan")


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(32), nullable=True)
    village = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True, default="Odisha")
    block_tehsil = Column(String(255), nullable=True)
    farm_name = Column(String(255), nullable=True)
    farm_size = Column(Float, nullable=True, default=0.0)
    farm_unit = Column(String(32), nullable=True, default="acres")
    primary_crops = Column(Text, nullable=True)
    preferred_language = Column(String(16), nullable=True, default="en")
    trust_score = Column(Float, default=88.0, nullable=False)
    verified = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="farmer_profile")


class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    business_name = Column(String(255), nullable=True)
    buyer_type = Column(String(64), nullable=True, default="Processor")
    location = Column(String(255), nullable=True)
    phone = Column(String(32), nullable=True)
    trust_score = Column(Float, default=92.0, nullable=False)
    payment_reliability = Column(Float, default=95.0, nullable=False)
    pickup_available = Column(Boolean, default=True, nullable=False)
    verified = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="buyer_profile")


class Farm(Base):
    __tablename__ = "farms"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    farmer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    size_acres = Column(Float, nullable=True, default=1.0)
    soil_type = Column(String(64), nullable=True)
    irrigation_type = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    farmer = relationship("User", back_populates="farms")


class ProduceListing(Base):
    __tablename__ = "produce_listings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    farmer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    farm_id = Column(String(36), nullable=True)
    crop = Column(String(128), nullable=False)
    variety = Column(String(128), nullable=True, default="Standard")
    quantity = Column(Float, nullable=False)
    unit = Column(String(32), nullable=False, default="kg")
    harvest_date = Column(String(32), nullable=True)
    expected_price = Column(Float, nullable=False)
    min_price = Column(Float, nullable=True)
    status = Column(String(32), nullable=False, default="active")
    quality_grade = Column(String(32), nullable=True, default="Grade A")
    ai_quality_score = Column(Float, nullable=True, default=90.0)
    freshness_score = Column(Float, nullable=True, default=95.0)
    uniformity_score = Column(Float, nullable=True, default=90.0)
    damage_percent = Column(Float, nullable=True, default=3.0)
    ai_price_min = Column(Float, nullable=True, default=30.0)
    ai_price_max = Column(Float, nullable=True, default=34.0)
    image_url = Column(String(512), nullable=True, default="assets/images/tomato.jpg")
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    farmer = relationship("User", back_populates="produce_listings")
    images = relationship("ProduceImage", back_populates="listing", cascade="all, delete-orphan")


class ProduceImage(Base):
    __tablename__ = "produce_images"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    listing_id = Column(String(36), ForeignKey("produce_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(String(512), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    listing = relationship("ProduceListing", back_populates="images")


class BuyerDemand(Base):
    __tablename__ = "buyer_demands"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    buyer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop = Column(String(128), nullable=False)
    variety = Column(String(128), nullable=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String(32), nullable=False, default="kg")
    target_price = Column(Float, nullable=False)
    location = Column(String(255), nullable=True)
    delivery_deadline = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default="open")
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class Offer(Base):
    __tablename__ = "offers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    listing_id = Column(String(36), ForeignKey("produce_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    buyer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    demand_id = Column(String(36), nullable=True)
    offered_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(32), nullable=False, default="kg")
    counter_price = Column(Float, nullable=True)
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    messages = relationship("NegotiationMessage", back_populates="offer", cascade="all, delete-orphan")


class NegotiationMessage(Base):
    __tablename__ = "negotiation_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    offer_id = Column(String(36), ForeignKey("offers.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    proposed_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    offer = relationship("Offer", back_populates="messages")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    listing_id = Column(String(36), nullable=True)
    buyer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    farmer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String(32), nullable=False, default="kg")
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(32), nullable=False, default="confirmed")
    vehicle_no = Column(String(64), nullable=True, default="OD-02-KL-9081")
    driver_name = Column(String(128), nullable=True, default="Santosh Das")
    driver_phone = Column(String(32), nullable=True, default="+91 94371 90234")
    pickup_eta = Column(String(64), nullable=True, default="Today 11:30 AM")
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    order = relationship("Order", back_populates="status_history")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    carrier_name = Column(String(128), default="KrishiLink Logistics Network", nullable=False)
    driver_name = Column(String(128), default="Santosh Das", nullable=False)
    driver_phone = Column(String(32), default="+91 94371 90234", nullable=False)
    vehicle_number = Column(String(64), default="OD-02-KL-9081", nullable=False)
    origin = Column(String(255), default="Khordha Farm Field, Odisha", nullable=False)
    destination = Column(String(255), default="ABC Foods Processing Center, Bhubaneswar", nullable=False)
    current_location = Column(String(255), default="NH-16 En Route (14km away)", nullable=False)
    status = Column(String(32), default="in_transit", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    updates = relationship("ShipmentUpdate", back_populates="shipment", cascade="all, delete-orphan")


class ShipmentUpdate(Base):
    __tablename__ = "shipment_updates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    shipment_id = Column(String(36), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    location = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    shipment = relationship("Shipment", back_populates="updates")


class QualityAssessment(Base):
    __tablename__ = "quality_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    listing_id = Column(String(36), nullable=True, index=True)
    inspector_id = Column(String(36), nullable=True)
    score = Column(Float, default=92.0, nullable=False)
    grade = Column(String(16), default="A", nullable=False)
    moisture = Column(Float, default=88.0, nullable=False)
    purity = Column(Float, default=98.0, nullable=False)
    defects = Column(Float, default=2.0, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    raised_by = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, nullable=False)
    evidence_url = Column(String(512), nullable=True)
    status = Column(String(32), default="open", nullable=False)
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class EscrowAccount(Base):
    __tablename__ = "escrow_accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    status = Column(String(32), default="locked", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), nullable=True)
    farmer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    gross_amount = Column(Float, nullable=False)
    logistics_fee = Column(Float, default=0.0, nullable=False)
    platform_fee = Column(Float, default=0.0, nullable=False)
    net_payout = Column(Float, nullable=False)
    bank_ref = Column(String(128), nullable=False)
    status = Column(String(32), default="settled", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reviewee_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), nullable=True)
    rating = Column(Integer, default=5, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(64), default="info", nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class PricePrediction(Base):
    __tablename__ = "price_predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    requester_id = Column(String(36), nullable=False)
    crop = Column(String(128), nullable=False)
    location = Column(String(255), nullable=False)
    predicted_price = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    requester_id = Column(String(36), nullable=False)
    crop = Column(String(128), nullable=False)
    location = Column(String(255), nullable=False)
    demand_level = Column(String(64), nullable=True)
    confidence = Column(Float, nullable=True)
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class OtpCode(Base):
    __tablename__ = "otp_codes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    identifier = Column(String(255), nullable=False, index=True)  # email or phone
    code = Column(String(8), nullable=False)
    purpose = Column(String(32), default="login", nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

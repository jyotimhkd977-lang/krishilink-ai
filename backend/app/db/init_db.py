"""Database initialization and prototype seeding."""

import logging
from datetime import datetime, timezone

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.entities import (
    BuyerDemand,
    BuyerProfile,
    EscrowAccount,
    Farm,
    FarmerProfile,
    Notification,
    Order,
    OrderStatusHistory,
    ProduceListing,
    Settlement,
    Shipment,
    ShipmentUpdate,
    User,
)

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Create all SQLite tables and seed demo prototype data."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing_user = db.query(User).first()
        if existing_user:
            return

        logger.info("Seeding initial prototype data into SQLite database...")
        now = datetime.now(timezone.utc)

        # 1. Farmer Ramesh Kumar
        farmer_id = "farmer-ramesh-001"
        farmer_user = User(
            id=farmer_id,
            email="ramesh@krishilink.ai",
            phone="+919876543210",
            password_hash=hash_password("password123"),
            role="farmer",
            is_active=True,
            email_verified=True,
            created_at=now,
        )
        db.add(farmer_user)

        farmer_profile = FarmerProfile(
            user_id=farmer_id,
            full_name="Ramesh Kumar",
            phone="+919876543210",
            village="Jatani Gram",
            district="Khordha",
            state="Odisha",
            block_tehsil="Jatani",
            farm_name="Ramesh Organic Fields",
            farm_size=4.5,
            farm_unit="acres",
            primary_crops="Tomato, Potato, Paddy",
            preferred_language="en",
            trust_score=94.5,
            verified=True,
            created_at=now,
        )
        db.add(farmer_profile)

        # 2. Buyer Priya Sharma (ABC Foods)
        buyer_id = "buyer-priya-001"
        buyer_user = User(
            id=buyer_id,
            email="priya@abcfoods.in",
            phone="+919876543211",
            password_hash=hash_password("password123"),
            role="buyer",
            is_active=True,
            email_verified=True,
            created_at=now,
        )
        db.add(buyer_user)

        buyer_profile = BuyerProfile(
            user_id=buyer_id,
            business_name="ABC Foods India Ltd.",
            buyer_type="Processor",
            location="Bhubaneswar Industrial Estate, Odisha",
            phone="+919876543211",
            trust_score=96.0,
            payment_reliability=98.0,
            pickup_available=True,
            verified=True,
            created_at=now,
        )
        db.add(buyer_profile)

        # 3. Farmer Farm
        farm = Farm(
            id="farm-khordha-001",
            farmer_id=farmer_id,
            name="Khordha Main Field",
            location="Jatani, Khordha, Odisha",
            size_acres=4.5,
            soil_type="Alluvial Loam",
            irrigation_type="Drip & Borewell",
            created_at=now,
        )
        db.add(farm)

        # 4. Produce Listings
        listings = [
            ProduceListing(
                id="prod-1",
                farmer_id=farmer_id,
                farm_id="farm-khordha-001",
                crop="Hybrid Red Tomato",
                variety="Abhinav F1",
                quantity=500.0,
                unit="kg",
                harvest_date="2026-09-08",
                expected_price=32.0,
                min_price=30.0,
                status="active",
                quality_grade="Grade A",
                ai_quality_score=92.0,
                freshness_score=95.0,
                uniformity_score=89.0,
                damage_percent=4.0,
                ai_price_min=31.0,
                ai_price_max=33.0,
                image_url="assets/images/tomato.jpg",
                created_at=now,
            ),
            ProduceListing(
                id="prod-2",
                farmer_id=farmer_id,
                farm_id="farm-khordha-001",
                crop="Organic Potato",
                variety="Kufri Jyoti",
                quantity=1200.0,
                unit="kg",
                harvest_date="2026-09-10",
                expected_price=24.0,
                min_price=22.0,
                status="active",
                quality_grade="Grade A",
                ai_quality_score=89.0,
                freshness_score=92.0,
                uniformity_score=91.0,
                damage_percent=3.0,
                ai_price_min=23.0,
                ai_price_max=25.0,
                image_url="assets/images/potato.jpg",
                created_at=now,
            ),
            ProduceListing(
                id="prod-3",
                farmer_id=farmer_id,
                farm_id="farm-khordha-001",
                crop="Golden Sona Masoori Paddy",
                variety="BPT 5204",
                quantity=2500.0,
                unit="kg",
                harvest_date="2026-09-15",
                expected_price=20.0,
                min_price=18.0,
                status="active",
                quality_grade="Grade B+",
                ai_quality_score=84.0,
                freshness_score=88.0,
                uniformity_score=85.0,
                damage_percent=6.0,
                ai_price_min=19.0,
                ai_price_max=21.0,
                image_url="assets/images/wheat.jpg",
                created_at=now,
            ),
            ProduceListing(
                id="prod-4",
                farmer_id=farmer_id,
                farm_id="farm-khordha-001",
                crop="Fresh Green Chilli",
                variety="G-4 Hot",
                quantity=150.0,
                unit="kg",
                harvest_date="2026-09-07",
                expected_price=48.0,
                min_price=44.0,
                status="active",
                quality_grade="Grade A",
                ai_quality_score=94.0,
                freshness_score=96.0,
                uniformity_score=93.0,
                damage_percent=2.0,
                ai_price_min=46.0,
                ai_price_max=50.0,
                image_url="assets/images/onion.jpg",
                created_at=now,
            ),
        ]
        for listing in listings:
            db.add(listing)

        # 5. Buyer Demands
        demands = [
            BuyerDemand(
                id="demand-1",
                buyer_id=buyer_id,
                crop="Hybrid Red Tomato",
                variety="Processing Grade",
                quantity=500.0,
                unit="kg",
                target_price=32.0,
                location="Bhubaneswar Industrial Estate",
                delivery_deadline="Tomorrow 12:00 PM",
                status="open",
                created_at=now,
            ),
            BuyerDemand(
                id="demand-2",
                buyer_id=buyer_id,
                crop="Organic Potato",
                variety="Table Potato",
                quantity=1000.0,
                unit="kg",
                target_price=24.0,
                location="Cuttack Hub",
                delivery_deadline="3 days",
                status="open",
                created_at=now,
            ),
        ]
        for demand in demands:
            db.add(demand)

        # 6. Sample Confirmed Order
        order_1 = Order(
            id="KL90812",
            listing_id="prod-1",
            buyer_id=buyer_id,
            farmer_id=farmer_id,
            quantity=500.0,
            unit="kg",
            unit_price=32.0,
            total_amount=16000.0,
            status="confirmed",
            vehicle_no="OD-02-KL-9081",
            driver_name="Santosh Das",
            driver_phone="+91 94371 90234",
            pickup_eta="Today 11:30 AM",
            created_at=now,
        )
        db.add(order_1)

        history = OrderStatusHistory(
            id="hist-1",
            order_id="KL90812",
            status="confirmed",
            note="AI Match accepted. Smart consolidation vehicle assigned.",
            created_at=now,
        )
        db.add(history)

        # 7. Logistics Shipment
        shipment = Shipment(
            id="ship-1",
            order_id="KL90812",
            carrier_name="KrishiLink Smart Consolidation Network",
            driver_name="Santosh Das",
            driver_phone="+91 94371 90234",
            vehicle_number="OD-02-KL-9081",
            origin="Khordha Farm Field, Odisha",
            destination="ABC Foods Facility, Bhubaneswar",
            current_location="NH-16 En Route (14km away)",
            status="in_transit",
            created_at=now,
        )
        db.add(shipment)

        update = ShipmentUpdate(
            id="upd-1",
            shipment_id="ship-1",
            location="Jatani Toll Plaza",
            status="in_transit",
            notes="Consolidated pickup with nearby farms. On schedule.",
            created_at=now,
        )
        db.add(update)

        # 8. Escrow Account
        escrow = EscrowAccount(
            id="esc-1",
            order_id="KL90812",
            amount=16000.0,
            status="locked",
            created_at=now,
        )
        db.add(escrow)

        # 9. Settlement Statement
        settlement = Settlement(
            id="settle-1",
            order_id="KL90812",
            farmer_id=farmer_id,
            gross_amount=47850.0,
            logistics_fee=0.0,
            platform_fee=0.0,
            net_payout=47850.0,
            bank_ref="DBT-KL-2026-904128",
            status="settled",
            created_at=now,
        )
        db.add(settlement)

        # 10. Notifications
        notifications = [
            Notification(
                id="notif-1",
                user_id=farmer_id,
                title="AI Price Intelligence Alert",
                message="Tomato mandi price in Khordha jumped by +8.2% to ₹30.50/kg today.",
                type="price_alert",
                is_read=False,
                created_at=now,
            ),
            Notification(
                id="notif-2",
                user_id=farmer_id,
                title="Instant Buyer Match",
                message="ABC Foods India Ltd. submitted an offer of ₹32/kg for your 500 kg Tomato.",
                type="match",
                is_read=False,
                created_at=now,
            ),
            Notification(
                id="notif-3",
                user_id=farmer_id,
                title="Smart Logistics Update",
                message="Consolidation truck OD-02-KL-9081 is scheduled to arrive at your farm at 11:30 AM.",
                type="logistics",
                is_read=False,
                created_at=now,
            ),
            Notification(
                id="notif-4",
                user_id=farmer_id,
                title="Escrow Payment Locked",
                message="₹16,000 for Order #KL90812 is safely held in KrishiEscrow. Instant payout upon delivery.",
                type="payment",
                is_read=True,
                created_at=now,
            ),
        ]
        for notif in notifications:
            db.add(notif)

        db.commit()
        logger.info("SQLite prototype data seeded successfully.")
    except Exception as exc:
        db.rollback()
        logger.error(f"Error seeding database: {exc}")
    finally:
        db.close()

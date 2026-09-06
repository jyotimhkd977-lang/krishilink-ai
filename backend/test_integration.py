"""Automated integration verification script for SQLite & SMTP services."""

import sys
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.entities import OtpCode, User, ProduceListing, Order
from app.schemas.auth import Role
from app.services.auth import AuthService
from app.services.produce import ProduceService
from app.services.orders import OrderService
from app.services.notifications import NotificationService

def main():
    print("--- 1. Testing Database Initializer ---")
    init_db()
    db = SessionLocal()
    users_count = db.query(User).count()
    listings_count = db.query(ProduceListing).count()
    orders_count = db.query(Order).count()
    print(f"Users in SQLite: {users_count}")
    print(f"Listings in SQLite: {listings_count}")
    print(f"Orders in SQLite: {orders_count}")
    db.close()
    assert users_count >= 2, "Expected at least 2 seeded users"

    print("\n--- 2. Testing Password Login ---")
    auth = AuthService()
    login_res = auth.login("ramesh@krishilink.ai", "password123", "127.0.0.1")
    token = login_res["access_token"]
    print("Logged in as Ramesh Kumar successfully!")
    print(f"JWT Token: {token[:30]}...")

    print("\n--- 3. Testing SMTP Email OTP Flow ---")
    test_email = "newfarmer@agri.in"
    auth.send_email_otp(test_email, Role.farmer)

    db = SessionLocal()
    otp_record = db.query(OtpCode).filter(OtpCode.identifier == test_email, OtpCode.is_used == False).first()
    print(f"Retrieved OTP for {test_email}: {otp_record.code if otp_record else 'None'}")
    assert otp_record is not None, "OTP record must exist in SQLite"
    otp_code = otp_record.code
    db.close()

    verify_res = auth.verify_email_otp(test_email, otp_code, Role.farmer)
    print("Email OTP verified successfully!")
    print(f"Verified User ID: {verify_res['user'].id}, Email: {verify_res['user'].email}")

    print("\n--- 4. Testing Produce Service ---")
    produce_srv = ProduceService()
    listings = produce_srv.list_listings(token, "farmer-ramesh-001", "farmer")
    print(f"Found {len(listings)} listings for Ramesh Kumar:")
    for l in listings:
        print(f"  - {l['crop']} ({l['quantity']} {l['unit']}) @ ₹{l['expected_price']}/kg [{l['status']}]")

    print("\n--- 5. Testing Orders Service ---")
    order_srv = OrderService()
    orders = order_srv.list_orders(token, "farmer-ramesh-001", "farmer")
    print(f"Found {len(orders)} orders for Ramesh Kumar:")
    for o in orders:
        print(f"  - Order #{o['id']}: Status={o['status']}, Total=₹{o['total_amount']}")

    print("\n--- 6. Testing Notifications Service ---")
    notif_srv = NotificationService()
    notifs = notif_srv.list_notifications(token, unread_only=False, limit=5)
    print(f"Found {len(notifs)} notifications:")
    for n in notifs:
        print(f"  - [{n['type']}] {n['title']}")

    print("\nALL INTEGRATION TESTS PASSED SUCCESSFULLY! 🚀")

if __name__ == "__main__":
    main()

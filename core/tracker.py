"""
Real-Time Order Lifecycle & Self-Service Tracker
Project Udyam Digital - Accel Telecom
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class OrderTrackerEngine:
    def __init__(self):
        # In-memory mock store for demo orders
        self.orders = {}
        self._initialize_mock_orders()

    def _initialize_mock_orders(self):
        self.orders = {
            "ORD-UDYAM-8021": {
                "order_id": "ORD-UDYAM-8021",
                "customer_name": "Dr. Sneha Rao",
                "business_name": "Balaji Dental Care LLP",
                "city": "Kochi",
                "products": ["Biz Fibre 300", "Business Postpaid 299 (x2)", "Cloud Backup 1 TB"],
                "monthly_value": 2597.0,
                "created_date": "2026-07-10",
                "expected_activation_date": "2026-07-15",
                "current_step": 5,  # 1 to 7
                "assigned_engineer": {
                    "name": "Karthik Nair",
                    "phone": "+91 98401 •••••",
                    "badge_id": "AIRTEL-FE-492",
                    "slot": "2026-07-15, 02:00 PM - 04:00 PM"
                },
                "status_message": "Field engineer is en-route for optical fibre termination and router configuration.",
                "timeline": [
                    {"step": 1, "title": "Order Placed & Quote Accepted", "date": "2026-07-10 11:30 AM", "done": True},
                    {"step": 2, "title": "Smart KYC Verified (GSTIN & Udyam)", "date": "2026-07-10 11:34 AM", "done": True},
                    {"step": 3, "title": "Automated Port Feasibility Clearance", "date": "2026-07-11 09:15 AM", "done": True},
                    {"step": 4, "title": "Wi-Fi 6 CPE & SIMs Dispatched", "date": "2026-07-12 04:00 PM", "done": True},
                    {"step": 5, "title": "Field Engineer On-Site Installation", "date": "2026-07-15 02:00 PM", "done": False, "in_progress": True},
                    {"step": 6, "title": "End-to-End Speed & SLA Testing", "date": "Pending", "done": False},
                    {"step": 7, "title": "Services Live & Unified Billing Started", "date": "Pending", "done": False}
                ]
            },
            "ORD-UDYAM-9412": {
                "order_id": "ORD-UDYAM-9412",
                "customer_name": "Rajesh Gupta",
                "business_name": "Saffron Kirana & Retail",
                "city": "Jaipur",
                "products": ["Biz 5G AirFiber 100", "Cloud POS & Billing"],
                "monthly_value": 1498.0,
                "created_date": "2026-07-14",
                "expected_activation_date": "2026-07-16",
                "current_step": 3,
                "assigned_engineer": {
                    "name": "Suresh Meena",
                    "phone": "+91 94140 •••••",
                    "badge_id": "AIRTEL-FE-118",
                    "slot": "2026-07-16, 10:00 AM - 12:00 PM"
                },
                "status_message": "Self-install kit dispatched; engineer booked for plug-and-play outdoor antenna alignment.",
                "timeline": [
                    {"step": 1, "title": "Order Placed & Quote Accepted", "date": "2026-07-14 03:20 PM", "done": True},
                    {"step": 2, "title": "Smart KYC Verified (Aadhaar & Electricity Bill)", "date": "2026-07-14 03:23 PM", "done": True},
                    {"step": 3, "title": "5G AirFiber Outdoor Unit Dispatched", "date": "2026-07-15 10:00 AM", "done": True, "in_progress": True},
                    {"step": 4, "title": "Engineer Signal Optimization & Install", "date": "2026-07-16 10:00 AM", "done": False},
                    {"step": 5, "title": "UPI & POS Latency Certification", "date": "Pending", "done": False},
                    {"step": 6, "title": "Activated & Live", "date": "Pending", "done": False}
                ]
            }
        }

    def get_order(self, order_id: str) -> Optional[Dict]:
        return self.orders.get(order_id.strip().upper())

    def create_new_order(
        self,
        customer_name: str,
        business_name: str,
        city: str,
        product_names: List[str],
        monthly_total: float,
        install_days: int = 5
    ) -> Dict:
        """Dynamically creates a new tracked order when checkout completes."""
        new_id = f"ORD-UDYAM-{len(self.orders) + 9501}"
        today = datetime.now()
        target_date = today + timedelta(days=install_days)

        order_data = {
            "order_id": new_id,
            "customer_name": customer_name,
            "business_name": business_name,
            "city": city,
            "products": product_names,
            "monthly_value": round(monthly_total, 2),
            "created_date": today.strftime("%Y-%m-%d"),
            "expected_activation_date": target_date.strftime("%Y-%m-%d"),
            "current_step": 2,
            "assigned_engineer": {
                "name": "Amit Sharma (Enterprise Field Force)",
                "phone": "+91 98110 •••••",
                "badge_id": "AIRTEL-FE-772",
                "slot": f"{target_date.strftime('%Y-%m-%d')}, 11:00 AM - 01:00 PM"
            },
            "status_message": f"Smart KYC cleared instantly. Fibre port allocated; installation scheduled for {target_date.strftime('%d %b %Y')}.",
            "timeline": [
                {"step": 1, "title": "Order Placed & Quote Accepted", "date": today.strftime("%Y-%m-%d %H:%M"), "done": True},
                {"step": 2, "title": "Smart KYC Verified (DigiLocker & GSTIN)", "date": today.strftime("%Y-%m-%d %H:%M"), "done": True},
                {"step": 3, "title": "Fibre Feasibility & Optical Port Tagging", "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"), "done": False, "in_progress": True},
                {"step": 4, "title": "Hardware Dispatch & Field Engineer Alignment", "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"), "done": False},
                {"step": 5, "title": "Premises Cabling & Router Activation", "date": target_date.strftime("%Y-%m-%d"), "done": False},
                {"step": 6, "title": "Speed SLA & Unified Billing Activation", "date": target_date.strftime("%Y-%m-%d"), "done": False}
            ]
        }

        self.orders[new_id] = order_data
        return order_data


"""
reset_timeslots.py
------------------
Run this once to replace all existing time slots in the MySQL database
with the new 6:00 AM – 12:00 PM range (30-minute intervals).

Usage (from the backend/ directory):
    python reset_timeslots.py
"""

import sys
import os

# Make sure we can import from the backend package
sys.path.insert(0, os.path.dirname(__file__))

from datetime import time
from app import create_app
from extensions import db
from models import TimeSlot, Order

app = create_app()

NEW_SLOTS = [
    ("6:00 AM - 6:30 AM",   time(6,  0),  time(6,  30), 10),
    ("6:30 AM - 7:00 AM",   time(6,  30), time(7,  0),  10),
    ("7:00 AM - 7:30 AM",   time(7,  0),  time(7,  30), 12),
    ("7:30 AM - 8:00 AM",   time(7,  30), time(8,  0),  12),
    ("8:00 AM - 8:30 AM",   time(8,  0),  time(8,  30), 12),
    ("8:30 AM - 9:00 AM",   time(8,  30), time(9,  0),  12),
    ("9:00 AM - 9:30 AM",   time(9,  0),  time(9,  30), 15),
    ("9:30 AM - 10:00 AM",  time(9,  30), time(10, 0),  15),
    ("10:00 AM - 10:30 AM", time(10, 0),  time(10, 30), 15),
    ("10:30 AM - 11:00 AM", time(10, 30), time(11, 0),  15),
    ("11:00 AM - 11:30 AM", time(11, 0),  time(11, 30), 15),
    ("11:30 AM - 12:00 PM", time(11, 30), time(12, 0),  15),
]

with app.app_context():
    # Deactivate (soft-delete) all existing slots that have linked orders
    existing = TimeSlot.query.all()
    for slot in existing:
        has_orders = Order.query.filter_by(time_slot_id=slot.id).first()
        if has_orders:
            slot.is_active = False   # keep for historical orders, just hide
        else:
            db.session.delete(slot)  # safe to hard-delete unused slots

    db.session.commit()
    print(f"Cleaned up {len(existing)} old time slot(s).")

    # Insert the new slots
    for label, start, end, max_orders in NEW_SLOTS:
        db.session.add(TimeSlot(
            label=label,
            start_time=start,
            end_time=end,
            max_orders=max_orders,
            is_active=True
        ))

    db.session.commit()
    print("OK - New time slots inserted successfully:")
    for label, *_ in NEW_SLOTS:
        print(f"   • {label}")

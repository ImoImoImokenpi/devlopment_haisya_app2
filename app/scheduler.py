from flask_apscheduler import APScheduler
from datetime import datetime
from .models import Room
from .matching.service import run_matching
from . import db

scheduler = APScheduler()

def check_deadlines():
    now = datetime.utcnow()

    rooms = Room.query.filter(Room.deadline <= now).all()

    for room in rooms:
        run_matching(room.id)

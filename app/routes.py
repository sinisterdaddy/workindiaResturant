from flask import Blueprint, request, jsonify
from . import db
from .models import User, DiningPlace, Booking
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
import os

bp = Blueprint('main', __name__)

@bp.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    new_user = User(
        username=data['username'],
        email=data['email']
    )
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"status": "Account successfully created", "status_code": 200, "user_id": new_user.id})

@bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({"status": "Login successful", "status_code": 200, "user_id": user.id, "access_token": access_token})
    else:
        return jsonify({"status": "Incorrect username/password provided. Please retry", "status_code": 401})

@bp.route('/api/dining-place/create', methods=['POST'])
def create_dining_place():
    admin_api_key = request.headers.get('X-API-Key')
    if admin_api_key != os.getenv('ADMIN_API_KEY'):
        return jsonify({"message": "Unauthorized", "status_code": 403})
    
    data = request.get_json()
    new_place = DiningPlace(
        name=data['name'],
        address=data['address'],
        phone_no=data['phone_no'],
        website=data.get('website', None),
        operational_hours_open=datetime.strptime(data['operational_hours']['open_time'], '%H:%M:%S').time(),
        operational_hours_close=datetime.strptime(data['operational_hours']['close_time'], '%H:%M:%S').time()
    )
    db.session.add(new_place)
    db.session.commit()
    return jsonify({"message": f"{new_place.name} added successfully", "place_id": new_place.id, "status_code": 200})

@bp.route('/api/dining-place', methods=['GET'])
def search_dining_places():
    search_query = request.args.get('name')
    places = DiningPlace.query.filter(DiningPlace.name.ilike(f'%{search_query}%')).all()
    results = [
        {
            "place_id": place.id,
            "name": place.name,
            "address": place.address,
            "phone_no": place.phone_no,
            "website": place.website,
            "operational_hours": {
                "open_time": place.operational_hours_open.strftime('%H:%M:%S'),
                "close_time": place.operational_hours_close.strftime('%H:%M:%S')
            }
        }
        for place in places
    ]
    return jsonify({"results": results})

@bp.route('/api/dining-place/availability', methods=['GET'])
def get_availability():
    place_id = request.args.get('place_id')
    start_time = datetime.strptime(request.args.get('start_time'), '%Y-%m-%dT%H:%M:%SZ')
    end_time = datetime.strptime(request.args.get('end_time'), '%Y-%m-%dT%H:%M:%SZ')

    bookings = Booking.query.filter_by(place_id=place_id).filter(
        Booking.start_time < end_time,
        Booking.end_time > start_time
    ).all()

    if bookings:
        next_available_slot = max([booking.end_time for booking in bookings])
        return jsonify({"status": "Unavailable", "next_available_slot": next_available_slot.isoformat() + 'Z'})
    else:
        return jsonify({"status": "Available", "next_available_slot": end_time.isoformat() + 'Z'})

@bp.route('/api/dining-place/book', methods=['POST'])
@jwt_required()
def book_slot():
    user_id = get_jwt_identity()
    data = request.get_json()
    place_id = data['place_id']
    start_time = datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%SZ')
    end_time = datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M:%SZ')

    bookings = Booking.query.filter_by(place_id=place_id).filter(
        Booking.start_time < end_time,
        Booking.end_time > start_time
    ).all()

    if bookings:
        return jsonify({"status": "Slot already booked", "status_code": 409})
    else:
        new_booking = Booking(
            user_id=user_id,
            place_id=place_id,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(new_booking)
        db.session.commit()
        return jsonify({"status": "Booking successful", "booking_id": new_booking.id, "status_code": 200})

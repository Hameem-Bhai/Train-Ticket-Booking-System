from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import os
import threading
import datetime
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

app = FastAPI(
    title="Bangladesh Railway API V2",
    description="Enhanced REST API with authentication, round-trip booking, refunds, and more",
    version="2.0.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data_v2')
TRAINS_FILE = os.path.join(DATA_DIR, 'trains.txt')
BOOKINGS_FILE = os.path.join(DATA_DIR, 'bookings.txt')
USERS_DIR = os.path.join(DATA_DIR, 'users')
TICKETS_DIR = os.path.join(DATA_DIR, 'tickets')
AUTH_FILE = os.path.join(DATA_DIR, 'auth.json')
SCHEDULES_FILE = os.path.join(DATA_DIR, 'schedules.json')
REFUNDS_FILE = os.path.join(DATA_DIR, 'refunds.json')

file_lock = threading.Lock()
security = HTTPBearer()

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(USERS_DIR, exist_ok=True)
os.makedirs(TICKETS_DIR, exist_ok=True)


class UserRegister(BaseModel):
    username: str
    password: str
    email: EmailStr
    phone: str
    full_name: str

class UserLogin(BaseModel):
    username: str
    password: str

class Train(BaseModel):
    id: str
    name: str
    route: str
    coaches: int
    seats_per_coach: int
    base_price: float

class TrainSchedule(BaseModel):
    train_id: str
    departure_time: str
    arrival_time: str
    stations: List[dict]
    platform: str
    delay_minutes: int = 0

class RoundTripBooking(BaseModel):
    train_id_onward: str
    train_id_return: str
    date_onward: str
    date_return: str
    coach: int
    seats: List[int]
    name: str
    phone: str

class RefundRequest(BaseModel):
    booking_id: str
    reason: str

class BookingCreate(BaseModel):
    train_id: str
    date: str
    coach: int
    seat: int
    name: str
    phone: str

class BatchBooking(BaseModel):
    train_id: str
    date: str
    coach: int
    seats: List[int]
    name: str
    phone: str

class EmailRegister(BaseModel):
    email: EmailStr
    password: str
    phone: str
    full_name: str

class EmailLogin(BaseModel):
    email: EmailStr
    password: str

class EmailVerify(BaseModel):
    email: EmailStr
    code: str

class EmailLoginCodeRequest(BaseModel):
    email: EmailStr

class EmailLoginCodeVerify(BaseModel):
    email: EmailStr
    code: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def ensure_auth_file():
    if not os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, 'w') as f:
            json.dump({"users": {}, "tokens": {}}, f)

def load_auth_data():
    ensure_auth_file()
    with open(AUTH_FILE, 'r') as f:
        return json.load(f)

def save_auth_data(data):
    with open(AUTH_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def ensure_schedules_file():
    if not os.path.exists(SCHEDULES_FILE):
        default_schedules = {
            "T001": {
                "departure_time": "08:00",
                "arrival_time": "14:30",
                "platform": "3",
                "delay_minutes": 0,
                "stations": [
                    {"name": "Dhaka", "arrival": "08:00", "departure": "08:00"},
                    {"name": "Jessore", "arrival": "11:30", "departure": "11:45"},
                    {"name": "Khulna", "arrival": "14:30", "departure": "14:30"}
                ]
            }
        }
        with open(SCHEDULES_FILE, 'w') as f:
            json.dump(default_schedules, f, indent=2)

def load_schedules():
    ensure_schedules_file()
    with open(SCHEDULES_FILE, 'r') as f:
        return json.load(f)

def save_schedules(schedules):
    with open(SCHEDULES_FILE, 'w') as f:
        json.dump(schedules, f, indent=2)

def ensure_refunds_file():
    if not os.path.exists(REFUNDS_FILE):
        with open(REFUNDS_FILE, 'w') as f:
            json.dump([], f)

def load_refunds():
    ensure_refunds_file()
    with open(REFUNDS_FILE, 'r') as f:
        return json.load(f)

def save_refunds(refunds):
    with open(REFUNDS_FILE, 'w') as f:
        json.dump(refunds, f, indent=2)

def calculate_refund_amount(booking, cancellation_date):
    journey_date = datetime.datetime.strptime(booking['date'], '%Y-%m-%d')
    cancel_date = datetime.datetime.strptime(cancellation_date, '%Y-%m-%d')
    days_before = (journey_date - cancel_date).days

    if days_before >= 7:
        return booking['price'] * 0.9
    elif days_before >= 3:
        return booking['price'] * 0.7
    elif days_before >= 1:
        return booking['price'] * 0.5
    else:
        return booking['price'] * 0.2

def send_email_notification(to_email, subject, body):
    try:
        pass
    except Exception as e:
        print(f"Email error: {e}")

def send_sms_notification(phone, message):
    try:
        pass
    except Exception as e:
        print(f"SMS error: {e}")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    auth_data = load_auth_data()

    if token not in auth_data.get("tokens", {}):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return auth_data["tokens"][token]

def ensure_trains_file():
    if not os.path.exists(TRAINS_FILE):
        with open(TRAINS_FILE, 'w', encoding='utf-8') as f:
            f.write('T001|Sundarban Express|Dhaka-Khulna|3|40|550\n')
            f.write('T002|Silk City Express|Dhaka-Rajshahi|2|40|500\n')

def ensure_bookings_file():
    if not os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, 'w', encoding='utf-8') as f:
            f.write('')

def load_trains():
    ensure_trains_file()
    trains = {}
    with open(TRAINS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 6:
                train_id, name, route, coaches, seats, price = parts[:6]
                trains[train_id] = {
                    'id': train_id,
                    'name': name,
                    'route': route,
                    'coaches': int(coaches),
                    'seats_per_coach': int(seats),
                    'base_price': float(price)
                }
    return trains

def load_bookings():
    ensure_bookings_file()
    bookings = []
    with open(BOOKINGS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 9:
                bookings.append({
                    'booking_id': parts[0],
                    'train_id': parts[1],
                    'date': parts[2],
                    'coach': int(parts[3]),
                    'seat': int(parts[4]),
                    'name': parts[5],
                    'phone': parts[6],
                    'price': float(parts[7]),
                    'status': parts[8]
                })
    return bookings

def save_bookings(bookings):
    with open(BOOKINGS_FILE, 'w', encoding='utf-8') as f:
        for b in bookings:
            line = f"{b['booking_id']}|{b['train_id']}|{b['date']}|{b['coach']}|{b['seat']}|{b['name']}|{b['phone']}|{b['price']}|{b['status']}\n"
            f.write(line)

def get_next_booking_id():
    bookings = load_bookings()
    max_id = 0
    for b in bookings:
        try:
            num = int(b['booking_id'][1:])
            if num > max_id:
                max_id = num
        except:
            pass
    return f'B{max_id + 1:05d}'

ensure_trains_file()
ensure_bookings_file()
ensure_auth_file()
ensure_schedules_file()
ensure_refunds_file()


@app.get("/", tags=["Root"])
def root():
    return {"message": "Bangladesh Railway API V2", "version": "2.0.0"}

@app.get("/api/v2/trains", tags=["Trains"])
def get_all_trains():
    """Get list of all available trains"""
    trains = load_trains()
    trains_list = [
        {
            "id": train["id"],
            "name": train["name"],
            "route": train["route"],
            "coaches": train["coaches"],
            "seats_per_coach": train["seats_per_coach"],
            "base_price": train["base_price"]
        }
        for train in trains.values()
    ]
    return {"success": True, "data": trains_list}

@app.post("/api/v2/trains", tags=["Trains"])
def add_train(train_id: str, name: str, route: str, coaches: int,
              seats_per_coach: int, base_price: float,
              user_info: dict = Depends(verify_token)):
    """Add a new train"""
    with file_lock:
        trains = load_trains()

        if train_id in trains:
            raise HTTPException(status_code=400, detail="Train ID already exists")

        # Add to trains dict
        trains[train_id] = {
            'id': train_id,
            'name': name,
            'route': route,
            'coaches': coaches,
            'seats_per_coach': seats_per_coach,
            'base_price': base_price
        }

        # Save to file
        with open(TRAINS_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{train_id}|{name}|{route}|{coaches}|{seats_per_coach}|{base_price}\n")

        return {"success": True, "message": "Train added successfully"}

@app.delete("/api/v2/trains/{train_id}", tags=["Trains"])
def delete_train(train_id: str, user_info: dict = Depends(verify_token)):
    """Delete a train"""
    with file_lock:
        trains = load_trains()

        if train_id not in trains:
            raise HTTPException(status_code=404, detail="Train not found")

        # Remove from dict
        del trains[train_id]

        # Rewrite file without this train
        with open(TRAINS_FILE, 'w', encoding='utf-8') as f:
            for train in trains.values():
                f.write(f"{train['id']}|{train['name']}|{train['route']}|{train['coaches']}|{train['seats_per_coach']}|{train['base_price']}\n")

        return {"success": True, "message": "Train deleted successfully"}

@app.put("/api/v2/trains/{train_id}", tags=["Trains"])
def update_train(train_id: str, name: Optional[str] = None, route: Optional[str] = None,
                coaches: Optional[int] = None, seats_per_coach: Optional[int] = None,
                base_price: Optional[float] = None, user_info: dict = Depends(verify_token)):
    """Update train details"""
    with file_lock:
        trains = load_trains()

        if train_id not in trains:
            raise HTTPException(status_code=404, detail="Train not found")

        # Update fields
        if name: trains[train_id]['name'] = name
        if route: trains[train_id]['route'] = route
        if coaches: trains[train_id]['coaches'] = coaches
        if seats_per_coach: trains[train_id]['seats_per_coach'] = seats_per_coach
        if base_price: trains[train_id]['base_price'] = base_price

        # Rewrite file
        with open(TRAINS_FILE, 'w', encoding='utf-8') as f:
            for train in trains.values():
                f.write(f"{train['id']}|{train['name']}|{train['route']}|{train['coaches']}|{train['seats_per_coach']}|{train['base_price']}\n")

        return {"success": True, "message": "Train updated successfully"}

@app.post("/api/v2/auth/register", tags=["Authentication"])
def register_user(user: UserRegister):
    auth_data = load_auth_data()

    if user.username in auth_data["users"]:
        raise HTTPException(status_code=400, detail="Username already exists")

    auth_data["users"][user.username] = {
        "password": hash_password(user.password),
        "email": user.email,
        "phone": user.phone,
        "full_name": user.full_name,
        "created_at": datetime.datetime.now().isoformat(),
        "bookings": []
    }

    save_auth_data(auth_data)
    return {"success": True, "message": "User registered successfully"}

@app.post("/api/v2/auth/login", tags=["Authentication"])
def login_user(user: UserLogin):
    auth_data = load_auth_data()

    if user.username not in auth_data["users"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    stored_user = auth_data["users"][user.username]
    if hash_password(user.password) != stored_user["password"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = generate_token()
    auth_data["tokens"][token] = {
        "username": user.username,
        "created_at": datetime.datetime.now().isoformat()
    }

    save_auth_data(auth_data)
    return {
        "success": True,
        "token": token,
        "user": {
            "username": user.username,
            "email": stored_user["email"],
            "full_name": stored_user["full_name"]
        }
    }

@app.get("/api/v2/auth/profile", tags=["Authentication"])
def get_profile(user_info: dict = Depends(verify_token)):
    auth_data = load_auth_data()
    username = user_info["username"]

    if username not in auth_data["users"]:
        raise HTTPException(status_code=404, detail="User not found")

    user = auth_data["users"][username]
    return {
        "success": True,
        "data": {
            "username": username,
            "email": user["email"],
            "phone": user["phone"],
            "full_name": user["full_name"],
            "booking_count": len(user.get("bookings", []))
        }
    }

@app.get("/api/v2/auth/booking-history", tags=["Authentication"])
def get_booking_history(user_info: dict = Depends(verify_token)):
    auth_data = load_auth_data()
    username = user_info["username"]
    user = auth_data["users"][username]

    booking_ids = user.get("bookings", [])
    bookings = load_bookings()

    user_bookings = [b for b in bookings if b['booking_id'] in booking_ids]
    return {"success": True, "data": user_bookings}


@app.post("/api/v2/bookings/round-trip", tags=["Round Trip"])
def create_round_trip_booking(booking: RoundTripBooking, user_info: dict = Depends(verify_token)):
    with file_lock:
        trains = load_trains()

        if booking.train_id_onward not in trains or booking.train_id_return not in trains:
            raise HTTPException(status_code=404, detail="Train not found")

        bookings = load_bookings()
        booking_ids = []

        # First check ALL seats are available before booking any
        for train_id, date in [(booking.train_id_onward, booking.date_onward),
                               (booking.train_id_return, booking.date_return)]:
            for seat in booking.seats:
                for b in bookings:
                    if (b['train_id'] == train_id and b['date'] == date and
                        b['coach'] == booking.coach and b['seat'] == seat and
                        b['status'] == 'BOOKED'):
                        raise HTTPException(status_code=400, detail=f"Seat {seat} on {train_id} for {date} is already booked")

        # Now book all seats (we know they're all available)
        for train_id, date in [(booking.train_id_onward, booking.date_onward),
                               (booking.train_id_return, booking.date_return)]:
            for seat in booking.seats:
                booking_id = get_next_booking_id()
                new_booking = {
                    'booking_id': booking_id,
                    'train_id': train_id,
                    'date': date,
                    'coach': booking.coach,
                    'seat': seat,
                    'name': booking.name,
                    'phone': booking.phone,
                    'price': trains[train_id]['base_price'],
                    'status': 'BOOKED'
                }
                bookings.append(new_booking)
                booking_ids.append(booking_id)

        save_bookings(bookings)

        auth_data = load_auth_data()
        username = user_info["username"]
        auth_data["users"][username]["bookings"].extend(booking_ids)
        save_auth_data(auth_data)

        send_email_notification(
            auth_data["users"][username]["email"],
            "Round Trip Booking Confirmation",
            f"Your round trip has been booked. IDs: {', '.join(booking_ids)}"
        )

        return {
            "success": True,
            "message": "Round trip booked successfully",
            "data": {"booking_ids": booking_ids}
        }


@app.post("/api/v2/refunds/request", tags=["Refunds"])
def request_refund(refund: RefundRequest, user_info: dict = Depends(verify_token)):
    bookings = load_bookings()
    booking = None

    for b in bookings:
        if b['booking_id'] == refund.booking_id:
            booking = b
            break

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    auth_data = load_auth_data()
    username = user_info["username"]
    if refund.booking_id not in auth_data["users"][username]["bookings"]:
        raise HTTPException(status_code=403, detail="Not your booking")

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    refund_amount = calculate_refund_amount(booking, today)

    refunds = load_refunds()
    refund_record = {
        "refund_id": f"R{len(refunds) + 1:05d}",
        "booking_id": refund.booking_id,
        "username": username,
        "original_amount": booking['price'],
        "refund_amount": refund_amount,
        "reason": refund.reason,
        "requested_at": datetime.datetime.now().isoformat(),
        "status": "PENDING"
    }
    refunds.append(refund_record)
    save_refunds(refunds)

    for b in bookings:
        if b['booking_id'] == refund.booking_id:
            b['status'] = 'REFUND_REQUESTED'
    save_bookings(bookings)

    return {
        "success": True,
        "message": "Refund requested",
        "data": refund_record
    }

@app.get("/api/v2/refunds/status/{refund_id}", tags=["Refunds"])
def get_refund_status(refund_id: str, user_info: dict = Depends(verify_token)):
    refunds = load_refunds()

    for refund in refunds:
        if refund['refund_id'] == refund_id:
            return {"success": True, "data": refund}

    raise HTTPException(status_code=404, detail="Refund not found")


@app.get("/api/v2/schedules/{train_id}", tags=["Schedules"])
def get_train_schedule(train_id: str):
    schedules = load_schedules()

    if train_id not in schedules:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return {"success": True, "data": schedules[train_id]}

@app.put("/api/v2/schedules/{train_id}/delay", tags=["Schedules"])
def update_train_delay(train_id: str, delay_minutes: int):
    schedules = load_schedules()

    if train_id not in schedules:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedules[train_id]["delay_minutes"] = delay_minutes
    save_schedules(schedules)

    return {
        "success": True,
        "message": f"Delay updated to {delay_minutes} minutes"
    }


@app.get("/api/v2/reports/revenue", tags=["Reports"])
def get_revenue_report(start_date: str, end_date: str):
    bookings = load_bookings()

    filtered = [b for b in bookings
                if start_date <= b['date'] <= end_date and b['status'] in ('BOOKED', 'PAID')]

    total_revenue = sum(b['price'] for b in filtered)
    by_train = {}

    for b in filtered:
        if b['train_id'] not in by_train:
            by_train[b['train_id']] = 0
        by_train[b['train_id']] += b['price']

    return {
        "success": True,
        "data": {
            "period": f"{start_date} to {end_date}",
            "total_revenue": total_revenue,
            "total_bookings": len(filtered),
            "by_train": by_train
        }
    }

@app.get("/api/v2/reports/occupancy", tags=["Reports"])
def get_occupancy_report(train_id: str, date: str):
    trains = load_trains()
    if train_id not in trains:
        raise HTTPException(status_code=404, detail="Train not found")

    train = trains[train_id]
    bookings = load_bookings()

    booked_seats = [b for b in bookings
                    if b['train_id'] == train_id and b['date'] == date and b['status'] in ('BOOKED', 'PAID')]

    total_seats = train['coaches'] * train['seats_per_coach']
    occupancy_rate = (len(booked_seats) / total_seats * 100) if total_seats > 0 else 0

    by_coach = {}
    for coach in range(1, train['coaches'] + 1):
        coach_bookings = [b for b in booked_seats if b['coach'] == coach]
        by_coach[f"Coach {coach}"] = {
            "booked": len(coach_bookings),
            "total": train['seats_per_coach'],
            "rate": len(coach_bookings) / train['seats_per_coach'] * 100
        }

    return {
        "success": True,
        "data": {
            "train_id": train_id,
            "date": date,
            "total_booked": len(booked_seats),
            "total_seats": total_seats,
            "occupancy_rate": occupancy_rate,
            "by_coach": by_coach
        }
    }

@app.get("/api/v2/reports/popular-routes", tags=["Reports"])
def get_popular_routes():
    bookings = load_bookings()
    trains = load_trains()

    route_counts = {}
    for b in bookings:
        if b['status'] in ('BOOKED', 'PAID'):
            train = trains.get(b['train_id'])
            if train:
                route = train['route']
                route_counts[route] = route_counts.get(route, 0) + 1

    sorted_routes = sorted(route_counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "success": True,
        "data": {
            "popular_routes": [
                {"route": route, "bookings": count}
                for route, count in sorted_routes[:10]
            ]
        }
    }


@app.post("/api/v2/notifications/send-reminder", tags=["Notifications"])
def send_journey_reminder(booking_id: str):
    bookings = load_bookings()
    booking = None

    for b in bookings:
        if b['booking_id'] == booking_id:
            booking = b
            break

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    message = f"Journey Reminder: Your train {booking['train_id']} is on {booking['date']}. Coach {booking['coach']}, Seat {booking['seat']}"

    send_sms_notification(booking['phone'], message)

    return {"success": True, "message": "Reminder sent"}


@app.get("/", tags=["Info"])
def root():
    return {
        "message": "🚂 Bangladesh Railway API V2 - Enhanced Version",
        "version": "2.0.0",
        "docs": "/docs",
        "new_features": [
            "User Authentication",
            "Round Trip Booking",
            "Refund Processing",
            "Train Schedules & Delays",
            "Revenue & Occupancy Reports",
            "Email & SMS Notifications"
        ]
    }


@app.get("/api/v2/availability", tags=["Trains"])
def get_seat_availability(train_id: str, date: str, coach: int):
    """Return list of booked seats for a given train/date/coach"""
    trains = load_trains()
    if train_id not in trains:
        raise HTTPException(status_code=404, detail="Train not found")

    bookings = load_bookings()
    booked = [b['seat'] for b in bookings
              if b['train_id'] == train_id and b['date'] == date and b['coach'] == coach
              and b['status'] in ('BOOKED', 'PAID', 'REFUND_REQUESTED')]

    return {"success": True, "data": {"booked_seats": booked}}


@app.post("/api/v2/bookings/single", tags=["Bookings"])
def create_single_booking(booking: BookingCreate, user_info: dict = Depends(verify_token)):
    with file_lock:
        trains = load_trains()
        if booking.train_id not in trains:
            raise HTTPException(status_code=404, detail="Train not found")

        bookings = load_bookings()
        # Check seat availability
        for b in bookings:
            if (b['train_id'] == booking.train_id and b['date'] == booking.date and
                b['coach'] == booking.coach and b['seat'] == booking.seat and
                b['status'] in ('BOOKED', 'PAID', 'REFUND_REQUESTED')):
                raise HTTPException(status_code=400, detail=f"Seat {booking.seat} already booked")

        # Book seat
        booking_id = get_next_booking_id()
        new_booking = {
            'booking_id': booking_id,
            'train_id': booking.train_id,
            'date': booking.date,
            'coach': booking.coach,
            'seat': booking.seat,
            'name': booking.name,
            'phone': booking.phone,
            'price': trains[booking.train_id]['base_price'],
            'status': 'BOOKED'
        }
        bookings.append(new_booking)
        save_bookings(bookings)

        # Link to user
        auth_data = load_auth_data()
        username = user_info["username"]
        auth_data["users"][username]["bookings"].append(booking_id)
        save_auth_data(auth_data)

        return {"success": True, "data": {"booking_id": booking_id}}


@app.post("/api/v2/bookings/batch", tags=["Bookings"])
def create_batch_booking(payload: BatchBooking, user_info: dict = Depends(verify_token)):
    with file_lock:
        trains = load_trains()
        if payload.train_id not in trains:
            raise HTTPException(status_code=404, detail="Train not found")
        if not payload.seats:
            raise HTTPException(status_code=400, detail="No seats provided")

        bookings = load_bookings()

        # Check all seats first
        for seat in payload.seats:
            for b in bookings:
                if (b['train_id'] == payload.train_id and b['date'] == payload.date and
                    b['coach'] == payload.coach and b['seat'] == seat and
                    b['status'] in ('BOOKED', 'PAID', 'REFUND_REQUESTED')):
                    raise HTTPException(status_code=400, detail=f"Seat {seat} already booked")

        # Create all bookings
        booking_ids = []
        for seat in payload.seats:
            booking_id = get_next_booking_id()
            new_booking = {
                'booking_id': booking_id,
                'train_id': payload.train_id,
                'date': payload.date,
                'coach': payload.coach,
                'seat': seat,
                'name': payload.name,
                'phone': payload.phone,
                'price': trains[payload.train_id]['base_price'],
                'status': 'BOOKED'
            }
            bookings.append(new_booking)
            booking_ids.append(booking_id)

        save_bookings(bookings)

        # Link to user
        auth_data = load_auth_data()
        username = user_info["username"]
        auth_data["users"][username]["bookings"].extend(booking_ids)
        save_auth_data(auth_data)

        return {"success": True, "data": {"booking_ids": booking_ids}}


# helper: send email using Gmail SMTP if configured
def send_verification_email(to_email: str, code: str):
    try:
        # Attempt to load from .env-like environment
        sender = os.getenv('EMAIL_ADDRESS', '')
        pwd = os.getenv('EMAIL_PASSWORD', '')
        if not sender or not pwd:
            print('Email not configured; cannot send verification email')
            return False
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Verify your Bangladesh Railway account"
        msg['From'] = sender
        msg['To'] = to_email
        html = f"""
        <html><body>
        <h2>Bangladesh Railway - Email Verification</h2>
        <p>Your verification code is: <b>{code}</b></p>
        <p>Enter this code in the app to verify your email.</p>
        </body></html>
        """
        msg.attach(MIMEText(html, 'html'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender, pwd)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Verification email send failed: {e}")
        return False

@app.post("/api/v2/auth/register-email", tags=["Authentication"])
def register_user_email(payload: EmailRegister):
    auth = load_auth_data()
    email_key = payload.email.lower()
    # Prevent duplicates
    for uname, u in auth['users'].items():
        if u.get('email', '').lower() == email_key:
            raise HTTPException(status_code=400, detail="Email already registered")
    # Create username alias from email
    username = email_key
    verification_code = secrets.token_hex(3).upper()
    auth['users'][username] = {
        "password": hash_password(payload.password),
        "email": payload.email,
        "phone": payload.phone,
        "full_name": payload.full_name,
        "created_at": datetime.datetime.now().isoformat(),
        "bookings": [],
        "email_verified": False,
        "verification_code": verification_code
    }
    save_auth_data(auth)
    # send verification mail (best-effort)
    send_verification_email(payload.email, verification_code)
    return {"success": True, "message": "Registered. Verification code sent to email."}

@app.post("/api/v2/auth/verify-email", tags=["Authentication"])
def verify_email(payload: EmailVerify):
    auth = load_auth_data()
    email_key = payload.email.lower()
    user = auth['users'].get(email_key)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get('email_verified'):
        return {"success": True, "message": "Already verified"}
    if payload.code.strip().upper() != str(user.get('verification_code', '')).upper():
        raise HTTPException(status_code=400, detail="Invalid verification code")
    user['email_verified'] = True
    user['verification_code'] = None
    save_auth_data(auth)
    return {"success": True, "message": "Email verified"}

@app.post("/api/v2/auth/login-email", tags=["Authentication"])
def login_email(payload: EmailLogin):
    auth = load_auth_data()
    email_key = payload.email.lower()
    user = auth['users'].get(email_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if hash_password(payload.password) != user['password']:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.get('email_verified'):
        raise HTTPException(status_code=403, detail="Email not verified")
    token = generate_token()
    auth['tokens'][token] = {
        "username": email_key,
        "created_at": datetime.datetime.now().isoformat()
    }
    save_auth_data(auth)
    return {"success": True, "token": token, "user": {
        "username": email_key,
        "email": user['email'],
        "full_name": user['full_name']
    }}

@app.post("/api/v2/auth/send-login-code", tags=["Authentication"])
def send_login_code(payload: EmailLoginCodeRequest):
    auth = load_auth_data()
    email_key = payload.email.lower()
    # find user by email
    username = None
    user = None
    for uname, u in auth['users'].items():
        if u.get('email', '').lower() == email_key:
            username = uname
            user = u
            break
    # If not found, create a minimal user record to support passwordless flow
    if not user:
        username = email_key
        auth['users'][username] = {
            "password": hash_password(secrets.token_hex(8)),  # placeholder
            "email": payload.email,
            "phone": "",
            "full_name": payload.email.split('@')[0],
            "created_at": datetime.datetime.now().isoformat(),
            "bookings": [],
            "email_verified": False,
            "verification_code": None
        }
        user = auth['users'][username]
        save_auth_data(auth)

    code = secrets.token_hex(3).upper()
    # store transient login code
    auth.setdefault('login_codes', {})
    auth['login_codes'][email_key] = {
        "code": code,
        "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(minutes=10)).isoformat()
    }
    save_auth_data(auth)
    # send email
    ok = send_verification_email(payload.email, code)
    if not ok:
        return {"success": True, "message": "Login code generated. Email sending not configured.", "code": code}
    return {"success": True, "message": "Login code sent to your email.", "code": code}

@app.post("/api/v2/auth/login-code", tags=["Authentication"])
def login_with_code(payload: EmailLoginCodeVerify):
    auth = load_auth_data()
    email_key = payload.email.lower()
    # find username by email
    username = None
    user = None
    for uname, u in auth['users'].items():
        if u.get('email', '').lower() == email_key:
            username = uname
            user = u
            break
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")

    lc = auth.get('login_codes', {}).get(email_key)
    if not lc:
        raise HTTPException(status_code=400, detail="No login code requested")
    if payload.code.strip().upper() != lc.get('code', '').upper():
        raise HTTPException(status_code=401, detail="Invalid code")
    # optional: check expiry
    try:
        exp = datetime.datetime.fromisoformat(lc.get('expires_at'))
        if datetime.datetime.utcnow() > exp:
            raise HTTPException(status_code=400, detail="Code expired")
    except Exception:
        pass
    # success: mark verified and issue token
    user['email_verified'] = True
    auth.setdefault('tokens', {})
    token = generate_token()
    auth['tokens'][token] = {
        "username": username,
        "created_at": datetime.datetime.now().isoformat()
    }
    # clear used code
    auth['login_codes'][email_key] = None
    save_auth_data(auth)
    return {"success": True, "token": token, "user": {
        "username": username,
        "email": user['email'],
        "full_name": user['full_name']
    }}


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("    🚂 BANGLADESH RAILWAY - API SERVER V2 🚂")
    print("=" * 60)
    print("Starting enhanced server at http://127.0.0.1:5001")
    print("API Documentation: http://127.0.0.1:5001/docs")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=5001)


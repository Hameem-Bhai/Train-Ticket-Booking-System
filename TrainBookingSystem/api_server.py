

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import threading
import datetime

app = FastAPI(
    title="Bangladesh Railway API",
    description="REST API for managing train ticket bookings, user files, and ticket files.",
    version="1.0.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TRAINS_FILE = os.path.join(DATA_DIR, 'trains.txt')
BOOKINGS_FILE = os.path.join(DATA_DIR, 'bookings.txt')
USERS_DIR = os.path.join(DATA_DIR, 'users')
TICKETS_DIR = os.path.join(DATA_DIR, 'tickets')

file_lock = threading.Lock()

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(USERS_DIR, exist_ok=True)
os.makedirs(TICKETS_DIR, exist_ok=True)


class Train(BaseModel):
    id: str
    name: str
    route: str
    coaches: int
    seats_per_coach: int
    base_price: float

class TrainCreate(BaseModel):
    id: str
    name: str
    route: str
    coaches: int
    seats_per_coach: int
    base_price: float

class TrainUpdate(BaseModel):
    name: Optional[str] = None
    route: Optional[str] = None
    coaches: Optional[int] = None
    seats_per_coach: Optional[int] = None
    base_price: Optional[float] = None

class Booking(BaseModel):
    booking_id: str
    train_id: str
    date: str
    coach: int
    seat: int
    name: str
    phone: str
    price: float
    status: str

class BookingCreate(BaseModel):
    train_id: str
    date: str
    coach: int
    seat: int
    name: str
    phone: str

class BookingUpdate(BaseModel):
    status: Optional[str] = None

class UserFile(BaseModel):
    phone: str
    content: str

class TicketRequest(BaseModel):
    booking_id: Optional[str] = None
    phone: Optional[str] = None
    train_id: Optional[str] = None
    date: Optional[str] = None

class SeatInfo(BaseModel):
    seat: int
    available: bool

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


def ensure_trains_file():
    """Initialize trains.txt if it doesn't exist"""
    if not os.path.exists(TRAINS_FILE):
        with open(TRAINS_FILE, 'w', encoding='utf-8') as f:
            f.write('T001|Sundarban Express|Dhaka-Khulna|3|40|550\n')
            f.write('T002|Silk City Express|Dhaka-Rajshahi|2|40|500\n')
            f.write('T003|Turna Nishita Express|Dhaka-Chittagong|3|40|600\n')
            f.write('T004|Ekota Express|Dhaka-Dinajpur|2|40|650\n')
            f.write('T005|Lalmoni Express|Dhaka-Lalmonirhat|2|40|700\n')
            f.write('T006|Joyantika Express|Dhaka-Sylhet|2|40|550\n')
            f.write('T007|Paharika Express|Chittagong-Sylhet|2|40|500\n')
            f.write('T008|Intercity Express|Dhaka-Chittagong|2|40|600\n')
            f.write('T009|Upaban Express|Dhaka-Sylhet|2|40|650\n')
            f.write('T010|Kalni Express|Dhaka-Sylhet|2|40|600\n')
            f.write('T011|Bijoy Express|Chittagong-Mymensingh|2|40|550\n')
            f.write('T012|Bandhan Express|Khulna-Kolkata|2|40|1200\n')
            f.write('T013|Dhumketu Express|Dhaka-Rajshahi|2|40|700\n')
            f.write('T014|Shonar Bangla Express|Dhaka-Chittagong|2|40|800\n')

def ensure_bookings_file():
    """Initialize bookings.txt if it doesn't exist"""
    if not os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, 'w', encoding='utf-8') as f:
            f.write('')

def load_trains() -> dict:
    """Load all trains from file"""
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

def save_trains(trains: dict):
    """Save all trains to file"""
    with open(TRAINS_FILE, 'w', encoding='utf-8') as f:
        for t in trains.values():
            line = f"{t['id']}|{t['name']}|{t['route']}|{t['coaches']}|{t['seats_per_coach']}|{t['base_price']:.2f}\n"
            f.write(line)

def load_bookings() -> list:
    """Load all bookings from file"""
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

def save_bookings(bookings: list):
    """Save all bookings to file"""
    with open(BOOKINGS_FILE, 'w', encoding='utf-8') as f:
        for b in bookings:
            line = f"{b['booking_id']}|{b['train_id']}|{b['date']}|{b['coach']}|{b['seat']}|{b['name']}|{b['phone']}|{b['price']}|{b['status']}\n"
            f.write(line)

def get_next_booking_id() -> str:
    """Generate next booking ID"""
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


@app.get("/api/trains", tags=["Trains"])
def get_all_trains():
    """READ: Get all trains"""
    trains = load_trains()
    return {"success": True, "data": list(trains.values())}

@app.get("/api/trains/{train_id}", tags=["Trains"])
def get_train(train_id: str):
    """READ: Get a specific train by ID"""
    trains = load_trains()
    if train_id not in trains:
        raise HTTPException(status_code=404, detail="Train not found")
    return {"success": True, "data": trains[train_id]}

@app.post("/api/trains", tags=["Trains"])
def create_train(train: TrainCreate):
    """CREATE: Add a new train"""
    with file_lock:
        trains = load_trains()
        if train.id in trains:
            raise HTTPException(status_code=400, detail="Train ID already exists")
        trains[train.id] = {
            'id': train.id,
            'name': train.name,
            'route': train.route,
            'coaches': train.coaches,
            'seats_per_coach': train.seats_per_coach,
            'base_price': train.base_price
        }
        save_trains(trains)
    return {"success": True, "message": f"Train {train.id} created successfully"}

@app.put("/api/trains/{train_id}", tags=["Trains"])
def update_train(train_id: str, train: TrainUpdate):
    """UPDATE: Modify an existing train"""
    with file_lock:
        trains = load_trains()
        if train_id not in trains:
            raise HTTPException(status_code=404, detail="Train not found")
        if train.name is not None:
            trains[train_id]['name'] = train.name
        if train.route is not None:
            trains[train_id]['route'] = train.route
        if train.coaches is not None:
            trains[train_id]['coaches'] = train.coaches
        if train.seats_per_coach is not None:
            trains[train_id]['seats_per_coach'] = train.seats_per_coach
        if train.base_price is not None:
            trains[train_id]['base_price'] = train.base_price
        save_trains(trains)
    return {"success": True, "message": f"Train {train_id} updated successfully"}

@app.delete("/api/trains/{train_id}", tags=["Trains"])
def delete_train(train_id: str):
    """DELETE: Remove a train"""
    with file_lock:
        trains = load_trains()
        if train_id not in trains:
            raise HTTPException(status_code=404, detail="Train not found")
        del trains[train_id]
        save_trains(trains)
    return {"success": True, "message": f"Train {train_id} deleted successfully"}


@app.get("/api/bookings", tags=["Bookings"])
def get_all_bookings(train_id: Optional[str] = None, date: Optional[str] = None, phone: Optional[str] = None):
    """READ: Get all bookings with optional filters"""
    bookings = load_bookings()
    if train_id:
        bookings = [b for b in bookings if b['train_id'] == train_id]
    if date:
        bookings = [b for b in bookings if b['date'] == date]
    if phone:
        bookings = [b for b in bookings if b['phone'] == phone]
    return {"success": True, "data": bookings}

@app.get("/api/bookings/{booking_id}", tags=["Bookings"])
def get_booking(booking_id: str):
    """READ: Get a specific booking by ID"""
    bookings = load_bookings()
    for b in bookings:
        if b['booking_id'] == booking_id:
            return {"success": True, "data": b}
    raise HTTPException(status_code=404, detail="Booking not found")

@app.post("/api/bookings", tags=["Bookings"])
def create_booking(booking: BookingCreate):
    """CREATE: Create a new booking"""
    with file_lock:
        trains = load_trains()
        if booking.train_id not in trains:
            raise HTTPException(status_code=404, detail="Train not found")
        train = trains[booking.train_id]
        if booking.coach < 1 or booking.coach > train['coaches']:
            raise HTTPException(status_code=400, detail="Invalid coach number")
        if booking.seat < 1 or booking.seat > train['seats_per_coach']:
            raise HTTPException(status_code=400, detail="Invalid seat number")

        bookings = load_bookings()
        for b in bookings:
            if (b['train_id'] == booking.train_id and
                b['date'] == booking.date and
                b['coach'] == booking.coach and
                b['seat'] == booking.seat and
                b['status'] == 'BOOKED'):
                raise HTTPException(status_code=400, detail="Seat already booked")

        booking_id = get_next_booking_id()
        new_booking = {
            'booking_id': booking_id,
            'train_id': booking.train_id,
            'date': booking.date,
            'coach': booking.coach,
            'seat': booking.seat,
            'name': booking.name,
            'phone': booking.phone,
            'price': train['base_price'],
            'status': 'BOOKED'
        }
        bookings.append(new_booking)
        save_bookings(bookings)
    return {"success": True, "message": f"Booking {booking_id} created", "data": {"booking_id": booking_id}}

@app.put("/api/bookings/{booking_id}", tags=["Bookings"])
def update_booking(booking_id: str, update: BookingUpdate):
    """UPDATE: Update booking status (BOOKED -> PAID or CANCELLED)"""
    with file_lock:
        bookings = load_bookings()
        found = False
        for b in bookings:
            if b['booking_id'] == booking_id:
                if update.status:
                    b['status'] = update.status
                found = True
                break
        if not found:
            raise HTTPException(status_code=404, detail="Booking not found")
        save_bookings(bookings)
    return {"success": True, "message": f"Booking {booking_id} updated"}

@app.put("/api/bookings/cancel/{booking_id}", tags=["Bookings"])
def cancel_booking(booking_id: str):
    """UPDATE: Cancel a booking"""
    with file_lock:
        bookings = load_bookings()
        found = False
        for b in bookings:
            if b['booking_id'] == booking_id and b['status'] == 'BOOKED':
                b['status'] = 'CANCELLED'
                found = True
                break
        if not found:
            raise HTTPException(status_code=404, detail="Booking not found or already cancelled")
        save_bookings(bookings)
    return {"success": True, "message": f"Booking {booking_id} cancelled"}

@app.put("/api/bookings/pay/{booking_id}", tags=["Bookings"])
def pay_booking(booking_id: str):
    """UPDATE: Mark booking as paid"""
    with file_lock:
        bookings = load_bookings()
        found = False
        for b in bookings:
            if b['booking_id'] == booking_id and b['status'] == 'BOOKED':
                b['status'] = 'PAID'
                found = True
                break
        if not found:
            raise HTTPException(status_code=404, detail="Booking not found or already processed")
        save_bookings(bookings)
    return {"success": True, "message": f"Booking {booking_id} marked as paid"}

@app.delete("/api/bookings/{booking_id}", tags=["Bookings"])
def delete_booking(booking_id: str):
    """DELETE: Remove a booking permanently"""
    with file_lock:
        bookings = load_bookings()
        original_len = len(bookings)
        bookings = [b for b in bookings if b['booking_id'] != booking_id]
        if len(bookings) == original_len:
            raise HTTPException(status_code=404, detail="Booking not found")
        save_bookings(bookings)
    return {"success": True, "message": f"Booking {booking_id} deleted"}


@app.get("/api/seats/{train_id}/{date}/{coach}", tags=["Seats"])
def get_available_seats(train_id: str, date: str, coach: int):
    """READ: Get seat availability for a specific train/date/coach"""
    trains = load_trains()
    if train_id not in trains:
        raise HTTPException(status_code=404, detail="Train not found")
    train = trains[train_id]

    bookings = load_bookings()
    taken = set()
    for b in bookings:
        if (b['train_id'] == train_id and
            b['date'] == date and
            b['coach'] == coach and
            b['status'] in ('BOOKED', 'PAID')):
            taken.add(b['seat'])

    seats = []
    for s in range(1, train['seats_per_coach'] + 1):
        seats.append({'seat': s, 'available': s not in taken})
    return {"success": True, "data": seats}


@app.get("/api/users/{phone}", tags=["User Files"])
def get_user_file(phone: str):
    """READ: Get user file content"""
    path = os.path.join(USERS_DIR, f'{phone}.txt')
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="User file not found")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return {"success": True, "data": {"phone": phone, "content": content}}

@app.post("/api/users/{phone}", tags=["User Files"])
def create_user_file(phone: str):
    """CREATE: Create a new user file"""
    path = os.path.join(USERS_DIR, f'{phone}.txt')
    if os.path.exists(path):
        raise HTTPException(status_code=400, detail="User file already exists")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'USER {phone}\n')
        f.write(f'CREATED {datetime.datetime.now().isoformat()}\n')
    return {"success": True, "message": f"User file for {phone} created"}

@app.put("/api/users/{phone}", tags=["User Files"])
def update_user_file(phone: str):
    """UPDATE: Append booking summary to user file"""
    path = os.path.join(USERS_DIR, f'{phone}.txt')
    bookings = load_bookings()
    user_bookings = [b for b in bookings if b['phone'] == phone]
    with open(path, 'a', encoding='utf-8') as f:
        f.write(f'UPDATE {datetime.datetime.now().isoformat()} COUNT={len(user_bookings)}\n')
        for b in user_bookings:
            f.write(f"  - {b['booking_id']} | {b['train_id']} | {b['date']} | Coach {b['coach']} Seat {b['seat']} | {b['status']}\n")
    return {"success": True, "message": f"User file for {phone} updated"}

@app.delete("/api/users/{phone}", tags=["User Files"])
def delete_user_file(phone: str):
    """DELETE: Remove user file"""
    path = os.path.join(USERS_DIR, f'{phone}.txt')
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="User file not found")
    os.remove(path)
    return {"success": True, "message": f"User file for {phone} deleted"}


def generate_ticket_text(booking_id: str) -> Optional[str]:
    """Generate ticket text content"""
    bookings = load_bookings()
    booking = None
    for b in bookings:
        if b['booking_id'] == booking_id:
            booking = b
            break
    if not booking:
        return None

    trains = load_trains()
    train = trains.get(booking['train_id'])
    if not train:
        return None

    border = '=' * 60
    mid_border = '-' * 60
    lines = [
        border,
        '         🚂 BANGLADESH RAILWAY - TICKET 🚂',
        border,
        f"Booking ID    : {booking['booking_id']}",
        f"Train         : {train['id']} - {train['name']}",
        f"Route         : {train['route']}",
        f"Date          : {booking['date']}",
        f"Coach         : {booking['coach']}",
        f"Seat          : {booking['seat']}",
        mid_border,
        f"Passenger     : {booking['name']}",
        f"Phone         : {booking['phone']}",
        f"Price         : {booking['price']:.2f} Tk",
        f"Status        : {booking['status']}",
        mid_border,
        f"Issued        : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        border,
        'Thank you for choosing Bangladesh Railway!',
        border
    ]
    return '\n'.join(lines)

@app.get("/api/tickets/text/{booking_id}", tags=["Ticket Files"])
def get_ticket_text(booking_id: str):
    """READ: Get ticket text content"""
    path = os.path.join(TICKETS_DIR, f'ticket_{booking_id}.txt')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "data": {"booking_id": booking_id, "content": content, "path": path}}
    content = generate_ticket_text(booking_id)
    if not content:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"success": True, "data": {"booking_id": booking_id, "content": content, "path": None}}

@app.post("/api/tickets/text/{booking_id}", tags=["Ticket Files"])
def create_ticket_text(booking_id: str):
    """CREATE: Generate and save ticket text file"""
    content = generate_ticket_text(booking_id)
    if not content:
        raise HTTPException(status_code=404, detail="Booking not found")
    path = os.path.join(TICKETS_DIR, f'ticket_{booking_id}.txt')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return {"success": True, "message": f"Ticket file created", "data": {"path": path}}

@app.put("/api/tickets/text/{booking_id}", tags=["Ticket Files"])
def update_ticket_text(booking_id: str):
    """UPDATE: Regenerate ticket text file"""
    content = generate_ticket_text(booking_id)
    if not content:
        raise HTTPException(status_code=404, detail="Booking not found")
    path = os.path.join(TICKETS_DIR, f'ticket_{booking_id}.txt')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return {"success": True, "message": f"Ticket file updated", "data": {"path": path}}

@app.delete("/api/tickets/text/{booking_id}", tags=["Ticket Files"])
def delete_ticket_text(booking_id: str):
    """DELETE: Remove ticket text file"""
    path = os.path.join(TICKETS_DIR, f'ticket_{booking_id}.txt')
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Ticket file not found")
    os.remove(path)
    return {"success": True, "message": f"Ticket file deleted"}


@app.get("/api/tickets/image/{booking_id}", tags=["Ticket Images"])
def get_ticket_image_info(booking_id: str):
    """READ: Check if ticket image exists"""
    path = os.path.join(TICKETS_DIR, f'ticket_{booking_id}.png')
    exists = os.path.exists(path)
    return {"success": True, "data": {"booking_id": booking_id, "exists": exists, "path": path if exists else None}}

@app.post("/api/tickets/image/{booking_id}", tags=["Ticket Images"])
def create_ticket_image(booking_id: str):
    """CREATE: Generate ticket image with QR code"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import qrcode
    except ImportError:
        raise HTTPException(status_code=500, detail="PIL or qrcode not installed")

    bookings = load_bookings()
    booking = None
    for b in bookings:
        if b['booking_id'] == booking_id:
            booking = b
            break
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    trains = load_trains()
    train = trains.get(booking['train_id'])
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")

    W, H = 800, 400
    img = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype('arial.ttf', 24)
        label_font = ImageFont.truetype('arial.ttf', 16)
        small_font = ImageFont.truetype('arial.ttf', 12)
    except:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    d.text((20, 20), '🚂 BANGLADESH RAILWAY - TICKET', fill=(0, 0, 0), font=title_font)
    y = 70
    for label, value in [
        ('Booking ID', booking['booking_id']),
        ('Train', f"{train['id']} - {train['name']}"),
        ('Route', train['route']),
        ('Date', booking['date']),
        ('Coach/Seat', f"Coach {booking['coach']} - Seat {booking['seat']}"),
        ('Passenger', booking['name']),
        ('Phone', booking['phone']),
        ('Price', f"{booking['price']:.2f} Tk"),
        ('Status', booking['status'])
    ]:
        d.text((20, y), f"{label}: {value}", fill=(0, 0, 0), font=label_font)
        y += 28

    try:
        qr_data = f"TICKET|{booking['booking_id']}|{train['id']}|{booking['name']}|{booking['date']}"
        qr = qrcode.QRCode(version=4, box_size=6, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color='black', back_color='white').convert('RGB')
        qr_img = qr_img.resize((180, 180))
        img.paste(qr_img, (W - 200, 100))
    except:
        pass

    path = os.path.join(TICKETS_DIR, f'ticket_{booking_id}.png')
    img.save(path)
    return {"success": True, "message": "Ticket image created", "data": {"path": path}}

@app.put("/api/tickets/image/{booking_id}", tags=["Ticket Images"])
def update_ticket_image(booking_id: str):
    """UPDATE: Regenerate ticket image"""
    return create_ticket_image(booking_id)

@app.delete("/api/tickets/image/{booking_id}", tags=["Ticket Images"])
def delete_ticket_image(booking_id: str):
    """DELETE: Remove ticket image file"""
    path = os.path.join(TICKETS_DIR, f'ticket_{booking_id}.png')
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Ticket image not found")
    os.remove(path)
    return {"success": True, "message": "Ticket image deleted"}


def generate_group_ticket_text(phone: str, train_id: str = None, date: str = None) -> Optional[str]:
    """Generate group ticket text for all bookings by phone"""
    bookings = load_bookings()
    user_bookings = [b for b in bookings if b['phone'] == phone and b['status'] in ('BOOKED', 'PAID')]
    if train_id:
        user_bookings = [b for b in user_bookings if b['train_id'] == train_id]
    if date:
        user_bookings = [b for b in user_bookings if b['date'] == date]

    if not user_bookings:
        return None

    trains = load_trains()
    first = user_bookings[0]
    train = trains.get(first['train_id'])
    if not train:
        return None

    total = sum(b['price'] for b in user_bookings)
    seats = ', '.join([f"C{b['coach']}-S{b['seat']}" for b in sorted(user_bookings, key=lambda x: (x['coach'], x['seat']))])

    border = '=' * 70
    mid_border = '-' * 70
    lines = [
        border,
        '         🚂 BANGLADESH RAILWAY - GROUP TICKET 🚂',
        border,
        f"Passenger     : {first['name']}",
        f"Phone         : {first['phone']}",
        f"Train         : {train['id']} - {train['name']}",
        f"Route         : {train['route']}",
        f"Date          : {first['date']}",
        mid_border,
        f"Total Tickets : {len(user_bookings)}",
        f"Seats         : {seats}",
        f"Total Price   : {total:.2f} Tk",
        mid_border,
        'BOOKING DETAILS:',
        mid_border
    ]

    for b in user_bookings:
        lines.append(f"  {b['booking_id']} | Coach {b['coach']} Seat {b['seat']} | {b['price']:.2f} Tk | {b['status']}")

    lines.extend([
        mid_border,
        f"Issued        : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        border,
        'Thank you for choosing Bangladesh Railway!',
        border
    ])
    return '\n'.join(lines)

@app.get("/api/tickets/group/{phone}", tags=["Group Tickets"])
def get_group_ticket(phone: str, train_id: Optional[str] = None, date: Optional[str] = None):
    """READ: Get group ticket content"""
    content = generate_group_ticket_text(phone, train_id, date)
    if not content:
        raise HTTPException(status_code=404, detail="No bookings found")
    return {"success": True, "data": {"phone": phone, "content": content}}

@app.post("/api/tickets/group/{phone}", tags=["Group Tickets"])
def create_group_ticket(phone: str, train_id: Optional[str] = None, date: Optional[str] = None):
    """CREATE: Generate and save group ticket file"""
    content = generate_group_ticket_text(phone, train_id, date)
    if not content:
        raise HTTPException(status_code=404, detail="No bookings found")
    filename = f'ticket_{phone}_{date or "all"}.txt'
    path = os.path.join(TICKETS_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return {"success": True, "message": "Group ticket created", "data": {"path": path}}

@app.put("/api/tickets/group/{phone}", tags=["Group Tickets"])
def update_group_ticket(phone: str, train_id: Optional[str] = None, date: Optional[str] = None):
    """UPDATE: Regenerate group ticket file"""
    return create_group_ticket(phone, train_id, date)

@app.delete("/api/tickets/group/{phone}", tags=["Group Tickets"])
def delete_group_ticket(phone: str, date: Optional[str] = None):
    """DELETE: Remove group ticket file"""
    filename = f'ticket_{phone}_{date or "all"}.txt'
    path = os.path.join(TICKETS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Group ticket file not found")
    os.remove(path)
    return {"success": True, "message": "Group ticket deleted"}


@app.get("/api/stats", tags=["Statistics"])
def get_statistics():
    """READ: Get booking statistics"""
    trains = load_trains()
    bookings = load_bookings()

    total_bookings = len(bookings)
    booked = len([b for b in bookings if b['status'] == 'BOOKED'])
    paid = len([b for b in bookings if b['status'] == 'PAID'])
    cancelled = len([b for b in bookings if b['status'] == 'CANCELLED'])
    total_revenue = sum(b['price'] for b in bookings if b['status'] in ('BOOKED', 'PAID'))

    user_files = len([f for f in os.listdir(USERS_DIR) if f.endswith('.txt')])

    ticket_txt = len([f for f in os.listdir(TICKETS_DIR) if f.endswith('.txt')])
    ticket_img = len([f for f in os.listdir(TICKETS_DIR) if f.endswith('.png')])

    return {
        "success": True,
        "data": {
            "trains": len(trains),
            "total_bookings": total_bookings,
            "booked": booked,
            "paid": paid,
            "cancelled": cancelled,
            "total_revenue": total_revenue,
            "user_files": user_files,
            "ticket_text_files": ticket_txt,
            "ticket_image_files": ticket_img
        }
    }


@app.get("/", tags=["Info"])
def root():
    """API Welcome message"""
    return {
        "message": "🚂 Welcome to Bangladesh Railway API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "trains": "/api/trains",
            "bookings": "/api/bookings",
            "seats": "/api/seats/{train_id}/{date}/{coach}",
            "users": "/api/users/{phone}",
            "tickets_text": "/api/tickets/text/{booking_id}",
            "tickets_image": "/api/tickets/image/{booking_id}",
            "tickets_group": "/api/tickets/group/{phone}",
            "statistics": "/api/stats"
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("       🚂 BANGLADESH RAILWAY - API SERVER 🚂")
    print("=" * 60)
    print("Starting server at http://127.0.0.1:5000")
    print("API Documentation: http://127.0.0.1:5000/docs")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=5000)


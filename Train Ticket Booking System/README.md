# Bangladesh Railway - Ticket Booking System

A complete train ticket booking system with REST API backend and GUI frontend.

## Features

- **REST API Server** - All file operations through API endpoints
- **GUI Application** - Modern, user-friendly interface
- **Train Management** - Create, Read, Update, Delete trains
- **Booking System** - Book, Cancel, Pay for tickets
- **Ticket Generation** - Text and Image tickets with QR codes
- **User Files** - Per-user booking history
- **Search & Filter** - Find bookings easily

## File Structure

```
TrainBookingSystem/
├── api_server.py      # REST API server (FastAPI)
├── api_client.py      # API client module
├── main.py            # GUI application
├── requirements.txt   # Python dependencies
├── README.md          # This file
└── data/              # Data storage
    ├── trains.txt     # Train information
    ├── bookings.txt   # Booking records
    ├── users/         # User files
    └── tickets/       # Generated tickets
```

## Installation

1. Install Python 3.8+
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## How to Run

### Step 1: Start the API Server
```bash
cd TrainBookingSystem
uvicorn api_server:app --reload
```

The API will be available at: http://127.0.0.1:8000
API Documentation: http://127.0.0.1:8000/docs

### Step 2: Run the GUI Application
Open a new terminal:
```bash
cd TrainBookingSystem
python main.py
```

## API Endpoints Summary

### Trains (CRUD)
- `GET /api/trains` - List all trains
- `GET /api/trains/{id}` - Get train details
- `POST /api/trains` - Create train
- `PUT /api/trains/{id}` - Update train
- `DELETE /api/trains/{id}` - Delete train

### Bookings (CRUD)
- `GET /api/bookings` - List bookings
- `GET /api/bookings/{id}` - Get booking
- `POST /api/bookings` - Create booking
- `PUT /api/bookings/{id}` - Update status
- `PUT /api/bookings/cancel/{id}` - Cancel
- `PUT /api/bookings/pay/{id}` - Mark paid
- `DELETE /api/bookings/{id}` - Delete

### User Files (CRUD)
- `GET /api/users/{phone}` - Get user file
- `POST /api/users/{phone}` - Create user file
- `PUT /api/users/{phone}` - Update user file
- `DELETE /api/users/{phone}` - Delete user file

### Ticket Files (CRUD)
- `GET /api/tickets/text/{id}` - Get ticket text
- `POST /api/tickets/text/{id}` - Create ticket text
- `PUT /api/tickets/text/{id}` - Update ticket text
- `DELETE /api/tickets/text/{id}` - Delete ticket text

### Ticket Images (CRUD)
- `GET /api/tickets/image/{id}` - Get image info
- `POST /api/tickets/image/{id}` - Create image
- `PUT /api/tickets/image/{id}` - Update image
- `DELETE /api/tickets/image/{id}` - Delete image

### Group Tickets (CRUD)
- `GET /api/tickets/group/{phone}` - Get group ticket
- `POST /api/tickets/group/{phone}` - Create group ticket
- `PUT /api/tickets/group/{phone}` - Update group ticket
- `DELETE /api/tickets/group/{phone}` - Delete group ticket

### Statistics
- `GET /api/stats` - Get system statistics

## Data File Formats

### trains.txt
```
T001|Sundarban Express|Dhaka-Khulna|3|40|550
```
Format: ID|Name|Route|Coaches|SeatsPerCoach|Price

### bookings.txt
```
B00001|T001|2025-12-15|1|5|John Doe|01712345678|550.00|BOOKED
```
Format: BookingID|TrainID|Date|Coach|Seat|Name|Phone|Price|Status

### users/{phone}.txt
User booking history and updates

### tickets/ticket_{id}.txt
Generated ticket text files

### tickets/ticket_{id}.png
Generated ticket images with QR codes

## Requirements Summary

This project demonstrates:
- **8 API-based file operations** (Create, Read, Update, Delete)
- Each operation category has **2+ implementations**
- **User files** - Individual user data management
- **Ticket files** - Text and image generation
- **Complete CRUD** for trains, bookings, users, tickets

## License

Educational project - Bangladesh Railway Booking System


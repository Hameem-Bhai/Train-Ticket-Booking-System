
import requests
from typing import Optional, List, Dict, Any

class TrainAPIClient:


    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url
        self.timeout = 10

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:

        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"success": False, "message": "Not found", "data": None}
            elif response.status_code == 400:
                return {"success": False, "message": response.json().get("detail", "Bad request"), "data": None}
            else:
                return {"success": False, "message": f"Error: {response.status_code}", "data": None}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "API server not running. Start with: uvicorn api_server:app --reload", "data": None}
        except Exception as e:
            return {"success": False, "message": str(e), "data": None}



    def get_trains(self) -> List[Dict]:
        result = self._request("GET", "/api/trains")
        return result.get("data", []) if result.get("success") else []

    def get_train(self, train_id: str) -> Optional[Dict]:

        result = self._request("GET", f"/api/trains/{train_id}")
        return result.get("data") if result.get("success") else None

    def create_train(self, train_id: str, name: str, route: str, coaches: int, seats_per_coach: int, base_price: float) -> tuple:

        data = {
            "id": train_id,
            "name": name,
            "route": route,
            "coaches": coaches,
            "seats_per_coach": seats_per_coach,
            "base_price": base_price
        }
        result = self._request("POST", "/api/trains", json=data)
        return result.get("success", False), result.get("message", "Failed")

    def update_train(self, train_id: str, name: str = None, route: str = None,
                     coaches: int = None, seats_per_coach: int = None, base_price: float = None) -> tuple:

        data = {}
        if name is not None: data["name"] = name
        if route is not None: data["route"] = route
        if coaches is not None: data["coaches"] = coaches
        if seats_per_coach is not None: data["seats_per_coach"] = seats_per_coach
        if base_price is not None: data["base_price"] = base_price
        result = self._request("PUT", f"/api/trains/{train_id}", json=data)
        return result.get("success", False), result.get("message", "Failed")

    def delete_train(self, train_id: str) -> tuple:
        """DELETE: Remove a train"""
        result = self._request("DELETE", f"/api/trains/{train_id}")
        return result.get("success", False), result.get("message", "Failed")


    def get_bookings(self, train_id: str = None, date: str = None, phone: str = None) -> List[Dict]:

        params = {}
        if train_id: params["train_id"] = train_id
        if date: params["date"] = date
        if phone: params["phone"] = phone
        result = self._request("GET", "/api/bookings", params=params)
        return result.get("data", []) if result.get("success") else []

    def get_booking(self, booking_id: str) -> Optional[Dict]:

        result = self._request("GET", f"/api/bookings/{booking_id}")
        return result.get("data") if result.get("success") else None

    def book(self, train_id: str, date: str, coach: int, seat: int, name: str, phone: str) -> tuple:

        data = {
            "train_id": train_id,
            "date": date,
            "coach": coach,
            "seat": seat,
            "name": name,
            "phone": phone
        }
        result = self._request("POST", "/api/bookings", json=data)
        if result.get("success"):
            booking_id = result.get("data", {}).get("booking_id")
            return booking_id, None
        return None, result.get("message", "Failed")

    def cancel(self, booking_id: str) -> bool:

        result = self._request("PUT", f"/api/bookings/cancel/{booking_id}")
        return result.get("success", False)

    def mark_paid(self, booking_id: str) -> bool:

        result = self._request("PUT", f"/api/bookings/pay/{booking_id}")
        return result.get("success", False)

    def mark_paid_by_phone(self, train_id: str, date: str, phone: str) -> bool:

        bookings = self.get_bookings(train_id=train_id, date=date, phone=phone)
        success = False
        for b in bookings:
            if b['status'] == 'BOOKED':
                if self.mark_paid(b['booking_id']):
                    success = True
        return success

    def delete_booking(self, booking_id: str) -> tuple:

        result = self._request("DELETE", f"/api/bookings/{booking_id}")
        return result.get("success", False), result.get("message", "Failed")



    def get_available_seats(self, train_id: str, date: str, coach: int) -> List[Dict]:
        result = self._request("GET", f"/api/seats/{train_id}/{date}/{coach}")
        return result.get("data", []) if result.get("success") else []

    def list_available_seats(self, train_id: str, date: str, coach: int) -> List[Dict]:
        return self.get_available_seats(train_id, date, coach)



    def get_user_file(self, phone: str) -> Optional[str]:
        result = self._request("GET", f"/api/users/{phone}")
        if result.get("success"):
            return result.get("data", {}).get("content")
        return None

    def create_user_file(self, phone: str) -> tuple:
        result = self._request("POST", f"/api/users/{phone}")
        return result.get("success", False), result.get("message", "Failed")

    def update_user_file(self, phone: str) -> tuple:
        result = self._request("PUT", f"/api/users/{phone}")
        return result.get("success", False), result.get("message", "Failed")

    def delete_user_file(self, phone: str) -> tuple:
        result = self._request("DELETE", f"/api/users/{phone}")
        return result.get("success", False), result.get("message", "Failed")




    def get_ticket_text(self, booking_id: str) -> Optional[str]:
        result = self._request("GET", f"/api/tickets/text/{booking_id}")
        if result.get("success"):
            return result.get("data", {}).get("content")
        return None

    def create_ticket_text_file(self, booking_id: str) -> Optional[str]:

        result = self._request("POST", f"/api/tickets/text/{booking_id}")
        if result.get("success"):
            return result.get("data", {}).get("path")
        return None

    def update_ticket_text_file(self, booking_id: str) -> Optional[str]:

        result = self._request("PUT", f"/api/tickets/text/{booking_id}")
        if result.get("success"):
            return result.get("data", {}).get("path")
        return None

    def delete_ticket_text_file(self, booking_id: str) -> bool:
        result = self._request("DELETE", f"/api/tickets/text/{booking_id}")
        return result.get("success", False)

    def save_ticket_file(self, booking_id: str, directory: str = None, **kwargs) -> Optional[str]:
        return self.create_ticket_text_file(booking_id)

    def generate_ticket_text(self, booking_id: str, **kwargs) -> Optional[str]:
        return self.get_ticket_text(booking_id)


    def get_ticket_image_info(self, booking_id: str) -> Dict:
        result = self._request("GET", f"/api/tickets/image/{booking_id}")
        return result.get("data", {}) if result.get("success") else {}

    def create_ticket_image_file(self, booking_id: str) -> Optional[str]:
        result = self._request("POST", f"/api/tickets/image/{booking_id}")
        if result.get("success"):
            return result.get("data", {}).get("path")
        return None

    def update_ticket_image_file(self, booking_id: str) -> Optional[str]:
        result = self._request("PUT", f"/api/tickets/image/{booking_id}")
        if result.get("success"):
            return result.get("data", {}).get("path")
        return None

    def delete_ticket_image_file(self, booking_id: str) -> bool:
        result = self._request("DELETE", f"/api/tickets/image/{booking_id}")
        return result.get("success", False)

    def save_ticket_image(self, booking_id: str, directory: str = None, **kwargs) -> Optional[str]:
        return self.create_ticket_image_file(booking_id)




    def get_group_ticket(self, phone: str, train_id: str = None, date: str = None) -> Optional[str]:
        params = {}
        if train_id: params["train_id"] = train_id
        if date: params["date"] = date
        result = self._request("GET", f"/api/tickets/group/{phone}", params=params)
        if result.get("success"):
            return result.get("data", {}).get("content")
        return None

    def create_group_ticket(self, phone: str, train_id: str = None, date: str = None) -> Optional[str]:
        params = {}
        if train_id: params["train_id"] = train_id
        if date: params["date"] = date
        result = self._request("POST", f"/api/tickets/group/{phone}", params=params)
        if result.get("success"):
            return result.get("data", {}).get("path")
        return None

    def update_group_ticket(self, phone: str, train_id: str = None, date: str = None) -> Optional[str]:
        params = {}
        if train_id: params["train_id"] = train_id
        if date: params["date"] = date
        result = self._request("PUT", f"/api/tickets/group/{phone}", params=params)
        if result.get("success"):
            return result.get("data", {}).get("path")
        return None

    def delete_group_ticket(self, phone: str, date: str = None) -> bool:
        params = {}
        if date: params["date"] = date
        result = self._request("DELETE", f"/api/tickets/group/{phone}", params=params)
        return result.get("success", False)

    def save_aggregated_ticket(self, phone: str, directory: str = None, train_id: str = None, date: str = None, **kwargs) -> Optional[str]:
        return self.create_group_ticket(phone, train_id, date)

    def generate_aggregated_ticket_text(self, phone: str, train_id: str = None, date: str = None, **kwargs) -> Optional[str]:
        return self.get_group_ticket(phone, train_id, date)

    def save_aggregated_ticket_image(self, phone: str, directory: str = None, train_id: str = None, date: str = None, **kwargs) -> Optional[str]:
        return None


    def get_statistics(self) -> Dict:
        result = self._request("GET", "/api/stats")
        return result.get("data", {}) if result.get("success") else {}


    def list_bookings(self, train_id: str = None, date: str = None) -> List[Dict]:
        return self.get_bookings(train_id=train_id, date=date)

    def list_bookings_by_phone(self, phone: str, train_id: str = None, date: str = None) -> List[Dict]:
        bookings = self.get_bookings(train_id=train_id, date=date, phone=phone)
        return bookings

    def list_bookings_by_name(self, name: str, train_id: str = None, date: str = None) -> List[Dict]:
        bookings = self.get_bookings(train_id=train_id, date=date)
        return [b for b in bookings if b['name'].lower() == name.lower()]

    def list_all_bookings(self) -> List[Dict]:
        return self.get_bookings()

    def check_api_connection(self) -> bool:
        result = self._request("GET", "/")
        return result.get("message") is not None and "Railway" in str(result.get("message", ""))




if __name__ == "__main__":
    print("=" * 60)
    print("       🚂 BANGLADESH RAILWAY - API CLIENT TEST")
    print("=" * 60)

    client = TrainAPIClient()

    if client.check_api_connection():
        print("✓ Connected to API server")
        print("\nTrains available:")
        for t in client.get_trains():
            print(f"  - {t['id']}: {t['name']} ({t['route']})")
    else:
        print("✗ Cannot connect to API server")
        print("  Start it with: uvicorn api_server:app --reload")


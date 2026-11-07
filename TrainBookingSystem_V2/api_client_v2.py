import requests
from typing import Optional, List, Dict, Any

class TrainAPIClientV2:

    def __init__(self, base_url: str = "http://127.0.0.1:5001"):
        self.base_url = base_url
        self.timeout = 10
        self.token = None

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"

        headers = kwargs.get('headers', {})
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        kwargs['headers'] = headers

        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"success": False, "message": "Not found", "data": None}
            elif response.status_code in (400, 401, 403):
                return {"success": False, "message": response.json().get("detail", "Error"), "data": None}
            else:
                return {"success": False, "message": f"Error: {response.status_code}", "data": None}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "API V2 server not running. Start with: python api_server_v2.py", "data": None}
        except Exception as e:
            return {"success": False, "message": str(e), "data": None}

    def register(self, username: str, password: str, email: str, phone: str, full_name: str) -> tuple:
        data = {
            "username": username,
            "password": password,
            "email": email,
            "phone": phone,
            "full_name": full_name
        }
        result = self._request("POST", "/api/v2/auth/register", json=data)
        return result.get("success", False), result.get("message", "Failed")

    def login(self, username: str, password: str) -> tuple:
        data = {"username": username, "password": password}
        result = self._request("POST", "/api/v2/auth/login", json=data)

        if result.get("success"):
            self.token = result.get("token")
            return True, result.get("user")
        return False, result.get("message", "Login failed")

    def register_email(self, email: str, password: str, phone: str, full_name: str) -> tuple:
        data = {"email": email, "password": password, "phone": phone, "full_name": full_name}
        result = self._request("POST", "/api/v2/auth/register-email", json=data)
        return result.get("success", False), result.get("message", "Failed")

    def verify_email(self, email: str, code: str) -> tuple:
        data = {"email": email, "code": code}
        result = self._request("POST", "/api/v2/auth/verify-email", json=data)
        return result.get("success", False), result.get("message", "Failed")

    def login_email(self, email: str, password: str) -> tuple:
        data = {"email": email, "password": password}
        result = self._request("POST", "/api/v2/auth/login-email", json=data)
        if result.get("success"):
            self.token = result.get("token")
            return True, result.get("user")
        return False, result.get("message", "Login failed")

    def send_login_code(self, email: str) -> tuple:
        data = {"email": email}
        result = self._request("POST", "/api/v2/auth/send-login-code", json=data)
        return result.get("success", False), result.get("message", "Failed"), result.get("code")

    def login_with_code(self, email: str, code: str) -> tuple:
        data = {"email": email, "code": code}
        result = self._request("POST", "/api/v2/auth/login-code", json=data)
        if result.get("success"):
            self.token = result.get("token")
            return True, result.get("user")
        return False, result.get("message", "Login failed")

    def get_profile(self) -> Optional[Dict]:
        if not self.token:
            return None
        result = self._request("GET", "/api/v2/auth/profile")
        return result.get("data") if result.get("success") else None

    def get_booking_history(self) -> List[Dict]:
        if not self.token:
            return []
        result = self._request("GET", "/api/v2/auth/booking-history")
        return result.get("data", []) if result.get("success") else []

    def book_round_trip(self, train_id_onward: str, train_id_return: str,
                        date_onward: str, date_return: str, coach: int,
                        seats: List[int], name: str, phone: str) -> tuple:
        if not self.token:
            return None, "Not logged in"

        data = {
            "train_id_onward": train_id_onward,
            "train_id_return": train_id_return,
            "date_onward": date_onward,
            "date_return": date_return,
            "coach": coach,
            "seats": seats,
            "name": name,
            "phone": phone
        }
        result = self._request("POST", "/api/v2/bookings/round-trip", json=data)

        if result.get("success"):
            return result.get("data", {}).get("booking_ids"), None
        return None, result.get("message", "Failed")

    def request_refund(self, booking_id: str, reason: str) -> tuple:
        if not self.token:
            return None, "Not logged in"

        data = {"booking_id": booking_id, "reason": reason}
        result = self._request("POST", "/api/v2/refunds/request", json=data)

        if result.get("success"):
            return result.get("data"), None
        return None, result.get("message", "Failed")

    def get_refund_status(self, refund_id: str) -> Optional[Dict]:
        if not self.token:
            return None
        result = self._request("GET", f"/api/v2/refunds/status/{refund_id}")
        return result.get("data") if result.get("success") else None

    def get_train_schedule(self, train_id: str) -> Optional[Dict]:
        result = self._request("GET", f"/api/v2/schedules/{train_id}")
        return result.get("data") if result.get("success") else None

    def update_train_delay(self, train_id: str, delay_minutes: int) -> bool:
        result = self._request("PUT", f"/api/v2/schedules/{train_id}/delay",
                               params={"delay_minutes": delay_minutes})
        return result.get("success", False)

    def get_revenue_report(self, start_date: str, end_date: str) -> Optional[Dict]:
        result = self._request("GET", "/api/v2/reports/revenue",
                               params={"start_date": start_date, "end_date": end_date})
        return result.get("data") if result.get("success") else None

    def get_occupancy_report(self, train_id: str, date: str) -> Optional[Dict]:
        result = self._request("GET", "/api/v2/reports/occupancy",
                               params={"train_id": train_id, "date": date})
        return result.get("data") if result.get("success") else None

    def get_popular_routes(self) -> Optional[Dict]:
        result = self._request("GET", "/api/v2/reports/popular-routes")
        return result.get("data") if result.get("success") else None

    def send_journey_reminder(self, booking_id: str) -> bool:
        result = self._request("POST", "/api/v2/notifications/send-reminder",
                               params={"booking_id": booking_id})
        return result.get("success", False)

    def get_trains(self) -> List[Dict]:
        """Get list of all available trains"""
        result = self._request("GET", "/api/v2/trains")
        return result.get("data", []) if result.get("success") else []

    def add_train(self, train_id: str, name: str, route: str, coaches: int,
                  seats_per_coach: int, base_price: float) -> tuple:
        """Add a new train (admin only)"""
        if not self.token:
            return False, "Not logged in"

        data = {
            "train_id": train_id,
            "name": name,
            "route": route,
            "coaches": coaches,
            "seats_per_coach": seats_per_coach,
            "base_price": base_price
        }
        result = self._request("POST", "/api/v2/trains", json=data)
        return result.get("success", False), result.get("message", "Failed")

    def delete_train(self, train_id: str) -> tuple:
        """Delete a train (admin only)"""
        if not self.token:
            return False, "Not logged in"

        result = self._request("DELETE", f"/api/v2/trains/{train_id}")
        return result.get("success", False), result.get("message", "Failed")

    def update_train(self, train_id: str, **kwargs) -> tuple:
        """Update train details (admin only)"""
        if not self.token:
            return False, "Not logged in"

        result = self._request("PUT", f"/api/v2/trains/{train_id}", json=kwargs)
        return result.get("success", False), result.get("message", "Failed")

    def check_api_connection(self) -> bool:
        result = self._request("GET", "/")
        return result.get("message") is not None and "V2" in str(result.get("message", ""))

    def get_seat_availability(self, train_id: str, date: str, coach: int) -> List[int]:
        """Get list of booked seats for given train/date/coach"""
        result = self._request("GET", "/api/v2/availability",
                               params={"train_id": train_id, "date": date, "coach": coach})
        if result.get("success"):
            data = result.get("data", {})
            return data.get("booked_seats", [])
        return []

    def book_single(self, train_id: str, date: str, coach: int, seat: int,
                    name: str, phone: str) -> tuple:
        if not self.token:
            return None, "Not logged in"
        data = {
            "train_id": train_id,
            "date": date,
            "coach": coach,
            "seat": seat,
            "name": name,
            "phone": phone
        }
        result = self._request("POST", "/api/v2/bookings/single", json=data)
        if result.get("success"):
            return result.get("data", {}).get("booking_id"), None
        return None, result.get("message", "Failed")

    def book_batch(self, train_id: str, date: str, coach: int, seats: List[int],
                   name: str, phone: str) -> tuple:
        if not self.token:
            return None, "Not logged in"
        data = {
            "train_id": train_id,
            "date": date,
            "coach": coach,
            "seats": seats,
            "name": name,
            "phone": phone
        }
        result = self._request("POST", "/api/v2/bookings/batch", json=data)
        if result.get("success"):
            return result.get("data", {}).get("booking_ids"), None
        return None, result.get("message", "Failed")


if __name__ == "__main__":
    print("=" * 60)
    print("    🚂 BANGLADESH RAILWAY - API CLIENT V2 TEST")
    print("=" * 60)

    client = TrainAPIClientV2()

    if client.check_api_connection():
        print("✓ Connected to API V2 server")
        print("\nTesting registration...")
        success, msg = client.register("testuser", "password123", "test@example.com", "01700000000", "Test User")
        print(f"Register: {msg}")

        print("\nTesting login...")
        success, user = client.login("testuser", "password123")
        if success:
            print(f"✓ Logged in as: {user}")
        else:
            print(f"✗ Login failed: {user}")
    else:
        print("✗ Cannot connect to API V2 server")
        print("  Start it with: python api_server_v2.py")

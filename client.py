import urllib.request
import urllib.parse
import json
from getpass import getpass

BASE_URL = "http://localhost/RESTAPITASK/service.php"

current_user_id = None
current_token = None
current_user = None


def main():
    print_banner()
    while True:
        if current_user_id is None:
            show_guest_menu()
        else:
            show_dashboard_menu()


def show_guest_menu():
    print("\n┌─────────────────────────────────┐")
    print("│         AUTOTRACK  MENU          │")
    print("├─────────────────────────────────┤")
    print("│  [1] Register                    │")
    print("│  [2] Login                       │")
    print("│  [0] Exit                        │")
    print("└─────────────────────────────────┘")
    choice = input("Choice: ").strip()

    if choice == "1":
        do_register()
    elif choice == "2":
        do_login()
    elif choice == "0":
        print("Goodbye!")
        exit(0)
    else:
        print("[!] Invalid option.")


def show_dashboard_menu():
    print("\n┌─────────────────────────────────┐")
    print(f"│  Logged in as: {current_user:<17} │")
    print("├─────────────────────────────────┤")
    print("│  [1] List My Cars                │")
    print("│  [2] Add Car                     │")
    print("│  [3] Update Car (brand/model)    │")
    print("│  [4] Update Car Location         │")
    print("│  [5] Delete Car                  │")
    print("│  [6] Logout                      │")
    print("│  [0] Exit                        │")
    print("└─────────────────────────────────┘")
    choice = input("Choice: ").strip()

    if choice == "1":
        do_get_cars()
    elif choice == "2":
        do_add_car()
    elif choice == "3":
        do_update_car()
    elif choice == "4":
        do_update_location()
    elif choice == "5":
        do_delete_car()
    elif choice == "6":
        do_logout()
    elif choice == "0":
        print("Goodbye!")
        exit(0)
    else:
        print("[!] Invalid option.")


def do_register():
    global current_user_id, current_token, current_user
    print("\n── REGISTER ──")
    username = input("Username : ").strip()
    password = input("Password : ").strip()
    email    = input("Email    : ").strip()

    if not username or not password or not email:
        print("[!] All fields are required.")
        return

    response = post("register", {"username": username, "password": password, "email": email})
    status   = response.get("status")
    message  = response.get("message", "")

    if status == "success":
        print(f"[✓] {message}")
    else:
        print(f"[!] {message}")


def do_login():
    global current_user_id, current_token, current_user
    print("\n── LOGIN ──")
    username = input("Username : ").strip()
    password = input("Password : ").strip()

    response = post("login", {"username": username, "password": password})
    status   = response.get("status")
    message  = response.get("message", "")

    if status == "success":
        current_user_id = str(response.get("user_id", ""))
        current_token   = response.get("token", "")
        current_user    = username
        print(f"[✓] {message}")
        print(f"    Token : {current_token}")
    else:
        print(f"[!] {message}")


def do_logout():
    global current_user_id, current_token, current_user
    response = post("logout", {"user_id": current_user_id})
    message  = response.get("message", "Logged out.")
    print(f"[✓] {message}")
    current_user_id = None
    current_token   = None
    current_user    = None


def do_get_cars():
    params   = urllib.parse.urlencode({"action": "getCars", "user_id": current_user_id, "token": current_token})
    url      = f"{BASE_URL}?{params}"
    response = get(url)
    status   = response.get("status")

    if status != "success":
        print(f"[!] {response.get('message', 'Unknown error.')}")
        return

    data = response.get("data", [])
    if not data:
        print("[i] No cars registered yet.")
        return

    print(f"\n── YOUR CARS ({len(data)}) ──")
    print(f"{'ID':<6} {'PLATE':<14} {'BRAND':<12} {'MODEL':<16} {'LOCATION':<30} {'LAST UPDATED':<22}")
    print("─" * 104)

    for car in data:
        print(
            f"{str(car.get('car_id','')):<6} "
            f"{car.get('plate_number',''):<14} "
            f"{car.get('brand',''):<12} "
            f"{car.get('model',''):<16} "
            f"{car.get('location',''):<30} "
            f"{car.get('last_updated',''):<22}"
        )


def do_add_car():
    print("\n── ADD CAR ──")
    plate = input("Plate Number : ").strip()
    brand = input("Brand        : ").strip()
    model = input("Model        : ").strip()

    if not plate or not brand or not model:
        print("[!] All fields are required.")
        return

    response = post("addCar", {
        "user_id":      current_user_id,
        "token":        current_token,
        "plate_number": plate,
        "brand":        brand,
        "model":        model,
    })
    print_result(response)


def do_update_car():
    print("\n── UPDATE CAR (brand / model) ──")
    car_id = input("Car ID : ").strip()
    brand  = input("Brand  : ").strip()
    model  = input("Model  : ").strip()

    if not car_id or not brand or not model:
        print("[!] All fields are required.")
        return

    response = post("updateCar", {"car_id": car_id, "brand": brand, "model": model})
    print_result(response)


def do_update_location():
    print("\n── UPDATE LOCATION ──")
    car_id   = input("Car ID      : ").strip()
    location = input("New Location: ").strip()

    if not car_id or not location:
        print("[!] Car ID and location are required.")
        return

    response = post("updateLocation", {"car_id": car_id, "location": location})
    status   = response.get("status")

    if status == "success":
        print(f"[✓] Location updated → {response.get('location', location)}")
    else:
        print(f"[!] {response.get('message', 'Unknown error.')}")


def do_delete_car():
    print("\n── DELETE CAR ──")
    car_id = input("Car ID (confirm delete): ").strip()

    if not car_id:
        print("[!] Car ID required.")
        return

    confirm = input("Are you sure? (yes/no): ").strip()
    if confirm.lower() != "yes":
        print("[i] Cancelled.")
        return

    response = post("deleteCar", {"car_id": car_id})
    print_result(response)


def post(action, fields):
    try:
        params  = urllib.parse.urlencode({"action": action})
        url     = f"{BASE_URL}?{params}"
        data    = urllib.parse.urlencode(fields).encode("utf-8")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        req     = urllib.request.Request(url, data=data, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        return {"status": "error", "message": f"Cannot connect to server: {e}"}


def get(url):
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        return {"status": "error", "message": f"Cannot connect to server: {e}"}


def print_result(response):
    status  = response.get("status")
    message = response.get("message", "")
    print(f"[✓] {message}" if status == "success" else f"[!] {message}")


def print_banner():
    print("╔══════════════════════════════════════╗")
    print("║   AUTOTRACK — Car Registration &     ║")
    print("║          Tracking System             ║")
    print("║          Python Console Client       ║")
    print("╚══════════════════════════════════════╝")
    print(f"  API → {BASE_URL}")


if __name__ == "__main__":
    main()

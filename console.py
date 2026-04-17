import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://localhost/RESTAPITASK/service.php"

# Global state variables
user_id = None
token = None
username = None

def main():
    banner()
    while True:
        if user_id is None:
            guest_menu()
        else:
            dashboard()

# ─── MENUS ────────────────────────────────────────────────────────────────────

def guest_menu():
    print("\n=========================================")
    print("            GUEST PORTAL                 ")
    print("=========================================")
    print("  [1] Register New Account")
    print("  [2] Secure Login")
    print("  [0] Exit System")
    print("-----------------------------------------")
    
    choice = input("  [?] Select an option: ").strip()
    
    if choice == "1":
        register()
    elif choice == "2":
        login()
    elif choice == "0":
        print("\n[*] Shutting down AutoTrack. Goodbye!")
        sys.exit(0)
    else:
        print("\n[!] Invalid choice. Please try again.")

def dashboard():
    print("\n=========================================")
    print(f"  DASHBOARD          User: {username:<12}")
    print("=========================================")
    print("  [1] View Fleet / Cars")
    print("  [2] Register New Car")
    print("  [3] Edit Car Details")
    print("  [4] Update Car Location")
    print("  [5] Delete Car")
    print("  [6] Logout")
    print("  [0] Exit System")
    print("-----------------------------------------")
    
    choice = input("  [?] Select an action: ").strip()
    
    if choice == "1": view_cars()
    elif choice == "2": add_car()
    elif choice == "3": update_car()
    elif choice == "4": update_location()
    elif choice == "5": delete_car()
    elif choice == "6": logout()
    elif choice == "0":
        print("\n[*] Shutting down AutoTrack. Goodbye!")
        sys.exit(0)
    else:
        print("\n[!] Invalid choice. Please try again.")

# ─── FEATURES ─────────────────────────────────────────────────────────────────

def register():
    print("\n--- REGISTRATION ---")
    u = input("  [?] Username : ")
    p = input("  [?] Password : ")
    e = input("  [?] Email    : ")

    body = {"username": u, "password": p, "email": e}
    res_str = post("register", body)
    res = parse_json(res_str)
    print(f"\n[*] {res.get('message', 'Unknown response')}")

def login():
    global user_id, token, username
    print("\n--- SYSTEM LOGIN ---")
    u = input("  [?] Username : ")
    p = input("  [?] Password : ")

    res_str = post("login", {"username": u, "password": p})
    res = parse_json(res_str)

    if res.get("status") == "success":
        user_id = str(res.get("user_id"))
        token = str(res.get("token"))
        username = u
        print(f"\n[+] Login successful! Welcome back, {username}.")
    else:
        print(f"\n[!] Error: {res.get('message', 'Login failed.')}")

def logout():
    global user_id, token, username
    post("logout", {"user_id": user_id})
    user_id = token = username = None
    print("\n[-] You have been securely logged out.")

def view_cars():
    url = f"{BASE_URL}?action=getCars&user_id={enc(user_id)}&token={enc(token)}"
    res_str = get(url)
    res = parse_json(res_str)

    if res.get("status") != "success":
        print(f"\n[!] Error: {res.get('message', 'Failed to fetch cars.')}")
        return

    cars = res.get("data", [])
    if not cars:
        print("\n[*] No cars found in your fleet.")
        return

    total = len(cars)
    unknown = 0

    print("\n=========================================================================")
    print("| ID  | PLATE      | BRAND      | MODEL      | LOCATION               |")
    print("=========================================================================")

    for c in cars:
        loc = c.get("location")
        if not loc or not str(loc).strip():
            loc = "Unknown"
            unknown += 1
            
        # Format strings equivalent to printf %-10s
        c_id = str(c.get("car_id", ""))
        plate = str(c.get("plate_number", ""))
        brand = str(c.get("brand", ""))
        model = str(c.get("model", ""))
        
        print(f"| {c_id:<3} | {plate:<10} | {brand:<10} | {model:<10} | {loc:<22} |")
        
    print("=========================================================================")
    print(f"  Fleet Overview: {total} Total | {total - unknown} Tracked | {unknown} Unknown Location")

def add_car():
    print("\n--- REGISTER NEW CAR ---")
    p = input("  [?] Plate Number : ")
    b = input("  [?] Brand        : ")
    m = input("  [?] Model        : ")

    body = {
        "user_id": user_id, "token": token,
        "plate_number": p, "brand": b, "model": m
    }
    res_str = post("addCar", body)
    print(f"\n[*] {parse_json(res_str).get('message', '')}")

def update_car():
    print("\n--- EDIT CAR DETAILS ---")
    car_id = input("  [?] Target Car ID : ")
    b = input("  [?] New Brand     : ")
    m = input("  [?] New Model     : ")

    body = {"car_id": car_id, "brand": b, "model": m}
    res_str = post("updateCar", body)
    print(f"\n[*] {parse_json(res_str).get('message', '')}")

def update_location():
    print("\n--- UPDATE LOCATION ---")
    car_id = input("  [?] Target Car ID : ")
    loc = input("  [?] New Location  : ")

    body = {"car_id": car_id, "location": loc}
    res_str = post("updateLocation", body)
    print(f"\n[*] {parse_json(res_str).get('message', '')}")

def delete_car():
    print("\n--- DELETE CAR ---")
    car_id = input("  [?] Target Car ID : ")

    res_str = post("deleteCar", {"car_id": car_id})
    print(f"\n[*] {parse_json(res_str).get('message', '')}")

# ─── HTTP & HELPERS ───────────────────────────────────────────────────────────

def post(action, data):
    try:
        url = f"{BASE_URL}?action={action}"
        # URL encode the dictionary data natively
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        
        req = urllib.request.Request(url, data=encoded_data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"\n[DEBUG] POST error: {e}")
        return '{"status":"error","message":"Server error"}'

def get(url):
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"\n[DEBUG] GET error: {e}")
        return '{"status":"error"}'

def parse_json(json_str):
    """Safely handles the string-to-dictionary conversion"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {}

def enc(s):
    """URL encodes a string safely"""
    return urllib.parse.quote(str(s))

def banner():
    print("\n" +
          "    ___         __        __               __  \n" +
          "   /   | __  __/ /_____  / /_  _________  / /__\n" +
          "  / /| |/ / / / __/ __ \\/ __ \\/ ___/ __ \\/ //_/\n" +
          " / ___ / /_/ / /_/ /_/ / / / / /__/ /_/ / ,<   \n" +
          "/_/  |_\\__,_/\\__/\\____/_/ /_/\\___/\\____/_/|_|  \n" +
          "                                               ")

if __name__ == "__main__":
    main()
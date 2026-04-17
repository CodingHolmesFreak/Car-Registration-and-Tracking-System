import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Scanner;

public class client {

    private static final String BASE_URL = "http://localhost/adet/service.php";

    private static String currentUserId = null;
    private static String currentToken  = null;
    private static String currentUser   = null;

    private static final HttpClient http    = HttpClient.newHttpClient();
    private static final Scanner    scanner = new Scanner(System.in);

    public static void main(String[] args) {
        printBanner();
        while (true) {
            if (currentUserId == null) {
                showGuestMenu();
            } else {
                showDashboardMenu();
            }
        }
    }

    private static void showGuestMenu() {
        System.out.println("\n┌─────────────────────────────────┐");
        System.out.println("│         AUTOTRACK  MENU          │");
        System.out.println("├─────────────────────────────────┤");
        System.out.println("│  [1] Register                    │");
        System.out.println("│  [2] Login                       │");
        System.out.println("│  [0] Exit                        │");
        System.out.println("└─────────────────────────────────┘");
        System.out.print("Choice: ");

        String choice = scanner.nextLine().trim();
        switch (choice) {
            case "1" -> doRegister();
            case "2" -> doLogin();
            case "0" -> { System.out.println("Goodbye!"); System.exit(0); }
            default  -> System.out.println("[!] Invalid option.");
        }
    }

    private static void showDashboardMenu() {
        System.out.println("\n┌─────────────────────────────────┐");
        System.out.printf( "│  Logged in as: %-17s │%n", currentUser);
        System.out.println("├─────────────────────────────────┤");
        System.out.println("│  [1] List My Cars                │");
        System.out.println("│  [2] Add Car                     │");
        System.out.println("│  [3] Update Car (brand/model)    │");
        System.out.println("│  [4] Update Car Location         │");
        System.out.println("│  [5] Delete Car                  │");
        System.out.println("│  [6] Logout                      │");
        System.out.println("│  [0] Exit                        │");
        System.out.println("└─────────────────────────────────┘");
        System.out.print("Choice: ");

        String choice = scanner.nextLine().trim();
        switch (choice) {
            case "1" -> doGetCars();
            case "2" -> doAddCar();
            case "3" -> doUpdateCar();
            case "4" -> doUpdateLocation();
            case "5" -> doDeleteCar();
            case "6" -> doLogout();
            case "0" -> { System.out.println("Goodbye!"); System.exit(0); }
            default  -> System.out.println("[!] Invalid option.");
        }
    }

    private static void doRegister() {
        System.out.println("\n── REGISTER ──");
        System.out.print("Username : "); String username = scanner.nextLine().trim();
        System.out.print("Password : "); String password = scanner.nextLine().trim();
        System.out.print("Email    : "); String email    = scanner.nextLine().trim();

        if (username.isEmpty() || password.isEmpty() || email.isEmpty()) {
            System.out.println("[!] All fields are required."); return;
        }

        Map<String, String> body = new LinkedHashMap<>();
        body.put("username", username);
        body.put("password", password);
        body.put("email",    email);

        String response = post("register", body);
        String message  = extractField(response, "message");
        String status   = extractField(response, "status");

        if ("success".equals(status)) {
            System.out.println("[✓] " + message);
        } else {
            System.out.println("[!] " + message);
        }
    }

    private static void doLogin() {
        System.out.println("\n── LOGIN ──");
        System.out.print("Username : "); String username = scanner.nextLine().trim();
        System.out.print("Password : "); String password = scanner.nextLine().trim();

        Map<String, String> body = new LinkedHashMap<>();
        body.put("username", username);
        body.put("password", password);

        String response = post("login", body);
        String status   = extractField(response, "status");
        String message  = extractField(response, "message");

        if ("success".equals(status)) {
            currentUserId = extractField(response, "user_id");
            currentToken  = extractField(response, "token");
            currentUser   = username;
            System.out.println("[✓] " + message);
            System.out.println("    Token : " + currentToken);
        } else {
            System.out.println("[!] " + message);
        }
    }

    private static void doLogout() {
        Map<String, String> body = new LinkedHashMap<>();
        body.put("user_id", currentUserId);

        String response = post("logout", body);
        String message  = extractField(response, "message");
        System.out.println("[✓] " + message);

        currentUserId = null;
        currentToken  = null;
        currentUser   = null;
    }

    private static void doGetCars() {
        String url      = BASE_URL + "?action=getCars&user_id=" + enc(currentUserId) + "&token=" + enc(currentToken);
        String response = get(url);
        String status   = extractField(response, "status");

        if (!"success".equals(status)) {
            System.out.println("[!] " + extractField(response, "message")); return;
        }

        // Parse the "data" array manually
        String data = extractArray(response, "data");
        if (data == null || data.isBlank()) {
            System.out.println("[i] No cars registered yet."); return;
        }

        String[] objects = splitJsonObjects(data);
        System.out.println("\n── YOUR CARS (" + objects.length + ") ──");
        System.out.printf("%-6s %-14s %-12s %-16s %-30s %-22s%n",
                "ID", "PLATE", "BRAND", "MODEL", "LOCATION", "LAST UPDATED");
        System.out.println("─".repeat(104));

        for (String obj : objects) {
            System.out.printf("%-6s %-14s %-12s %-16s %-30s %-22s%n",
                    extractField(obj, "car_id"),
                    extractField(obj, "plate_number"),
                    extractField(obj, "brand"),
                    extractField(obj, "model"),
                    extractField(obj, "location"),
                    extractField(obj, "last_updated"));
        }
    }

    private static void doAddCar() {
        System.out.println("\n── ADD CAR ──");
        System.out.print("Plate Number : "); String plate = scanner.nextLine().trim();
        System.out.print("Brand        : "); String brand = scanner.nextLine().trim();
        System.out.print("Model        : "); String model = scanner.nextLine().trim();

        if (plate.isEmpty() || brand.isEmpty() || model.isEmpty()) {
            System.out.println("[!] All fields are required."); return;
        }

        Map<String, String> body = new LinkedHashMap<>();
        body.put("user_id",      currentUserId);
        body.put("token",        currentToken);
        body.put("plate_number", plate);
        body.put("brand",        brand);
        body.put("model",        model);

        String response = post("addCar", body);
        printResult(response);
    }

    private static void doUpdateCar() {
        System.out.println("\n── UPDATE CAR (brand / model) ──");
        System.out.print("Car ID : "); String carId = scanner.nextLine().trim();
        System.out.print("Brand  : "); String brand = scanner.nextLine().trim();
        System.out.print("Model  : "); String model = scanner.nextLine().trim();

        if (carId.isEmpty() || brand.isEmpty() || model.isEmpty()) {
            System.out.println("[!] All fields are required."); return;
        }

        Map<String, String> body = new LinkedHashMap<>();
        body.put("car_id", carId);
        body.put("brand",  brand);
        body.put("model",  model);

        String response = post("updateCar", body);
        printResult(response);
    }

    private static void doUpdateLocation() {
        System.out.println("\n── UPDATE LOCATION ──");
        System.out.print("Car ID      : "); String carId    = scanner.nextLine().trim();
        System.out.print("New Location: "); String location = scanner.nextLine().trim();

        if (carId.isEmpty() || location.isEmpty()) {
            System.out.println("[!] Car ID and location are required."); return;
        }

        Map<String, String> body = new LinkedHashMap<>();
        body.put("car_id",   carId);
        body.put("location", location);

        String response = post("updateLocation", body);
        String status   = extractField(response, "status");
        if ("success".equals(status)) {
            System.out.println("[✓] Location updated → " + extractField(response, "location"));
        } else {
            System.out.println("[!] " + extractField(response, "message"));
        }
    }

    private static void doDeleteCar() {
        System.out.println("\n── DELETE CAR ──");
        System.out.print("Car ID (confirm delete): "); String carId = scanner.nextLine().trim();

        if (carId.isEmpty()) { System.out.println("[!] Car ID required."); return; }

        System.out.print("Are you sure? (yes/no): ");
        if (!"yes".equalsIgnoreCase(scanner.nextLine().trim())) {
            System.out.println("[i] Cancelled."); return;
        }

        Map<String, String> body = new LinkedHashMap<>();
        body.put("car_id", carId);

        String response = post("deleteCar", body);
        printResult(response);
    }

    private static String post(String action, Map<String, String> fields) {
        try {
            StringBuilder sb = new StringBuilder();
            for (var entry : fields.entrySet()) {
                if (!sb.isEmpty()) sb.append("&");
                sb.append(enc(entry.getKey())).append("=").append(enc(entry.getValue()));
            }

            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(BASE_URL + "?action=" + enc(action)))
                    .header("Content-Type", "application/x-www-form-urlencoded")
                    .POST(HttpRequest.BodyPublishers.ofString(sb.toString()))
                    .build();

            HttpResponse<String> res = http.send(req, HttpResponse.BodyHandlers.ofString());
            return res.body();
        } catch (Exception e) {
            return "{\"status\":\"error\",\"message\":\"Cannot connect to server: " + e.getMessage() + "\"}";
        }
    }

    private static String get(String url) {
        try {
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .GET()
                    .build();
            HttpResponse<String> res = http.send(req, HttpResponse.BodyHandlers.ofString());
            return res.body();
        } catch (Exception e) {
            return "{\"status\":\"error\",\"message\":\"Cannot connect to server: " + e.getMessage() + "\"}";
        }
    }

    private static String extractField(String json, String key) {
        if (json == null) return "";
        String pattern = "\"" + key + "\"";
        int idx = json.indexOf(pattern);
        if (idx < 0) return "";
        int colon = json.indexOf(":", idx + pattern.length());
        if (colon < 0) return "";
        int start = colon + 1;
        while (start < json.length() && json.charAt(start) == ' ') start++;
        if (start >= json.length()) return "";

        if (json.charAt(start) == '"') {
            int end = start + 1;
            while (end < json.length()) {
                if (json.charAt(end) == '"' && json.charAt(end - 1) != '\\') break;
                end++;
            }
            return json.substring(start + 1, end);
        } else {
            int end = start;
            while (end < json.length() && ",}]".indexOf(json.charAt(end)) < 0) end++;
            return json.substring(start, end).trim();
        }
    }

    private static String extractArray(String json, String key) {
        String pattern = "\"" + key + "\"";
        int idx = json.indexOf(pattern);
        if (idx < 0) return null;
        int bracket = json.indexOf("[", idx + pattern.length());
        if (bracket < 0) return null;
        int depth = 0, i = bracket;
        for (; i < json.length(); i++) {
            if (json.charAt(i) == '[') depth++;
            else if (json.charAt(i) == ']') { depth--; if (depth == 0) break; }
        }
        return json.substring(bracket + 1, i).trim();
    }

    private static String[] splitJsonObjects(String arrayContent) {
        java.util.List<String> objects = new java.util.ArrayList<>();
        int depth = 0, start = -1;
        for (int i = 0; i < arrayContent.length(); i++) {
            char c = arrayContent.charAt(i);
            if (c == '{') { if (depth == 0) start = i; depth++; }
            else if (c == '}') {
                depth--;
                if (depth == 0 && start >= 0) {
                    objects.add(arrayContent.substring(start, i + 1));
                    start = -1;
                }
            }
        }
        return objects.toArray(new String[0]);
    }

    private static void printResult(String response) {
        String status  = extractField(response, "status");
        String message = extractField(response, "message");
        System.out.println("success".equals(status) ? "[✓] " + message : "[!] " + message);
    }

    private static String enc(String value) {
        return URLEncoder.encode(value == null ? "" : value, StandardCharsets.UTF_8);
    }

    private static void printBanner() {
        System.out.println("╔══════════════════════════════════════╗");
        System.out.println("║   AUTOTRACK — Car Registration &     ║");
        System.out.println("║          Tracking System             ║");
        System.out.println("║          Java Console Client         ║");
        System.out.println("╚══════════════════════════════════════╝");
        System.out.println("  API → " + BASE_URL);
    }
}
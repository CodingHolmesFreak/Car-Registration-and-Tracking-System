<?php
header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");

//  DB CONNECTION
$conn = new mysqli("localhost", "root", "", "car_api_db");

if ($conn->connect_error) {
    echo json_encode(["status" => "error", "message" => "Database connection failed"]);
    exit;
}

$action = $_REQUEST['action'] ?? '';

//  ROUTER
switch ($action) {
    case "register": register($conn); break;
    case "login": login($conn); break;
    case "logout": logout($conn); break;

    case "addCar": addCar($conn); break;
    case "getCars": getCars($conn); break;
    case "updateCar": updateCar($conn); break;
    case "deleteCar": deleteCar($conn); break;
    case "updateLocation": updateLocation($conn); break;

    default:
        echo json_encode(["status" => "error", "message" => "Invalid action"]);
}

//  AUTH FUNCTIONS

function register($conn) {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    $email = $_POST['email'] ?? '';

    if (!$username || !$password || !$email) {
        echo json_encode(["status" => "error", "message" => "All fields required"]);
        return;
    }

    $check = $conn->query("SELECT * FROM users WHERE username='$username'");
    if ($check->num_rows > 0) {
        echo json_encode(["status" => "exists", "message" => "Username already exists"]);
        return;
    }

    $hashed = password_hash($password, PASSWORD_DEFAULT);

    $conn->query("INSERT INTO users (username, password, email) VALUES ('$username', '$hashed', '$email')");

    echo json_encode(["status" => "success", "message" => "User registered"]);
}

function login($conn) {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';

    $result = $conn->query("SELECT * FROM users WHERE username='$username'");

    if ($result->num_rows == 0) {
        echo json_encode(["status" => "not_found", "message" => "User not found"]);
        return;
    }

    $user = $result->fetch_assoc();

    if (!password_verify($password, $user['password'])) {
        echo json_encode(["status" => "unauthorized", "message" => "Wrong password"]);
        return;
    }

    $token = bin2hex(random_bytes(16));
    $conn->query("UPDATE users SET token='$token' WHERE user_id=".$user['user_id']);

    echo json_encode([
        "status" => "success",
        "message" => "Login successful",
        "user_id" => $user['user_id'],
        "token" => $token
    ]);
}

function logout($conn) {
    $user_id = $_POST['user_id'] ?? '';
    $conn->query("UPDATE users SET token=NULL WHERE user_id='$user_id'");
    echo json_encode(["status" => "success", "message" => "Logged out"]);
}

//  CAR FUNCTIONS

function addCar($conn) {
    $user_id = $_POST['user_id'] ?? '';
    $token = $_POST['token'] ?? '';
    $plate = $_POST['plate_number'] ?? '';
    $brand = $_POST['brand'] ?? '';
    $model = $_POST['model'] ?? '';

    if (!auth($conn, $user_id, $token)) return;

    if (!$plate || !$brand || !$model) {
        echo json_encode(["status" => "error", "message" => "Missing car details"]);
        return;
    }

    $conn->query("INSERT INTO cars (user_id, plate_number, brand, model, location, last_updated)
                  VALUES ('$user_id', '$plate', '$brand', '$model', 'Unknown', NOW())");

    echo json_encode(["status" => "success", "message" => "Car added"]);
}

function getCars($conn) {
    $user_id = $_GET['user_id'] ?? '';
    $token = $_GET['token'] ?? '';

    if (!auth($conn, $user_id, $token)) return;

    $result = $conn->query("SELECT * FROM cars WHERE user_id='$user_id'");

    $cars = [];
    while ($row = $result->fetch_assoc()) {
        $cars[] = $row;
    }

    echo json_encode(["status" => "success", "data" => $cars]);
}

function updateCar($conn) {
    $car_id = $_POST['car_id'] ?? '';
    $brand = $_POST['brand'] ?? '';
    $model = $_POST['model'] ?? '';

    $conn->query("UPDATE cars SET brand='$brand', model='$model' WHERE car_id='$car_id'");

    echo json_encode(["status" => "success", "message" => "Car updated"]);
}

function deleteCar($conn) {
    $car_id = $_POST['car_id'] ?? '';
    $conn->query("DELETE FROM cars WHERE car_id='$car_id'");
    echo json_encode(["status" => "success", "message" => "Car deleted"]);
}

function updateLocation($conn) {
    $car_id = $_POST['car_id'] ?? '';
    $location = $_POST['location'] ?? '';

    if (!$location) {
        echo json_encode(["status" => "error", "message" => "Location required"]);
        return;
    }

    $conn->query("UPDATE cars SET location='$location', last_updated=NOW() WHERE car_id='$car_id'");

    echo json_encode([
        "status" => "success",
        "message" => "Location updated",
        "location" => $location
    ]);
}

//  AUTH CHECK
function auth($conn, $user_id, $token) {
    $check = $conn->query("SELECT * FROM users WHERE user_id='$user_id' AND token='$token'");
    if ($check->num_rows == 0) {
        echo json_encode(["status" => "unauthorized", "message" => "Invalid token"]);
        return false;
    }
    return true;
}
?>
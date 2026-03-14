import socket
import threading
import cv2
import pygame
import time

# ==========================================
# 1. NETWORK SETTINGS
# ==========================================
CAM_IP = "10.91.21.160"  
STREAM_URL = f"http://{CAM_IP}:81/stream"

# UDP Sockets
ESP32_BROADCAST_IP = "255.255.255.255"
TELEMETRY_PORT = 12345 # Listening to ESP32
COMMAND_PORT = 12346   # Sending to ESP32

# Setup Receiver (Telemetry)
sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_recv.bind(("0.0.0.0", TELEMETRY_PORT))

# Setup Sender (Commands)
sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_send.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# ==========================================
# 2. GAMEPAD SETUP (PYGAME)
# ==========================================
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("❌ ERROR: No Gamepad detected! Plug in the USB dongle and restart.")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"🎮 Connected to: {joystick.get_name()}")

# ==========================================
# 3. BACKGROUND TELEMETRY LISTENER
# ==========================================
sensor_data = "Waiting for Wall-E data..."

def listen_udp():
    global sensor_data
    while True:
        try:
            data, _ = sock_recv.recvfrom(1024)
            sensor_data = data.decode('utf-8')
        except Exception:
            pass

threading.Thread(target=listen_udp, daemon=True).start()

# ==========================================
# 4. MAIN LOOP (VIDEO + CONTROLLER)
# ==========================================
print(f"📡 Connecting to Camera Stream at {STREAM_URL}...")
cap = cv2.VideoCapture(STREAM_URL)

# Variables
servo_h = 90
servo_v = 25
auto_mode = 0
last_y_button = False

print("🚀 Dashboard running! Press 'q' in the video window to quit.")

while True:
    pygame.event.pump() # Update controller inputs

    # --- READ CONTROLLER ---
    # Left Stick for Driving (Arcade Drive)
    # Axis 1 is Up/Down (Inverted, so we multiply by -1)
    # Axis 0 is Left/Right
    fwd_rev = -joystick.get_axis(1) 
    turn = joystick.get_axis(0)

    # Deadzones to stop drifting
    if abs(fwd_rev) < 0.1: fwd_rev = 0
    if abs(turn) < 0.1: turn = 0

    base_speed = int(fwd_rev * 255)
    turn_speed = int(turn * 150)

    # Mix speeds for left/right motors
    left_motor = max(-255, min(255, base_speed + turn_speed))
    right_motor = max(-255, min(255, base_speed - turn_speed))

    # Right Stick X for Horizontal Servo (Axis 3 usually on PC dongles)
    rx = joystick.get_axis(3)
    if abs(rx) > 0.1:
        servo_h = int(90 + (rx * 20)) # Maps to approx 70 - 110
    else:
        servo_h = 90 # Snap back to center

    # D-Pad for Vertical Servo (Hat 0)
    hat = joystick.get_hat(0)
    if hat[1] == 1:   # Up
        servo_v -= 2
    elif hat[1] == -1: # Down
        servo_v += 2
    servo_v = max(0, min(50, servo_v)) # Constrain to 0-50

    # Y Button (Button 3) for Auto Mode Toggle
    current_y_button = joystick.get_button(3)
    if current_y_button and not last_y_button:
        auto_mode = 1 if auto_mode == 0 else 0
        print(f"Toggled Auto Mode: {auto_mode}")
    last_y_button = current_y_button

    # --- SEND COMMAND TO ESP32 ---
    # Format: "LeftSpeed,RightSpeed,ServoH,ServoV,AutoMode"
    command_str = f"{left_motor},{right_motor},{servo_h},{servo_v},{auto_mode}"
    sock_send.sendto(command_str.encode('utf-8'), (ESP32_BROADCAST_IP, COMMAND_PORT))

    # --- UPDATE VIDEO FEED ---
    ret, frame = cap.read()
    if ret:
        # Draw the black HUD bar
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
        
        # Overlay the Telemetry Data
        cv2.putText(frame, sensor_data, (10, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow("Wall-E Mission Control", frame)

    # Run loop at ~30 FPS
    time.sleep(0.03)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pygame.quit()
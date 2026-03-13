import socket
import threading
import cv2

CAM_IP = "10.91.21.160"  
STREAM_URL = f"http://10.91.21.160:81/stream"

UDP_IP = "0.0.0.0"
UDP_PORT = 12345
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sensor_data = "Waiting for Wall-E data..."

def listen_udp():
    global sensor_data
    print("Listening for robot telemetry...")
    while True:
        try:
            data, _ = sock.recvfrom(1024)
            sensor_data = data.decode('utf-8')
        except Exception as e:
            pass

threading.Thread(target=listen_udp, daemon=True).start()

print(f"Connecting to Camera Stream at {STREAM_URL}...")
cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    print("ERROR: Could not open camera stream. Check the IP address!")
    exit()

print("Dashboard running. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Lost connection to camera. Retrying...")
        continue

    cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
    cv2.putText(frame, sensor_data, (10, 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow("Wall-E Mission Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
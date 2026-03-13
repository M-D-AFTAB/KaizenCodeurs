#include <Bluepad32.h>
#include <ESP32Servo.h>
#include <WiFi.h>
#include <WiFiUdp.h>

const char* ssid = "Galaxy M53 5G";
const char* password = "Aftab0006$";
WiFiUDP udp;
IPAddress broadcastIP(255, 255, 255, 255);
const int udpPort = 12345;

#define IN1 16
#define IN2 17
#define IN3 22
#define IN4 23
#define ENA 14
#define ENB 15

#define TRIG_PIN 32
#define ECHO_PIN 33
#define ENC_LEFT 34
#define ENC_RIGHT 35

#define SERVO_HORIZ 25
#define SERVO_VERT 26

ControllerPtr myControllers[BP32_MAX_GAMEPADS];
Servo headHoriz;
Servo headVert;

bool isAutonomous = false;
bool lastButtonState = false;
int vertAngle = 25;

volatile long leftTicks = 0;
volatile long rightTicks = 0;
float currentDist = 0.0;

void IRAM_ATTR countLeft() { leftTicks++; }
void IRAM_ATTR countRight() { rightTicks++; }

void updateDistance() {
    digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    long duration = pulseIn(ECHO_PIN, HIGH, 30000); 
    if (duration > 0) currentDist = (duration * 0.0343) / 2;
}

void drive(int left, int right) {
    digitalWrite(IN1, left > 0 ? HIGH : LOW); digitalWrite(IN2, left < 0 ? HIGH : LOW);
    digitalWrite(IN3, right > 0 ? HIGH : LOW); digitalWrite(IN4, right < 0 ? HIGH : LOW);
    analogWrite(ENA, abs(left)); analogWrite(ENB, abs(right));
}
void stopMotors() { drive(0, 0); }

void onConnectedController(ControllerPtr ctl) {
    for (int i = 0; i < BP32_MAX_GAMEPADS; i++) {
        if (myControllers[i] == nullptr) { myControllers[i] = ctl; break; }
    }
}
void onDisconnectedController(ControllerPtr ctl) {
    for (int i = 0; i < BP32_MAX_GAMEPADS; i++) {
        if (myControllers[i] == ctl) { myControllers[i] = nullptr; break; }
    }
}

void sendTelemetry() {
    static unsigned long lastUdp = 0;
    if (millis() - lastUdp > 100) {
        char payload[100];
        snprintf(payload, sizeof(payload), "MODE:%s | L:%ld | R:%ld | DIST:%.1fcm", 
                 isAutonomous ? "AUTO" : "MANUAL", leftTicks, rightTicks, currentDist);
        
        udp.beginPacket(broadcastIP, udpPort);
        udp.print(payload);
        udp.endPacket();
        lastUdp = millis();
    }
}

void setup() {
    Serial.begin(115200);

    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");
    while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
    Serial.println("\nWiFi Connected!");

    pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
    pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
    pinMode(ENA, OUTPUT); pinMode(ENB, OUTPUT);
    pinMode(TRIG_PIN, OUTPUT); pinMode(ECHO_PIN, INPUT);
    pinMode(ENC_LEFT, INPUT_PULLUP); pinMode(ENC_RIGHT, INPUT_PULLUP);

    attachInterrupt(digitalPinToInterrupt(ENC_LEFT), countLeft, RISING);
    attachInterrupt(digitalPinToInterrupt(ENC_RIGHT), countRight, RISING);

    headHoriz.attach(SERVO_HORIZ); headVert.attach(SERVO_VERT);
    headHoriz.write(90); headVert.write(vertAngle);

    BP32.setup(&onConnectedController, &onDisconnectedController);
    stopMotors();
}

void loop() {
    BP32.update();
    updateDistance();
    
    for (auto ctl : myControllers) {
        if (ctl && ctl->isConnected()) {
            
            bool currentButton = ctl->y();
            if (currentButton && !lastButtonState) {
                isAutonomous = !isAutonomous;
                stopMotors();
            }
            lastButtonState = currentButton;

            if (!isAutonomous) {
                int fwd = map(ctl->throttle(), 0, 1023, 0, 255);
                int rev = map(ctl->brake(), 0, 1023, 0, 255);
                int baseSpeed = fwd - rev;
                int turn = map(ctl->axisX(), -511, 512, -150, 150);
                drive(constrain(baseSpeed - turn, -255, 255), constrain(baseSpeed + turn, -255, 255));

                int rx = ctl->axisRX(); 
                int hAngle = map(rx, -511, 512, 70, 110);
                headHoriz.write(hAngle);

                uint8_t dpad = ctl->dpad();
                if (dpad & 0x01) vertAngle += 2;
                if (dpad & 0x02) vertAngle -= 2;
                vertAngle = constrain(vertAngle, 0, 50);
                headVert.write(vertAngle);
            }
        }
    }

    if (isAutonomous) {
        if (currentDist > 0 && currentDist < 15.0) { 
            stopMotors();
        } else {
            drive(100, 100);
        }
    }

    sendTelemetry();
    delay(10);
}
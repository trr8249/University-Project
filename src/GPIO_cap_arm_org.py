# HTTP 요청을 처리하기 위한 기본 웹 서버 모듈
from http.server import BaseHTTPRequestHandler, HTTPServer
# 라즈베리파이의 GPIO 핀을 제어하기 위한 모듈
import RPi.GPIO as GPIO
import time

# GPIO 설정
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# DC 모터 핀 목록
dc_pins = [0, 5, 6, 13, 19, 26, 16, 20]
for pin in dc_pins:
    GPIO.setup(pin, GPIO.OUT)

# 서보모터 핀 설정
SERVO_GRIP = 10  # 그립
SERVO_JOINT1 = 9
SERVO_JOINT2 = 11

GPIO.setup(SERVO_GRIP, GPIO.OUT)
GPIO.setup(SERVO_JOINT1, GPIO.OUT)
GPIO.setup(SERVO_JOINT2, GPIO.OUT)

# PWM 객체 초기화 (100Hz)
servo_grip = GPIO.PWM(SERVO_GRIP, 100)
servo_joint1 = GPIO.PWM(SERVO_JOINT1, 100)
servo_joint2 = GPIO.PWM(SERVO_JOINT2, 100)

# 서보 각도 → 듀티비 변환 함수
def angle_to_duty(angle):
    return ((angle * 0.01) + 0.5) * 10

# DC모터 정지
def stop_dc_motors():
    for pin in dc_pins:
        GPIO.output(pin, False)

# DC모터 상태 설정
def set_dc_motors(state_list):
    for pin, state in zip(dc_pins, state_list):
        GPIO.output(pin, state)

# 서보 모터 움직이기
def move_servos(angle1, angle2, delay=0.2):
    # 각도를 PWM 듀티사이클로 변환
    duty1 = angle_to_duty(angle1)  # 관절1 각도
    duty2 = angle_to_duty(angle2)  # 관절2 각도
    servo_joint1.ChangeDutyCycle(duty1)
    servo_joint2.ChangeDutyCycle(duty2)
    time.sleep(delay)
    servo_joint1.ChangeDutyCycle(0)
    servo_joint2.ChangeDutyCycle(0)

# 암 위로 올리기 시퀀스
def arm_up():
    # 관절1과 관절2를 순차적으로 위로 들어 올리는 동작
    # angle 리스트는 각도 증가 시퀀스를 정의하며,
    # 각 값은 servo_joint1, servo_joint2에 전달됨
    # 관절1: 아래 → 위 (70 → 150도)
    # 관절2: 관절1보다 약간 적게 움직임 (최대 145도까지)
    for angle in [70, 90, 110, 130, 150]:
        # 관절1에 angle 적용, 관절2는 마지막 단계에서 145로 제한
        move_servos(angle, angle if angle < 150 else 145)


# 암 내리기 시퀀스
def arm_down():
    # 관절1과 관절2를 순차적으로 아래로 내리는 동작
    # angle 리스트는 각도 감소 시퀀스를 정의함
    for angle in [140, 120, 100, 80, 60]:
        move_servos(angle, angle)  # 관절1, 2 동일 각도 적용

# 그립 동작
def grip_open():
    duty = angle_to_duty(20)
    servo_grip.ChangeDutyCycle(duty)
    time.sleep(0.2)
    servo_grip.ChangeDutyCycle(0)

def grip_close():
    duty = angle_to_duty(180)
    servo_grip.ChangeDutyCycle(duty)

# HTTP 요청 처리 클래스
class RequestHandler_httpd(BaseHTTPRequestHandler):
    def do_GET(self):
        message = b'Plz bee'
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', len(message))
        self.end_headers()
        self.wfile.write(message)

        # 요청 파싱
        request = self.requestline[5:-9]
        print("Request:", request)

        # 기본 PWM 시작
        servo_grip.start(0)
        servo_joint1.start(0)
        servo_joint2.start(0)

        # DC모터 제어 명령
        if request == '0':
            stop_dc_motors()
        elif request == '1':
            set_dc_motors([True, False, True, False, True, False, True, False])
        elif request == '2':
            set_dc_motors([False, True, False, True, False, True, False, True])
        elif request == '3':
            set_dc_motors([False, True, True, False, True, False, False, True])
        elif request == '4':
            set_dc_motors([True, False, False, True, False, True, False, True])

        # 암 제어
        elif request == '11':
            arm_up()
        elif request == '12':
            arm_down()

        # 그립 제어
        elif request == '21':
            grip_close()
        elif request == '22':
            grip_open()

# 서버 실행
server_address = ('192.168.82.193', 8080)
httpd = HTTPServer(server_address, RequestHandler_httpd)
print('Starting HTTP server...')
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down server.")
    GPIO.cleanup()

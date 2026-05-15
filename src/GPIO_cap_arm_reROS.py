import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import RPi.GPIO as GPIO
import time

class ManipulatorController(Node):
    def __init__(self):
        super().__init__('manipulator_controller')

        # 토픽 구독: Int32 타입의 명령을 받음
        self.subscription = self.create_subscription(
            Int32,
            'arm_command',
            self.listener_callback,
            10
        )

        # GPIO 설정
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # DC 모터 출력핀
        self.dc_pins = [0, 5, 6, 13, 19, 26, 16, 20]
        for pin in self.dc_pins:
            GPIO.setup(pin, GPIO.OUT)

        # 서보모터 출력핀
        self.servo1 = GPIO.PWM(10, 100)  # 그립
        self.servo2 = GPIO.PWM(9, 100)   # 관절1
        self.servo3 = GPIO.PWM(11, 100)  # 관절2

        for pin in [9, 10, 11]:
            GPIO.setup(pin, GPIO.OUT)

        self.servo1.start(0)
        self.servo2.start(0)
        self.servo3.start(0)

        self.get_logger().info('Manipulator controller node started')

    def listener_callback(self, msg):
        command = msg.data
        self.get_logger().info(f'Received command: {command}')

        if command == 0:
            self.stop_motors()
        elif command == 1:
            self.move_forward()
        elif command == 2:
            self.move_backward()
        elif command == 3:
            self.turn_left()
        elif command == 4:
            self.turn_right()
        elif command == 11:
            self.arm_up()
        elif command == 12:
            self.arm_down()
        elif command == 21:
            self.grip_on()
        elif command == 22:
            self.grip_off()

    def stop_motors(self):
        for pin in self.dc_pins:
            GPIO.output(pin, False)

    def move_forward(self):
        GPIO.output(0, True)
        GPIO.output(5, False)
        GPIO.output(6, True)
        GPIO.output(13, False)
        GPIO.output(19, True)
        GPIO.output(26, False)
        GPIO.output(16, True)
        GPIO.output(20, False)

    def move_backward(self):
        GPIO.output(0, False)
        GPIO.output(5, True)
        GPIO.output(6, False)
        GPIO.output(13, True)
        GPIO.output(19, False)
        GPIO.output(26, True)
        GPIO.output(16, False)
        GPIO.output(20, True)

    def turn_left(self):
        GPIO.output(0, False)
        GPIO.output(5, True)
        GPIO.output(6, True)
        GPIO.output(13, False)
        GPIO.output(19, True)
        GPIO.output(26, False)
        GPIO.output(16, False)
        GPIO.output(20, True)

    def turn_right(self):
        GPIO.output(0, True)
        GPIO.output(5, False)
        GPIO.output(6, False)
        GPIO.output(13, True)
        GPIO.output(19, False)
        GPIO.output(26, True)
        GPIO.output(16, False)
        GPIO.output(20, True)

    def angle_to_duty(self, angle):
        return ((angle * 0.01) + 0.5) * 10

    def move_servos(self, angle1, angle2, delay=0.2):
        duty1 = self.angle_to_duty(angle1)
        duty2 = self.angle_to_duty(angle2)
        self.servo2.ChangeDutyCycle(duty1)
        self.servo3.ChangeDutyCycle(duty2)
        time.sleep(delay)
        self.servo2.ChangeDutyCycle(0)
        self.servo3.ChangeDutyCycle(0)

    def arm_up(self):
        for angle in [70, 90, 110, 130, 150]:
            angle2 = angle if angle < 150 else 145
            self.move_servos(angle, angle2)

    def arm_down(self):
        for angle in [140, 120, 100, 80, 60]:
            self.move_servos(angle, angle)

    def grip_on(self):
        duty = self.angle_to_duty(180)
        self.servo1.ChangeDutyCycle(duty)
        time.sleep(0.2)
        self.servo1.ChangeDutyCycle(0)

    def grip_off(self):
        duty = self.angle_to_duty(20)
        self.servo1.ChangeDutyCycle(duty)
        time.sleep(0.2)
        self.servo1.ChangeDutyCycle(0)


def main(args=None):
    rclpy.init(args=args)
    node = ManipulatorController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('Shutting down...')
    finally:
        GPIO.cleanup()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
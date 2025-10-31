import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import os
import time
import math
import pymycobot
from packaging import version

GRIPPER_MIN_DEG = -40.0
GRIPPER_MAX_DEG = 9.0

def map_rad_to_1_100(rad):
    deg = math.degrees(rad)
    t = (deg - GRIPPER_MIN_DEG) / (GRIPPER_MAX_DEG - GRIPPER_MIN_DEG)
    t = max(0.0, min(1.0, t))

    return int(round(1 + t * (100 - 1)))

# min low version require
MIN_REQUIRE_VERSION = '3.6.6'

current_verison = pymycobot.__version__
print('current pymycobot library version: {}'.format(current_verison))
if version.parse(current_verison) < version.parse(MIN_REQUIRE_VERSION):
    raise RuntimeError('The version of pymycobot library must be greater than {} or higher. The current version is {}. Please upgrade the library version.'.format(MIN_REQUIRE_VERSION, current_verison))
else:
    print('pymycobot library version meets the requirements!')
    from pymycobot import MyCobot280

class Slider_Subscriber(Node):
    def __init__(self):
        super().__init__("control_sync_plan")
        self.subscription = self.create_subscription(
            JointState,
            "joint_states",
            self.listener_callback,
            10
        )
        self.subscription
        
        self.robot_m5 = os.popen("ls /dev/ttyUSB0").readline()[:-1]
        self.robot_wio = os.popen("ls /dev/ttyACM*").readline()[:-1]
        if self.robot_m5:
            port = self.robot_m5
        else:
            port = self.robot_wio
        self.get_logger().info("port:%s, baud:%d" % (port, 1000000))
        self.mc = MyCobot280(port, 1000000)
        time.sleep(0.05)
        if self.mc.get_fresh_mode() == 0:
            self.mc.set_fresh_mode(1)
            time.sleep(0.05)

        self.rviz_order = [
            'link1_to_link2',
            'link2_to_link3',
            'link3_to_link4',
            'link4_to_link5',
            'link5_to_link6',
            'link6_to_link6_flange',
        ]

        self.gripper_order =[
            'gripper_controller'
        ]

    def listener_callback(self, msg):
        joint_state_dict = {name: msg.position[i] for i, name in enumerate(msg.name)}
        data_list = []
        for joint in self.rviz_order:
            if joint in joint_state_dict:
                radians_to_angles = round(math.degrees(joint_state_dict[joint]), 3)
                data_list.append(radians_to_angles)

        gripper_list = []
        for gripper in self.gripper_order:
            if gripper in joint_state_dict:
                    value_1_100 = map_rad_to_1_100(joint_state_dict[gripper])
                    gripper_list.append(value_1_100)

        print('data_list: {}'.format(data_list))
        self.mc.send_angles(data_list, 35)

        print('gripper_list: {}'.format(gripper_list))
        self.mc.set_gripper_value(gripper_list[0], 35)


def main(args=None):
    rclpy.init(args=args)
    slider_subscriber = Slider_Subscriber()
    
    rclpy.spin(slider_subscriber)
    
    slider_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

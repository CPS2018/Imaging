#!/usr/bin/env python
import rospy
import actionlib
import simulation_control.msg
#from apriltags2_ros.msg import AprilTagDetectionArray
from geometry_msgs.msg import PoseStamped, Point
from std_msgs.msg import Bool, String


class descend_on_object_server():
    def __init__(self):

        #variables
        self.local_pose = PoseStamped()
        self.des_pose = PoseStamped()
        self.object_pose = Point()
        #publishers
        self.mode_control = rospy.Publisher('/position_control/set_mode', String, queue_size=10)
        self.vel_control = rospy.Publisher('/position_control/set_velocity', PoseStamped, queue_size=10)
        #subscribers
        rospy.Subscriber('/color_detection/cam_point', Point, self.get_cam_pos_callback)
        rospy.Subscriber('/mavros/local_position/pose', PoseStamped, self._local_pose_callback)
        rospy.Subscriber('/position_control/distance', Bool, self.distance_reached_cb)

        self.rate = rospy.Rate(20)
        self.result = simulation_control.msg.descend_on_objectResult()
        self.action_server = actionlib.SimpleActionServer('descend_on_object',
                                                          simulation_control.msg.descend_on_objectAction,
                                                          execute_cb=self.execute_cb, auto_start=False)
        self.last_object_pose = Point()
        self.action_server.start()


    def execute_cb(self, goal):
        rospy.loginfo("Starting to descend")
        self.mode_control.publish('velctr')
        rospy.sleep(0.1)
        while self.local_pose.pose.position.z > 1:

            self.rate.sleep()
            if self.detected and (abs(self.object_pose.x) > 0.1 or abs(self.object_pose.y) > 0.1):# and (self.last_object_pose.x != self.object_pose.x and self.last_object_pose.y != self.object_pose.y):
                self.last_object_pose = self.object_pose
                self.des_pose.pose.position.x = self.object_pose.x
                self.des_pose.pose.position.y = self.object_pose.y
                self.des_pose.pose.position.z = self.local_pose.pose.position.z
                print("des_pose: \n{}".format(self.des_pose.pose.position))
                print("object_pose: \n{}".format(self.object_pose))
                self.vel_control.publish(self.des_pose)
                rospy.loginfo("Centering...")

                while not self.target_reached:#abs(self.object_pose.x) > 0.1 and abs(self.object_pose.y) > 0.1:
                    print(self.target_reached)
                    rospy.sleep(2)
            elif self.detected and abs(self.object_pose.x) < 0.1 and abs(self.object_pose.y) < 0.1:
                self.des_pose.pose.position.x = 0
                self.des_pose.pose.position.y = 0
                self.des_pose.pose.position.z = self.local_pose.pose.position.z - 0.5
                rospy.loginfo("Descending...")
                self.vel_control.publish(self.des_pose)
                while not self.target_reached:#self.local_pose.pose.position.z > self.des_pose.pose.position.z + 0.1:
                    print(self.target_reached)
                    rospy.sleep(2)

        self.rate.sleep()

        rospy.loginfo("Hovering 1 meter above detected object")
        self.des_pose.pose.position.x = 0
        self.des_pose.pose.position.y = 0
        self.des_pose.pose.position.z = self.local_pose.pose.position.z - 0.5
        self.vel_control.publish(self.des_pose)
        rospy.sleep(1)
        self.result.position_reached.data = True
        self.action_server.set_succeeded(self.result)

    def get_cam_pos_callback(self, data):
        if data.x != float("inf"):
            self.detected = True
            self.object_pose = data
        else:
            self.detected = False

    #def detection_array_callback(self, array):
    #    if array.detections:
    #        self.detected = True
    #        self.object_pose = array.detections[0].pose.pose.pose.position
    #    else:
    #        self.detected = False

    def _local_pose_callback(self, data):
        self.local_pose = data
    def distance_reached_cb(self, data):
        self.target_reached = data.data

if __name__ == '__main__':
    try:

        rospy.init_node('descend_on_object_server')
        descend_on_object_server()
    except rospy.ROSInterruptException:
        pass
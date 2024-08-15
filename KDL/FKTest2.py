#!/usr/bin/env python
# -*- coding: utf-8 -*-

import PyKDL as kdl
import numpy as np
from urdf_parser_py.urdf import URDF

def test_urdf_loading():
    robot = URDF.from_xml_file('/home/yahboom/dofbot_ws/src/dofbot_moveit/urdf/dofbot.urdf')
    print(f"Robot name: {robot.name}")
    print(f"Number of joints: {len(robot.joints)}")
    print(f"Number of links: {len(robot.links)}")

test_urdf_loading()

def create_chain_from_urdf(urdf_file):
    robot = URDF.from_xml_file(urdf_file)
    chain = kdl.Chain()
    for joint in robot.joints:
        if joint.type == 'revolute':
            xyz = joint.origin.xyz
            rpy = joint.origin.rpy
            joint_axis = kdl.Vector(*joint.axis)
            kdl_joint = kdl.Joint(joint.name, kdl.Vector(*xyz), joint_axis, kdl.Joint.RotAxis)
            kdl_frame = kdl.Frame(kdl.Rotation.RPY(*rpy), kdl.Vector(*xyz))
            segment = kdl.Segment(kdl_joint, kdl_frame)
            chain.addSegment(segment)
    return chain

urdf_file = '/home/yahboom/dofbot_ws/src/dofbot_moveit/urdf/dofbot.urdf'
chain = create_chain_from_urdf(urdf_file)

# Set sample angles for each joint (in degrees)
sample_angles = [30, 45, -30, 60, 15]  # Adjust these values as needed

# Convert sample angles to radians and create JntArray
joint_angles = kdl.JntArray(chain.getNrOfJoints())
for i in range(chain.getNrOfJoints()):
    joint_angles[i] = np.deg2rad(sample_angles[i])

# Compute forward kinematics
fk_solver = kdl.ChainFkSolverPos_recursive(chain)
end_effector_frame = kdl.Frame()
fk_solver.JntToCart(joint_angles, end_effector_frame)

# Extract end-effector position
position = end_effector_frame.p
print("\nEnd-effector position:")
print(f"X: {position.x():.6f}")
print(f"Y: {position.y():.6f}")
print(f"Z: {position.z():.6f}")

# Extract end-effector rotation matrix
rotation = end_effector_frame.M
print("\nEnd-effector rotation matrix:")
for i in range(3):
    print(f"{rotation[i, 0]:.6f}  {rotation[i, 1]:.6f}  {rotation[i, 2]:.6f}")

# Calculate and display Roll-Pitch-Yaw angles
rpy = rotation.GetRPY()
print("\nEnd-effector orientation (Roll-Pitch-Yaw angles in degrees):")
print(f"Roll: {np.rad2deg(rpy[0]):.2f}")
print(f"Pitch: {np.rad2deg(rpy[1]):.2f}")
print(f"Yaw: {np.rad2deg(rpy[2]):.2f}")

print("\nJoint angles used (in degrees):")
for i, angle in enumerate(sample_angles):
    print(f"Joint {i+1}: {angle:.2f}")
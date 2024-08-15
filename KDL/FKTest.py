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
            # Extract the joint origin
            xyz = joint.origin.xyz
            rpy = joint.origin.rpy

            # Create the joint and frame
            joint_axis = kdl.Vector(*joint.axis)
            kdl_joint = kdl.Joint(joint.name, kdl.Vector(*xyz), joint_axis, kdl.Joint.RotAxis)
            kdl_frame = kdl.Frame(kdl.Rotation.RPY(*rpy), kdl.Vector(*xyz))
            segment = kdl.Segment(kdl_joint, kdl_frame)
            chain.addSegment(segment)
    return chain

urdf_file = '/home/yahboom/dofbot_ws/src/dofbot_moveit/urdf/dofbot.urdf'  
chain = create_chain_from_urdf(urdf_file)

# Define joint angles (radians) for testing
joint_angles = kdl.JntArray(chain.getNrOfJoints())
for i in range(chain.getNrOfJoints()):
    joint_angles[i] = np.deg2rad(30)  # Sample angle

# Compute forward kinematics
fk_solver = kdl.ChainFkSolverPos_recursive(chain)
end_effector_frame = kdl.Frame()
fk_solver.JntToCart(joint_angles, end_effector_frame)

# Output end-effector position
position = end_effector_frame.p
print("End-effector position:", position)

# Output end-effector rotation
rotation = end_effector_frame.M
print("End-effector rotation matrix:")
for i in range(3):
    print(rotation[i, 0], rotation[i, 1], rotation[i, 2])
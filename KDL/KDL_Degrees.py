import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import PyKDL as kdl
from urdf_parser_py.urdf import URDF
from kdl_parser_py.urdf import treeFromUrdfModel

# Load the URDF file
urdf_file_path = '/home/jetson/Documents/test_beto/ARM.urdf'
robot = URDF.from_xml_file(urdf_file_path)

# Create the KDL tree from the URDF model
(ok, tree) = treeFromUrdfModel(robot)
if not ok:
    print("Failed to create KDL tree from URDF")
    exit(1)

# Extract the kinematic chain from the base link to the end-effector link
base_link = 'base_link'
end_effector_link = 'link5'
chain = tree.getChain(base_link, end_effector_link)

# Initialize the FK and IK solver
fk_solver = kdl.ChainFkSolverPos_recursive(chain)
ik_solver = kdl.ChainIkSolverPos_LMA(chain)

# Number of joints
num_joints = chain.getNrOfJoints()

# Example initial joint angles (in radians)
initial_angles = [0.0] * num_joints

# Example correction values (in radians)
corrections = [0.0] * num_joints

# Initialize joint angles
joint_angles = kdl.JntArray(num_joints)
for i in range(num_joints):
    joint_angles[i] = initial_angles[i]

# Define a reachable target position for the end-effector
target_position = kdl.Vector(0.0, 0.05, 0.05)

# Define the desired end-effector frame (position and orientation)
target_frame = kdl.Frame(target_position)

# Solve inverse kinematics
result_angles = kdl.JntArray(num_joints)
ik_result = ik_solver.CartToJnt(joint_angles, target_frame, result_angles)

# Extract joint limits from URDF
joint_limits = []
for joint in robot.joints:
    if joint.type in ['revolute', 'prismatic']:
        joint_limits.append((joint.limit.lower, joint.limit.upper))

if ik_result >= 0:
    # Clamp joint angles within the specified limits
    clamped_angles = kdl.JntArray(num_joints)
    for i in range(num_joints):
        clamped_angles[i] = max(joint_limits[i][0], min(result_angles[i], joint_limits[i][1]))
    
    print("Inverse kinematics solution found (clamped):")
    for i in range(num_joints):
        angle_degrees = np.degrees(clamped_angles[i])
        print(f"Joint {i}: {angle_degrees:.2f} degrees")

    # Apply corrections to the clamped angles
    corrected_angles = kdl.JntArray(num_joints)
    for i in range(num_joints):
        corrected_angles[i] = clamped_angles[i] + corrections[i]

    print("\nInverse kinematics solution with corrections:")
    for i in range(num_joints):
        angle_degrees = np.degrees(corrected_angles[i])
        print(f"Joint {i}: {angle_degrees:.2f} degrees")
else:
    print("Inverse kinematics solver failed.")
    exit(1)

# Initialize a list to store the positions of each link using clamped angles
link_positions_initial = []

# Compute forward kinematics for each link using clamped angles
for i in range(num_joints + 1):
    frame = kdl.Frame()
    fk_solver.JntToCart(clamped_angles, frame, i)
    position = frame.p
    link_positions_initial.append([position.x(), position.y(), position.z()])
    print(f"Link {i}: Position (initial) = {position.x()}, {position.y()}, {position.z()}")

# Convert positions to numpy array for easier plotting
link_positions_initial = np.array(link_positions_initial)

# Plotting the robot arm in 3D based on clamped IK result
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Plot the links
ax.plot(link_positions_initial[:, 0], link_positions_initial[:, 1],
        link_positions_initial[:, 2], 'o-', label="Robot Arm (Initial IK)")

# Plot the joints
ax.scatter(link_positions_initial[:, 0], link_positions_initial[:, 1],
           link_positions_initial[:, 2], c='r', marker='o')

# Set plot labels and title
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('3D Plot of Robot Arm (Initial IK)')

plt.legend()
plt.show()
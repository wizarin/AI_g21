
# Import the Supervisor class from the Webots controller library
from controller import Supervisor

# Create a Supervisor object to interact with the simulation
supervisor = Supervisor()

# Get the simulation's basic timestep in ms
timestep = int(supervisor.getBasicTimeStep())

# Get a reference to the robot being controlled by this Supervisor
robot_node = supervisor.getSelf()

# Check that the Supervisor can access its own robot node
if robot_node is None:
    raise RuntimeError(
        "Could not obtain the Supervisor node. "
        "Set the robot's supervisor field to TRUE in the scene tree"
    )

# Get references to the spider's position and orientation fields
translation = robot_node.getField("translation")
rotation = robot_node.getField("rotation")

# Get the robot's current position and orientation
position = robot_node.getPosition()
orientation = robot_node.getOrientation()

# Print the robot's current position and orientation
print("Robot position:", position)
print("Robot orientation:", orientation)

# Get the current simulation time in seconds
current_time = supervisor.getTime()

# Print the current simulation time
print("Simulation time:", current_time)

# Save the robot's initial position and orientation
initial_translation = translation.getSFVec3f()
initial_rotation = rotation.getSFRotation()

# Advance the simulation by one timestep
supervisor.step(timestep)

import math
from controller import Robot
import random

# =========================================================
# INITIALISE ROBOT
# =========================================================

robot = Robot()

timestep = int(robot.getBasicTimeStep())


# =========================================================
# LEGS
# =========================================================

right_legs = ["R1", "R2", "R3", "R4"]
left_legs  = ["L1", "L2", "L3", "L4"]

all_legs = right_legs + left_legs


# =========================================================
# TARGET STANDING POSITION
# =========================================================

TARGET_ANGLES = {

    "R": {
        "hip_joint": 0.0,
        "thigh_joint": 1.0,
        "knee_joint": -0.5
    },

    "L": {
        "hip_joint": 0.0,
        "thigh_joint": -1.0,
        "knee_joint": 0.5
    }
}


# =========================================================
# GPS
# =========================================================

gps = robot.getDevice("gps")

if gps is None:
    print("ERROR: GPS not found!")
    exit()

gps.enable(timestep)


# =========================================================
# MOTOR SETTINGS
# =========================================================

MOTOR_VELOCITY = 1.5

# Small movement made each cycle.
#
# 0.5 degrees is deliberately small so that we can
# observe the effect on the actual robot height.
#
LOWER_STEP = math.radians(0.5)


# =========================================================
# GET MOTORS
# =========================================================

motors = {}

for side, leg_list in [
    ("R", right_legs),
    ("L", left_legs)
]:

    for leg in leg_list:

        for joint_type in [
            "hip_joint",
            "thigh_joint",
            "knee_joint"
        ]:

            motor_name = f"{leg}_{joint_type}"

            motor = robot.getDevice(motor_name)

            if motor:

                motors[motor_name] = motor
                motor.setVelocity(MOTOR_VELOCITY)

            else:

                print(
                    f"WARNING: Motor '{motor_name}' not found!"
                )


# =========================================================
# SET INITIAL STANDING POSITION
# =========================================================

print("")
print("==============================================")
print("SETTING INITIAL STANDING POSITION")
print("==============================================")


for side, leg_list in [
    ("R", right_legs),
    ("L", left_legs)
]:

    angles = TARGET_ANGLES[side]

    for leg in leg_list:

        motors[
            f"{leg}_hip_joint"
        ].setPosition(
            angles["hip_joint"]
        )

        motors[
            f"{leg}_thigh_joint"
        ].setPosition(
            angles["thigh_joint"]
        )

        motors[
            f"{leg}_knee_joint"
        ].setPosition(
            angles["knee_joint"]
        )


# =========================================================
# WAIT FOR STANDING POSITION
# =========================================================

print("Waiting for standing position...")

for _ in range(
    int(3.0 * 1000 / timestep)
):

    if robot.step(timestep) == -1:
        exit()


# =========================================================
# READ INITIAL GPS HEIGHT
# =========================================================

position = gps.getValues()

current_z = position[2]

print("")
print("==============================================")
print("INITIAL GPS POSITION")
print("==============================================")
print(
    f"X = {position[0]:.4f} m"
)
print(
    f"Y = {position[1]:.4f} m"
)
print(
    f"Z = {position[2]:.4f} m"
)

print("")
print(
    f"Target Z = 0.3000 m"
)
print(
    f"Current Z = {current_z:.4f} m"
)


# =========================================================
# CURRENT JOINT TARGETS
# =========================================================

right_thigh = TARGET_ANGLES["R"]["thigh_joint"]
right_knee = TARGET_ANGLES["R"]["knee_joint"]
right_hip = TARGET_ANGLES["R"]["hip_joint"]

left_thigh = TARGET_ANGLES["L"]["thigh_joint"]
left_knee = TARGET_ANGLES["L"]["knee_joint"]
left_hip = TARGET_ANGLES["L"]["hip_joint"]

joints = [right_thigh, right_knee, right_hip, left_thigh, left_knee, left_hip]
# =========================================================
# LOWER ROBOT
# =========================================================

print("")
print("==============================================")
print("LOWERING ROBOT")
print("==============================================")
print("")

def pop_gen(pop_size, n_vectors=300):
    pop = []
    for _ in range(pop_size):
        individual = []
        for _ in range(n_vectors):
            vector = []
            for _ in range(8):                       # 8 legs
                vector.append(random.randint(-157, 157) / 100)   # hip
                vector.append(random.randint(-157, 157) / 100)   # thigh
                vector.append(random.randint(-200, 100) / 100)   # knee
            individual.append(vector)
        pop.append(individual)
    return pop

TARGET_Z = 0.300

pop_size = 10
pop = pop_gen(pop_size)

dist_fitnesses = []

for idx, individual in enumerate(pop):
    start_x = gps.getValues()[0]

    for vector in individual:
        j = 0
        for leg in all_legs:
            for joint_type in ["hip_joint", "thigh_joint", "knee_joint"]:
                motors[f"{leg}_{joint_type}"].setPosition(vector[j])
                j += 1

        for _ in range(5):
            if robot.step(timestep) == -1:
                exit()

    end_x = gps.getValues()[0]
    dist_fit = end_x - start_x
    dist_fitnesses.append(dist_fit)
    print(f"Individual {idx}: fitness = {dist_fit:.4f}")
   
ranking = sorted(range(len(dist_fitnesses)),
                 key=lambda i: dist_fitnesses[i],
                 reverse=True)

print("")
print("Ranking (best to worst):")
for rank, i in enumerate(ranking, start=1):
    print(f"Rank {rank}. Individual {i}: fitness = {dist_fitnesses[i]:.4f}")

ranked_pop = [pop[i] for i in ranking]
best = ranked_pop[0]


# =========================================================
# TOURNAMENT SELECTION
# =========================================================

tourn_size = 3
new_pop = []
new_fitnesses = []

for _ in range(len(ranked_pop)):
    tournament = []

    for _ in range(tourn_size):
        ranked_index = random.randrange(len(ranked_pop))
        original_index = ranking[ranked_index]
        fitness = dist_fitnesses[original_index]

        tournament.append((ranked_index, fitness, ranked_pop[ranked_index]))

    ranked_index, fitness, winner = min(tournament, key=lambda item: item[0])

    print(f"Selected winner: fitness = {fitness:.4f}")

    new_pop.append(winner)
    new_fitnesses.append(fitness)

print(f"Selected {len(new_pop)} individuals for new_pop.")
print("New population fitnesses:", new_fitnesses)


# =========================================================
# HOLD POSITION
# =========================================================

print("")
print("Robot is holding its position.")

while robot.step(timestep) != -1:

    pass
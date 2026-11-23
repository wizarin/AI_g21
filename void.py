import math
from controller import Robot
from controller import Supervisor
import random

# =========================================================
# INITIALISE ROBOT
# =========================================================

robot = Supervisor() # allows each run to be teleported to an upright position

timestep = int(robot.getBasicTimeStep())

# =========================================================
# GA SETTINGS
# =========================================================

TARGET_Z = 0.300
pop_size = 30
GENERATIONS = 250
TOURNAMENT_SIZE = 3
CROSSOVER_RATE = 1.0 # chance to breed currently 100% but can be changed
MUTATION_RATE = 0.05 # chance to be mutated currently 2%
MUTATION_SIGMA = 0.15 # size of mutation 15%
ELITE_COUNT = 2 # parent carried to the next generation  

W_HEIGHT_SCORE = 10.0   # main term: stay high
W_SURVIVAL     = 5.0    # stay up for the whole gait
W_FORWARD      = 1.0    # small bonus for moving forward while upright
W_DRIFT        = 0.5    # small penalty for sideways drift
FALL_Z         = 0.15   # below this the spider counts as collapsed (tune!)
STEPS_PER_VECTOR = 5    # same as the original loops
HEIGHT_GATE = 0.7


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

# ---------------------------------------------------------
self_node = robot.getSelf()  #getFromDef("SPIDER_ROOT")
trans_field = self_node.getField("translation")
rot_field = self_node.getField("rotation")

START_TRANS = list(trans_field.getSFVec3f())
START_ROT = list(rot_field.getSFRotation())
STAND_Z = current_z
STAND_HEIGHT = STAND_Z


def set_one_leg_from_vector(vector, vector_index):
    """Apply the genes for one leg and leave all other legs unchanged."""
    leg_index = vector_index % len(all_legs)
    leg = all_legs[leg_index]
    gene_index = leg_index * 3

    for joint_offset, joint_type in enumerate(
        ["hip_joint", "thigh_joint", "knee_joint"]
    ):
        motors[f"{leg}_{joint_type}"].setPosition(
            vector[gene_index + joint_offset]
        )

def reset_to_standing():
    self_node.resetPhysics()
    trans_field.setSFVec3f([START_TRANS[0], START_TRANS[1], START_TRANS[2] + 0.05])
    rot_field.setSFRotation(START_ROT)
    self_node.resetPhysics()
    
    for leg in all_legs:
        side = "R" if leg in right_legs else "L"
        for joint_type in ["hip_joint", "thigh_joint", "knee_joint"]:
            motors[f"{leg}_{joint_type}"].setPosition(
                TARGET_ANGLES[side][joint_type]
            )

    for _ in range(int(1.5 * 1000 / timestep)):
        if robot.step(timestep) == -1:
            exit()

# Saving the standing pose 
# We can teleport back to it
# ---------------------------------------------------------

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
            for _ in range(8):                       
                vector.append(random.randint(-157, 157) / 100)   
                vector.append(random.randint(-157, 157) / 100)   
                vector.append(random.randint(-200, 100) / 100) 
            individual.append(vector)
        pop.append(individual)
    return pop

pop = pop_gen(pop_size)

dist_fitnesses = []

#------------------------------------------------
for idx, individual in enumerate(pop):
    start_x = gps.getValues()[0]

    for vector_index, vector in enumerate(individual):
        set_one_leg_from_vector(vector, vector_index)

        for _ in range(5):
            if robot.step(timestep) == -1:
                exit()

    end_x = gps.getValues()[0]
    dist_fit = end_x - start_x
    dist_fitnesses.append(dist_fit)
    print(f"Individual {idx}: fitness = {dist_fit:.4f}")

# plays every random individual on the robot once
# records how far each moved forward.
#------------------------------------------------
  
#------------------------------------------------ 
ranking = sorted(range(len(dist_fitnesses)),
                 key=lambda i: dist_fitnesses[i],
                 reverse=True)

print("")
print("Ranking (best to worst):")
for rank, i in enumerate(ranking, start=1):
    print(f"Rank {rank}. Individual {i}: fitness = {dist_fitnesses[i]:.4f}")

ranked_pop = [pop[i] for i in ranking]
best = ranked_pop[0]
# ranks scores best to worst
#------------------------------------------------

# =========================================================
# GENETIC ALGORITHM: BREEDING, CROSSOVER, MUTATION
# =========================================================

def gene_bounds(gene_index):
    if gene_index % 3 == 2:       
        return -2.00, 1.00
    return -1.57, 1.57


# ---------------------------------------------------------
def evaluate(individual):

    for leg in all_legs:
        side = "R" if leg in right_legs else "L"
        for joint_type in ["hip_joint", "thigh_joint", "knee_joint"]:
            motors[f"{leg}_{joint_type}"].setPosition(
                TARGET_ANGLES[side][joint_type]
            )

    for _ in range(int(1.0 * 1000 / timestep)):
        if robot.step(timestep) == -1:
            exit()

    start_x = gps.getValues()[0]

    for vector_index, vector in enumerate(individual):
        set_one_leg_from_vector(vector, vector_index)

        for _ in range(5):
            if robot.step(timestep) == -1:
                exit()

    return gps.getValues()[0] - start_x
    
# Fitness evaluation. The legs are reset to the
# standing pose 
# ---------------------------------------------------------


# ---------------------------------------------------------
# Tournament selection
# ---------------------------------------------------------

def tournament_select(population, fitnesses, k=TOURNAMENT_SIZE):
    contenders = random.sample(range(len(population)), k)
    winner = max(contenders, key=lambda i: fitnesses[i])
    return population[winner]


# ---------------------------------------------------------
# Two-point crossover
# ---------------------------------------------------------
def two_point_crossover(parent1, parent2):

    n = len(parent1)
    p1, p2 = sorted(random.sample(range(1, n), 2))

    child1 = parent1[:p1] + parent2[p1:p2] + parent1[p2:]
    child2 = parent2[:p1] + parent1[p1:p2] + parent2[p2:]

    child1 = [list(v) for v in child1]
    child2 = [list(v) for v in child2]

    return child1, child2


# ---------------------------------------------------------
# Mutation
# ---------------------------------------------------------
def mutate(individual):

    for vector in individual:
        for g in range(len(vector)):
            if random.random() < MUTATION_RATE:
                low, high = gene_bounds(g)
                vector[g] += random.gauss(0, MUTATION_SIGMA)
                vector[g] = max(low, min(high, vector[g]))

    return individual


# ---------------------------------------------------------
# Height-first fitness
#
# Idea: standing up is rewarded first, walking is a bonus

#   height_score : average body height over the whole run
#   survival     : fraction of the vectors played before the
#                  body dropped below FALL_Z 
#   forward      : distance along X
#   drift        : sideways movement Y
#
# Assumes X = forward, Y = sideways, Z = height.
# ---------------------------------------------------------


def evaluate_height_first(individual):

    start = gps.getValues()
    height_samples = []
    vectors_done = 0
    fallen = False

    for vector_index, vector in enumerate(individual):
        set_one_leg_from_vector(vector, vector_index)

        for _ in range(STEPS_PER_VECTOR):
            if robot.step(timestep) == -1:
                exit()
            height_samples.append(gps.getValues()[2])

        vectors_done += 1

    end = gps.getValues()

    total_steps = len(individual) * STEPS_PER_VECTOR
    missing = total_steps - len(height_samples)
    if missing > 0:
        height_samples.extend([height_samples[-1]] * missing)

    capped = [min(max(z, 0.0), STAND_HEIGHT) for z in height_samples]
    height_score = (sum(capped) / len(capped)) / STAND_HEIGHT
    survival     = vectors_done / len(individual)
    if fallen:
        survival = (vectors_done - 1) / len(individual)

    forward = end[0] - start[0]
    drift   = abs(end[1] - start[1])

    gate = max(0.0, (height_score - HEIGHT_GATE) / (1.0 - HEIGHT_GATE))   # 0 below 0.7, up to 1.0 at full height

    fitness = (W_HEIGHT_SCORE * height_score
               + W_SURVIVAL   * survival
               + W_FORWARD    * forward * gate
               - W_DRIFT      * drift)
    return fitness

def evaluate_with_reset(individual):
    reset_to_standing()
    return evaluate_height_first(individual)

evaluate = evaluate_with_reset

# ---------------------------------------------------------
# Evolution loop
# ---------------------------------------------------------
print("")
print("==============================================")
print("STARTING EVOLUTION")
print("==============================================")

population = [list(map(list, ind)) for ind in ranked_pop]
fitnesses  = [dist_fitnesses[i] for i in ranking]

ga_best_individual = population[0]
ga_best_fitness    = fitnesses[0]


print("Re-scoring generation 0 from the standing pose...")
fitnesses = [evaluate(ind) for ind in population]
ga_best_fitness    = max(fitnesses)
ga_best_individual = population[fitnesses.index(ga_best_fitness)]

for generation in range(1, GENERATIONS + 1):

    order = sorted(range(len(population)),
                   key=lambda i: fitnesses[i],
                   reverse=True)

    new_population = [population[i] for i in order[:ELITE_COUNT]]
    new_fitnesses  = [fitnesses[i]  for i in order[:ELITE_COUNT]]

    children = []
    while len(new_population) + len(children) < pop_size:

        parent1 = tournament_select(population, fitnesses)
        parent2 = tournament_select(population, fitnesses)

        if random.random() < CROSSOVER_RATE:
            child1, child2 = two_point_crossover(parent1, parent2)
        else:
            child1 = [list(v) for v in parent1]
            child2 = [list(v) for v in parent2]

        children.append(mutate(child1))
        if len(new_population) + len(children) < pop_size:
            children.append(mutate(child2))

    for child in children:
        new_population.append(child)
        new_fitnesses.append(evaluate(child))

    population = new_population
    fitnesses  = new_fitnesses

    gen_best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
    gen_avg      = sum(fitnesses) / len(fitnesses)

    if fitnesses[gen_best_idx] > ga_best_fitness:
        ga_best_fitness    = fitnesses[gen_best_idx]
        ga_best_individual = population[gen_best_idx]

    print(
        f"Generation {generation:2d}: "
        f"best = {fitnesses[gen_best_idx]:.4f}  "
        f"avg = {gen_avg:.4f}  "
        f"overall best = {ga_best_fitness:.4f}"
    )

print("")
print(f"Evolution finished. Best fitness = {ga_best_fitness:.4f}")

best = ga_best_individual 

# ---------------------------------------------------------
# Replay the best gait
# ---------------------------------------------------------
print("Replaying best individual...")
reset_to_standing()
while True:                
    for vector_index, vector in enumerate(best):
        set_one_leg_from_vector(vector, vector_index)
        for _ in range(5):
            if robot.step(timestep) == -1:
                exit()
                
# =========================================================
# HOLD POSITION
# =========================================================

print("")
print("Robot is holding its position.")

while robot.step(timestep) != -1:

    pass
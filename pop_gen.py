#A function to generate a population based on a chromosome. (Input: Population size, Chromosome. Output: starting population) 
#Takes a population (10 or something) and a blueprint (list of lists   300x24)

#have limits

import random

def pop_gen(pop_size, chromosome):
    pop = [[]]*pop_size
    for i in range(pop_size):
        for j in range(len(chromosome)):
            for k in range(0, len(chromosome[j]), 3):
                chromosome[j][k] = random.randint(-157,157)/100
                chromosome[j][k+1] = random.randint(-200,100)/100
                chromosome[j][k+2] = random.randint(-157,157)/100
        pop[i] = chromosome
    return pop


pop_size = 10
chromosome = [[[]]*24]*300

pop = pop_gen(pop_size, chromosome)

print(pop, len(pop), len(pop[0]), len(pop[0][0]))

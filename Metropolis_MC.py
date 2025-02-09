## Import libraries
import argparse
from pickletools import float8
import numpy as np
import matplotlib.pyplot as plt
from tqdm import trange, tqdm
from tqdm import tqdm, trange
import wandb
import networkx as nx
import pandas as pd

from LS_Algorithm import get_nme

## Initialization and supplementary functions

def adj_matrix(G):
    '''
    creates adj and neighbors:
    adj: 2D adjacency matrix of a graph
    neighbors: list of lists of neighbors (indexes from 0 to N-1, where N is a number of nodes)
    '''
    adj = nx.to_numpy_array(G)
 
    neighbors = []
    for i in range(nx.number_of_nodes(G)):
        neighbors_ = [neighbor for neighbor in nx.neighbors(G, i)]
        neighbors.append(neighbors_)
    return adj, neighbors


def system_initialization(G, N_sensors, random_state=None):
    '''
    - Uses previously stated function adj_matrix to initialize 
    all needed information about graph
    - Initializes sensors positions
    ----------------------------------
    G: graph
    adj: adjacency matrix
    N_sensors: number of sensors
    sensors: ndarray of sensors' indexes 
    '''
    n = nx.number_of_edges(G)
    N_nodes = nx.number_of_nodes(G)

    adj, neighbors = adj_matrix(G)
    if random_state is None:
        sensors = np.array([(N_nodes*i)//N_sensors for i in range(N_sensors)])
    else:
        rng_gen = np.random.RandomState(random_state)
        sensors = rng_gen.choice(np.arange(N_nodes), N_sensors)

    return adj, neighbors, sensors

## Metropolis algorithm

def step(sensors, E_tot, Statistics, neighbors, adj):
    '''
    one step of a Metropolis algorithm cycle:

    1. shifts one random sensor to the neighboring node
    2. calculates the difference in energy
    3. accepts\rejects new location of the sensor
    '''

    # choose the random sensor which can be shifted
    while(True):
        choice = rng.choice
        old_sensor_number = choice(np.arange(N_sensors)) # from 0 to max number of sensors
        old_node_number = sensors[old_sensor_number] # number on a graph - from 0 to 284

        num_of_neighbors = len(neighbors[old_node_number])
        # skip to the next step if there are no neighbors
        if num_of_neighbors == 0:
            # no neighbors
            continue

        # choose the random neighboring node of the chosen one
        neighboring_unoccupied_locs = [neighbor_number for neighbor_number in neighbors[old_node_number]
                                       if neighbor_number not in sensors]
        num_of_unoccupied_neghbors = len(neighboring_unoccupied_locs)
        if num_of_unoccupied_neghbors == 0:
            # no unoccupied neghbors
            continue
        neighboring_loc = choice(neighboring_unoccupied_locs)
        new_node_number = neighbors[old_node_number][neighboring_loc]
        break

    #shift the sensor
    # sensors_new = np.delete(sensors, old_sensor_number) 
    # sensors_new = np.append(sensors_new, new_node_number)
    sensors_new = sensors.copy()
    sensors_new[old_sensor_number] = new_node_number
    # calculate the difference in energy
    E_new = get_nme(sensors_new, ks, G)
    dE = E_new - E_tot
    # accept/reject
    dp = np.exp(-dE/T)
    rand = rng.random()
    wandb.log({'E/random': rand, 'E/acceptance probability': dp}, commit=False)
    if dp > rand:
        # accept
        E_tot = E_new
        Statistics[0] +=1
        return sensors_new, E_tot, Statistics
    else:
        # reject
        #return the sensor back
        Statistics[1] +=1
        return sensors, E_tot, Statistics

    
def cycle(sensors, E_tot, neighbors, adj, steps):
    '''
    cycle of metropolis algorithm's steps
    stores information about energy levels during the simulation
    '''
    sensors_loc_df.loc[0] = sensors
    Statistics = np.array([0.,  # 'accepted'
                           0.]) # 'rejected'

    best_sensor_loc = sensors.copy()
    E_min = E_tot
    # best_step = 0


    for i in trange(1,steps+1):
        sensors, E_tot, Statistics = step(sensors, E_tot, 
                                          Statistics, neighbors, adj)
        sensors_loc_df.loc[i] = sensors
        if E_tot < E_min:
            best_sensor_loc = sensors.copy()
            
            E_min = E_tot
            best_step = i
            wandb.log({'E/Emin': E_min, 'Best sensor location': best_sensor_loc, 'best step': best_step},commit=False)
        
        wandb.log({'E/E': E_tot, 'Statistics/accepted':Statistics[0], 
                   'Statistics/rejected':Statistics[1]})
        
    Statistics /= steps
    return sensors, E_tot, Statistics,\
           best_sensor_loc, E_min

def simulation(adj, neighbors, sensors, steps):
    '''
    does the simulation and returns numerical results
    '''
    E_tot = get_nme(sensors, ks, G)
    sensors, E_tot, Statistics, best_sensor_loc, E_min =\
        cycle(sensors, E_tot, neighbors, adj, steps)
    print(f'E min: {E_min}\n best location:{best_sensor_loc}')
    # verification of right energy calculation
    E_fin = get_nme(sensors, ks, G)
    assert np.isclose(E_fin, E_tot), f'E_fin={E_fin}, E_tot={E_tot}'

    return sensors, Statistics, \
           best_sensor_loc, E_min

def init_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--T',default=0.01, type=float)
    parser.add_argument('--N_sensors',default=5, type=int)
    parser.add_argument('--random_state',default=None, type=int)
    parser.add_argument('--steps',default=10_000, type=int)
    return parser.parse_args()

if __name__ == '__main__':
    ks = 2 #coarse_graining grid size
    G = nx.read_gpickle(f"pore_network_0{ks}.gpickle")
    rng = np.random.RandomState(42)
    args = init_parser()
    hyperparameter_defaults = dict(
        steps = 10**4
        )
    wandb.init(config=hyperparameter_defaults, entity="emmanuel-vsevolod")
    wandb.config.update(args)

    config = wandb.config
    T = config.T
    N_sensors = config.N_sensors
    steps = config.steps
    random_state = config.random_state
    sensors_loc_df = pd.DataFrame(columns=np.arange(N_sensors))
    adj, neighbors, sensors = system_initialization(G, N_sensors, random_state)
    sensors, Statistics, best_sensor_loc, E_min =\
        simulation(adj, neighbors, sensors, steps)
    wandb.log({'sensors movement table': sensors_loc_df}, commit=False)
    data = {"best_location":best_sensor_loc}
    df = pd.DataFrame(data)
    best_loc_table = wandb.Table(data=df)
    wandb.log({'best location table':best_loc_table}, commit=False)
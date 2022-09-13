import pandas as pd
import numpy as np
import networkx as nx
from LS_Algorithm import get_node_pos_dict

import matplotlib.animation as animation
import matplotlib.pyplot as plt



ks = 2 #coarse_graining grid size
G = nx.read_gpickle(f"pore_network_0{ks}.gpickle")
df = pd.read_csv('25sensors_sensormovement.csv')
pos = get_node_pos_dict(G, np.arange(G.number_of_nodes()))

fig, ax = plt.subplots(figsize=(24, 24))
nodes = nx.draw_networkx_nodes(G, pos, node_color='gray')
edges = nx.draw_networkx_edges(G, pos)

def animate(i):
    sensors = list(df.iloc[i])
    ax.set_title('Step {:>3d}'.format(i), fontsize=32)
    all_colors = ['']*G.number_of_nodes()
    for i in range(G.number_of_nodes()):
        if i in sensors:
            all_colors[i] = i/G.number_of_nodes()
        else:
            all_colors[i] = 0
    nodes.set_array(all_colors)

anim = animation.FuncAnimation(fig, animate, frames = 100, blit=False, interval=20, repeat=False )
savefile = '25sensors.gif'
pillowwriter = animation.PillowWriter(fps=60)
anim.save(savefile, writer=pillowwriter)

# plt.show()
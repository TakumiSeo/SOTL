from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import datetime
import numpy as np
import warnings
warnings.simplefilter('ignore')

# FOR SIT PC
# if 'SUMO_HOME' in os.environ:
#     tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
#     sys.path.append(tools)
# else:
#     sys.exit("please declare environment variable 'SUMO_HOME'")

# FOR my ubuntu laptop
os.system("export SUMO_HOME=/usr/share/sumo")
try:
    sys.path.append("/usr/share/sumo/tools")
except ImportError:
    sys.exit("please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')")
import traci
from utils import import_train_configuration, set_sumo
from gen_vp import TrafficGenerator
# from dqn_net import DeepQNetwork
# from memory import Memory


def run(sumo_cmd, max_steps):
    step = 0
    traci.start(sumo_cmd)
    while step < max_steps:
        traci.simulationStep()
        id_list = traci.person.getIDList()
        for i, id in enumerate(id_list):
            if id == 'p0':
                pass
            # print('{}:{}:{}'.format(i, id, traci.person.getWaitingTime(id)))
            print('{}:{}:{}'.format(i, id, traci.person.getLaneID(id)))
        step += 1
    traci.close()
    sys.stdout.flush()


if __name__ == '__main__':
    config = import_train_configuration(config_file='sim.ini')
    sumo_cmd_f = set_sumo(config['gui'], config['sumocfg_file_name'], config['max_steps'])

    print('config:{}'.format(config))
    print('sumo_cmd:{}'.format(sumo_cmd_f))

    TrafficGen = TrafficGenerator(
        max_steps=config['max_steps'],
        n_cars_generated=config['n_cars_generated'],
        n_peds_generated=config['n_peds_generated']
    )

    TrafficGen.generate_routefile(seed=5400)

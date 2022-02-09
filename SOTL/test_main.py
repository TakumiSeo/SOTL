from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import optparse
import datetime
import numpy as np
import warnings
warnings.simplefilter('ignore')
os.system("export SUMO_HOME=/usr/share/sumo")
try:
    sys.path.append("/usr/share/sumo/tools")
except ImportError:
    sys.exit("please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')")

from sumolib import checkBinary
import traci
from utils import import_train_configuration, set_sumo

PHASE_NS_GREEN = 0  # action 0 code 00
PHASE_NS_YELLOW = 1
PHASE_NSL_GREEN = 2  # action 1 code 01
PHASE_NSL_YELLOW = 3
PHASE_EW_GREEN = 4  # action 2 code 10
PHASE_EW_YELLOW = 5
PHASE_EWL_GREEN = 6  # action 3 code 11
PHASE_EWL_YELLOW = 7


def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true",
                          default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options


# contains TraCI control loop
# 目的は信号の切り替えを自由に行うこと
def run(sumo_cmd, max_steps):
    step = 0
    traci.start(sumo_cmd)
    while step < max_steps:
        traci.simulationStep()
        print(green_phases())
        # if step % 3 == 0:
        #     traci.trafficlight.setPhase("TL", PHASE_NS_GREEN)
        # elif (step % 20 == 0) and (step % 3 != 0):
        #     traci.trafficlight.setPhase("TL", PHASE_EW_GREEN)
        # print(traci.trafficlight.getPhase('TL'))
        step += 1

    traci.close()
    sys.stdout.flush()

def green_phases():
    logic = traci.trafficlight.getCompleteRedYellowGreenDefinition('TL')[0]
    #get only the green phases
    green_phases = [p.state for p in logic.getPhases()
                    if 'y' not in p.state
                    and ('G' in p.state or 'g' in p.state)]

    #sort to ensure parity between sims (for RL actions)
    return sorted(green_phases)

# main entry point
if __name__ == "__main__":
    config = import_train_configuration(config_file='sim.ini')
    sumo_cmd_f = set_sumo(config['nogui'], config['sumocfg_file_name'], config['max_steps'])
    max_steps = config['max_steps']
    net_file = {'cfg': 'intersection/sumo_config_japan.sumocfg',
                'net': 'intersection/environment_japan.net.xml'}
    run(sumo_cmd_f, max_steps)

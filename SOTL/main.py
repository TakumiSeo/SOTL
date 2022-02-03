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
from SOTL.src.distprocs import DistProcs

def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true",
                          default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options


# contains TraCI control loop
def run(sumo_cmd, max_steps):
    step = 0
    traci.start(sumo_cmd)
    while step < max_steps:
        traci.simulationStep()
        step += 1

    traci.close()
    sys.stdout.flush()


# main entry point
if __name__ == "__main__":
    config = import_train_configuration(config_file='sim.ini')
    sumo_cmd_f = set_sumo(config['nogui'], config['sumocfg_file_name'], config['max_steps'])
    max_steps = config['max_steps']
    net_file = {'cfg':'intersection/sumo_config_japan.sumocfg',
                'net':'intersection/environment_japan.net.xml'}
    traci.start(sumo_cmd_f)
    DistProcs(netfiles=net_file, trc=traci, sim_len=max_steps, nogui=config['nogui'], demand=config['demand'])


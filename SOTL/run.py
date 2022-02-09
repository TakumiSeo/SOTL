import os, sys, time
import warnings
warnings.simplefilter('ignore')
os.system("export SUMO_HOME=/usr/share/sumo")
try:
    sys.path.append("/usr/share/sumo/tools")
except ImportError:
    sys.exit("please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')")

from SOTL.src.distprocs import DistProcs
from sumolib import checkBinary
import traci
from utils import import_train_configuration, set_sumo


def main():
    start_t = time.time()
    print('start running main')
    config = import_train_configuration(config_file='sim.ini')

    sumo_cmd_f = set_sumo(config['nogui'], config['sumocfg_file_name'], config['max_steps'])

    params = {'nogui': config['nogui'], 'demand': config['demand'], 'mode': config['mode'],
              'r': config['red'], 'y': config['yellow'], 'g_min': config['green'],
              'tsc': config['tsc'], 'mu': config['mu'], 'theta': config['theta'], 'omega': config['omega']}

    max_steps = config['max_steps']
    net_file = {'cfg': 'intersection/sumo_config_jap_test.sumocfg',
                'net': 'intersection/env_jap_test.net.xml'}

    traci.start(sumo_cmd_f)

    distprocs = DistProcs(netfiles=net_file, trc=traci, sim_len=max_steps, nogui=config['nogui'],
              demand=config['demand'], offset=0.25, params=params, sumo_cmd=sumo_cmd_f)

    distprocs.run()
    queue_length = distprocs.get_queue_length_data()

    with open(os.path.join('save_data/', 'plot_queue' + '_data.txt'), "w") as file:
        for value in queue_length:
            file.write("%s\n" % value)

if __name__ == '__main__':
    main()
from SOTL.utils import import_train_configuration, set_sumo
from SOTL.sotl_run import SimSOTL
from SOTL.generator import TrafficGenerator
def run_test():
    print('start running main')
    config = import_train_configuration(config_file='sim.ini')

    sumo_cmd_f = set_sumo(config['nogui'], config['sumocfg_file_name'], config['max_steps'])

    params = {'nogui': config['nogui'], 'demand': config['demand'], 'mode': config['mode'],
              'r': config['red'], 'y': config['yellow'], 'g_min': config['green'],
              'tsc': config['tsc'], 'mu': config['mu'], 'theta': config['theta'], 'omega': config['omega']}

    max_steps = config['max_steps']
    net_file = {'cfg': 'intersection/sumo_config_japan.sumocfg',
                'net': 'intersection/environment_japan.net.xml'}
    traffic_gen = TrafficGenerator(max_steps=max_steps, n_cars_generated=1000)

    sim_sotl = SimSOTL(TrafficGen=traffic_gen, params=params, sumo_cmd=sumo_cmd_f, netdata=)
import configparser
from sumolib import checkBinary
import os
import sys

def import_train_configuration(config_file):
    content = configparser.ConfigParser()
    content.read(config_file)
    config = {}
    config['nogui'] = content['simulation'].getboolean('nogui')
    config['demand'] = content['simulation'].get('demand')
    config['total_episodes'] = content['simulation'].getint('total_episodes')
    config['max_steps'] = content['simulation'].getint('max_steps')
    config['sumocfg_file_name'] = content['dir']['sumocfg_file_name']
    config['red'] = content['simulation'].getint('red')
    config['green'] = content['simulation'].getint('green')
    config['yellow'] = content['simulation'].getint('yellow')
    config['mode'] = content['simulation'].get('mode')
    config['tsc'] = content['tsc'].get('tsc')
    config['mu'] = content['tsc'].getint('mu')
    config['theta'] = content['tsc'].getint('theta')
    config['omega'] = content['tsc'].getint('omega')

    return config


def set_sumo(nogui, sumocfg_file_name, max_steps):
    """
    Configure various parameters of SUMO
    """
    # setting the cmd mode or the visual mode
    if nogui == True:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # setting the cmd command to run sumo at simulation time
    sumo_cmd = [sumoBinary, "-c", os.path.join('intersection', sumocfg_file_name), "--no-step-log", "true",
                "--waiting-time-memory", str(max_steps), '--collision.action', 'teleport']

    return sumo_cmd


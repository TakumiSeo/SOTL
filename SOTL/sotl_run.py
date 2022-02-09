import os, sys
import numpy as np
import timeit
from collections import deque
import warnings
warnings.simplefilter('ignore')
os.system("export SUMO_HOME=/usr/share/sumo")
try:
    sys.path.append("/usr/share/sumo/tools")
except ImportError:
    sys.exit("please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')")
import traci
# phase codes based on environment.net.xml
PHASE_NS_GREEN = 0  # action 0 code 00
PHASE_NS_YELLOW = 1
PHASE_NSL_GREEN = 2  # action 1 code 01
PHASE_NSL_YELLOW = 3
PHASE_EW_GREEN = 4  # action 2 code 10
PHASE_EW_YELLOW = 5
PHASE_EWL_GREEN = 6  # action 3 code 11
PHASE_EWL_YELLOW = 7

class SimSOTL:
    def __init__(self, TrafficGen, params, sumo_cmd, netdata):
        self._TrafficGen = TrafficGen
        self.g_min = params['g_min']
        self.theta = params['theta']
        self.mu = params['mu']
        self.omega = params['omega']
        self.max_steps = params['max_steps']
        self.kappa = 0
        self.sumo_cmd = sumo_cmd
        self.time_in_phase = 0
        self.phase_index = 0
        self.g_phases = self.green_phases()
        self.phase_red_lanes = self.get_phase_red_lanes()
        self.phase_deque = deque([self.g_phases[self.phase_index]])
        self.all_red = len((self.g_phases[0]))*'r'
        self.phase = self.all_red
        self.netdata = netdata
        self.phase_lanes = self.phase_lanes(self.g_phases)

    def run(self, episode):
        start_time = timeit.default_timer()
        self._TrafficGen.generate_rutefile(seed=episode)
        traci.start(self.sumo_cmd)
        print('Simulating')
        while self.time_in_phase < self.max_steps:
            next_phase = self.next_phase()
            self.simulate(next_phase)
            traci.simulationStep()
            print(self.time_in_phase)


    def next_phase(self):
        max_lane = None
        light_phase = traci.trafficlight.getPhase('TL')
        ap_red, ap_red_len = self.red_approach(light_phase=light_phase)
        n = max(ap_red_len)
        self.kappa += n
        max_lane = max(ap_red_len, key=ap_red_len.get)
        if self.time_in_phase >= self.g_min:
            if n > self.mu or n == 0:
                if self.kappa > self.theta:
                    self.phase_index += 1
                    self.kappa = 0
        next_green = self.g_phases[self.phase_index % len(self.green_phases())]
        phases = self.get_intermediate_phases(self.phase, next_green)
        self.phase_deque.extend(phases+[next_green])

        next_phase = self.phase_deque.popleft()
        if next_phase is not self.phase:
            self.time_in_phase = 0

        return next_phase

    def simulate(self, next_phase):
        pass

    def get_phase_red_lanes(self):
        all_incoming_lanes = []
        for g in self.green_phases():
            all_incoming_lanes.extend(self.phase_lanes[g])
        all_incoming_lanes = set(all_incoming_lanes)

        #store all lanes that are red
        #under any given green phase
        phase_red_lanes = {}
        for g in self.green_phases():
            phase_red_lanes[g] = all_incoming_lanes - set(self.phase_lanes[g])

        return phase_red_lanes
    def green_phases(self):
        logic = traci.trafficlight.getCompleteRedYellowGreenDefinition('TL')[0]
        #get only the green phases
        green_phases = [p.state for p in logic.getPhases()
                        if 'y' not in p.state
                        and ('G' in p.state or 'g' in p.state)]

        #sort to ensure parity between sims (for RL actions)
        return sorted(green_phases)

    def get_intermediate_phases(self, phase, next_phase):
        if phase == next_phase or phase == self.all_red:
            return []
        else:
            yellow_phase = ''.join([p if p == 'r' else 'y' for p in phase])
            return [yellow_phase, self.all_red]
    def phase_lanes(self, actions):
        phase_lanes = {a:[] for a in actions}
        for a in actions:
            green_lanes = set()
            red_lanes = set()
            for s in range(len(a)):
                if a[s] == 'g' or a[s] == 'G':
                    green_lanes.add(self.netdata['inter']['TL']['tlsindex'][s])
                elif a[s] == 'r':
                    red_lanes.add(self.netdata['inter']['TL']['tlsindex'][s])

            ###some movements are on the same lane, removes duplicate lanes
            pure_green = [l for l in green_lanes if l not in red_lanes]
            if len(pure_green) == 0:
                phase_lanes[a] = list(set(green_lanes))
            else:
                phase_lanes[a] = list(set(pure_green))
        return phase_lanes

    def red_approach(self, light_phase):
        red_lane_dict = {'NS': [], 'NSL': [], 'EW': [], 'EWL': []}
        red_lane_len_dict = {'0': 0, '2': 0, '4': 0, '6': 0}
        light_0_list = ['N2TL_0', 'N2TL_1', 'N2TL_2', 'S2TL_0', 'S2TL_1', 'S2TL_2']
        light_2_list = ['N2TL_3', 'S2TL_3']
        light_4_list = ['E2TL_0', 'E2TL_1', 'E2TL_2', 'W2TL_0', 'W2TL_1', 'W2TL_2']
        light_6_list = ['E2TL_3', 'W2TL_3']
        car_list = traci.vehicle.getIDList()
        for car_id in car_list:
            road_id = traci.vehicle.getRoadID(car_id)
            if light_phase == 0:
                if road_id not in light_0_list:
                    if ('N_E' in car_id) or ('S_W' in car_id):
                        red_lane_dict['NSL'].append(car_id)
                    elif ('E_W' in car_id) or ('W_E' in car_id):
                        red_lane_dict['EW'].append(car_id)
                    elif ('E_S' in car_id) or ('W_N' in car_id):
                        red_lane_dict['EWL'].append(car_id)
                    else:
                        pass
            elif light_phase == 2:
                if road_id not in light_2_list:
                    if ('N_S' in car_id) or ('S_N' in car_id):
                        red_lane_dict['NS'].append(car_id)
                    elif ('E_W' in car_id) or ('W_E' in car_id):
                        red_lane_dict['EW'].append(car_id)
                    elif ('E_S' in car_id) or ('W_N' in car_id):
                        red_lane_dict['EWL'].append(car_id)
                    else:
                        pass
            elif light_phase == 4:
                if road_id not in light_4_list:
                    if ('N_S' in car_id) or ('S_N' in car_id):
                        red_lane_dict['NS'].append(car_id)
                    elif ('N_E' in car_id) or ('S_W' in car_id):
                        red_lane_dict['NSL'].append(car_id)
                    elif ('E_S' in car_id) or ('W_N' in car_id):
                        red_lane_dict['EWL'].append(car_id)
                    else:
                        pass
            elif light_phase == 6:
                if road_id not in light_6_list:
                    if ('N_S' in car_id) or ('S_N' in car_id):
                        red_lane_dict['NS'].append(car_id)
                    elif ('N_E' in car_id) or ('S_W' in car_id):
                        red_lane_dict['NSL'].append(car_id)
                    elif ('E_W' in car_id) or ('W_E' in car_id):
                        red_lane_dict['EW'].append(car_id)
                    else:
                        pass

        for k in red_lane_dict.keys():
            if k is '0':
                red_lane_len_dict['NS'] = len(red_lane_dict[k])
            elif k is '2':
                red_lane_len_dict['NSL'] = len(red_lane_dict[k])
            elif k is '4':
                red_lane_len_dict['EW'] = len(red_lane_dict[k])
            elif k is '6':
                red_lane_len_dict['EWL'] = len(red_lane_dict[k])
            else:
                pass
        return red_lane_dict, red_lane_len_dict





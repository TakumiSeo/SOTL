import os, sys, copy
import numpy as np

from SOTL.src.trafficmetrics import TrafficMetrics

class TrafficSignalController:
    """Abstract base class for all traffic signal controller.
    Build your own traffic signal controller by implementing the follow methods.
    """
    def __init__(self, trc, tsc_id, mode, netdata, red_t, yellow_t):
        self.trc = trc
        self.id = tsc_id
        self.netdata = netdata
        self.red_t = red_t
        self.yellow_t = yellow_t
        self.green_phases = self.get_tl_green_phases()
        self.phase_time = 0
        self.all_red = len((self.green_phases[0]))*'r'
        self.phase = self.all_red
        self.phase_lanes = self.phase_lanes(self.green_phases)
        #create subscription for this traffic signal junction to gather
        #vehicle information efficiently
        self.trc.junction.subscribeContext(tsc_id, self.trc.constants.CMD_GET_VEHICLE_VARIABLE, 150,
                                            [self.trc.constants.VAR_LANEPOSITION,
                                             self.trc.constants.VAR_SPEED,
                                             self.trc.constants.VAR_LANE_ID])
        #get all incoming lanes to intersection
        self.incoming_lanes = set()
        for p in self.phase_lanes:
            for l in self.phase_lanes[p]:
                self.incoming_lanes.add(l)

        self.incoming_lanes = sorted(list(self.incoming_lanes))
        #lane capacity is the lane length divided by the average vehicle length+stopped headway
        self.lane_capacity = np.array([float(self.netdata['lane'][lane]['length'])/7.5 for lane in self.incoming_lanes])
        #for collecting various traffic metrics at the intersection
        #can be extended in trafficmetric.py class to collect new metrics
        self.metric_args = ['queue', 'delay']
        self.trafficmetrics = TrafficMetrics(tsc_id, self.incoming_lanes, netdata, self.metric_args, mode)

        self.ep_rewards = []

    def run(self):
        data = self.get_subscription_data()
        self.trafficmetrics.update(data)
        self.update(data)
        self.increment_controller()

    def get_metrics(self):
        for m in self.metric_args:
            metric = self.trafficmetrics.get_metric(m)
            print(metric)

    def get_traffic_metrics_history(self):
        return {m: self.trafficmetrics.get_history(m) for m in self.metric_args}

    def increment_controller(self):
        if self.phase_time == 0:
            ###get new phase and duration
            next_phase = self.next_phase()
            self.trc.trafficlight.setRedYellowGreenState(self.id, next_phase)
            self.phase = next_phase
            self.phase_time = self.next_phase_duration()
        self.phase_time -= 1

    def get_intermediate_phases(self, phase, next_phase):
        if phase == next_phase or phase == self.all_red:
            return []
        else:
            yellow_phase = ''.join([p if p == 'r' else 'y' for p in phase])
            return [yellow_phase, self.all_red]

    def next_phase(self):
        raise NotImplementedError("Subclasses should implement this!")

    def next_phase_duration(self):
        raise NotImplementedError("Subclasses should implement this!")

    def update(self, data):
        """Implement this function to perform any
           traffic signal class specific control/updates
        """
        raise NotImplementedError("Subclasses should implement this!")

    def get_subscription_data(self):
        #use SUMO subscription to retrieve vehicle info in batches
        #around the traffic signal controller
        tl_data = self.trc.junction.getContextSubscriptionResults(self.id)
        #create empty incoming lanes for use else where
        lane_vehicles = {l: {} for l in self.incoming_lanes}
        if tl_data is not None:
            for v in tl_data:
                lane = tl_data[v][self.trc.constants.VAR_LANE_ID]
                if lane not in lane_vehicles:
                    lane_vehicles[lane] = {}
                lane_vehicles[lane][v] = tl_data[v]
        return lane_vehicles

    def get_tl_green_phases(self):
        logic = self.trc.trafficlight.getCompleteRedYellowGreenDefinition(self.id)[0]
        #get only the green phases
        green_phases = [p.state for p in logic.getPhases()
                         if 'y' not in p.state
                         and ('G' in p.state or 'g' in p.state)]

        #sort to ensure parity between sims (for RL actions)
        return sorted(green_phases)

    def phase_lanes(self, actions):
        phase_lanes = {a:[] for a in actions}
        for a in actions:
            green_lanes = set()
            red_lanes = set()
            for s in range(len(a)):
                if a[s] == 'g' or a[s] == 'G':
                    green_lanes.add(self.netdata['inter'][self.id]['tlsindex'][s])
                elif a[s] == 'r':
                    red_lanes.add(self.netdata['inter'][self.id]['tlsindex'][s])
            ###some movements are on the same lane, removes duplicate lanes
            pure_green = [l for l in green_lanes if l not in red_lanes]
            if len(pure_green) == 0:
                phase_lanes[a] = list(set(green_lanes))
            else:
                phase_lanes[a] = list(set(pure_green))
        return phase_lanes

    #helper functions for rl controllers
    def input_to_one_hot(self, phases):
        identity = np.identity(len(phases))
        one_hots = {phases[i]:identity[i,:]  for i in range(len(phases))}
        return one_hots

    def int_to_input(self, phases):
        return { p:phases[p] for p in range(len(phases)) }

    def get_state(self):
        #the state is the normalized density of all incoming lanes
        return np.concatenate([self.get_normalized_density(), self.get_normalized_queue()])

    def get_normalized_density(self):
        #number of vehicles in each incoming lane divided by the lane's capacity
        return np.array([len(self.data[lane]) for lane in self.incoming_lanes])/self.lane_capacity

    def get_normalized_queue(self):
        lane_queues = []
        for lane in self.incoming_lanes:
            q = 0
            for v in self.data[lane]:
                if self.data[lane][v][self.trc.constants.VAR_SPEED] < 0.3:
                    q += 1
            lane_queues.append(q)
        return np.array(lane_queues)/self.lane_capacity

    def empty_intersection(self):
        for lane in self.incoming_lanes:
            if len(self.data[lane]) > 0:
                return False
        return True

    def get_reward(self):
        #return negative delay as reward
        delay = int(self.trafficmetrics.get_metric('delay'))
        if delay == 0:
            r = 0
        else:
            r = -delay

        self.ep_rewards.append(r)
        return r

    def empty_dtse(self, n_lanes, dist, cell_size):
        return np.zeros((n_lanes, int(dist/cell_size)+3 ))

    def phase_dtse(self, phase_lanes, lane_to_int, dtse):
        phase_dtse = {}
        for phase in phase_lanes:
            copy_dtse = np.copy(dtse)
            for lane in phase_lanes[phase]:
                copy_dtse[lane_to_int[lane],:] = 1.0
            phase_dtse[phase] = copy_dtse
        return phase_dtse


    def get_dtse(self):
        dtse = np.copy(self._dtse)
        for lane,i in zip(self.incoming_lanes, range(len(self.incoming_lanes))):
            for v in self.data[lane]:
                pos = self.data[lane][v][self.trc.constants.VAR_LANEPOSITION]
                dtse[i, pos:pos+1] = 1.0

        return dtse
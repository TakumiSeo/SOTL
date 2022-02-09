import numpy as np
from sumolib import checkBinary
from SOTL.src.trafficsignalcontroller import TrafficSignalController
from SOTL.src.vehiclegen import VehicleGen
from SOTL.src.tscfactory import tsc_factory as tsc_f


class SumoSim:
    def __init__(self, trc, cfg_fp, sim_len, tsc, nogui, netdata, demand):
        self.trc = trc
        self.cfg_fp = cfg_fp
        self.sim_len = sim_len
        self.tsc = tsc
        self.sumo_cmd = 'sumo' if nogui else 'sumo-gui'
        self.netdata = netdata
        self.demand = demand
        self.queue_length = []

    def gen_sim(self):
        sumoBinary = checkBinary(self.sumo_cmd)
        self.t = 0
        self.v_start_times = {}
        self.v_travel_times = {}
        self.vehiclegen = None
        print('sumosim demand:{}'.format(self.demand))
        # self.vehiclegen = VehicleGen(self.trc,
        #                              self.netdata,
        #                              self.sim_len,
        #                              self.demand)
        print('generate simulation')

    def get_traffic_lights(self):
        #find all the junctions with traffic lights
        trafficlights = self.trc.trafficlight.getIDList()
        junctions = self.trc.junction.getIDList()
        tl_juncs = set(trafficlights).intersection(set(junctions))
        tls = []
        #only keep traffic lights with more than 1 green phase
        for tl in tl_juncs:
            #subscription to get traffic light phases
            self.trc.trafficlight.subscribe(tl, [self.trc.constants.TL_COMPLETE_DEFINITION_RYG])
            tldata = self.trc.trafficlight.getAllSubscriptionResults()
            logic = tldata[tl][self.trc.constants.TL_COMPLETE_DEFINITION_RYG][0]

            #for some reason this throws errors for me in SUMO 1.2
            #have to do subscription based above
            '''
            logic = self.conn.trafficlight.getCompleteRedYellowGreenDefinition(tl)[0] 
            '''
            #get only the green phases
            green_phases = [p.state for p in logic.getPhases()
                             if 'y' not in p.state
                             and ('G' in p.state or 'g' in p.state)]
            if len(green_phases) > 1:
                tls.append(tl)

        #for some reason these intersections cause problems with tensorflow
        #I have no idea why, it doesn't make any sense, if you don't believe me
        #then comment this and try it, if you an fix it you are the real MVP
        # if self.args.sim == 'lust':
        #     lust_remove = ['-12', '-78', '-2060']
        #     for r in lust_remove:
        #         if r in tls:
        #             tls.remove(r)
        return set(tls)

    def get_queue_length(self):
        halt_N = self.trc.edge.getLastStepHaltingNumber("N2TL")
        halt_S = self.trc.edge.getLastStepHaltingNumber("S2TL")
        halt_E = self.trc.edge.getLastStepHaltingNumber("E2TL")
        halt_W = self.trc.edge.getLastStepHaltingNumber("W2TL")
        queue_length = halt_N + halt_S + halt_E + halt_W
        return queue_length

    def update_netdata(self):
        tl_junc = self.get_traffic_lights()
        tsc = {tl: TrafficSignalController(self.trc, tl, 'test', self.netdata, 2, 3)
                for tl in tl_junc}

        for t in tsc:
            self.netdata['inter'][t]['incoming_lanes'] = tsc[t].incoming_lanes
            self.netdata['inter'][t]['green_phases'] = tsc[t].green_phases

        all_intersections = set(self.netdata['inter'].keys())
        #only keep intersections that we want to control
        for i in all_intersections - tl_junc:
            del self.netdata['inter'][i]

        return self.netdata

    def create_tsc(self, params):
        self.tl_junc = self.get_traffic_lights()
        # if not neural_networks:
        #     neural_networks = {tl:None for tl in self.tl_junc}
        #create traffic signal controllers for the junctions with lights
        self.tsc = {tl: tsc_f(tl=tl, params=params, netdata=self.netdata, trc=self.trc) for tl in self.tl_junc}

    def run_offset(self, offset):
        while self.t < offset:
            if self.vehiclegen:
                self.vehiclegen.run()
            self.update_travel_times()
            self.sim_step()

    def run(self):
        while self.t < self.sim_len:
            if self.vehiclegen:
                self.vehiclegen.run()
            self.update_travel_times()

            for t in self.tsc:
                self.tsc[t].run()
            self.store_queue_length(self.get_queue_length())
            self.sim_step()

    def store_queue_length(self, q):
        self.queue_length.append(q)

    def transfer_queue_length(self):
        return self.queue_length

    def sim_step(self):
        self.trc.simulationStep()
        self.t += 1

    def update_travel_times(self):
        for v in self.trc.simulation.getDepartedIDList():
            self.v_start_times[v] = self.t

        for v in self.trc.simulation.getArrivedIDList():
            self.v_travel_times[v] = self.t - self.v_start_times[v]
            del self.v_start_times[v]

    def get_travel_times(self):
        return [self.v_travel_times[v] for v in self.v_travel_times]

    def sim_stats(self):
        tt = self.get_travel_times()
        if len(tt) > 0:
            return [str(int(np.mean(tt))), str(int(np.std(tt)))]
        else:
            return [str(int(0.0)), str(int(0.0))]

    def get_tsc_metrics(self):
        tsc_metrics = {}
        for tsc in self.tsc:
            tsc_metrics[tsc] = self.tsc[tsc].get_traffic_metrics_history()
        return tsc_metrics

    def close(self):
        self.trc.close()

import numpy as np

class VehicleGen:
    def __init__(self, trc, netdata, sim_len, demand):
        np.random.seed()
        self.v_data = None
        self.vehicles_created = 0
        self.trc = trc
        self.netdata = netdata
        # for generating vehicles
        self.origins = self.netdata['origin']
        self.destinations = self.netdata['destination']
        self.add_origin_routes()
        self.sim_len = sim_len
        self.t = 0
        self.demand = demand
        self.gen_vehicles = self.gen_single()
        # elif self.demand == 'dynamic':
        #     mode = None
        #     self.v_schedule = self.gen_dynamic_demand(mode)
        #     self.gen_vehicles = self.gen_dynamic
        # else:
        #     print('pass')

    def run(self):
        self.gen_vehicles()
        self.t += 1

    def gen_dynamic(self):
        pass

    def gen_dynamic_demand(self, mode):
        pass

    def add_origin_routes(self):
        for origin in self.origins:
            self.trc.route.add(origin, [origin])

    def gen_single(self):
        if self.trc.vehicle.getIDCount() == 0:
            veh_spawn_edge = np.random.choice(self.origins)
            self.gen_veh([veh_spawn_edge])

    def gen_veh(self, veh_edges):
        for e in veh_edges:
            vid = e + str(self.vehicles_created)
            self.trc.vehicle.addFull(vid, e, departLane='best')
            self.set_veh_route(vid)
            self.vehicles_created += 1

    def set_veh_route(self, veh):
        current_edge = self.trc.vehicle.getRoute(veh)[0]
        route = [current_edge]
        while current_edge not in self.destinations:
            next_edge = np.random.choice(self.netdata['edge'][current_edge]['outgoing'])
            route.append(next_edge)
            current_edge = next_edge
        self.trc.vehicle.setRoute(veh, route)






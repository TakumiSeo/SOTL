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
        self.scale = 1.4
        self.t = 0
        self.demand = demand
        # if demand == 'single':
        #     self.gen_vehicles = self.gen_single()
        # elif demand == 'dynamic':
        self.v_schedule = self.gen_dynamic_demand('test')
        self.gen_vehicles = self.gen_dynamic()
        # else:
        #     print('pass')

    def run(self):
        self.gen_vehicles()
        # except:
        #     print('except')
        #     pass
        self.t += 1

    def gen_dynamic(self):
        ###get next set of edges from v schedule, use them to add new vehicles
        ###this is batch vehicle generation
        try:
            new_veh_edges = next(self.v_schedule)
            self.gen_veh(new_veh_edges)
        except StopIteration:
            print('no vehicles left')

    def add_origin_routes(self):
        for origin in self.origins:
            print(self.trc)
            self.trc.route.add(origin, [origin])

    def gen_single(self):
        print('gen single')
        if self.trc.vehicle.getIDCount() == 0:
            veh_spawn_edge = np.random.choice(self.origins)
            self.gen_veh([veh_spawn_edge])
            print(self.gen_veh([veh_spawn_edge]))

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

    def gen_dynamic_demand(self, mode):
        t = np.linspace(1*np.pi, 2*np.pi, self.sim_len)
        sine = np.sin(t) + 1.55
        v_schedule = []
        second = 1.0
        for t in range(int(self.sim_len)):
            n_veh = 0.0
            while second > 0.0:
                headway = np.random.exponential(sine[t], size=1)
                second -= headway
                if second > 0.0:
                    n_veh += 1
            second += 1.0
            v_schedule.append(int(n_veh))

        # randomly shift traffic pattern as a form of data augmentation
        random_shift = 0

        v_schedule = np.concatenate((v_schedule[random_shift:], v_schedule[:random_shift]))
        # zero out the last mins for better comparisons cuz of random shift
        v_schedule[-60:] = 0
        # randomly select from origins, these are where vehicles asre generated
        v_schedule = [np.random.choice(self.origins, size=int(self.scale*n_veh), replace=True)
                      if n_veh > 0 else [] for n_veh in v_schedule]
        return v_schedule.__iter__()






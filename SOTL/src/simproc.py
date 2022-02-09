import sys, os, time
from SOTL.src.sumosim import SumoSim
from SOTL.src.helper_funcs import get_time_now, check_and_make_dir
from SOTL.src.picklefuncs import save_data, load_data

class SimProc:
    def __init__(self, trc, cfg_fg, sim_len, tsc, nogui, netdata, demand, offset, params):
        self.sim = SumoSim(trc=trc, cfg_fp=cfg_fg, sim_len=sim_len, tsc=tsc,
                           nogui=nogui, netdata=netdata, demand=demand)
        self.offset = offset
        self.initial = True
        self.params = params

    def run(self):
        learner = False
        load = False
        neural_networks = None
        # print('sim proc '+str(self.idx)+' waiting at barrier ---------')
        # write_to_log(' ACTOR #'+str(self.idx)+' WAITING AT SYNC WEIGHTS BARRIER...')
        # self.barrier.wait()
        # write_to_log(' ACTOR #'+str(self.idx)+'  BROKEN SYNC BARRIER...')
        self.initial = False
        #just run one sim for stats
        self.run_sim(neural_networks)
        self.write_to_csv(self.sim.sim_stats())
        with open(str(1000)+'.csv', 'a+') as f:
            f.write('-----------------\n')
        self.write_sim_tsc_metrics()
        #self.write_travel_times()
        self.sim.close()
        print('------------------\nFinished on sim process '+' Closing\n---------------')


    def run_sim(self, neural_networks):
        start_t = time.time()
        self.sim.gen_sim()

        if self.initial is True:
            self.initial = False
            self.sim.run_offset(self.offset)

        self.sim.create_tsc(params=self.params)
        self.sim.run()

    def get_queue_length(self):
        q = self.sim.transfer_queue_length()
        return q

    def write_to_csv(self, data):
        with open('sotl_sim.csv', 'a+') as f:
            f.write(','.join(data)+'\n')

    def write_sim_tsc_metrics(self):
        tsc_metrics = self.sim.get_tsc_metrics()
        print(tsc_metrics)
        fname = get_time_now()
        path = 'metrics/'+str('sotl')
        for tsc in tsc_metrics:
            for m in tsc_metrics[tsc]:
                mpath = path + '/' + str(m) + '/' + str(tsc) + '/'
                check_and_make_dir(mpath)
                save_data(mpath+fname+'_.txt', tsc_metrics[tsc][m])
        travel_times = self.sim.get_travel_times()
        path += '/traveltime/'
        check_and_make_dir(path)
        save_data(path+fname+'.txt', travel_times)







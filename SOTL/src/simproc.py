import sys, os, time
from SOTL.src.sumosim import SumoSim

class SimProc:
    def __init__(self):
        pass

    def run(self):
        learner = False
        if self.args.load == True and self.args.mode == 'test':
            load = True
        else:
            load = False

        neural_networks = None

        # print('sim proc '+str(self.idx)+' waiting at barrier ---------')
        # write_to_log(' ACTOR #'+str(self.idx)+' WAITING AT SYNC WEIGHTS BARRIER...')
        # self.barrier.wait()
        # write_to_log(' ACTOR #'+str(self.idx)+'  BROKEN SYNC BARRIER...')
        # if self.args.l > 0 and self.args.mode == 'train':
        #     neural_networks = self.sync_nn_weights(neural_networks)
        #barrier
        #grab weights from learner or load from file
        #barrier
        #
        # if self.args.mode == 'train':
        #     while not self.finished_updates():
        #         self.run_sim(neural_networks)
        #         if (self.eps == 1.0 or self.eps < 0.02):
        #             self.write_to_csv(self.sim.sim_stats())
        #         #self.write_travel_times()
        #         self.sim.close()

        print(str(self.idx)+' test  waiting at offset ------------- '+str(self.offset))
        print(str(self.idx)+' test broken offset =================== '+str(self.offset))
        self.initial = False
        #just run one sim for stats
        self.run_sim(neural_networks)
        if self.mode == 'test':
            self.write_to_csv(self.sim.sim_stats())
            with open(str(1000)+'.csv','a+') as f:
                f.write('-----------------\n')
        self.write_sim_tsc_metrics()
        #self.write_travel_times()
        self.sim.close()
        print('------------------\nFinished on sim process '+str(self.idx)+' Closing\n---------------')



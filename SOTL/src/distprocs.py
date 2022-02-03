import sys, os, subprocess, time
import numpy as np
from SOTL.src.networkdata import NetworkData
from SOTL.src.sumosim import SumoSim


class DistProcs:
    def __init__(self, netfiles, trc, sim_len, nogui, demand):
        nd = NetworkData(netfiles['net'])
        netdata = nd.get_net_data()
        print('distproc demand:{}'.format(demand))
        sim = SumoSim(trc=trc, cfg_fp=netfiles['cfg'], sim_len=sim_len, nogui=nogui, netdata=netdata, demand=demand)
        sim.gen_sim()
        netdata = sim.update_netdata()
        sim.close()
        print('...finished with dummy sim\n')
        tsc_ids = netdata['inter'].keys()

    def create_mp_stats_dict(self, tsc_ids):
        ###use this mp shared dict for data between procs
        manager = Manager()
        rl_stats = manager.dict({})
        for i in tsc_ids:
            rl_stats[i] = manager.dict({})
            rl_stats[i]['n_exp'] = 0
            rl_stats[i]['updates'] = 0
            rl_stats[i]['max_r'] = 1.0
            rl_stats[i]['online'] = None
            rl_stats[i]['target'] = None
            rl_stats['n_sims'] = 0
            rl_stats['total_sims'] = 104
            rl_stats['delay'] = manager.list()
            rl_stats['queue'] = manager.list()
            rl_stats['throughput'] = manager.list()

        return rl_stats

    def get_exploration_rates(self, eps, n_actors, mode, net):
        if mode == 'test':
            return [eps for _ in range(n_actors)]
        elif mode == 'train':
            if net == 'lust':
                #for lust we restrict the exploration rates
                e = [1.0, 0.5, eps]
                erates = []
                for i in range(n_actors):
                    erates.append(e[i % len(e)])
                return erates
            else:
                return np.linspace(1.0, eps, num=n_actors)

    def get_start_offsets(self, mode, simlen, offset, n_actors):
        if mode == 'test':
            return [0]*n_actors
        elif mode == 'train':
            return np.linspace(0, simlen*offset, num=n_actors)


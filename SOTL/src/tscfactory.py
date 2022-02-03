from SOTL.trafficsignalcontrollers.sotltsc import SOTLTSC

def tsc_factory(tl, params, netdata, trc):
    return SOTLTSC(trc, tl, params['mode'], netdata, params['r'], params['y'],
                   params['g_min'], params['theta'], params['omega'],
                   params['mu'])
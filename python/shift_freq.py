from valon5009 import Valon5009
import time



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('f0', metavar='freq_ini', type=int, 
                        help='initial frequency')
    parser.add_argument('total_time', type=int, 
                        help='total time')
    parser.add_argument('delta_time', type=int,
                        help='time for each step in frequency')
    parser.add_argument('--inc', dest='inc_delta', type=float, default=1.0,
                        help='factor to increment delta_time after each step')
    parser.add_argument('--ch', dest='n_chan', type=int, default=2**14,
                        help='number of channels')
    parser.add_argument('--bw', dest='bw', type=float, default=250.0,
                        help='bandwidth')
    parser.add_argument('--dev', dest='dev', type=str, default='/dev/ttyUSB1',
                        help='dev for clock')

    args = parser.parse_args()

    clk = Valon5009(args.dev)
    f0 = args.f0
    bw = args.bw
    n_chan = args.n_chan
    step = bw / n_chan
    total_time = args.total_time
    delta_time = args.delta_time
    inc_delta = args.inc_delta
    t0 = time.time()
    while (time.time() - t0 < total_time):
        print ("[%lf] Setting freq %.6lf" % (time.time(), f0))
        clk.set_freq(1, f0)
        t1 = time.time()
        while (time.time() - t1 < delta_time):
            pass
        delta_time *= inc_delta
        f0 += step


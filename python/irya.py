#!/usr/bin/env python
'''
\nAuthor: Daniel Diaz, January 2018
'''

#TODO: add support for ADC histogram plotting.
#TODO: add support for determining ADC input level 

import corr,time,numpy,struct,sys,logging,pylab,matplotlib, time
from irya_libs import IryaRoach
import numpy as np
import os

integration_time = 1

#bitstream = 'spec_2018_Sep_21_1213.bof'
#bitstream = 'spec_2018_Sep_26_1205.bof'
katcp_port=7147

def exit_fail():
    print 'FAILURE DETECTED. Log entries:\n'#,lh.printMessages()
    try:
        fpga.stop()
    except: pass
    raise
    exit()

def exit_clean():
    try:
        fpga.stop()
    except: pass
    exit()

def get_data(channels=2048):
    #get the data...    
    acc_n = fpga.read_uint('acc_cnt')
    a_0=struct.unpack('>%dl' % int(channels/2),fpga.read('even',int(channels/2)*4,0))
    a_1=struct.unpack('>%dl' % int(channels/2),fpga.read('odd',int(channels/2)*4,0))

    interleave_a=[]

    for i in range(int(channels/2)):
        interleave_a.append(a_0[i])
        interleave_a.append(a_1[i])
    return acc_n, interleave_a 

def save_to_file(data,timestamp,integration_time,numchannels, bandwidth):
    fname = "%s%06d.dat" % (time.strftime('%Y%m%d%H%M%S', time.localtime(timestamp)), int((timestamp*1e6)%1e6))
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'datas')
    path = os.path.join(path, fname)
    f = open(path, "wb")
    f.write(struct.pack(">dddi%dl" % numchannels, timestamp, integration_time, bandwidth, int(numchannels),*data))
    f.close()

def read_bw():
    global clk, bw
    oldbw = bw
    try:
        if not (clk.isOpen()):
            clk.open()
        bw = clk.get_freq()[1]/2.
        clk.close()
    except:
        bw = oldbw
    return(bw)

def plot_spectrum():
    global channel_max, last_acc, last_time,  bw, clk, integration_time, channels, specs, savefile
    acc_n, interleave_a = get_data(channels)
    interleave_a = np.asarray(interleave_a)
    interleave_a[0:5] = 0
    interleave_a[-5:] = 0
    if last_acc != acc_n:
        t = time.time()
        last_acc = acc_n


        interleave_a[np.where(interleave_a == 0)] = 1
        matplotlib.pyplot.clf()
        matplotlib.pylab.plot(np.linspace(0,bw,channels), 10*np.log10(interleave_a))
        #matplotlib.pylab.semilogy(np.linspace(0,bw,channels), interleave_a)
        matplotlib.pylab.title('Integration number %i.'%acc_n)
        matplotlib.pylab.ylabel('Power (arbitrary units)')
        matplotlib.pylab.ylim(0)
        matplotlib.pylab.grid()
        #matplotlib.pylab.xlabel('Channel')
        #matplotlib.pylab.xlim(0,channels)
        matplotlib.pylab.xlabel('Freq (MHz)')
        fig.canvas.draw()
        if np.argmax(interleave_a) != channel_max:
            channel_max = np.argmax(interleave_a)
            #print (channel_max)
        if (acc_n > 0):
            #bw = read_bw()
            if (savefile):
                save_to_file(interleave_a, t, t-last_time, channels, bw)
            msg = "Accumulation time = %.4lf seconds." % (t - last_time)
            last_time = t
            msg = "%s Detection in channel %d.\r" % (msg,channel_max)
            print msg
    if (acc_n <= specs) or (specs == 0):
        fig.canvas.manager.window.after(100, plot_spectrum)
    else:
        print ("Adquisition finished...")
        exit_clean()


#START OF MAIN:

if __name__ == '__main__':
    from optparse import OptionParser


    p = OptionParser()
    p.set_usage('spectrometer.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-t', '--time', dest='time', type='float',default=2, help='Set the time to accumulations')
    p.add_option('-o', '--obstime', dest='obstime', type='int',default=300, help='Set the observation duration')
    p.add_option('-c', '--channels', dest='channels', type='int',default=2**14, help='Set the number channels.')
    p.add_option('-N', '--specs', dest='specs', type='int',default=0, help='Set the number of spectrums to read.')
    p.add_option('--bw', dest='bandwidth', type='float',default=250., help='Set the bandwidth [MHz] between 12.5-700.')
    p.add_option('-g', '--gain', dest='gain', type='int',default=0xffffffff, help='Set the digital gain (6bit quantisation scalar). Default is 0xffffffff (max), good for wideband noise. Set lower for CW tones.')
    p.add_option('-s', '--skip', dest='skip', action='store_true', help='Skip reprogramming the FPGA and configuring EQ.')
    p.add_option('-b', '--bof', dest='boffile',type='str', default='spec16_2018_Oct_10_0905.bof', help='Specify the bof file to load')
    p.add_option('--no-save', dest='nosave', action='store_true', help='Not save data files.', default=False)
    opts, args = p.parse_args(sys.argv[1:])

    savefile = not (opts.nosave)
    if args==[]:
        print 'Please specify a ROACH board. Run with the -h flag to see all options.\nExiting.'
        exit()
    else:
        roach = args[0] 
    if opts.bandwidth < 12.5 or opts.bandwidth > 700.:
        print "Please specify a bandwidth (MHz) between 12.5 y  700."
        exit()
    if opts.boffile != '':
        bitstream = opts.boffile

try:
    try:
        from valon5009 import Valon5009 
        clk = Valon5009('/dev/ttyUSB2')
        if opts.bandwidth is not None:
            print ("Setting bandwidth at %.2lf MHz..." % opts.bandwidth)
            clk.set_freq(2,opts.bandwidth * 2.)
        bw = clk.get_freq()[1]/2.
        clk.close()
    except:
        bw = opts.bandwidth
    print ("Bandwidth set at %.2lf MHz..." % bw)

    loggers = []
    lh=corr.log_handlers.DebugLogHandler()
    logger = logging.getLogger(roach)
    logger.addHandler(lh)
    logger.setLevel(10)
    channel_max = 0
    channels = opts.channels

    print('Connecting to server %s on port %i... '%(roach,katcp_port)),
    #fpga = corr.katcp_wrapper.FpgaClient(roach, katcp_port, timeout=10,logger=logger)
    fpga = IryaRoach(roach, katcp_port, timeout=10,logger=logger)
    
    time.sleep(1)

    if fpga.is_connected():
        print 'ok\n'
    else:
        print 'ERROR connecting to server %s on port %i.\n'%(roach,katcp_port)
        exit_fail()

    print '------------------------'
    print 'Programming FPGA with %s...' %bitstream,
    if not opts.skip:
        fpga.progdev(bitstream)
        print 'done'
    else:
        print 'Skipped.'

    integration_time = opts.time
    specs = opts.specs
    #acc_len = int (opts.time * ((2**(np.log2(bw*1e6))) / channels))
    #acc_len = int(opts.time * 2**(int(np.ceil(np.log2(bw*1e6)))) / (channels * 2.))
    acc_len = int(opts.time * bw * 1e6 / (channels))
    print "Setting accumulation time at %.2lf sec... " % opts.time
    print 'Configuring accumulation period to %d...' % acc_len,
    fpga.write_int('acc_len',acc_len)
    print 'done'

    print 'Resetting counters...',
    fpga.write_int('cnt_rst',1) 
    fpga.write_int('cnt_rst',0) 
    print 'done'

    print 'Setting digital gain of all channels to %i...'%opts.gain,
    if not opts.skip:
        fpga.write_int('gain',opts.gain) #write the same gain for all inputs, all channels
        print 'done'
    else:   
        print 'Skipped.'

    if not savefile:
        print "Not save file"

    last_time = time.time()
    last_acc = None 
    #set up the figure with a subplot to be plotted
    fig = matplotlib.pyplot.figure()
    ax = fig.add_subplot(1,1,1)

    # start the process
    print 'Plot started.'
    fig.canvas.manager.window.after(100, plot_spectrum)
    matplotlib.pyplot.show()
    print '\nBye'

except KeyboardInterrupt:
    exit_clean()
except Exception as e:
    print (e)
    exit_fail()

exit_clean()


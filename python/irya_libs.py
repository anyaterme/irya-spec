import matplotlib.pyplot as plt
import astropy.units as u
import numpy as np
import struct
from colour import Color
import datetime

def find_nearest(array, value):
    idx = (np.abs(array - value)).argmin()
    return array[idx]

def find_nearest_index(array, value):
    idx = (np.abs(array - value)).argmin()
    return idx

try:
    import casperfpga
    import corr,time,numpy,struct,sys,logging,pylab
    class IryaRoach(casperfpga.CasperFpga):
        def __init__(self, *args, **kwargs):
            print ("You are using casperfpga.CasperFpga")
            super(IryaRoach, self).__init__(*args, **kwargs)
            reply, _ = self.transport.katcprequest( name='fpgastatus', request_timeout=self.transport._timeout, require_ok=False)
            if (reply.arguments[0] == 'invalid'):
                self.roach_version=1
            else:
                self.roach_version=2

        def listbof(self):
            return self.transport.listbof()

        def is_running(self):
            if self.roach_version == 2:
                reply, _ = self.transport.katcprequest( name='fpgastatus', request_timeout=self.transport._timeout, require_ok=False)
            else:
                reply, _ = self.transport.katcprequest( name='status', request_timeout=self.transport._timeout, require_ok=False)
            return reply.arguments[0] == 'ok'

        def progdev(self, filename):
            if (".fpg" in filename):
                self.upload_to_ram_and_program(filename)
                return True
            if (".bof" in filename):
                if (filename not in self.listbof()):
                    self.transport.upload_to_flash(filename)
                self.program(filename.split('/')[-1])
                return True
            return False

        def program(self, filename=None):
            """
            Program the FPGA with the specified binary file.
            :param filename: name of file to program, can vary depending on
                the formats supported by the device. e.g. fpg, bof, bin
            :return:
            """
            # raise DeprecationWarning('This does not seem to be used anymore.'
            #                          'Use upload_to_ram_and_program')
            # TODO - The logic here is for broken TCPBORPHSERVER, needs fixing
            if 'program_filename' in self.transport.system_info.keys():
                if filename is None:
                    filename = self.transport.system_info['program_filename']
                elif filename != self.transport.system_info['program_filename']:
                    print('%s: programming filename %s, configured ' 'programming filename %s' % (self.transport.host, filename, self.transport.system_info['program_filename']))
                    # This doesn't seem as though it should really be an error...
            if filename is None:
                raise RuntimeError('Cannot program with no filename given. ' 'Exiting.')
            unhandled_informs = []
            # set the unhandled informs callback
            self.transport.unhandled_inform_handler = \
                lambda msg: unhandled_informs.append(msg)
            reply, _ = self.transport.katcprequest(name='progdev', request_timeout=10, request_args=(filename, ))
            self.transport.unhandled_inform_handler = None
            if reply.arguments[0] == 'ok':
                complete_okay = False
                for inf in unhandled_informs:
                    if (inf.name == 'fpga') and (inf.arguments[0] == 'ready'):
                        complete_okay = True
                if not complete_okay: # Modify to do an extra check
                    if self.is_running():
                        complete_okay = True
                    else:
                        raise RuntimeError('%s: programming %s failed.' % (self.transport.host, filename))
                self.transport.system_info['last_programmed'] = filename
            else:
                raise RuntimeError('%s: progdev request %s failed.' % (self.transport.host, filename))
            if filename[-3:] == 'fpg':
                self.transport.get_system_information()
            else:
                print('%s: %s is not an fpg file, could not parse ' 'system information.' % (self.transport.host, filename))
            print('%s: programmed %s okay.' % (self.transport.host, filename))


        def write_int(self, device_name, data, offset=0, blindwrite=False):
            return(super(IryaRoach, self).write_int(device_name, data, word_offset=offset, blindwrite=blindwrite))

        def read_int(self, device_name, offset=0):
            return(super(IryaRoach, self).read_int(device_name, word_offset=offset))

        def est_brd_clk(self):
            return(self.estimate_fpga_clock())

        def read_ram(self,device, n_words=1024, data_format='B', offset=0):
            size_cat = {'b':1., 'B':1., 'l':4., 'L':4., 'f':4., 'd':8., 'Q':8., 'q':8.}
            if device in self.listdev():
                snapshot = self.read(device,n_words * size_cat[data_format],offset=offset)
                string_data = struct.unpack('>%d%s' % (n_words, data_format), snapshot)
                array_data = np.array(string_data, dtype='float')
                return array_data
            else:
                print "ERROR. %s is not present in bof file." % device
                return np.zeros(n_words)

        def wait_connected(self, timeout=5):
            init_time = time.time()
            while init_time + timeout > time.time() and not self.is_connected():
                pass
            return self.is_connected()
            
        def read_full_stream(self, device_prefix, n_words=1024, data_format='B', offset=0):
            bram_names = []
            list_dev = self.listdev()
            for dev in list_dev:
                if device_prefix in dev:
                    bram_names.append(dev)
            bram_names.sort()
            num_brams = len (bram_names)
            print "Reading %d devices: %s" % (num_brams, bram_names)
            y = np.zeros(n_words)
            for k in range(num_brams):
                data = self.read_ram(bram_names[k], int(n_words/num_brams), data_format, offset)
                y[k::num_brams] = data
            return y

        def stop(self):
            pass
except Exception as e:
    print ("WARNING!!!!!", e)
    pass


class Spectrum():
    def __init__ (self, path=None, bw=1., channels=1, integ=1.):
        if path is not None:
            f = open (path,"rb")
            data_raw = f.read()
            f.close()
            try:
                (self.timestamp, self.integration, self.bw, self.channels) = struct.unpack(">dddi", data_raw[:28])
                self.data = np.asarray(struct.unpack(">%dl" % self.channels, data_raw[28:]))
            except:
                (self.timestamp, self.integration, self.bw, self.channels) = struct.unpack(">fffi", data_raw[:28])
                self.data = np.asarray(struct.unpack(">%dl" % self.channels, data_raw[16:]))
        else:
            self.bw = bw
            self.integration = integ
            self.channels=channels
            self.data = np.random.random(channels)

        self.data_db = self.data

        self.data_db[np.where(self.data_db == 0)] = 1
        self.data_db = 10 * np.log10(self.data_db)

        self.bandwidth = np.linspace(0,self.bw,self.channels)

    def show(self, zoom=None, units=u.MHz):

        if zoom is None:
            spec_x = np.linspace(0, (self.bw*u.MHz).to(units), self.channels)
            spec_y = self.data
        else:
            if hasattr(zoom,'unit'):
                spec_x = np.linspace(0, (self.bw*u.MHz).to(units), self.channels)
                idx0 = find_nearest_index(spec_x, zoom[0])
                idx1 = find_nearest_index(spec_x, zoom[1])
                spec_x = spec_x[idx0:idx1]
                spec_y = self.data[idx0:idx1]
            else:
                spec_x = np.linspace(0, (self.bw*u.MHz).to(units), self.channels)
                spec_x = spec_x[zoom[0]:zoom[1]]
                spec_y = self.data[zoom[0]:zoom[1]]
        plt.xlabel('Freq (%s)' % spec_x.unit)
        plt.ylabel('Arbitrary units')
        plt.plot(spec_x, spec_y)
        #plt.show()

    def detections(self, sigma=3):
        channels = np.where(self.data > np.mean(self.data) + sigma*np.std(self.data))
        return channels, self.bandwidth[channels],self.data[channels]

    def show_detections(self, sigma=3, zoom=None, show_labels=True, db = False):
        if db :
            data = self.data_db
        else:
            data = self.data
        if zoom is None:
            spec_x = np.linspace(0, (self.bw*u.MHz), self.channels)
            spec_y = data
        else:
            if hasattr(zoom,'unit'):
                spec_x = np.linspace(0, (self.bw*u.MHz).to(zoom.unit), self.channels)
                idx0 = find_nearest_index(spec_x, zoom[0])
                idx1 = find_nearest_index(spec_x, zoom[1])
                spec_x = spec_x[idx0:idx1]
                spec_y = data[idx0:idx1]
            else:
                spec_x = np.linspace(0, (self.bw*u.MHz).to(units), self.channels)
                spec_x = spec_x[zoom[0]:zoom[1]]
                spec_y = data[zoom[0]:zoom[1]]




        plt.plot(spec_x, spec_y)
        channels = np.where(spec_y > np.mean(data) + sigma*np.std(data))
        freq = spec_x[channels]
        data = spec_y[channels]
        colors = list(Color('red').range_to(Color("Blue"),len(channels[0])))
        labels=('o','v','^','<','>','8','s','p','*','h','H','D','d','P','X')
        plots = []
        legend_labels = []
        for i in range(len(channels[0])):
            plots.append(plt.scatter(freq[i],data[i],color=colors[i].get_rgb(),marker=labels[i % len(labels)]))
            if db :
                label = "%d - %s - %s dB" % (channels[0][i], "{0:0.03f}".format(freq[i]), "{0:0.03f}".format(data[i]))
            else:
                label = "%d - %s" % (channels[0][i], "{0:0.03f}".format(freq[i]))
            legend_labels.append(label)
        if show_labels:
            plt.legend(list(plots), list(legend_labels))

        if db:
            plt.ylabel('Power dB (arbitrary units)')
        else:
            plt.ylabel('Power (arbitrary units)')
        plt.xlabel('Freq (MHz)')
        #plt.title(str(datetime.datetime.fromtimestamp(self.timestamp)))
        #plt.show()
        return channels, freq, data

    def get_channel(self, freq):
        if not hasattr(freq,'unit'):
            freq = freq * u.MHz

        return find_nearest_index(self.bandwidth * u.MHz, freq)

    def clean_noise(self, sigma=3):
        nonoise = np.copy(self.data)
        nonoise = nonoise - (np.mean(self.data) + sigma * np.std(self.data))
        nonoise[np.where(nonoise<0)]=0
        return nonoise

    def get_snr(self):
        detections = self.detections()
        if(len (detections[0]) > 0):
            return max(detections[2] * 1. / self.get_noise())
        else:
            return 0.

    def get_harmonic(self, freq):
        if not hasattr(freq, 'unit'):
            freq = freq * u.MHz
        bw = (self.bw*u.MHz).to(freq.unit)
        fact =  ((-1)**int(int(freq.value/bw.value)%2) * (freq.value%bw.value))
        armonic = (bw.value + ((-1)**int(int(freq.value/bw.value)%2) * (freq.value%bw.value))) % (bw.value)
        armonic = armonic * freq.unit
        idx = find_nearest_index(self.bandwidth*u.MHz, armonic)
        return idx,armonic,self.data[idx]

    def get_noise(self):
        return np.mean(self.data)
        
class Spec():
    def __init__(self, roach_address, katcp_port=7147, bitstream=None, channels=2**13, acc_time=1, gain=0xffffffff, bw=200.):
        self.bw = bw
        loggers = []
        lh=corr.log_handlers.DebugLogHandler()
        logger = logging.getLogger(roach_address)
        logger.addHandler(lh)
        logger.setLevel(10)
        channel_max = 0
        self.channels = channels
        print('Connecting to server %s on port %i... '%(roach_address,katcp_port)),
        self.fpga = IryaRoach(roach_address, katcp_port, timeout=10,logger=logger)
        fpga = self.fpga
        time.sleep(1)
        if self.fpga.is_connected():
            print 'ok\n'
        else:
            print 'ERROR connecting to server %s on port %i.\n'%(roach_address,katcp_port)
            exit()

        if bitstream is not None:
            print '------------------------'
            print 'Programming FPGA with %s...' %bitstream,
            fpga.progdev(bitstream)
            print 'done'
            print 'Setting digital gain of all channels to %i...'%opts.gain,
            fpga.write_int('gain',opts.gain) #write the same gain for all inputs, all channels
            print 'done'
        else:
            print 'Using current program in FPGA.'

        acc_len = int (acc_time * (2**(np.log2(bw*1e6))) / channels)
        print 'Configuring accumulation period to %d...' % acc_len,
        fpga.write_int('acc_len',acc_len)
        print 'done'

        print 'Resetting counters...',
        fpga.write_int('cnt_rst',1) 
        fpga.write_int('cnt_rst',0) 
        print 'done'


import sys
import serial
import logging
import numpy as np

class Valon5009(serial.Serial):
    SRC_1 = 1
    SRC_2 = 2
    def __init__(self, port):
        super(Valon5009, self).__init__(port=port, baudrate=9600, timeout=1)
        try:
            if (not self.isOpen()):
                self.open()
        except serial.SerialException as e:
            logging.error("Could not open serial port {}: {}".format(self.name, e))
            sys.exit(1)

    def send_command(self, cmd):
        if self.isOpen():
            self.write(cmd.encode('ascii')+'\r\n')
        else:
            print "You have to open the port"


    def set_freq(self, source, freq):
        if source not in [1,2]:
            print("You must specify the source [1,2].")
            return False
        if freq < 25:
            print("Minimum frequency is 25 [MHz]")
            return False
        if freq > 6000:
            print("Maximum frequency is 6000 [MHz]")
            return False
        cmd = "s%d; f%lf" % (source, freq)
        self.send_command(cmd)
        self.readlines()
        return True

    def get_freq(self, source=None, verbose=False):
        if source not in [1,2]:
            cmd = "s1; f" 
            self.send_command(cmd)
            out1 = self.readlines()
            self.reset_output_buffer()
            cmd = "s2; f" 
            self.send_command(cmd)
            out2 = self.readlines()
            self.reset_output_buffer()
            if (verbose):
                print "Source 1: ", out1[1]
                print "Source 2: ", out2[1]
            return float((out1[1].split(';')[0].split(' ')[1])), float((out2[1].split(';')[0].split(' ')[1]))
        cmd = "s%d; f" % (source)
        self.send_command(cmd)
        out = self.readlines()
        self.reset_output_buffer()
        if (verbose):
            print "Source %d: " % source, out[1]
        return float((out[1].split(';')[0].split(' ')[1]))

    def set_pow(self, source=1, level=0):
        if source not in [1,2]:
            print("You must specify the source [1,2].")
            return False
        if level not in [0,1,2,3]:
            print("You must specify a valid power level [0,1,2,3].")
            return False
        cmd = "s%d;plev %d" % (source, level)
        self.send_command(cmd)
        out = self.readlines()
        self.reset_output_buffer()
        print out[1]
        return float((out[1].split(';')[0].split(' ')[1]))

    def get_pow(self, source=None):
        if source is None:
            return (self.get_pow(1), self.get_pow(2))
        else:
            if source not in [1,2]:
                print("You must specify the source [1,2].")
                return False
            cmd = "s%d;plev?" % (source)
            self.send_command(cmd)
            out = self.readlines()
            self.reset_output_buffer()
            return float((out[1].split(';')[0].split(' ')[1]))

    def set_att(self, source=1, att=0):
        if source not in [1,2]:
            print("You must specify the source [1,2].")
            return False

        valid_range = np.arange(0, 32, 0.5)
        if att not in valid_range:
            att = valid_range[np.argmin(abs(att-valid_range))]
            print "Your attenuation is not valid. Set attenuation to %.1lf" % att
        cmd = "s%d;att %d" % (source, att)
        self.send_command(cmd)
        out = self.readlines()
        self.reset_output_buffer()
        print out[1]
        return float((out[1].split(';')[0].split(' ')[1]))

    def get_att(self, source=None):
        if source is None:
            return(self.get_att(1), self.get_att(2))
        else:
            if source not in [1,2]:
                print("You must specify the source [1,2].")
                return False
            cmd = "s%d;att?" % (source)
            self.send_command(cmd)
            out = self.readlines()
            self.reset_output_buffer()
            return float((out[1].split(';')[0].split(' ')[1]))

    def save(self):
        cmd = "sav" 
        self.send_command(cmd)
        out = self.readlines()
        self.reset_output_buffer()
        print out[1]




if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser( description="Valon Synthetizer 5009 ctrl", epilog="""\ """)
    parser.add_argument('SERIALPORT')
    parser.add_argument( '-v', '--verbose', dest='verbosity', action='count', help='print more diagnostic messages (option can be given multiple times)', default=0)
    args = parser.parse_args()


    if args.verbosity > 3:
        args.verbosity = 3
    level = (logging.WARNING, logging.INFO, logging.DEBUG, logging.NOTSET)[args.verbosity]
    logging.basicConfig(level=logging.INFO)
    #logging.getLogger('root').setLevel(logging.INFO)
    logging.getLogger('valon5009').setLevel(level)
    valon = Valon5009(args.SERIALPORT)
    valon.get_freq(1)
    valon.get_freq(2)
    valon.write('s1; f')



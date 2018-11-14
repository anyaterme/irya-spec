import allantools # https://github.com/aewallin/allantools/
import glob
from irya_libs import *
import matplotlib.pyplot as plt

import argparse
import os

parser = argparse.ArgumentParser(description='Join spectrums')
parser.add_argument('path', metavar='<path>', type=str, help='path', default=".")
args = parser.parse_args()

files=glob.glob(os.path.join(args.path,'*.dat'))
files.sort()
spec_total=Spectrum(files[0])
spec_total.data *= 0
taus_spec = []
power = []
timestamps = []
chann = 3547
print "Reading %d spectrums..." % len(files)
for i in files:                                                        
    spec = Spectrum(i)          
    spec_total.data += spec.data
    taus_spec.append(spec.integration)
    timestamps.append(spec.timestamp)
    power.append(spec.data[chann])


rate = 1./np.mean(taus_spec)
#rate = 5
# fractional frequency data
print "Calculating allan variance from %d spectrums, with rate %.4lf Hz and %.1lf sec of duration..." % (len(files), rate, timestamps[-1] - timestamps[0])
(taus_used, adev, adeverror, adev_n) = allantools.adev(power, data_type='freq', rate=rate, taus='all')
plt.ylabel('Allan Desv')
plt.xlabel(r'T(s)')
plt.loglog(taus_used, adev)
aux = np.ediff1d(adev)
aux = aux / np.abs(aux)
idx = np.where(aux > 0)
print ("The optimum value is %lf sec." % (taus_used[idx[0][0]]))


import allantools # https://github.com/aewallin/allantools/
import glob
from irya_libs import *
import matplotlib.pyplot as plt

import argparse
import os

parser = argparse.ArgumentParser(description='Join spectrums')
parser.add_argument('path', metavar='<path>', type=str, help='path', default=".")
parser.add_argument("--norm", help="Normalize spectrum", action="store_true")
parser.add_argument("--num", type=int, default=-1, help="Number of espectrum")
args = parser.parse_args()


files=glob.glob(os.path.join(args.path,'*.dat'))
files.sort()
files = files[1:args.num]
spec_total=Spectrum(files[0])
spec_total.data *= 0
taus_spec = []
power = []
timestamps = []
chann_range = np.arange(8585, 8790)
#chann_range = 8585
print "Reading %d spectrums..." % len(files)
for i in files:                                                        
    spec = Spectrum(i)          
    spec_total.data += spec.data
    taus_spec.append(spec.integration)
    timestamps.append(spec.timestamp)
    power.append(spec.data[chann_range])



power = np.asarray(power)

#Normalize power (at mean)
if args.norm:
    max_by_chan=power.max(axis=0)
    mean = power.mean()
    power = power / mean
    #power = power * mean


rate = 1./np.mean(taus_spec)
taus = np.arange(0,int(rate*len(files)/2),rate)
print taus[-1]
# fractional frequency data
print "Calculating allan variance from %d spectrums, with rate %.4lf Hz and %.1lf sec of duration..." % (len(files), rate, timestamps[-1] - timestamps[0])
adev_avg = []
errors_avg =[]
for i in range(power.shape[1]):
    (taus_used, adev, adeverror, adev_n) = allantools.adev(power[:,i], data_type='freq', rate=rate, taus=taus)
    adev_avg.append(adev)
    errors_avg.append(adeverror)

adev_avg = np.asarray(adev_avg)
errors_avg = np.asarray(errors_avg)
plt.rcParams.update({'font.size': 20})
plt.loglog(taus_used, adev_avg.mean(axis=0), label = r'%d spectrums, rate %.4lf Hz, %.1lf sec' % (len(files), rate, timestamps[-1] - timestamps[0]))
#plt.errorbar(taus_used,adev_avg.mean(axis=0), yerr=errors_avg.mean(axis=0))


ideal_dev = np.sqrt(2. / (1.*250e6 / 2**14 * taus_used))
plt.loglog(taus_used, ideal_dev, label='Radiometer')

plt.ylabel('Allan Desv')
plt.xlabel(r'T(s)')
if not type(chann_range) is int:
    plt.title('IRyA Spectrometer, channel [%d - %d]' % (chann_range[0], chann_range[-1]))
else:
    plt.title('IRyA Spectrometer, channel %d' % (chann_range))

plt.legend()
plt.show()


#aux = np.ediff1d(adev)
#aux = aux / np.abs(aux)
#idx = np.where(aux > 0)
#if (len(idx[0]) > 0):
#    print ("The optimum value is %lf sec." % (taus_used[idx[0][0]]))
#else:
#    print ("The optimum value is %lf sec." % (taus_used[-1]))


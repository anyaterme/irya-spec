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
for i in files:                                                        
    spec = Spectrum(i)          
    spec_total.data += spec.data

spec_total.show_detections(show_labels=False)
#plt.rcParams.update({'font.size': 30})
plt.show()

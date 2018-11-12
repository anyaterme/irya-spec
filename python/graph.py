import glob
from irya_libs import *
import matplotlib.pyplot as plt

files=glob.glob('./datas/1420mhz/*.dat')
files.sort()
spec_total=Spectrum(files[0])
spec_total.data *= 0

for i in files:                                                        
    spec = Spectrum(i)          
    spec_total.data += spec.data

spec_total.show_detections(show_labels=False)
plt.show()

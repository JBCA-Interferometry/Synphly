# Observational variables.
## this data set contain data for C, K and X bands.
## The configuration bellow will select only data for C band.
import numpy as np
import argparse
import os
# from casaplotms import plotms
# from casatasks import *


base_path = ('/media/sagauga/starbyte/LIRGI_Sample/VLA-Archive/A_config/23A-324/C_band/Mrk331/23A'
             '-324/observation.60175.24214351852/')
name = '23A-324.sb44293606.eb44425144.60175.2421365162'
vis = base_path+name + '.ms'
flag_cmds_file = base_path+'flags/'+name+'.flagcmds' #the name of yout manual file flag.
output_vis_path = base_path


flux_calibrator = '0137+331=3C48'
bandpass_calibrator = '0137+331=3C48'
# flux_calibrator = '6'
# bandpass_calibrator = '6'
bandpass_calibrator_field = '0'

# amplitude_calibrator = '0521+166=3C138'
model_setjy = '3C48_C.im'
spw_skip_edge = '0~31:15~50'
spw_central = '0~31:25~45'
refant=None
all_spws = '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31'#only SPWs for C band.


phase_calibrators_all = 'J0010+1724' #
# phase_calibrators_all = '9,10,12,14,16,18,20' #
phase_calibrators_all_fields = 'J0010+1724' #
target_fields = 'MRK0331'

phase_calibrators_all_arr = phase_calibrators_all.split(',')
# phase_calibrators_all_fields_arr = phase_calibrators_all_fields.split(',')
target_fields_arr = target_fields.split(',')


if flux_calibrator != bandpass_calibrator:
    calibrators_all = flux_calibrator + ',' + bandpass_calibrator + ',' + phase_calibrators_all
else:
    calibrators_all = flux_calibrator +  ',' + phase_calibrators_all


calibrators_all_arr = list(np.unique(calibrators_all.split(',')))

all_fields_str = calibrators_all + ',' + target_fields
all_fields = list(np.unique((calibrators_all + ',' + target_fields).split(',')))


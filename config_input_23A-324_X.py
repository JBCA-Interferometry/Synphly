# Observational variables.
## this data set contain data for C, K and X bands.
## The configuration bellow will select only data for C band.
import numpy as np
base_path = '/run/media/sagauga/ssd_evo_2/23A-324/X_band/23A-324.sb44318273.eb44341564.60143.73620483796/'
name = '23A-324.sb44318273.eb44341564.60143.73620483796'
vis = base_path+name + '.ms/'
flag_cmds_file = base_path+'flags/'+name+'.flagcmds' #the name of yout manual file flag.
output_vis_path = base_path


flux_calibrator = '0137+331=3C48'
bandpass_calibrator = '0137+331=3C48'
# amplitude_calibrator = '0521+166=3C138'
model_setjy = '3C48_X.im'
spw_skip_edge = '0~31:6~58'
spw_central = '0~31:12~52'
refant='ea23,ea12,ea28'
all_spws = '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31'


phase_calibrators_all = 'J0237+2848' #
target_fields = 'MCG05-06-03'

phase_calibrators_all_arr = phase_calibrators_all.split(',')
target_fields_arr = target_fields.split(',')


calibrators_all = flux_calibrator + ',' + bandpass_calibrator + ',' + phase_calibrators_all
calibrators_all_arr = list(np.unique(calibrators_all.split(',')))

all_fields_str = calibrators_all + ',' + target_fields
all_fields = list(np.unique((calibrators_all + ',' + target_fields).split(',')))


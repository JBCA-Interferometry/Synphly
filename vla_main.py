import os, glob, re, logging
from sys import argv
import time, argparse
from datetime import datetime
import casatasks, casatools
import casalogger
import casaplotms
import numpy as np
import subprocess
import matplotlib
import configparser
import matplotlib.pyplot as plt

msmd = casatools.msmetadata()
ms = casatools.ms()
tb = casatools.table()

config = configparser.ConfigParser()
config.read('vla_config.ini')

try:
    console
except:
    logfile_name = datetime.now().strftime('vlapipe_%H_%M_%S_%d_%m_%Y.log')
    logging.basicConfig(filename=logfile_name,level=logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    # import casalogger.__main__
    casalogger.casalogger()


# loading data
load_data = config.getboolean('globals','load_data')
experiment = config.get('globals','experiment_name')
working_directory = config.get('globals', 'working_directory')
asdm_file = config.get('globals','asdm_file')
do_hanning = config.getboolean('globals','do_hanning')
singularity_path = config.get('globals','singularity_path')
use_singularity = config.getboolean('globals','use_singularity')
ms_info = config.getboolean('globals','ms_info')
report_verbosity = config.getint('globals','report_verbosity')

# sources

flux_calibrator = config.get('sources','flux_calibrator')
bandpass_calibrator = config.get('sources','bandpass_calibrator')
phase_calibrator = config.get('sources','phase_calibrator')
target = config.get('sources','target')

# flagging
do_flagging = config.getboolean('flagging','do_flagging')
do_pre_flagging = config.getboolean('flagging','do_pre_flagging')
use_aoflagger = config.getboolean('flagging','use_aoflagger')
aoflagger_sif = config.get('flagging','aoflagger_sif')
aoflagger_strategy = config.get('flagging','aoflagger_strategy')
edge_channel_frac = config.getfloat('flagging','edge_channel_frac')

# average
do_average = config.getboolean('average','do_average')
timebin_avg = config.get('average','timebin_avg')

# calibrate
do_split = config.getboolean('calibrate','do_split')
timebin = config.getfloat('calibrate','timebin')
width = config.getint('calibrate','width')
solint = config.get('calibrate','solint')
do_initial_cal = config.getboolean('calibrate','do_initial_cal')
do_setjy = config.getboolean('calibrate','do_setjy')
_refant = config.get('calibrate','refant')
do_refant = config.getboolean('calibrate','do_refant')
if _refant == 'None':
    refant = None
bp_solint_K = config.get('calibrate','bp_solint_K')
bp_solint_G_p = config.get('calibrate','bp_solint_G_p')
bp_solint_G_ap = config.get('calibrate','bp_solint_G_ap')
bp_solint_BP = config.get('calibrate','bp_solint_BP')
minsnr = config.getfloat('calibrate','minsnr')
do_bandpass = config.getboolean('calibrate','do_bandpass')


exec(open("./vla_functions.py").read())
exec(open("./vla_flagging.py").read())
exec(open('./vla_calibrate.py').read())

# defining vis here

vis = f"{working_directory}/{experiment}.ms"

# if do_split == True:
#     try: 
#         outputvis = vis.replace('.ms',f'_{timebin}s_{width}_split.ms')
#         logging.info(f"Splitting {vis} to {outputvis}")
#         split()
#         vis = outputvis
#     except:
#         logging.critical(f"Error occured while splitting")

try:
    steps_performed
except:
    steps_performed = []

try:
    set_working_dir()
except Exception as e:
    logging.error(f"An error occured while creating the working directory: {e}")


if load_data == True and 'load_data' not in steps_performed:
    try:
        logging.info("Running CASA task importasdm")
        vis_for_cal = importasdm()
        # getfields()
    except Exception as e:
        logging.critical(f"Exception {e} occured")

    steps_performed.append('load_data')

if ms_info == True:
    try:
        logging.info(f"Getting ms information")
        flux_calibrator,bandpass_calibrator,phase_calibrator,target = getms_info(vis=vis_for_cal)

        calibrators_all, calibrators_all_arr, all_fields_str, all_fields_arr, target_fields_arr = \
            (format_fields(flux_calibrator,bandpass_calibrator,phase_calibrator,target))
    except Exception as e:
        logging.critical(F"Error {e} while executing func getms_info")

if do_flagging == True:
    logging.info("Flagging data")
    # run_rflag()
    if do_pre_flagging and 'pre_flagging' not in steps_performed:
        pre_flagging(vis=vis_for_cal)
        steps_performed.append('pre_flagging')
    # manual_flagging()
    if use_aoflagger == True:
        if 'run_aoflagger' not in steps_performed:
            try:
                logging.info("Flagging with AOflagger")
                if use_singularity == True:
                    run_aoflagger_sif(vis=vis_for_cal)
                else:
                    run_aoflagger_nat(vis=vis_for_cal)
                steps_performed.append('run_aoflagger')
            except Exception as e:
                logging.critical(f"Exception {e}  while running AOflagger")
    else:
        logging.info("Flagging using aoflagger not requested")

if do_initial_cal == True and 'initial_corrections' not in steps_performed:
    try:
        logging.info("Correcting antenna pos, gaincurves, sys power and atmospheric corrections")
        init_tables, init_tables_dict = initial_corrections(vis=vis_for_cal)
        steps_performed.append('initial_corrections')
    except Exception as e:
        logging.critical(f"Exception {e} while performing initial corrections")

if do_setjy == True and 'flux_scale_setjy' not in steps_performed:
    flux_density_data, spws, fluxes = flux_scale_setjy(vis=vis_for_cal,
                                                       flux_density=None,
                                                       model_image=None)
    steps_performed.append('flux_scale_setjy')

if do_refant and 'select_refant' not in steps_performed:
    try:
        logging.info("Selecting ref antenna.")
        if refant is None:
            logging.info("No refant specified. Finding refant by fraction of good solutions.")
            tablename_refant = f"{working_directory}/calibration/find_refant.phase"
            ref_antenna = find_refant(msfile=vis_for_cal, field=calibrators_all,
                                      tablename=tablename_refant)
            ref_antenna_list = ref_antenna.split(',')
        else:
            logging.info("Using refant specified in the config file.")
            ref_antenna = refant
        steps_performed.append('select_refant')
    except Exception as e:
        logging.critical(f"Exception {e} while computing ref antenna.")

if do_bandpass == True and 'bandpass' not in steps_performed:
    try:
        logging.info("Running bandpass calibration")
        (gaintables_apply_BP, gainfield_bandpass_apply, gain_tables_dict,
         gaintables_apply_BP_dict, gainfields_apply_BP_dict) = bandpass_cal(i=1)
        steps_performed.append('bandpass')
    except Exception as e:
        logging.critical(f"Exception {e} while running bandpass calibration")

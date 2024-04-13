import os, glob, re, logging
from sys import argv
import time, argparse
from datetime import datetime
import casatasks, casatools
import casaplotms
import numpy as np
import subprocess
import matplotlib
import configparser

config = configparser.ConfigParser()
config.read('vla_config.ini')

logfile_name = datetime.now().strftime('vlapipe_%H_%M_%S_%d_%m_%Y.log')
logging.basicConfig(filename=logfile_name,level=logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)


# loading data
load_data = config.getboolean('globals','load_data')
experiment = config.get('globals','experiment_name')
working_directory = config.get('globals', 'working_directory')
asdm_file = config.get('globals','asdm_file')
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
use_aoflagger = config.getboolean('flagging','use_aoflagger')
aoflagger_sif = config.get('flagging','aoflagger_sif')
aoflagger_strategy = config.get('flagging','aoflagger_strategy')
edge_channel_frac = config.getfloat('flagging','edge_channel_frac')


# calibrate
do_split = config.getboolean('calibrate','do_split')
timebin = config.getfloat('calibrate','timebin')
width = config.getint('calibrate','width')
solint = config.getfloat('calibrate','solint')
do_initial_cal = config.getboolean('calibrate','do_initial_cal')
do_setjy = config.getboolean('calibrate','do_setjy')


exec(open("./vla_functions.py").read())
exec(open("./vla_flagging.py").read())
exec(open('./vla_calibrate.py').read())

# defining vis here

vis = experiment+'.ms'

# if do_split == True:
#     try: 
#         outputvis = vis.replace('.ms',f'_{timebin}s_{width}_split.ms')
#         logging.info(f"Splitting {vis} to {outputvis}")
#         split()
#         vis = outputvis
#     except:
#         logging.critical(f"Error occured while splitting")
    
try:
    set_working_dir()
except Exception as e:
    logging.error(f"An error occured while creating the working directory: {e}")


if load_data == True:
    try:
        logging.info("Running CASA task importasdm")
        importasdm()
        # getfields()
    except Exception as e:
        logging.critical(f"Exception {e} occured")

if ms_info == True:
    try:
        logging.info(f"Getting ms information")
        getms_info()
    except Exception as e:
        logging.critical(F"Error {e} while executing func getms_info")

if do_flagging == True:
    logging.info("Flagging data")
    # run_rflag()
    initial_flagging()
    # manual_flagging()
    if use_aoflagger == True:
        try:
            logging.info("Flagging with AOflagger")
            run_aoflagger_sif()
        except Exception as e:
            logging.critical(f"Exception {e}  while running AOflagger")
    else:
        logging.info("Flagging using aoflagger not requested")

if do_initial_cal == True:
    try:
        logging.info("Correcting antenna pos, gaincurves, sys power and atmospheric corrections")
        initial_corrections()
    except Exception as e:
        logging.critical(f"Exception {e} while performing initial corrections")

if do_setjy ==   True:
    flux_scale_setjy()
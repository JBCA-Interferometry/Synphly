def set_working_dir():

    """
    Creates a working dir if one does not exist
    """
    if not os.path.exists(working_directory):
        logging.info(f"{working_directory} does not exist, making one")
        os.makedirs(working_directory)
    else:
        logging.info(f"Working directory {working_directory} already exists")
    try:
        logging.info(f"Changing dir to {working_directory}")
        os.chdir(working_directory)
        logging.info(f"Changed directory to {working_directory}")
    except Exception as e:
        logging.error(f"An error occurred while changing directory: {e}")
    
    # logging.info(f"Setting logfile in working dir")

    flags_dir = os.path.join(working_directory).rstrip('/')+'/'+'flags'
    calibration_dir = os.path.join(working_directory).rstrip('/')+'/'+'calibration'
    plots_dir = os.path.join(working_directory).rstrip('/')+'/'+ 'plots'

    folders = [flags_dir,calibration_dir,plots_dir]
    for folder in folders:
        try: 
            if not os.path.exists(folder):
                logging.info(f"Dir {folder} does not exist. Will create one")
                os.makedirs(folder)
            else:
                logging.info(f"Dir {folder} exists. Will not create one")
        except Exception as e:
            logging.error(f"Error {e} occured while creating {folder}")

def importasdm():

    """
    
    Makes a measurement set from SDM files

    """
    importasdm_starttime = time.time()


    if not os.path.exists(vis):
        try:
            logging.info(f"Making {vis}")
            casatasks.importasdm(asdm=asdm_file, vis=vis,
                    process_syspower=True, process_caldevice=True, process_pointing=True,
                    process_flags=True, applyflags=True, savecmds=True, flagbackup=True,
                    verbose=True, with_pointing_correction=True,
                    outfile=vis.replace('.ms','.flagonline.txt'))
        except Exception as e:
            logging.critical(f"{vis} not made due to error:{e}")
    else:
        logging.info(f"{vis} exists, will not make a new one")

    ms = casatools.ms()
    """ Writes the verbose output of the task listobs """

    listfile = vis.replace(".ms","_listobs.txt")

    if os.path.exists(listfile):
        logging.info(f"Listobs file {listfile} exists")
    else:
        try:
            logging.info(f"Making {listfile}")
            ms.open(vis)  
            ms.summary(verbose=True, listfile=listfile)
            if os.path.isfile(listfile):
                logging.info("A file containing listobs output is saved.")
            else:
                logging.info("The listobs output was not saved in a .list file. Please check the CASA log.")
        except Exception as e:
            logging.critical(f"Error {e} occured when making listobs")

    importasdm_endtime = time.time() 
    logging.info(f"Exec time for data handle/conversion took {(importasdm_endtime-importasdm_starttime) / 60:.2f} minutes")
    

def getms_info():

    """
    Reads the ms and prints the fields and scans

    """

    msmd = casatools.msmetadata()

    msmd.open(vis)  
    fieldnames = msmd.fieldnames()
    
    fields = {}

    for index, item in enumerate(fieldnames):
        if any(char.isdigit() for char in item):
            fields[index] = item
    sources = [flux_calibrator,bandpass_calibrator,phase_calibrator,target]
    try:
        for source in sources:
            if source in fields.values():
                logging.info(f"{source} found in {vis}")
            else:
                logging.error(f"Source {source} not found in {vis}")

    except Exception as e:
        logging.critical(f"Exception {e} occured while getting sources")

    # get the scans
    for source in sources:
        myscan_numbers = msmd.scansforfield(source)
        myscanlist = myscan_numbers.tolist()
        logging.info(f"Scans {myscanlist} are observed on {source}")
    
    # get the nchan
    nchan = msmd.nchan(0)
    logging.info(f"Total channels {nchan}")

    # get bandwidth
    bandwidth = msmd.bandwidths()*1e-6
    nspw = len(bandwidth)
    total_bandwidth = bandwidth[0]*nspw
    logging.info(f"Data observed over a bandwidth of {total_bandwidth} MHz over {nspw} spw each {bandwidth[0]} MHz in size and divided into {nchan} channels")
                                                             
    msmd.done()

    """ Check the chan freqs and bandwidths"""

def split():

    """
    Creates a split measurement set
    """

    try:
        if not os.path.exists(outputvis):
            logging.info(f"Averaging every {timebin}s and {width} channels")
            casatasks.split(
                vis = vis, outputvis = outputvis,
                timebin = timebin, width = width,
                )
            logging.info("Split successful")
        else:
            logging.warning(f"{outputvis} exists. Will not create a new one")
            
    except Exception as e:
        logging.critical(f"Exception {e} occured ")

        

        

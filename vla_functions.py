def set_working_dir():

    """
    Creates a working dir if one does not exist
    """
    if not os.path.exists(working_directory):
        logging.info(f"{working_directory} does not exist, making one")
        os.makedirs(working_directory)
    else:
        logging.info(f"Working directory {working_directory} already exists")
    # try:
    #     logging.info(f"Changing dir to {working_directory}")
    #     os.chdir(working_directory)
    #     logging.info(f"Changed directory to {working_directory}")
    # except Exception as e:
    #     logging.error(f"An error occurred while changing directory: {e}")
    
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

    # do_hanning = True
    if do_hanning:
        vis_hs = vis.replace('.ms', '_hs.ms')
        if not os.path.exists(vis_hs):
            try:
                logging.info(f"Running Hanning smoothing on {vis}")
                casatasks.hanningsmooth(vis=vis, outputvis=vis_hs)
                logging.info(f"Hanning smoothing done on {vis}")
                logging.info(f"Setting to vis file to Hanning smoothed version [*_hs.ms]")
                vis_for_cal = vis_hs
            except Exception as e:
                logging.critical(f"Error {e} occurred when running hanningsmooth.")
        else:
            logging.info(f"{vis_hs} exists. Will not run hanningsmooth")
            vis_for_cal = vis_hs
    else:
        vis_for_cal = vis
    importasdm_endtime = time.time()
    logging.info(f"Exec time for data handle/conversion took "
                 f"{(importasdm_endtime-importasdm_starttime) / 60:.2f} minutes")
    return(vis_for_cal)

def get_fields(ms_list, type_str):
    list_obs = [x for x in ms_list if x.startswith(type_str)]
    field_names = []
    for LO in list_obs:
        field_names.append(ms_list[LO]['name'])
    fids = np.asarray(list_obs)
    for i in range(len(fids)):
        fids[i] = fids[i].replace('field_', '')
    return (fids, field_names)

def getms_info(vis):

    """
    Reads the ms and prints the fields and scans

    """

    msmd = casatools.msmetadata()

    msmd.open(vis)
    fieldnames = msmd.fieldnames()
    
    fields = {}
    sources = []
    for index, item in enumerate(fieldnames):
        if any(char.isdigit() for char in item):
            fields[index] = item

    if flux_calibrator == '':
        flux_intent = casatasks.listobs(vis=vis, intent='*CALIBRATE_FLUX*')
        _, flux_field_name = get_fields(flux_intent, 'field')
        sources.extend(flux_field_name)
        logging.info(f"Flux calibrator(s) -> {','.join(flux_field_name)}")
    else:
        sources.extend(flux_calibrator.split(','))

    if bandpass_calibrator == '':
        bandpass_intent = casatasks.listobs(vis=vis, intent='*CALIBRATE_BANDPASS*')
        _, bandpass_field_name = get_fields(bandpass_intent, 'field')
        sources.extend(bandpass_field_name)
        logging.info(f"Bandpass calibrator(s) -> {','.join(bandpass_field_name)}")
    else:
        sources.extend(bandpass_calibrator.split(','))

    if phase_calibrator == '':
        phase_intent = casatasks.listobs(vis=vis, intent='*CALIBRATE_PHASE*')
        _, phase_field_name = get_fields(phase_intent, 'field')
        sources.extend(phase_field_name)
        logging.info(f"Phase calibrator(s) -> {','.join(phase_field_name)}")
    else:
        sources.extend(phase_calibrator.split(','))

    if target == '':
        target_intent = casatasks.listobs(vis=vis, intent='*TARGET*')
        _, target_field_name = get_fields(target_intent, 'field')
        sources.extend(target_field_name)
        logging.info(f"Target(s) -> {','.join(target_field_name)}")
    else:
        sources.extend(target.split(','))

    # sources = [flux_calibrator,bandpass_calibrator,phase_calibrator,target]
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
    logging.info(f"Data observed over a bandwidth of {total_bandwidth} MHz over"
                 f" {nspw} spw each {bandwidth[0]} MHz in size and divided "
                 f"into {nchan} channels")
                                                             
    msmd.done()

    """ Check the chan freqs and bandwidths"""
    return(flux_calibrator,bandpass_calibrator,phase_calibrator,target)

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

        

        

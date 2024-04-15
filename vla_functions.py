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
        logging.info("Flux calibrator not provided. Will get from the ms.")
        flux_intent = casatasks.listobs(vis=vis, intent='*CALIBRATE_FLUX*')
        _, flux_field_name = get_fields(flux_intent, 'field')
        sources.extend(flux_field_name)
        _flux_calibrator = ','.join(flux_field_name)
        logging.info(f"Flux calibrator(s) -> {','.join(flux_field_name)}")
    else:
        sources.extend(flux_calibrator.split(','))

    if bandpass_calibrator == '':
        logging.info("Bandpass calibrator not provided. Will get from the ms.")
        bandpass_intent = casatasks.listobs(vis=vis, intent='*CALIBRATE_BANDPASS*')
        _, bandpass_field_name = get_fields(bandpass_intent, 'field')
        sources.extend(bandpass_field_name)
        _bandpass_calibrator = ','.join(bandpass_field_name)
        logging.info(f"Bandpass calibrator(s) -> {','.join(bandpass_field_name)}")
    else:
        sources.extend(bandpass_calibrator.split(','))

    if phase_calibrator == '':
        logging.info("Phase calibrator not provided. Will get from the ms.")
        phase_intent = casatasks.listobs(vis=vis, intent='*CALIBRATE_PHASE*')
        _, phase_field_name = get_fields(phase_intent, 'field')
        sources.extend(phase_field_name)
        _phase_calibrator = ','.join(phase_field_name)
        logging.info(f"Phase calibrator(s) -> {','.join(phase_field_name)}")
    else:
        sources.extend(phase_calibrator.split(','))

    if target == '':
        logging.info("Target not provided. Will get from the ms.")
        target_intent = casatasks.listobs(vis=vis, intent='*TARGET*')
        _, target_field_name = get_fields(target_intent, 'field')
        sources.extend(target_field_name)
        _target = ','.join(target_field_name)
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
    return(_flux_calibrator,_bandpass_calibrator,_phase_calibrator,_target)

def format_fields(flux_calibrator,bandpass_calibrator,phase_calibrator,target):

    """"""
    if flux_calibrator != bandpass_calibrator:
        calibrators_all = flux_calibrator + ',' + bandpass_calibrator + ',' + phase_calibrator
    else:
        calibrators_all = flux_calibrator +  ',' + phase_calibrator


    calibrators_all_arr = list(np.unique(calibrators_all.split(',')))

    target_fields_arr = target.split(',')

    all_fields_str = calibrators_all + ',' + target
    all_fields = list(np.unique((calibrators_all + ',' + target).split(',')))
    return(calibrators_all,calibrators_all_arr,all_fields_str,all_fields,target_fields_arr)

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

def find_refant(msfile, field, tablename):
    """
    This function comes from the e-MERLIN CASA Pipeline.
    https://github.com/e-merlin/eMERLIN_CASA_pipeline/blob/master/functions/eMCP_functions.py#L1501
    """
    # Find phase solutions per scan:
    if not os.path.exists(tablename):
        casatasks.gaincal(vis=msfile,
                          caltable=tablename,
                          field=field,
                          refantmode='flex',
                          solint='inf',
                          minblperant=3,
                          gaintype='G',
                          calmode='p')
    # find_casa_problems()
    # Read solutions (phases):
    tb.open(tablename + '/ANTENNA')
    antenna_names = tb.getcol('NAME')
    tb.close()
    tb.open(tablename)
    antenna_ids = tb.getcol('ANTENNA1')
    # times  = tb.getcol('TIME')
    flags = tb.getcol('FLAG')
    phases = np.angle(tb.getcol('CPARAM'))
    snrs = tb.getcol('SNR')
    tb.close()
    # Analyse number of good solutions:
    good_frac = []
    good_snrs = []
    for i, ant_id in enumerate(np.unique(antenna_ids)):
        cond = antenna_ids == ant_id
        # t = times[cond]
        f = flags[0, 0, :][cond]
        p = phases[0, 0, :][cond]
        snr = snrs[0, 0, :][cond]
        frac = 1.0 * np.count_nonzero(~f) / len(f) * 100.
        snr_mean = np.nanmean(snr[~f])
        good_frac.append(frac)
        good_snrs.append(snr_mean)
    sort_idx = np.argsort(good_frac)[::-1]
    print('Antennas sorted by % of good solutions:')
    for i in sort_idx:
        print('{0:3}: {1:4.1f}, <SNR> = {2:4.1f}'.format(antenna_names[i],
                                                         good_frac[i],
                                                         good_snrs[i]))
    if good_frac[sort_idx[0]] < 90:
        print('Small fraction of good solutions with selected refant!')
        print('Please inspect antennas to select optimal refant')
        print('You may want to use refantmode= flex" in default_params')
    pref_ant = antenna_names[sort_idx]
    pref_ant_list = ','.join(list(pref_ant))
    return pref_ant_list
        
def calibration_table_plot(table, stage='calibration',
                           table_type='gain_phase', kind='',
                           xaxis='time', yaxis='phase', antenna='', spw='',
                           fields=['0']):
    '''
    fields: if a string of fields, will plot data for all fields together.
                e.g. fields='0,1,2'
            if a list of fields, will plot the data for each field separated.
                e.g. fields=['0','1','2']
    '''

    calibration_dir = os.path.join(working_directory).rstrip('/')+'/'+'calibration'
    plots_dir = os.path.join(working_directory).rstrip('/')+'/'+ 'plots'

    if not os.path.exists(f"{plots_dir}/{stage}"):
        os.makedirs(f"{plots_dir}/{stage}")

    if yaxis == 'phase':
        plotrange = [-1, -1, -180, 180]
    else:
        plotrange = [-1, -1, -1, -1]

    if fields == '':
        plotfile = f"{plots_dir}/{stage}/{table_type}_{xaxis}_{yaxis}_field_all_ant_{antenna}_spw_{spw}.jpg"
        # plotfile = base_path + 'plots/' + stage + '/' + table_type + '_' + xaxis + '_' + yaxis + '_field_' + str(
        #     'all') + '_ant_' + antenna + '_spw_' + spw + '.jpg'
        # if not os.path.exists(plotfile):
        casaplotms.plotms(vis=table, xaxis=xaxis, yaxis=yaxis, field='',
                          gridcols=1, gridrows=1, coloraxis='spw', antenna=antenna, spw=spw,
                          plotrange=plotrange,
                          width=2000, height=800, showgui=False, overwrite=True, dpi=1200,
                          highres=True,
                          plotfile=plotfile)
    else:
        try:
            for FIELD in fields:
                plotfile = f"{plots_dir}/{stage}/{table_type}_{xaxis}_{yaxis}_field_{FIELD}_ant_{antenna}_spw_{spw}.jpg"
                # plotfile = base_path + 'plots/' + stage + '/' + table_type + '_' + xaxis + '_' + yaxis + '_field_' + str(
                #     FIELD) + '_ant_' + antenna + '_spw_' + spw + '.jpg'
                # if not os.path.exists(plotfile):
                casaplotms.plotms(vis=table, xaxis=xaxis, yaxis=yaxis, field=FIELD,
                                  # gridcols=4,gridrows=4,coloraxis='spw',antenna='',iteraxis='antenna',
                                  # width=2048,height=1280,dpi=256,overwrite=True,showgui=False,
                                  gridcols=1, gridrows=1, coloraxis='spw', antenna=antenna, spw=spw,
                                  plotrange=plotrange,
                                  width=2000, height=800, showgui=False, overwrite=True, dpi=1200,
                                  highres=True,
                                  plotfile=plotfile)
        except:
            print('     => Not going to plot calibration tables... Check your input fields list.  ')
    pass



def make_plots_stages(vis,stage='after', kind='',
                      plots=None, FIELDS='', plot_all_uv=False, avgantenna=True):
    """
    Make standard plots given a stage (before or after) of calibration.
    This can be useful to compare how calibration performs on the data.

    PS. This function takes a long time to complete if all plots are asked.
    """
    # Amplitude vs channel; Amplitude vs time; Amplitude vs Frequency;
    # phase vs time;
    make_plots_starttime = time.time()

    calibration_dir = os.path.join(working_directory).rstrip('/')+'/'+'calibration'
    plots_dir = os.path.join(working_directory).rstrip('/')+'/'+ 'plots'

    if not os.path.exists(f"{plots_dir}/{stage}"):
        os.makedirs(f"{plots_dir}/{stage}")
    if not os.path.exists(f"{plots_dir}/{stage}/chan_amp"):
        os.makedirs(f"{plots_dir}/{stage}/chan_amp")
    if not os.path.exists(f"{plots_dir}/{stage}/time_amp"):
        os.makedirs(f"{plots_dir}/{stage}/time_amp")
    if not os.path.exists(f"{plots_dir}/{stage}/freq_amp"):
        os.makedirs(f"{plots_dir}/{stage}/freq_amp")
    if not os.path.exists(f"{plots_dir}/{stage}/time_phase"):
        os.makedirs(f"{plots_dir}/{stage}/time_phase")
    if not os.path.exists(f"{plots_dir}/{stage}/amp_phase"):
        os.makedirs(f"{plots_dir}/{stage}/amp_phase")
    if not os.path.exists(f"{plots_dir}/{stage}/chan_phase"):
        os.makedirs(f"{plots_dir}/{stage}/chan_phase")

    if stage == 'before':
        ydatacolumn = 'data'
    if stage == 'after':
        ydatacolumn = 'corrected'


    # if plotting_level >= 1:
    for FIELD in FIELDS:
        # print('Plotting Chan vs Amp: Field')
        plotfile = f"{plots_dir}/{stage}/time_amp/time_amp_avg_{ydatacolumn}_field_{FIELD}_{kind}.jpg"
        casaplotms.plotms(vis=vis, xaxis='time', yaxis='amp', ydatacolumn=ydatacolumn,
                          avgchannel='9999', coloraxis='spw', field=FIELD,
                          xselfscale=True, yselfscale=True, correlation='RR,LL',
                          title='Time vs Amp, ' + str(FIELD), avgantenna=avgantenna,
                          gridrows=1, gridcols=1, width=2000, height=800, showgui=False,
                          overwrite=True, dpi=1200,
                          highres=True,
                          plotfile=plotfile)
        plotfile = f"{plots_dir}/{stage}/freq_amp/freq_amp_avg_{ydatacolumn}_field_{FIELD}_{kind}.jpg"
        casaplotms.plotms(vis=vis, xaxis='freq', yaxis='amp', ydatacolumn=ydatacolumn,
                          avgtime='9999', coloraxis='spw', field=FIELD,
                          xselfscale=True, yselfscale=True, correlation='RR,LL',
                          title='Freq vs Amp, ' + str(FIELD), avgantenna=avgantenna,
                          # width=800,height=540,dpi=600,overwrite=True,showgui=False,
                          gridrows=1, gridcols=1, width=2000, height=800, showgui=False,
                          overwrite=True, dpi=1200,
                          highres=True,
                          plotfile=plotfile)
        plotfile = f"{plots_dir}/{stage}/time_phase/time_phase_avg_{ydatacolumn}_field_{FIELD}_{kind}.jpg"
        casaplotms.plotms(vis=vis, xaxis='time', yaxis='phase', ydatacolumn=ydatacolumn, correlation='RR,LL',
                          avgchannel='9999', coloraxis='spw', field=FIELD,
                          title='Time vs Phase, ' + str(FIELD), avgantenna=avgantenna,
                          gridrows=1, gridcols=1, width=2000, height=800, showgui=False,
                          overwrite=True,
                          dpi=1200, highres=True,
                          plotrange=[-1, -1, -180, 180],
                          plotfile=plotfile)
        plotfile = f"{plots_dir}/{stage}/uvwave_amp_{ydatacolumn}_field_{FIELD}_{kind}.jpg"
        casaplotms.plotms(vis=vis, xaxis='uvwave', yaxis='amp', field=FIELD,
                          coloraxis='spw', correlation='RR,LL',
                          xselfscale=True, yselfscale=True,
                          ydatacolumn=ydatacolumn, avgchannel='9999', avgtime='9999',
                          width=2000, height=800, showgui=False, overwrite=True, dpi=1200,
                          highres=True,
                          plotfile=plotfile)
    make_plots_time = time.time() - make_plots_starttime
    logging.info(f"Plotting regarding {kind} for fields {FIELDS} took {make_plots_time / 60:.2f} minutes")
    pass
from casatasks import listobs


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

def import_data():

    """
    
    Makes a measurement set from SDM files

    """
    importasdm_starttime = time.time()
    if not os.path.exists(vis):
        try:
            logging.info(f"Making {vis}")
            importasdm(asdm=asdm_file, vis=vis,
                    process_syspower=True, process_caldevice=True, process_pointing=True,
                    process_flags=True, applyflags=True, savecmds=True, flagbackup=True,
                    verbose=True, with_pointing_correction=True,
                    outfile=vis.replace('.ms','.flagonline.txt'))

        except Exception as e:
            logging.critical(f"{vis} not made due to error:{e}")
    else:
        logging.info(f"{vis} exists, will not make a new one")

    # ms = casatools.ms()
    """ Writes the verbose output of the task listobs """

    # do_hanning = True
    if do_hanning:
        vis_hs = vis.replace('.ms', '_hs.ms')
        if not os.path.exists(vis_hs):
            try:
                logging.info(f"Running Hanning smoothing on {vis}")
                hanningsmooth(vis=vis, outputvis=vis_hs)
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

    listfile = vis_for_cal.replace(".ms","_listobs.txt")

    if os.path.exists(listfile):
        logging.info(f"Listobs file {listfile} exists")
    else:
        try:
            logging.info(f"Making {listfile}")
            ms.open(vis_for_cal)
            ms.summary(verbose=True, listfile=listfile)
            ms.close()
            if os.path.isfile(listfile):
                logging.info("A file containing listobs output is saved.")
            else:
                logging.info("The listobs output was not saved in a .list file. Please check the CASA log.")
        except Exception as e:
            logging.critical(f"Error {e} occured when making listobs")

    importasdm_endtime = time.time()
    logging.info(f"Exec time for data handle/conversion took "
                 f"{(importasdm_endtime-importasdm_starttime) / 60:.2f} minutes")
    return(vis_for_cal)

def average_ms(vis,time_avg=True,channel_avg=False,
               usewtspectrum=False,regridms=False):
    """
    Averages the ms in time and/or channel
    Paramaters
    ----------
    vis : str
        The measurement set to average
    time_avg : bool
        If True, averages in time
    channel_avg : bool
        If True, averages in channel
    """
    vis_for_cal_avg = vis.replace('.ms', f'.avg.ms')
    vis_avg_time_temp = None
    vis_avg_chan_temp = None
    if not os.path.exists(vis_for_cal_avg):
        if time_avg:
            vis_avg_time_temp = vis.replace('.ms', f'.avgtime_temp.ms')
            if not os.path.exists(vis_for_cal_avg):
                logging.info(f" ++==>> Averaging data to {timebin_avg} before calibration.")
                mstransform(vis=vis,
                            outputvis=vis_avg_time_temp,
                            datacolumn='data',
                            keepflags=True,
                            usewtspectrum=usewtspectrum,
                            regridms=regridms,
                            timeaverage=True,
                            timebin=timebin_avg)
        if channel_avg:
            vis_avg_chan_temp = vis.replace('.ms', f'.avgchan_temp.ms')
            vis_temp = vis_avg_time_temp if time_avg else vis
            if not os.path.exists(vis_for_cal_avg):
                logging.info(f" ++==>> Averaging data in frequency to {chan_out_avg} "
                             f"channels before calibration.")
                msmd.open(vis_temp)
                bandwidth = msmd.bandwidths()
                nspw = len(bandwidth)

                chan_freqs_all = np.empty(nspw, dtype=object)
                spws_freq = np.zeros(nspw)

                for nch in range(nspw):
                    chan_freqs_all[nch] = msmd.chanfreqs(nch)
                    spws_freq[nch] = np.nanmean(chan_freqs_all[nch])
                msmd.done()
                mean_freq = np.nanmean(spws_freq) * 1e-9
                shapes = np.asarray([arr.shape[0] for arr in chan_freqs_all])
                # chan_out_avg = 64
                chan_width_avg = list((shapes / chan_out_avg).astype(int))

                mstransform(vis=vis_temp,
                            outputvis=vis_avg_chan_temp,
                            datacolumn='data',
                            keepflags=True,
                            usewtspectrum=usewtspectrum,
                            regridms=regridms,
                            chanaverage=True,
                            chanbin=chan_width_avg)
        if time_avg and channel_avg:
            logging.info(f" ++==>> Data averaged to {timebin_avg} and {chan_out_avg} "
                         f"output channels.")
            os.system(f"mv {vis_avg_chan_temp} {vis_for_cal_avg}")
            os.system(f"rm -r {vis_avg_time_temp}")
        if time_avg and not channel_avg:
            logging.info(f" ++==>> Data averaged to {timebin_avg} seconds.")
            os.system(f"mv {vis_avg_time_temp} {vis_for_cal_avg}")
        if not time_avg and channel_avg:
            logging.info(f" ++==>> Data averaged to {chan_out_avg} output channels.")
            os.system(f"mv {vis_avg_chan_temp} {vis_for_cal_avg}")

    else:
        logging.info(f" --==>> Averaged ms {vis_for_cal_avg} already exists.")
        # vis_for_cal = vis_for_cal_avg
    listfile_avg = vis_for_cal_avg.replace(".ms", "_listobs.txt")
    logging.info(f" ++==>> Generating listobs file from averaged data: {listfile_avg}")
    listobs(vis=vis_for_cal_avg, listfile=listfile_avg)
    return(vis_for_cal_avg)


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

    # msmd = casatools.msmetadata()

    msmd.open(vis)
    fieldnames = msmd.fieldnames()
    
    fields = {}
    sources = []
    for index, item in enumerate(fieldnames):
        if any(char.isdigit() for char in item):
            fields[index] = item

    if flux_calibrator == '':
        logging.info("Flux calibrator not provided. Will get from the ms.")
        flux_intent = listobs(vis=vis, intent='*CALIBRATE_FLUX*')
        _, flux_field_name = get_fields(flux_intent, 'field')
        sources.extend(flux_field_name)
        _flux_calibrator = ','.join(flux_field_name)
        logging.info(f"Flux calibrator(s) -> {','.join(flux_field_name)}")
    else:
        sources.extend(flux_calibrator.split(','))
        _flux_calibrator = flux_calibrator

    if bandpass_calibrator == '':
        logging.info("Bandpass calibrator not provided. Will get from the ms.")
        bandpass_intent = listobs(vis=vis, intent='*CALIBRATE_BANDPASS*')
        _, bandpass_field_name = get_fields(bandpass_intent, 'field')
        sources.extend(bandpass_field_name)
        _bandpass_calibrator = ','.join(bandpass_field_name)
        logging.info(f"Bandpass calibrator(s) -> {','.join(bandpass_field_name)}")
    else:
        sources.extend(bandpass_calibrator.split(','))
        _bandpass_calibrator = bandpass_calibrator

    if phase_calibrator == '':
        logging.info("Phase calibrator not provided. Will get from the ms.")
        phase_intent = listobs(vis=vis, intent='*CALIBRATE_PHASE*')
        _, phase_field_name = get_fields(phase_intent, 'field')
        sources.extend(phase_field_name)
        _phase_calibrator = ','.join(phase_field_name)
        logging.info(f"Phase calibrator(s) -> {','.join(phase_field_name)}")
    else:
        sources.extend(phase_calibrator.split(','))
        _phase_calibrator = phase_calibrator

    if target == '':
        logging.info("Target not provided. Will get from the ms.")
        target_intent = listobs(vis=vis, intent='*TARGET*')
        _, target_field_name = get_fields(target_intent, 'field')
        sources.extend(target_field_name)
        _target = ','.join(target_field_name)
        logging.info(f"Target(s) -> {','.join(target_field_name)}")
    else:
        sources.extend(target.split(','))
        _target = target

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
    try:
        for source in sources:
            myscan_numbers = msmd.scansforfield(source)
            myscanlist = myscan_numbers.tolist()
            logging.info(f"Scans {myscanlist} are observed on {source}")
    except:
        pass
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

def __split():

    """
    Creates a split measurement set
    """

    try:
        if not os.path.exists(outputvis):
            logging.info(f"Averaging every {timebin}s and {width} channels")
            split(
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

    It finds the best reference antenna for calibration.

    Parameters
    ----------
    msfile : str
        The measurement set file
    field : str
        The field to calibrate
    tablename : str
        The name of the calibration table
    """
    # Find phase solutions per scan:
    if not os.path.exists(tablename):
        gaincal(vis=msfile,
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
        plotms(vis=table, xaxis=xaxis, yaxis=yaxis, field='',
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
                plotms(vis=table, xaxis=xaxis, yaxis=yaxis, field=FIELD,
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
                      plots=None, FIELDS='', plot_all_uv=False, avgantenna=True,
                      extra_plot=True):
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
        plotms(vis=vis, xaxis='time', yaxis='amp', ydatacolumn=ydatacolumn,
                          avgchannel='9999', coloraxis='baseline', field=FIELD,
                          xselfscale=True, yselfscale=True, correlation='RR,LL',
                          title='Time vs Amp, ' + str(FIELD), avgantenna=avgantenna,
                          gridrows=1, gridcols=1, width=2000, height=800, showgui=False,
                          overwrite=True, dpi=1200,
                          customsymbol=True,symbolsize=3,symbolshape='diamond',
                          highres=True,
                          plotfile=plotfile)
        plotfile = f"{plots_dir}/{stage}/freq_amp/freq_amp_avg_{ydatacolumn}_field_{FIELD}_{kind}.jpg"
        plotms(vis=vis, xaxis='freq', yaxis='amp', ydatacolumn=ydatacolumn,
                          avgtime='9999', coloraxis='baseline', field=FIELD,
                          xselfscale=True, yselfscale=True, correlation='RR,LL',
                          title='Freq vs Amp, ' + str(FIELD), avgantenna=avgantenna,
                          # width=800,height=540,dpi=600,overwrite=True,showgui=False,
                          gridrows=1, gridcols=1, width=2000, height=800, showgui=False,
                          overwrite=True, dpi=1200,
                          customsymbol=True,symbolsize=3,symbolshape='diamond',
                          highres=True,
                          plotfile=plotfile)
        plotfile = f"{plots_dir}/{stage}/time_phase/time_phase_avg_{ydatacolumn}_field_{FIELD}_{kind}.jpg"
        plotms(vis=vis, xaxis='time', yaxis='phase', ydatacolumn=ydatacolumn, correlation='RR,LL',
                          avgchannel='9999', coloraxis='baseline', field=FIELD,
                          title='Time vs Phase, ' + str(FIELD), avgantenna=avgantenna,
                          gridrows=1, gridcols=1, width=2000, height=800, showgui=False,
                          overwrite=True,
                          dpi=1200, highres=True,
                          customsymbol=True,symbolsize=3,symbolshape='diamond',
                          plotrange=[-1, -1, -180, 180],
                          plotfile=plotfile)
        plotfile = f"{plots_dir}/{stage}/uvwave_amp_{ydatacolumn}_field_{FIELD}_{kind}.jpg"
        plotms(vis=vis, xaxis='uvwave', yaxis='amp', field=FIELD,
                          coloraxis='baseline', correlation='RR,LL',
                          xselfscale=True, yselfscale=True,
                          ydatacolumn=ydatacolumn, avgchannel='9999', avgtime='9999',
                          width=2000, height=800, showgui=False, overwrite=True, dpi=1200,
                          customsymbol=True,symbolsize=3,symbolshape='diamond',
                          highres=True,
                          plotfile=plotfile)
        
        
        
        ydatacolumn2 = 'residual'
        ydatacolumn3 = 'corrected/model'
        ydatacolumn4 = 'model'
        if extra_plot == True:
            
            try:
            
                # plotfile = f"{plots_dir}/{stage}/uvwave_amp_{ydatacolumn2}_field_{FIELD}_{kind}.jpg"
                # plotms(vis=vis, xaxis='uvwave', yaxis='amp', field=FIELD,
                #                 coloraxis='baseline', correlation='RR,LL',
                #                 xselfscale=True, yselfscale=True,
                #                 ydatacolumn=ydatacolumn2, avgchannel='9999', avgtime='9999',
                #                 width=2000, height=800, showgui=False, overwrite=True, dpi=1200,
                #                 customsymbol=True,symbolsize=3,symbolshape='diamond',
                #                 highres=True,
                #                 plotfile=plotfile)
                #
                # plotfile = f"{plots_dir}/{stage}/freq_amp/freq_amp_avg_{ydatacolumn2}_field_{FIELD}_{kind}.jpg"
                # plotms(vis=vis, xaxis='freq', yaxis='amp', ydatacolumn=ydatacolumn2,
                #                 avgtime='9999', coloraxis='baseline', field=FIELD,
                #                 xselfscale=True, yselfscale=True, correlation='RR,LL',
                #                 title='Freq vs Amp, ' + str(FIELD), avgantenna=avgantenna,
                #                 # width=800,height=540,dpi=600,overwrite=True,showgui=False,
                #                 gridrows=1, gridcols=1, width=2000, height=800, showgui=False,
                #                 overwrite=True, dpi=1200,
                #                 customsymbol=True,symbolsize=3,symbolshape='diamond',
                #                 highres=True,
                #                 plotfile=plotfile)
                
                plotfile = f"{plots_dir}/{stage}/freq_amp/freq_amp_avg_{ydatacolumn4}_field_{FIELD}_{kind}.jpg"
                plotms(vis=vis, xaxis='freq', yaxis='amp', ydatacolumn=ydatacolumn4,
                                avgtime='9999', coloraxis='baseline', field=FIELD,
                                xselfscale=True, yselfscale=True, correlation='RR,LL',
                                title='Freq vs Amp, ' + str(FIELD), avgantenna=avgantenna,
                                # width=800,height=540,dpi=600,overwrite=True,showgui=False,
                                gridrows=1, gridcols=1, width=2000, height=800, showgui=False,
                                overwrite=True, dpi=1200,
                                customsymbol=True,symbolsize=3,symbolshape='diamond',
                                highres=True,
                                plotfile=plotfile)
                
                # plotfile = f"{plots_dir}/{stage}/uvwave_amp_corrected_div_model_field_{FIELD}_{kind}.jpg"
                # plotms(vis=vis, xaxis='uvwave', yaxis='amp', field=FIELD,
                #                 coloraxis='baseline', correlation='RR,LL',
                #                 xselfscale=True, yselfscale=True,
                #                 ydatacolumn=ydatacolumn3, avgchannel='9999', avgtime='9999',
                #                 width=2000, height=800, showgui=False, overwrite=True, dpi=1200,
                #                 customsymbol=True,symbolsize=3,symbolshape='diamond',
                #                 highres=True,
                #                 plotfile=plotfile)
            except:
                pass
            
    make_plots_time = time.time() - make_plots_starttime
    logging.info(f"Plotting regarding {kind} for fields {FIELDS} took {make_plots_time / 60:.2f} minutes")
    pass

def get_fields(ms_list, type_str):
    list_obs = [x for x in ms_list if x.startswith(type_str)]
    print("The list", type_str, ' is ', str(list_obs))
    field_names = []
    for LO in list_obs:
        field_names.append(ms_list[LO]['name'])
    fids = np.asarray(list_obs)
    for i in range(len(fids)):
        fids[i] = fids[i].replace('field_', '')
    return (fids, field_names)

def get_list(ms_list, type_str):
    list_obs = [x for x in ms_list if x.startswith(type_str)]
    print("The list", type_str, ' is ', str(list_obs))
    for LO in list_obs:
        print(ms_list[LO]['0']['FieldName'], ms_list[LO]['0']['FieldId'])
    return (list_obs)

def split_fields(vis_to_split,iter='',width=1):
    """
    Splits the ms into fields


    Parameter
    ----------
    vis : str
        The measurement set to split

    """
    # ms_amp = listobs(vis=vis_to_split, intent='*CALIBRATE_AMPLI*')
    # ms_ph = listobs(vis=vis_to_split, intent='*CALIBRATE_PHASE*')
    # ms_flux = listobs(vis=vis_to_split, intent='*CALIBRATE_FLUX*')
    # ms_bp = listobs(vis=vis_to_split, intent='*BANDPASS*')
    ms_all = listobs(vis=vis_to_split)
    # ms_science = listobs(vis=vis_to_split, intent='*TARGET*')



    all_ms_fields_ids, all_ms_fields_names = get_fields(ms_all, 'field')

    fields_split_dir = f"{working_directory}/fields"
    if not os.path.exists(fields_split_dir):
        print(f"Creating directory fields/.")
        # os.system(f"mkdir {fields_split_dir}")
        os.makedirs(fields_split_dir)
    for field_to_split in all_ms_fields_names:
        formated_field = field_to_split.replace(' ', '').replace('/', '')

        try:
            os.makedirs(f"{fields_split_dir}/{formated_field}")
        except:
            pass
        # split(vis=vis_to_split,
        #       outputvis=f'{fields_split_dir}/{formated_field}'
        #                 f'/{formated_field}.calibrated.avg12s.ms',
        #       datacolumn='corrected', field=target, timebin='12s')
        try:
            if os.path.exists(f'{fields_split_dir}/{formated_field}/'
                                f'{formated_field}.calibrated{iter}.ms'):
                print(f"{formated_field}.calibrated{iter}.ms exists. "
                        f"Will not create a new one.")
            else:
                print(f"Splitting field {field_to_split} into "
                            f"-->> {working_directory}/fields/{formated_field}"
                            f"/{formated_field}.calibrated{iter}.ms")
                split(vis=vis_to_split,
                        outputvis=f'{fields_split_dir}/{formated_field}/'
                                f'{formated_field}.calibrated{iter}.ms',
                        datacolumn='corrected', field=field_to_split)

            if os.path.exists(f'{fields_split_dir}/{formated_field}/'
                                f'{formated_field}.calibrated{iter}.avg{timebin_longer}.ms'):
                print(f"{formated_field}.calibrated{iter}.avg{timebin_longer}.ms exists. "
                        f"Will not create a new one")
            else:
                print(f"Splitting field {field_to_split} into "
                            f"-->> {working_directory}/fields/{formated_field}"
                            f"/{formated_field}.calibrated{iter}.avg{timebin_longer}.ms")
                split(vis=vis_to_split,
                        outputvis=f'{fields_split_dir}/{formated_field}/'
                                f'{formated_field}.calibrated{iter}.avg{timebin_longer}.ms',
                        datacolumn='corrected', field=field_to_split,timebin=timebin_longer)
        except Exception as e:
            print(e)
            pass

def flux_3C286(freq,a0=1.2515,a1=-0.4605,a2=-0.1715,a3=0.0336):
    return(a0 + a1*np.log10(freq) + a2*((np.log10(freq))**2.0) + a3*((np.log10(freq))*3.0))

def calculate_percentages(data):
    percentages = {}
    for category, subcategories in data.items():
        if isinstance(subcategories, dict):
            percentages[category] = {}
            for subcategory, values in subcategories.items():
                if 'flagged' in values and 'total' in values:
                    percentages[category][subcategory] = (values['flagged'] / values['total']) * 100
    return percentages

def plot_category_data(percentages_over_steps, category):
    run_steps = list(percentages_over_steps.keys())
    plt.figure(figsize=(10, 10))
    # Ensure category exists in all steps
    if not all(category in step for step in percentages_over_steps.values()):
        print(f"Category '{category}' not found in all data steps.")
        return

    subcategories = set()
    for step in percentages_over_steps.values():
        subcategories.update(step.get(category, {}).keys())

    for subcategory in subcategories:
        flagged_percentages = [
            percentages_over_steps[step].get(category, {}).get(subcategory, 0) for step
            in run_steps
        ]
        plt.plot(run_steps, flagged_percentages, label=subcategory, marker='o')

    plt.xlabel('Processing Step')
    plt.ylabel('Flagged Data (%)')
    plt.title(f'Flagged Data Over Processing Steps ({category.capitalize()})')
    plt.legend()
    plt.ylim(0, 100)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # os.path.join(working_directory).rstrip('/') + '/' + 'plots'

    plt.savefig(f'{os.path.dirname(working_directory)}/plots/flag_stats'
                f'_{category}_flagged_data.jpg', dpi=300,
                bbox_inches='tight')
    # plt.show()
    plt.clf()
    plt.close()


def plot_flag_stats(flag_stats):
    # Accumulate percentages with labels
    percentages_over_steps = {}
    for label, step in flag_stats.items():
        percentages_over_steps[label] = calculate_percentages(step)
    # Plotting data for each category
    # categories = ['antenna', 'array', 'correlation', 'field', 'observation', 'scan', 'spw']
    categories = ['field', 'observation', 'spw', 'correlation', 'antenna']
    for category in categories:
        plot_category_data(percentages_over_steps, category)

def check_longest_baseline(vis):
    ms.open(vis_for_cal)
    ms.selectinit(datadescid=0)
    uvw = ms.getdata('uvw')['uvw']
    ms.close()
    uvdist_meters = np.sqrt(uvw[0] ** 2 + uvw[1] ** 2)
    longest_baseline_meters = np.nanmax(uvdist_meters)
    band_name, mean_freq, max_freq, min_freq = check_band(vis)
    frequency_hz = max_freq*1e9  # Example: 5 GHz
    speed_of_light = 3e8  # m/s
    wavelength_meters = speed_of_light / frequency_hz
    longest_baseline_lambda = longest_baseline_meters / wavelength_meters
    return(longest_baseline_lambda)


def check_band(vis):
    band_name = None
    freq_ranges = {
        (1, 2): "L",
        (2, 4): "S",
        (4, 8): "C",
        (8, 12): "X",
        (12, 18): "U",  # U is the Ku band.
        (18, 26.5): "K",
        (26.5, 40): "A",  # A is the Ka band
        (40, 50): "Q",
    }
    msmd.open(vis)
    bandwidth = msmd.bandwidths()
    nspw = len(bandwidth)

    chan_freqs_all = np.empty(nspw, dtype=object)
    spws_freq = np.zeros(nspw)

    for nch in range(nspw):
        chan_freqs_all[nch] = msmd.chanfreqs(nch)
        spws_freq[nch] = np.nanmean(chan_freqs_all[nch])

    msmd.done()

    mean_freq = np.nanmean(spws_freq) * 1e-9
    max_freq = np.nanmax(spws_freq) * 1e-9
    min_freq = np.nanmin(spws_freq) * 1e-9
    for range_, band in freq_ranges.items():
        if mean_freq >= range_[0] and mean_freq <= range_[1]:
            band_name = band
    return(band_name,mean_freq,max_freq,min_freq)

def run_imaging_tclean(fields_to_image):
    # unit = 'mJy'
    # rms_std_factor = 3
    #rms_level = 0.037 #Natural
    # rms_level = 0.044 #Robust
    # rms_std = str(rms_level/rms_std_factor)+unit
    # ms_science = listobs(vis=vis_for_cal, intent='*TARGET*')
    # threshold =  rms_std
    # parallel = True
    calcpsf = True
    spw = ''
    outlierfile = ''
    # specmode = 'mfs'
    specmode = 'mvc'
    deconvolver = 'mtmfs'
    ext = ''
    # gridder = 'wproject'
    gridder = 'standard'
    wprojplanes = 1024
    scales = [0, 5, 20]
    interactive = False
    datacolumn = 'data'
    usemask = 'auto-multithresh'
    niter = 1500
    mask = ''
    cycleniter = 200
    smallscalebias = 0.75
    robust = 0.5
    weighting = 'briggs'
    gain = 0.1
    pblimit = -0.1
    nterms = 2
    sidelobethreshold = 3.0
    noisethreshold = 6.0
    lownoisethreshold = 4.0
    minbeamfrac = 0.2
    growiterations = 75
    negativethreshold = 0.0
    fastnoise = False
    phasecenter = ''
    psfphasecenter = ''
    usepointing = True
    uvtaper = ''
    uvrange = ''
    imsize = 3072
    if deconvolver == 'mtmfs':
        ext = ext + '.tt0'

    for field_to_image in fields_to_image:
        formated_field = field_to_image.replace(' ', '').replace('/', '')
        g_name = f"{working_directory}fields/{formated_field}/{formated_field}.calibrated.avg{timebin_longer}"
        # g_name = f"{working_directory}fields/{formated_field}/{formated_field}.calibrated"
        g_vis = g_name + '.ms'
        logging.info(f" ++==>> Checking splited visibility: {g_vis}")


        if os.path.exists(f'{g_vis}'):
            imagename = (f"{working_directory}/fields/{formated_field}/"
                         f"phasecal_image_{formated_field}.calibrated.avg{timebin_longer}")
            longest_baseline_lambda = check_longest_baseline(g_vis)
            cell_float = (180.0 * 3600 / (np.pi * 5)) * (1.0 /longest_baseline_lambda)
            cell = f'{cell_float:.2f}arcsec'
            logging.info(f" ++==>> Imaging field {formated_field}")
            logging.info(f"      > Image name prefix: {imagename}")
            logging.info(f"      > Cell size: {cell}")

            if not os.path.exists(imagename+'.image'+ext):
                tclean(vis=g_vis,
                       imagename=imagename,
                       spw=spw, field=field_to_image, outlierfile=outlierfile, gain=gain,
                       specmode=specmode, deconvolver=deconvolver, gridder=gridder,
                       wprojplanes=wprojplanes,
                       scales=scales, smallscalebias=smallscalebias,
                       imsize=imsize, cell=cell,
                       weighting=weighting, robust=robust,
                       niter=niter, interactive=interactive,
                       pblimit=pblimit, nterms=nterms,
                       usemask=usemask,
                       # threshold=threshold,
                       mask=mask, pbcor=True,
                       sidelobethreshold=sidelobethreshold,
                       noisethreshold=noisethreshold,
                       lownoisethreshold=lownoisethreshold,
                       minbeamfrac=minbeamfrac,fastnoise=fastnoise,
                       usepointing=usepointing, psfphasecenter=psfphasecenter,
                       phasecenter=phasecenter,
                       datacolumn=datacolumn, cycleniter=cycleniter, calcpsf=calcpsf,
                       growiterations=growiterations,
                       negativethreshold=negativethreshold, parallel=parallel,
                       verbose=True, uvtaper=uvtaper, uvrange=uvrange,
                       savemodel='none')
                exportfits(imagename=imagename + '.image' + ext,
                           fitsimage=imagename + '.image' + ext + '.fits',
                           velocity=True)
            else:
                logging.warning(f"Image {imagename+'.image'+ext} exists. Will not image again")


            eimshow(imagename+'.image'+ext+'.fits',
                    num_contours=6,
                    mad_factor=6)
def ctn(image):
    '''
        Name origin:
        ctn > casa to numpy
        Function that read fits files, using casa IA.open or astropy.io.fits.
        Note: For some reason, IA.open returns a rotated mirroed array, so we need
        to undo it by a rotation.
        '''
    import astropy.io.fits as pf
    if isinstance(image, str) == True:
        try:
            ia = IA()
            ia.open(image)
            try:
                numpy_array = ia.getchunk()[:, :, 0, 0]
            except:
                numpy_array = ia.getchunk()[:, :]
            ia.close()
            # casa gives a mirroed and 90-degree rotated image :(
            data_image = np.rot90(numpy_array)[::-1, ::]
            return (data_image)
        except:
            try:
                data_image = pf.getdata(image)
                return (data_image)
            except:
                print('Input image is not a fits file.')
                return(ValueError)
    else:
        print('Input image is not a string.')

def eimshow(imagename, num_contours=5, mad_factor=6, contour_max_factor=0.95,
                            cmap='magma_r',cutout_size=256):
    """
    enhanced-imshow.

    Parameters:
    - imagename: Path to the FITS file containing the image data.
    - num_contours: Number of contour levels (default is 10).
    - mad_factor: Factor to multiply the MAD value for the minimum contour level (default is 3).
    - contour_max_factor: Maximum fraction of the peak value for the highest contour (default is 0.95).
    - cmap: Colormap for the image display (default is 'viridis').
    """
    import matplotlib.ticker as mticker
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    class CustomFormatter(mticker.ScalarFormatter):
        def __init__(self, factor=1, **kwargs):
            self.factor = factor
            mticker.ScalarFormatter.__init__(self, **kwargs)

        def __call__(self, x, pos=None):
            x = x * self.factor
            if x == 0:
                return "0.00"
            return "{:.2f}".format(x)

    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    from astropy.io import fits
    from astropy.stats import mad_std
    from astropy.visualization import simple_norm

    # Read the image data from the FITS file
    with fits.open(imagename) as hdul:
        image_data = hdul[0].data
    if len(image_data.shape) == 4:
        image_data = image_data[0][0]
    # image_data = ctn(imagename)
    # Handle possible multi-dimensional data (take the first 2D slice if needed)
    # if image_data.ndim > 2:
    #     image_data = image_data[0]
    # Find the peak intensity position
    peak_y, peak_x = np.unravel_index(np.argmax(image_data), image_data.shape)

    # Calculate the robust standard deviation using MAD
    mad_std_value = mad_std(image_data)
    # Define the minimum contour level as proportional to the MAD
    min_contour_level = mad_factor * mad_std_value
    max_value = np.max(image_data)

    # If a cutout size is specified, extract the region centered on the peak
    if cutout_size is not None:
        half_size = cutout_size // 2
        x_min = max(peak_x - half_size, 0)
        x_max = min(peak_x + half_size, image_data.shape[1])
        y_min = max(peak_y - half_size, 0)
        y_max = min(peak_y + half_size, image_data.shape[0])
        image_data = image_data[y_min:y_max, x_min:x_max]



    # Set up figure and axis
    fig, ax = plt.subplots(figsize=(8, 8))

    # Plot the image using a logarithmic normalization for better visibility of all emission
    norm0 = simple_norm(image_data, stretch='linear', max_percent=99.0)
    img = ax.imshow(image_data, origin='lower', cmap='gray', norm=norm0, alpha=0.5)
    norm = simple_norm(image_data, stretch='sqrt', asinh_a=0.02, vmin=min_contour_level,
                       vmax=max_value)
    # Display the image
    img = ax.imshow(image_data, origin='lower', cmap=cmap, norm=norm)



    # Ensure the max contour doesn't exceed the image max value
    max_contour_level = contour_max_factor * max_value

    # Define geometric contour levels
    try:
        # contour_levels = np.geomspace(min_contour_level, max_contour_level, num_contours)
        levels_g = np.geomspace(2.0 * np.nanmax(image_data), 5 * mad_std_value, num_contours)
        levels_low = np.asarray([4 * mad_std_value, 3 * mad_std_value])
        levels_neg = np.asarray([-3]) * mad_std_value

        contour_palette_ = ['#000000', '#444444', '#666666', '#EEEEEE',
                            '#EEEEEE', '#FFFFFF']
        if '_r' in cmap:
            contour_palette = contour_palette_
        else:
            contour_palette = contour_palette_[::-1]

        # Add contours to the plot
        ax.contour(image_data, levels=levels_g[::-1], colors=contour_palette, linewidths=1.2)
        ax.contour(image_data, levels=levels_low[::-1], colors='brown', linewidths=1.0)
        ax.contour(image_data, levels=levels_neg, colors='k',
                   linewidths=1.0, alpha=1.0)
    except:
        logging.warning(f" --==>> Could not plot contours for {imagename}.")
        pass

    # Add colorbar
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%",
                              pad=0.05)  # Adjust 'pad' for space and 'size' for width
    cbar = fig.colorbar(img, cax=cax)
    cbar.set_label('Intensity [Jy/beam]')
    cbar.formatter = CustomFormatter(factor=1000, useMathText=True)
    cbar.update_ticks()
    # Add labels and grid
    ax.set_xlabel(r'Pixel $x$')
    ax.set_ylabel(r'Pixel $y$')
    ax.grid(False)
    plt.savefig(imagename.replace('.fits','')  + '_map.jpg', dpi=600,
                bbox_inches='tight')
    # Show the plot
    # plt.show()
    plt.clf()
    plt.close()
def initial_corrections(vis):
    """
    Init first corrections to the data, e.g. opacity, gain curve, etc.
    """

    initial_corrections_starttime = time.time()

    calibration_dir = os.path.join(working_directory).rstrip('/')+'/'+'calibration'
    plots_dir = os.path.join(working_directory).rstrip('/')+'/'+ 'plots'

    try:
        if not os.path.exists(calibration_dir):
            logging.warning("Calibration dir must be specified")
    except Exception as e:
        logging.error(f"Exception {e} while checking if {calibration_dir} exists")

    global init_tables
    init_tables = []
    #  antenna pos
    init_tables_dict = {}
    
    try:
        logging.info("Generating cal solutions for antenna positions")
        caltable = f"{calibration_dir}/{os.path.basename(vis.replace('.ms','_antpos.tb'))}"
        # os.system(f"rm -r {caltable}")
        if not os.path.exists(caltable):
            casatasks.gencal(vis=vis,caltable=caltable, caltype='antpos')
        init_tables.append(caltable)
        init_tables_dict['antpos'] = caltable
    except Exception as e:
        logging.critical(f"Exception {e} while generating {caltable}")

    # gain curves
    try:
        logging.info("Generating cal solutions for gaincurves")
        caltable = f"{calibration_dir}/{os.path.basename(vis.replace('.ms','_gaincurve.tb'))}"
        if not os.path.exists(caltable):
            # os.system(f"rm -r {caltable}")
            casatasks.gencal(vis=vis,caltable=caltable, caltype='gc')
        init_tables.append(caltable)
        init_tables_dict['gaincurve'] = caltable
    except Exception as e:
        logging.critical(f"Exception {e} while generating {caltable}")



    # NB: Implement tec corrections -- for low frequencies

    msmd = casatools.msmetadata()

    msmd.open(vis)
    bandwidth = msmd.bandwidths()
    nspw = len(bandwidth)
    msmd.done()
    spws = []

    for i in range(0, nspw):
        spws.append(str(i))
    all_spw = ', '.join(spws)
    

    try:
        logging.info("Generating cal tables for opacities")
        weather_plot = vis+'_weather.pdf'
        # os.system(f"rm -r {weather_plot}")
        myTau = casatasks.plotweather(vis=vis, seasonal_weight=0.5, doPlot=True, plotName=weather_plot)
        os.system(f'mv {weather_plot} {plots_dir}')
        try:
            caltable = f"{calibration_dir}/{os.path.basename(vis.replace('.ms', '_opacity.tb'))}"
            logging.info(f"Generating weather caltable {caltable}")
            if not os.path.exists(caltable):
            # fix the spw here
                casatasks.gencal(vis=vis,caltable=caltable,caltype='opac', spw=all_spw, parameter=myTau)
            init_tables.append(caltable)
            init_tables_dict['opacity'] = caltable
        except Exception as e:
            logging.critical(f"Exception {e} while generating cal for opacity")      
    except Exception as e:
        logging.critical(f"Exception {e} while running plotweather")


    # requantisation corrections

    try:
        logging.info("Generating cal solutions for rq")
        caltable = f"{calibration_dir}/{os.path.basename(vis.replace('.ms', '_rq.tb'))}"
        # os.system(f"rm -r {caltable}")
        if not os.path.exists(caltable):
            casatasks.gencal(vis=vis,caltable=caltable, caltype='rq')
        init_tables.append(caltable)
        init_tables_dict['rq'] = caltable
    except Exception as e:
        logging.critical(f"Exception {e} while generating {caltable}")

    #  switched power

    try:
        logging.info("Generating cal solutions for spwpow")
        caltable = f"{calibration_dir}/{os.path.basename(vis.replace('.ms', '_spwpow.tb'))}"
        # os.system(f"rm -r {caltable}")
        if not os.path.exists(caltable):
            casatasks.gencal(vis=vis,caltable=caltable, caltype='swpow')
        init_tables.append(caltable)
        init_tables_dict['swpow'] = caltable
    except Exception as e:
        logging.critical(f"Exception {e} while generating {caltable}")

    initial_corrections_endtime = time.time() 
    initial_corrections_time = initial_corrections_endtime- initial_corrections_starttime
    logging.info(f"Initial calibrations took {initial_corrections_time/ 60:.2f} minutes")
    return(init_tables, init_tables_dict)
    
def flux_scale_setjy(vis,flux_density=None,model_image=None):

    """
    Sets the flux scale
    """

    # try:
    #     logging.info("Clearing model column")
    #     casatasks.delmod(vis, otf=True, scr=False)
    #     logging.info("Successfully deleted model column")
    # except Exception as e:
    #     logging.critical(f"Exception {e} while deleting model column")
    #
    # try:
    #     logging.info("Re-initialize the calibration")
    #     casatasks.clearcal(vis)
    #     logging.info("Successfully cleared the calibration")
    # except Exception as e:
    #     logging.critical(f"Exception {e} while clearing calibrations")

    logging.info(f'Setting the flux scaling using {flux_calibrator}')


    # Get the frequency of the first spectral window
    # fix model here -- needs a way to check which models are available

    """
    Some high frequency observations may have spw 0 in a lower frequency band (e.g. X band)
    due to pointing calibration. So, using spw 0 may not be adequate.
    Instead, we can take an average between all channels and spectral windows.
    """
    # spw = 0
    # spw0_freq = msmd.chanfreqs(0)*1e-9

    msmd = casatools.msmetadata()
    msmd.open(vis)
    bandwidth = msmd.bandwidths()
    nspw = len(bandwidth)


    chan_freqs_all = np.empty(nspw, dtype=object)
    spws_freq = np.zeros(nspw)

    for nch in range(nspw):
        chan_freqs_all[nch] = msmd.chanfreqs(nch)
        spws_freq[nch] = np.mean(chan_freqs_all[nch])

    msmd.done()

    mean_freq = np.mean(spws_freq)*1e-9

    if ('3C286' in flux_calibrator) or ('1331+305' in flux_calibrator):
        model = "3C286"
    if ('3C48' in flux_calibrator) or ('0137+331' in flux_calibrator):
        model = "3C48"
    if ('3C147' in flux_calibrator) or ('0542+498' in flux_calibrator):
        model = "3C147"
    if ('3C138' in flux_calibrator) or ('0521+166' in flux_calibrator):
        model = "3C138"


    freq_ranges = {
        (1, 2): "L",
        (2, 4): "S",
        (4, 8): "C",
        (8, 12): "X",
        (12, 18): "U", #U is also the Ku band.
        (18,26.5):"K",
        (26.5,40): "A", #is Ka the A band?
        (40, 50): "Q",
            }

    available_models = ['3C123_P.im','3C138_K.im','3C138_Q.im','3C138_X.im','3C147_K.im',
                        '3C147_Q.im','3C147_X.im','3C286_C.im','3C286_P.im','3C286_U.im',
                        '3C380_P.im','3C48_K.im','3C48_Q.im','3C48_X.im','3C138_A.im',
                        '3C138_L.im','3C138_S.im','3C147_A.im','3C147_L.im','3C147_S.im',
                        '3C196_P.im','3C286_K.im','3C286_Q.im','3C286_X.im','3C48_A.im',
                        '3C48_L.im','3C48_S.im','3C138_C.im','3C138_P.im','3C138_U.im',
                        '3C147_C.im','3C147_P.im','3C147_U.im','3C286_A.im',
                        '3C286_L.im','3C286_S.im','3C295_P.im','3C48_C.im',
                        '3C48_P.im','3C48_U.im']
    # model = ''

    for range_,band in freq_ranges.items():
        if mean_freq>=range_[0] and mean_freq<=range_[1]:
            logging.info(f"Observations done in band: {band}")
            logging.info(f"Will use model {model}_{band}.im for absolute flux calibration")
            model = model+f'_{band}.im'

    if model not in available_models:
        logging.warning(f"Model {model} not available for band {band}.")
        logging.warning(f"Will use set flux density to [1,0,0,0] for absolute flux "
                        f"calibration, which may be wrong. Please, provide the flux density "
                        f"using the arguments fluxdensity=[I,Q,U,V] and standard='manual' in setjy.")
        flux_density = [1.0,0.0,0.0, 0.0]
    flux_density_data = None
    spws = None
    fluxes = None



    try:
        if flux_density is None:
            logging.info(f"Performing absolute flux calibration using {model}")
            flux_density_data = casatasks.setjy(vis=vis, field=flux_calibrator,
                                                spw='', model=model, scalebychan=True,
                                                standard='Perley-Butler 2017', listmodels=False,
                                                usescratch=True)

            plots_dir = os.path.join(working_directory).rstrip('/') + '/' + 'plots'
            spws = []
            fluxes = []
            # for key in list(flux_density_data['0'].keys())[:-1]:
            for spw_id in range(nspw):
                spws.append(spw_id)
                fluxes.append(flux_density_data['0'][str(spw_id)]['fluxd'][0])
            spws = np.asarray(spws)
            fluxes = np.asarray(fluxes)

            try:
                logging.info(f"Plotting the fluxes against frequency.")
                plt.figure(figsize=(8, 5))
                plt.plot(spws_freq*1e-9, fluxes, 'o', color='black')
                plt.xlabel('Frequency [GHz]')
                plt.ylabel(f"'Flux Density {flux_calibrator} [Jy]")
                plt.grid()
                plt.title('Flux density from setjy model')
                flux_plot = os.path.join(plots_dir, flux_calibrator + '_flux_density_model.pdf')
                plt.savefig(flux_plot, dpi=600)
                plt.clf()
                plt.close()
            except Exception as e:
                logging.warning(f"Flux plot not generated due to: {e}")
        else:
            """
            This should be properly implemented.
            Occasions that this can occur:
                - When the flux density must be explicitly set as there is no model available.
                - Similarly, when it is required to input a model image for the particular flux
                calibrator.
            """
            if model_image is not None:
                logging.warning(f"Using provided model image {model_image} for flux calibrator"
                                f" {flux_calibrator} at {band} band.")
                flux_density_data = casatasks.setjy(vis=vis, field=flux_calibrator,
                                                    spw='', model=model_image, scalebychan=True,
                                                    standard='Perley-Butler 2017', listmodels=False,
                                                    usescratch=True)
            else:
                flux_density_data = casatasks.setjy(vis=vis_to_use, field=flux_calibrator,
                                                    spw=all_spws, scalebychan=True,
                                                    standard='manual', fluxdensity=flux_density,
                                                    listmodels=False, usescratch=True)
    except Exception as e:
        logging.critical(f"Exception {e} while running setjy")

    return(flux_density_data, spws, fluxes)



def run_bandpass(vis, field, scan,
                 refant, spw, solint, minsnr,
                 gaintables, i, table_stage, combine, bandtype,
                 solnorm=False,
                 refantmode='strict', overwrite=False):

    calibration_dir = os.path.join(working_directory).rstrip('/') + '/' + 'calibration'
    try:
        logging.info(f"Running bandpass for field {field}.")
        logging.info(f" >> Stage {table_stage},  with solint of {solint}.")
        caltable = (f"{calibration_dir}/{i}{table_stage}{solint}_{os.path.basename(vis.replace('.ms','.tb'))}")
        logging.info(f"     ++=> Caltable will be:, {caltable}")
        # os.system(f"rm -r {caltable}")

        if overwrite:
            if os.path.exists(caltable):
                os.system(f"rm -r {caltable}")

            casatasks.bandpass(vis=vis, caltable=caltable, scan=scan,
                               field=field, refant=refant, spw=spw,
                               combine=combine, bandtype=bandtype,
                               solint=solint, minsnr=minsnr, solnorm=solnorm,
                               gaintable=gaintables)
        else:
            if not os.path.exists(caltable):
                casatasks.bandpass(vis=vis, caltable=caltable, scan=scan,
                                   field=field, refant=refant, spw=spw,
                                   combine=combine, bandtype=bandtype,
                                   solint=solint, minsnr=minsnr, solnorm=solnorm,
                                   gaintable=gaintables)
            else:
                logging.info('     --=> Caltable already exists. Not going to overwrite.')

        _gaintables_temp = gaintables.copy()
        _gaintables_temp.append(caltable)
        return (_gaintables_temp)
    except Exception as e:
        logging.critical(f"Exception {e} while generating {caltable}")

def run_gaincal(vis, field, scan,
                refant, spw, calmode, solint, minsnr,
                gaintype, gaintables, i, table_stage, combine='',
                refantmode='strict', overwrite=False):
    calibration_dir = os.path.join(working_directory).rstrip('/') + '/' + 'calibration'
    try:
        logging.info(f"Running gaincal [{calmode}] for field(s) {field}.")
        logging.info(f" >> Stage {table_stage},  with solint of {solint}.")
        caltable = (
            f"{calibration_dir}/{i}{table_stage}{solint}_{os.path.basename(vis.replace('.ms', '.tb'))}")
        logging.info(f"     ++=> Caltable will be:, {caltable}")

        if overwrite:
            if os.path.exists(caltable):
                os.system(f"rm -r {caltable}")
            casatasks.gaincal(vis=vis, caltable=caltable,scan=scan,
                              field=field, refant=refant, spw=spw, combine=combine,
                              calmode=calmode, solint=solint, minsnr=minsnr, gaintype=gaintype,
                              refantmode=refantmode,
                              # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                              gaintable=gaintables)
        else:
            if not os.path.exists(caltable):
                casatasks.gaincal(vis=vis, caltable=caltable, scan=scan,
                                  field=field, refant=refant, spw=spw, combine=combine,
                                  calmode=calmode, solint=solint, minsnr=minsnr, gaintype=gaintype,
                                  refantmode=refantmode,
                                  # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                                  gaintable=gaintables)
            else:
                logging.info('     --=> Caltable already exists. Not going to overwrite.')
        _gaintables_temp = gaintables.copy()
        _gaintables_temp.append(caltable)
        return (_gaintables_temp)
    except Exception as e:
        logging.critical(f"Exception {e} while generating {caltable}")


def get_chan_spws_map(vis):
    msmd = casatools.msmetadata()
    msmd.open(vis)
    bandwidth = msmd.bandwidths()
    nspw = len(bandwidth)

    chan_spw_skip_edge_map = np.empty(nspw, dtype=object)
    for spw_id in range(nspw):
        chan_spw_skip_edge_map[spw_id] = (f"{spw_id}:{int(edge_channel_frac*msmd.nchan(spw_id))}~"
                                          f"{int(((1-edge_channel_frac)*msmd.nchan(spw_id)))}")
    spw_skip_edge = ','.join(chan_spw_skip_edge_map)

    chan_spw_central_map = np.empty(nspw, dtype=object)
    for spw_id in range(nspw):
        chan_spw_central_map[spw_id] = (f"{spw_id}:"
                                        f"{int(0.2*msmd.nchan(spw_id))}~"
                                        f"{int(0.8*msmd.nchan(spw_id))}")
    spw_central = ','.join(chan_spw_central_map)
    msmd.done()
    return(spw_skip_edge,spw_central)

def bandpass_cal(i=1, do_plots=False):
    if do_plots:
        check_bandpass_plots(ref_antenna_list=ref_antenna_list,
                             field=bandpass_calibrator, spws=None)

    spw_skip_edge, spw_central = get_chan_spws_map(vis=vis_for_cal)

    overwrite = True

    gain_tables_dict = {}
    table_stage = '_bpcal_d_'
    solint = bp_solint_K
    gaintables_temp_K = run_gaincal(vis=vis_for_cal,
                                    field=bandpass_calibrator,
                                    gaintables=init_tables,
                                    scan='', refant=ref_antenna,
                                    spw=spw_skip_edge,
                                    calmode='p', gaintype='K',
                                    solint=solint,overwrite=overwrite,
                                    i=i, table_stage=table_stage,
                                    minsnr=minsnr
                                    )

    gain_tables_dict['bp_K'] = gaintables_temp_K[-1]

    calibration_table_plot(table=gain_tables_dict['bp_K'],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='ant1', yaxis='delay', fields='')

    calibration_table_plot(table=gain_tables_dict['bp_K'],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='time', yaxis='delay', fields='')

    table_stage = '_bpcal_p_'
    solint = bp_solint_G_p
    # solint = '16s'
    gaintables_temp_bpcal_p = run_gaincal(vis=vis_for_cal,
                                          field=bandpass_calibrator,
                                          gaintables=gaintables_temp_K,
                                          scan='', refant=ref_antenna,
                                          spw=spw_central, calmode='p', gaintype='G',
                                          solint=solint,overwrite=overwrite,
                                          i=i, table_stage=table_stage,
                                          minsnr=minsnr
                                          )
    gain_tables_dict['bp_p'] = gaintables_temp_bpcal_p[-1]

    calibration_table_plot(table=gain_tables_dict['bp_p'],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='chan', yaxis='phase', fields='')

    calibration_table_plot(table=gain_tables_dict['bp_p'],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='time', yaxis='phase', fields='')
    # Plot the phase gains for individual antennas.
    # for k in range(len(ref_antenna_list)):
    #     calibration_table_plot(table=gain_tables_dict['bp_p'],
    #                            stage='calibration', antenna=f"{ref_antenna_list[k]}",
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='time', yaxis='phase', fields='')

    table_stage = '_bpcal_ap_'
    solint = bp_solint_G_ap
    gaintables_temp_bpcal_ap = run_gaincal(vis=vis_for_cal,
                                           field=bandpass_calibrator,
                                           gaintables=gaintables_temp_bpcal_p,
                                           scan='', refant=ref_antenna,
                                           spw=spw_central, calmode='ap', gaintype='G',
                                           solint=solint, overwrite=overwrite,
                                           i=i, table_stage=table_stage,
                                           minsnr=minsnr
                                           )
    gain_tables_dict['bp_ap'] = gaintables_temp_bpcal_ap[-1]


    calibration_table_plot(table=gain_tables_dict['bp_ap'],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='time', yaxis='phase', fields='')

    calibration_table_plot(table=gain_tables_dict['bp_ap'],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='time', yaxis='amp', fields='')


    table_stage = '_bpcal_ap_inf_'
    solint = 'inf'
    gaintables_temp_bpcal_ap_inf = run_gaincal(vis=vis_for_cal,
                                           field=bandpass_calibrator,
                                           gaintables=gaintables_temp_bpcal_p,
                                           scan='', refant=ref_antenna,
                                           spw=spw_central, calmode='ap', gaintype='G',
                                           solint=solint, overwrite=False,
                                           i=i, table_stage=table_stage,
                                           minsnr=minsnr
                                           )
    gain_tables_dict['bp_ap_inf'] = gaintables_temp_bpcal_ap_inf[-1]


    calibration_table_plot(table=gain_tables_dict['bp_ap_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='time', yaxis='phase', fields='')

    calibration_table_plot(table=gain_tables_dict['bp_ap_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='time', yaxis='amp', fields='')

    table_stage = '_bpcal_BP_'
    solint = bp_solint_BP
    gaintables_temp_bpcal_BP = run_bandpass(vis=vis_for_cal,
                                            field=bandpass_calibrator,
                                            gaintables=gaintables_temp_bpcal_ap_inf,
                                            combine='scan', bandtype='B',
                                            scan='', refant=ref_antenna,
                                            spw='*', overwrite=True,
                                            solint=solint, solnorm=True,
                                            i=i, table_stage=table_stage,
                                            minsnr=minsnr
                                            )

    gain_tables_dict['bp_BP_inf'] = gaintables_temp_bpcal_BP[-1]

    calibration_table_plot(table=gain_tables_dict['bp_BP_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='chan', yaxis='phase', fields='')

    calibration_table_plot(table=gain_tables_dict['bp_BP_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='freq', yaxis='phase', fields='')

    calibration_table_plot(table=gain_tables_dict['bp_BP_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='chan', yaxis='amp', fields='')

    calibration_table_plot(table=gain_tables_dict['bp_BP_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='freq', yaxis='amp', fields='')

    logging.info(f"Consolidating tables for bandpass cal apply.")
    pre_cal_tables_temp = [gain_tables_dict['bp_K'],
                           gain_tables_dict['bp_p'],
                           # gain_tables_dict['bp_ap'],
                           gain_tables_dict['bp_ap_inf'],
                           gain_tables_dict['bp_BP_inf']]



    logging.info(f"Consolidating gainfields for bandpass cal apply.")
    gainfield_init = [''] * len(init_tables)
    gainfield_bandpass = [bandpass_calibrator] * len(pre_cal_tables_temp)
    gainfield_bandpass_apply = gainfield_init.copy()
    gainfield_bandpass_apply.extend(gainfield_bandpass)

    gaintables_apply_BP = init_tables.copy()
    gaintables_apply_BP.extend(pre_cal_tables_temp)

    gaintables_apply_BP_dict = {}
    gaintables_apply_BP_dict[f"BP_tables_run_{i}"] = gaintables_apply_BP
    gainfields_apply_BP_dict = {}
    gainfields_apply_BP_dict[f"BP_gainfields_run_{i}"] = gainfield_bandpass_apply


    logging.info(f"Creating flag-backup before applying initial bandpass.")
    casatasks.flagmanager(vis=vis_for_cal, mode='save',
                          versionname='before_bandpass_init_' + str(i),
                          comment='Flags before apply bandpass init, iteraction' + str(i) + '.')

    logging.info('     ++==>> Reporting flags before applycal to bandpass.')
    summary_before_applycal_to_bandpass = casatasks.flagdata(vis=vis_for_cal,
                                                             mode='summary',
                                                             field=bandpass_calibrator)
    report_flag(summary_before_applycal_to_bandpass, 'field')

    casatasks.applycal(vis=vis_for_cal, field=bandpass_calibrator,
                       gaintable=gaintables_apply_BP,
                       gainfield=gainfield_bandpass_apply,
                       calwt=False, flagbackup=False)

    logging.info('     ++==>> Reporting flags after applycal to bandpass.')
    summary_after_applycal_to_bandpass = casatasks.flagdata(vis=vis_for_cal, mode='summary',
                                                            field=bandpass_calibrator)
    report_flag(summary_after_applycal_to_bandpass, 'field')

    make_plots_stages(vis = vis_for_cal,stage='after', kind=f"after_bandpass_apply_iter_{i}",
                      FIELDS=bandpass_calibrator.split(','))

    return (gaintables_apply_BP, gainfield_bandpass_apply,
            gain_tables_dict,gaintables_apply_BP_dict,gainfields_apply_BP_dict)
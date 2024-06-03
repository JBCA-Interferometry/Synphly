available_models = ['3C123_P.im', '3C138_K.im', '3C138_Q.im', '3C138_X.im', '3C147_K.im',
                    '3C147_Q.im', '3C147_X.im', '3C286_C.im', '3C286_P.im', '3C286_U.im',
                    '3C380_P.im', '3C48_K.im', '3C48_Q.im', '3C48_X.im', '3C138_A.im',
                    '3C138_L.im', '3C138_S.im', '3C147_A.im', '3C147_L.im', '3C147_S.im',
                    '3C196_P.im', '3C286_K.im', '3C286_Q.im', '3C286_X.im', '3C48_A.im',
                    '3C48_L.im', '3C48_S.im', '3C138_C.im', '3C138_P.im', '3C138_U.im',
                    '3C147_C.im', '3C147_P.im', '3C147_U.im', '3C286_A.im',
                    '3C286_L.im', '3C286_S.im', '3C295_P.im', '3C48_C.im',
                    '3C48_P.im', '3C48_U.im']


def initial_corrections(vis):
    """
    Init first corrections to the data, e.g. opacity, gain curve, etc.
    """

    initial_corrections_starttime = time.time()

    calibration_dir = os.path.join(working_directory).rstrip('/') + '/' + 'calibration'
    plots_dir = os.path.join(working_directory).rstrip('/') + '/' + 'plots'

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
        caltable = f"{calibration_dir}/{os.path.basename(vis.replace('.ms', '_antpos.tb'))}"
        # os.system(f"rm -r {caltable}")
        if not os.path.exists(caltable):
            gencal(vis=vis, caltable=caltable, caltype='antpos')
        if os.path.exists(caltable):
            init_tables.append(caltable)
            init_tables_dict['antpos'] = caltable
    except Exception as e:
        logging.critical(f"Exception {e} while generating {caltable}")

    # gain curves
    try:
        logging.info("Generating cal solutions for gaincurves")
        caltable = f"{calibration_dir}/{os.path.basename(vis.replace('.ms', '_gaincurve.tb'))}"
        if not os.path.exists(caltable):
            # os.system(f"rm -r {caltable}")
            gencal(vis=vis, caltable=caltable, caltype='gc')
        init_tables.append(caltable)
        init_tables_dict['gaincurve'] = caltable
    except Exception as e:
        logging.critical(f"Exception {e} while generating {caltable}")

    # NB: Implement tec corrections -- for low frequencies
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
        weather_plot = vis + '_weather.pdf'
        # os.system(f"rm -r {weather_plot}")
        myTau = plotweather(vis=vis, seasonal_weight=0.5, doPlot=True, plotName=weather_plot)
        os.system(f'mv {weather_plot} {plots_dir}')
        try:
            caltable = f"{calibration_dir}/{os.path.basename(vis.replace('.ms', '_opacity.tb'))}"
            logging.info(f"Generating weather caltable {caltable}")
            if not os.path.exists(caltable):
                # fix the spw here
                gencal(vis=vis, caltable=caltable, caltype='opac', spw=all_spw, parameter=myTau)
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
            gencal(vis=vis, caltable=caltable, caltype='rq')
        init_tables.append(caltable)
        init_tables_dict['rq'] = caltable
    except Exception as e:
        logging.critical(f"Exception {e} while generating {caltable}")

    #  switched power

    # try:
    #     logging.info("Generating cal solutions for spwpow")
    #     caltable = f"{calibration_dir}/{os.path.basename(vis.replace('.ms', '_spwpow.tb'))}"
    #     # os.system(f"rm -r {caltable}")
    #     if not os.path.exists(caltable):
    #         gencal(vis=vis,caltable=caltable, caltype='swpow')
    #     init_tables.append(caltable)
    #     init_tables_dict['swpow'] = caltable
    # except Exception as e:
    #     logging.critical(f"Exception {e} while generating {caltable}")

    initial_corrections_endtime = time.time()
    initial_corrections_time = initial_corrections_endtime - initial_corrections_starttime
    logging.info(f"Initial calibrations took {initial_corrections_time / 60:.2f} minutes")
    return (init_tables, init_tables_dict)


def flux_scale_setjy(vis, flux_density=None, model_image=None, spix=None):
    """
    Sets the flux scale
    """

    try:
        logging.info("Clearing model column")
        delmod(vis, otf=True, scr=False)
        logging.info("Successfully deleted model column")
    except Exception as e:
        logging.critical(f"Exception {e} while deleting model column")

    try:
        logging.info("Re-initialize the calibration")
        clearcal(vis)
        logging.info("Successfully cleared the calibration")
    except Exception as e:
        logging.critical(f"Exception {e} while clearing calibrations")

    logging.info(f'Setting the flux scaling using {flux_calibrator}')
    if os.path.exists(vis + '.flagversions/flags.before_setjy/'):
        # logging.info(f"Restoring flags from {vis}.flagversions/flags.before_setjy/")
        flagmanager(vis=vis, mode='restore', versionname='before_setjy')
    else:
        # logging.info(f"Saving flags from {vis}.flagversions/flags.before_setjy/")
        flagmanager(vis=vis, mode='save', versionname='before_setjy')

    # Get the frequency of the first spectral window
    # fix model here -- needs a way to check which models are available

    """
    Some high frequency observations may have spw 0 in a lower frequency band (e.g. X band)
    due to pointing calibration. So, using spw 0 may not be adequate.
    Instead, we can take an average between all channels and spectral windows.
    """
    # spw = 0
    # spw0_freq = msmd.chanfreqs(0)*1e-9

    msmd.open(vis)
    bandwidth = msmd.bandwidths()
    nspw = len(bandwidth)

    chan_freqs_all = np.empty(nspw, dtype=object)
    spws_freq = np.zeros(nspw)

    for nch in range(nspw):
        chan_freqs_all[nch] = msmd.chanfreqs(nch)
        spws_freq[nch] = np.mean(chan_freqs_all[nch])

    msmd.done()

    mean_freq = np.mean(spws_freq) * 1e-9
    """
    To do: add all cross-identifications for each flux calibrator.
    """
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
        (12, 18): "U",  # U is also the Ku band.
        (18, 26.5): "K",
        (26.5, 40): "A",  # is Ka the A band?
        (40, 50): "Q",
    }

    # model = ''

    for range_, band in freq_ranges.items():
        if mean_freq >= range_[0] and mean_freq <= range_[1]:
            logging.info(f"Observations done in band: {band}")
            logging.info(f"Will use model {model}_{band}.im for absolute flux calibration")
            model = model + f'_{band}.im'

    if model not in available_models:
        logging.warning(f"Model {model} not available for band {band}.")
        logging.warning(f"Will use set flux density to [1,0,0,0] for absolute flux "
                        f"calibration, which may be wrong. Please, provide the flux density "
                        f"using the arguments fluxdensity=[I,Q,U,V] and standard='manual' in setjy.")
        flux_density = [1.0, 0.0, 0.0, 0.0]
    flux_density_data = None
    spws = None
    fluxes = None

    try:
        if flux_density == '':
            logging.info(f"Performing absolute flux calibration using {model}")
            flux_density_data = setjy(vis=vis, field=flux_calibrator,
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
                plt.plot(spws_freq * 1e-9, fluxes, 'o', color='black')
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
            if model_image != '':
                logging.warning(f"Using provided model image {model_image} for flux calibrator"
                                f" {flux_calibrator} at {band} band.")
                flux_density_data = setjy(vis=vis, field=flux_calibrator,
                                          spw='', model=model_image, scalebychan=True,
                                          standard='Perley-Butler 2017', listmodels=False,
                                          usescratch=True)
            else:
                flux_density_data = setjy(vis=vis_for_cal, field=flux_calibrator,
                                          spw='', scalebychan=True,
                                          standard='manual', fluxdensity=flux_density,
                                          reffreq=f'{mean_freq}GHz', spix=spix,
                                          listmodels=False, usescratch=True)
    except Exception as e:
        logging.critical(f"Exception {e} while running setjy")

    return (flux_density_data, spws, fluxes)


def run_bandpass(vis, field, scan,
                 refant, spw, solint, minsnr,
                 gaintables, i, table_stage, combine, bandtype,
                 solnorm=False,
                 refantmode='strict', overwrite=False):
    calibration_dir = os.path.join(working_directory).rstrip('/') + '/' + 'calibration'
    try:
        logging.info(f"Running bandpass for field {field}.")
        logging.info(f" >> Stage {table_stage},  with solint of {solint}.")
        caltable = (
            f"{calibration_dir}/{i}{table_stage}{solint}_{os.path.basename(vis.replace('.ms', '.tb'))}")
        logging.info(f"     ++=> Caltable will be:, {caltable}")
        # os.system(f"rm -r {caltable}")

        if overwrite:
            if os.path.exists(caltable):
                os.system(f"rm -r {caltable}")

            bandpass(vis=vis, caltable=caltable, scan=scan,
                     field=field, refant=refant, spw=spw,
                     combine=combine, bandtype=bandtype,
                     solint=solint, minsnr=minsnr, solnorm=solnorm,
                     gaintable=gaintables)
        else:
            if not os.path.exists(caltable):
                bandpass(vis=vis, caltable=caltable, scan=scan,
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
            gaincal(vis=vis, caltable=caltable, scan=scan,
                    field=field, refant=refant, spw=spw, combine=combine,
                    calmode=calmode, solint=solint, minsnr=minsnr, gaintype=gaintype,
                    refantmode=refantmode,
                    # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                    gaintable=gaintables)
        else:
            if not os.path.exists(caltable):
                gaincal(vis=vis, caltable=caltable, scan=scan,
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


def get_chan_spws_map(vis, compute_edge_for_flagging=False):
    msmd.open(vis)
    bandwidth = msmd.bandwidths()
    nspw = len(bandwidth)

    chan_spw_skip_edge_map = np.empty(nspw, dtype=object)
    for spw_id in range(nspw):
        chan_spw_skip_edge_map[spw_id] = (f"{spw_id}:{int(edge_channel_frac * msmd.nchan(spw_id))}~"
                                          f"{int(((1 - edge_channel_frac) * msmd.nchan(spw_id)))}")
    spw_skip_edge = ','.join(chan_spw_skip_edge_map)

    chan_spw_central_map = np.empty(nspw, dtype=object)
    for spw_id in range(nspw):
        chan_spw_central_map[spw_id] = (f"{spw_id}:"
                                        f"{int(0.3 * msmd.nchan(spw_id))}~"
                                        f"{int(0.7 * msmd.nchan(spw_id))}")
    spw_central = ','.join(chan_spw_central_map)

    if compute_edge_for_flagging:
        chan_spw_edge_flag = np.empty(nspw, dtype=object)
        for spw_id in range(nspw):
            chan_spw_edge_flag[spw_id] = \
                (f"{spw_id}:0~{int(edge_channel_flag_frac * msmd.nchan(spw_id))},"
                 f"{spw_id}:{int((1 - edge_channel_flag_frac) * msmd.nchan(spw_id))}~"
                 f"{msmd.nchan(spw_id) - 1}")
        chan_spw_edge_flag = ','.join(chan_spw_edge_flag)
    msmd.done()
    if compute_edge_for_flagging:
        return (spw_skip_edge, spw_central, chan_spw_edge_flag)
    else:
        return (spw_skip_edge, spw_central)


def bandpass_cal(i=1, do_plots=False, overwrite=False):
    if do_plots:
        check_bandpass_plots(ref_antenna_list=ref_antenna_list,
                             field=bandpass_calibrator, spws=None)

    spw_skip_edge, spw_central = get_chan_spws_map(vis=vis_for_cal)

    if os.path.exists(vis + '.flagversions/flags.before_bandpass_init_' + str(i) + '/'):
        logging.info(f"Restoring flags from {vis}.flagversions/flags.before_bandpass_init_{i}/")
        flagmanager(vis=vis, mode='restore', versionname='before_bandpass_init_' + str(i))

    # COMPUTE THE DELAY FOR THE BANDPASS CALIBRATOR
    gain_tables_BP_dict = {}
    table_stage_bpcal_d = '_bpcal_d_'
    """
    Each call of run_gaincal will take previous tables (e.g. init_tables) 
    compute the requested table (e.g. delay) and return the new list of tables -- 
    gaintables_temp_K --  i.e. the generated table appended to init_tables.
    """
    gaintables_temp_K = run_gaincal(vis=vis_for_cal,
                                    field=bandpass_calibrator,
                                    gaintables=init_tables,
                                    scan='', refant=ref_antenna,
                                    spw=spw_skip_edge,
                                    calmode='p', gaintype='K',
                                    solint=bp_solint_K, overwrite=overwrite,
                                    i=i, table_stage=table_stage_bpcal_d,
                                    minsnr=minsnr
                                    )

    gain_tables_BP_dict['bp_K'] = gaintables_temp_K[-1]

    calibration_table_plot(table=gain_tables_BP_dict['bp_K'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_d + bp_solint_K,
                           kind='', xaxis='ant1', yaxis='delay', fields='')

    calibration_table_plot(table=gain_tables_BP_dict['bp_K'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_d + bp_solint_K,
                           kind='', xaxis='time', yaxis='delay', fields='')

    # USING THE DELAY TABLE; COMPUTE THE PHASE FOR THE BANDPASS CALIBRATOR WITH A SHORT SOLINT
    table_stage_bpcal_p = '_bpcal_p_'
    gaintables_temp_bpcal_p = run_gaincal(vis=vis_for_cal,
                                          field=bandpass_calibrator,
                                          gaintables=gaintables_temp_K,
                                          scan='', refant=ref_antenna,
                                          spw=spw_central, calmode='p', gaintype='G',
                                          solint=bp_solint_G_p, overwrite=overwrite,
                                          i=i, table_stage=table_stage_bpcal_p,
                                          minsnr=minsnr
                                          )
    gain_tables_BP_dict['bp_p'] = gaintables_temp_bpcal_p[-1]

    # calibration_table_plot(table=gain_tables_BP_dict['bp_p'],
    #                        stage='calibration',
    #                        table_type=str(i) + table_stage_bpcal_p + bp_solint_G_p,
    #                        kind='', xaxis='freq', yaxis='phase', fields='')
    calibration_table_plot(table=gain_tables_BP_dict['bp_p'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_p + bp_solint_G_p,
                           kind='', xaxis='time', yaxis='phase', fields='')

    # Plot the phase gains for individual antennas.
    # for k in range(len(ref_antenna_list)):
    #     calibration_table_plot(table=gain_tables_dict['bp_p'],
    #                            stage='calibration', antenna=f"{ref_antenna_list[k]}",
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='time', yaxis='phase', fields='')

    # USING THE PREVIOUS DELAY AND SHORTER PHASES, COMPUTE THE AMPLITUDE GAINS FOR THE BANDPASS CALIBRATOR
    # THIS RUN IS DONE WITH A SHORTER SOLINT
    table_stage_bpcal_ap = '_bpcal_ap_'
    gaintables_temp_bpcal_ap = run_gaincal(vis=vis_for_cal,
                                           field=bandpass_calibrator,
                                           gaintables=gaintables_temp_bpcal_p,
                                           scan='', refant=ref_antenna,
                                           spw=spw_central, calmode='ap', gaintype='G',
                                           solint=bp_solint_G_ap, overwrite=overwrite,
                                           i=i, table_stage=table_stage_bpcal_ap,
                                           minsnr=minsnr
                                           )
    gain_tables_BP_dict['bp_ap'] = gaintables_temp_bpcal_ap[-1]

    calibration_table_plot(table=gain_tables_BP_dict['bp_ap'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_ap + bp_solint_G_ap,
                           kind='', xaxis='time', yaxis='phase', fields='')

    calibration_table_plot(table=gain_tables_BP_dict['bp_ap'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_ap + bp_solint_G_ap,
                           kind='', xaxis='time', yaxis='amp', fields='')

    # USING THE PREVIOUS DELAY AND SHORTER PHASES, COMPUTE THE AMPLITUDE GAINS FOR THE BANDPASS CALIBRATOR
    # NOW, WITH AN INF SOLINT FOR THE AMPLITUDE GAINS.
    table_stage_bpcal_ap_inf = '_bpcal_ap_inf_'
    bp_solint_G_ap_inf = 'inf'
    gaintables_temp_bpcal_ap_inf = run_gaincal(vis=vis_for_cal,
                                               field=bandpass_calibrator,
                                               gaintables=gaintables_temp_bpcal_p,
                                               scan='', refant=ref_antenna,
                                               combine='scan',
                                               spw=spw_central, calmode='ap', gaintype='G',
                                               solint=bp_solint_G_ap_inf, overwrite=overwrite,
                                               i=i, table_stage=table_stage_bpcal_ap_inf,
                                               minsnr=minsnr
                                               )
    gain_tables_BP_dict['bp_ap_inf'] = gaintables_temp_bpcal_ap_inf[-1]

    calibration_table_plot(table=gain_tables_BP_dict['bp_ap_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_ap_inf + bp_solint_G_ap_inf,
                           kind='', xaxis='time', yaxis='phase', fields='')

    calibration_table_plot(table=gain_tables_BP_dict['bp_ap_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_ap_inf + bp_solint_G_ap_inf,
                           kind='', xaxis='time', yaxis='amp', fields='')

    # NOW WE PROCEDD TO THE BANDPASS. WE CAN APPROACH IN TWO DIFFERENT WAYS:
    # 1. COMPUTE BANDPASS USING DELAYS AND SHORT PHASES [K > P]
    # 2. COMPUTE BANDPASS USING DELAYS, SHORT PHASES AND AMPLITUDES [K > P > AP]:
    #   2.1 USING SHORT AMPLITUDES [K > P > AP_SHORT]
    #   2.2 USING INF AMPLITUDES [K > P > AP_INF]
    table_stage_bpcal_BP_ap_inf = '_bpcal_BP_ap_inf'
    gaintables_temp_bpcal_BP_ap_inf = run_bandpass(vis=vis_for_cal,
                                                   field=bandpass_calibrator,
                                                   gaintables=gaintables_temp_bpcal_ap_inf,
                                                   combine='scan', bandtype='B',
                                                   scan='', refant=ref_antenna,
                                                   spw='*', overwrite=overwrite,
                                                   solint=bp_solint_BP, solnorm=False,
                                                   i=i, table_stage=table_stage_bpcal_BP_ap_inf,
                                                   minsnr=minsnr
                                                   )

    gain_tables_BP_dict['bp_BP_ap_inf'] = gaintables_temp_bpcal_BP_ap_inf[-1]

    calibration_table_plot(table=gain_tables_BP_dict['bp_BP_ap_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_BP_ap_inf + bp_solint_BP,
                           kind='', xaxis='chan', yaxis='phase', fields='')

    calibration_table_plot(table=gain_tables_BP_dict['bp_BP_ap_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_BP_ap_inf + bp_solint_BP,
                           kind='', xaxis='freq', yaxis='phase', fields='')

    calibration_table_plot(table=gain_tables_BP_dict['bp_BP_ap_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_BP_ap_inf + bp_solint_BP,
                           kind='', xaxis='chan', yaxis='amp', fields='')

    calibration_table_plot(table=gain_tables_BP_dict['bp_BP_ap_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_BP_ap_inf + bp_solint_BP,
                           kind='', xaxis='freq', yaxis='amp', fields='')

    table_stage_bpcal_BP_ap_short = '_bpcal_BP_ap_short'
    gaintables_temp_bpcal_BP_ap_short = run_bandpass(vis=vis_for_cal,
                                                     field=bandpass_calibrator,
                                                     gaintables=gaintables_temp_bpcal_ap,
                                                     combine='scan', bandtype='B',
                                                     scan='', refant=ref_antenna,
                                                     spw='*', overwrite=overwrite,
                                                     solint=bp_solint_BP, solnorm=False,
                                                     i=i, table_stage=table_stage_bpcal_BP_ap_short,
                                                     minsnr=minsnr
                                                     )

    gain_tables_BP_dict['bp_BP_ap_short'] = gaintables_temp_bpcal_BP_ap_short[-1]

    calibration_table_plot(table=gain_tables_BP_dict['bp_BP_ap_short'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_BP_ap_short + bp_solint_BP,
                           kind='', xaxis='chan', yaxis='phase', fields='')

    calibration_table_plot(table=gain_tables_BP_dict['bp_BP_ap_short'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_BP_ap_short + bp_solint_BP,
                           kind='', xaxis='freq', yaxis='phase', fields='')

    calibration_table_plot(table=gain_tables_BP_dict['bp_BP_ap_short'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_BP_ap_short + bp_solint_BP,
                           kind='', xaxis='chan', yaxis='amp', fields='')

    calibration_table_plot(table=gain_tables_BP_dict['bp_BP_ap_short'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_BP_ap_short + bp_solint_BP,
                           kind='', xaxis='freq', yaxis='amp', fields='')

    table_stage_bpcal_BP = '_bpcal_BP_'
    gaintables_temp_bpcal_BP = run_bandpass(vis=vis_for_cal,
                                            field=bandpass_calibrator,
                                            gaintables=gaintables_temp_bpcal_p,
                                            combine='scan', bandtype='B',
                                            scan='', refant=ref_antenna,
                                            spw='*', overwrite=overwrite,
                                            solint=bp_solint_BP, solnorm=False,
                                            i=i, table_stage=table_stage_bpcal_BP,
                                            minsnr=minsnr
                                            )

    gain_tables_BP_dict['bp_BP'] = gaintables_temp_bpcal_BP[-1]

    calibration_table_plot(table=gain_tables_BP_dict['bp_BP'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_BP + bp_solint_BP,
                           kind='', xaxis='chan', yaxis='phase', fields='')

    calibration_table_plot(table=gain_tables_BP_dict['bp_BP'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_BP + bp_solint_BP,
                           kind='', xaxis='freq', yaxis='phase', fields='')

    calibration_table_plot(table=gain_tables_BP_dict['bp_BP'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_BP + bp_solint_BP,
                           kind='', xaxis='chan', yaxis='amp', fields='')

    calibration_table_plot(table=gain_tables_BP_dict['bp_BP'],
                           stage='calibration',
                           table_type=str(i) + table_stage_bpcal_BP + bp_solint_BP,
                           kind='', xaxis='freq', yaxis='amp', fields='')

    logging.info(f"Consolidating tables for bandpass cal apply.")
    """
    There are different ways that we can use the previous tables to apply the bandpass calibrator. 
    - 
    """

    # tables_to_apply = ['bp_K','bp_p','bp_ap','bp_BP_ap_short']
    # pre_cal_tables_temp = []
    # for BPtable in tables_to_apply:
    #     pre_cal_tables_temp.append(gain_tables_BP_dict[BPtable])

    # IF ENOUGH SNR, THIS IS BETTER THAN THE OTHER TWO OPTIONS BELOW.
    pre_cal_tables_temp = [gain_tables_BP_dict['bp_K'],
                           gain_tables_BP_dict['bp_p'],
                           gain_tables_BP_dict['bp_ap'],
                           # gain_tables_BP_dict['bp_BP_ap_short'],
                           gain_tables_BP_dict['bp_BP_ap_inf']
                           ]

    # pre_cal_tables_temp = [gain_tables_BP_dict['bp_K'],
    #                        gain_tables_BP_dict['bp_p'],
    #                        gain_tables_BP_dict['bp_ap'],
    #                        # gain_tables_BP_dict['bp_BP_ap_short'],
    #                        gain_tables_BP_dict['bp_BP_ap_inf']
    #                        ]

    # pre_cal_tables_temp = [gain_tables_BP_dict['bp_K'],
    #                        gain_tables_BP_dict['bp_p'],
    #                        gain_tables_BP_dict['bp_BP']
    #                        ]

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

    # flagmanager(vis=vis_for_cal, mode='restore', versionname='before_bandpass_init_1')

    logging.info(f"Creating flag-backup before applying initial bandpass.")
    flagmanager(vis=vis_for_cal, mode='save',
                versionname='before_bandpass_init_' + str(i),
                comment='Flags before apply bandpass init, iteraction' + str(i) + '.')

    logging.info('     ++==>> Reporting flags before applycal to bandpass.')
    summary_before_applycal_to_bandpass = flagdata(vis=vis_for_cal,
                                                   mode='summary',
                                                   field=bandpass_calibrator)
    report_flag(summary_before_applycal_to_bandpass, 'field')

    logging.info(f"Applying bandpass solutions to bandpass calibrator {bandpass_calibrator}.")
    applycal(vis=vis_for_cal, field=bandpass_calibrator,
             gaintable=gaintables_apply_BP,
             gainfield=gainfield_bandpass_apply,
             applymode=bp_applymode,
             calwt=False, flagbackup=False)

    logging.info('     ++==>> Reporting flags after applycal to bandpass.')
    summary_after_applycal_to_bandpass = flagdata(vis=vis_for_cal, mode='summary',
                                                  field=bandpass_calibrator)
    report_flag(summary_after_applycal_to_bandpass, 'field')

    make_plots_stages(vis=vis_for_cal, stage='after', kind=f"after_bandpass_apply_iter_{i}",
                      FIELDS=bandpass_calibrator.split(','))

    return (gaintables_apply_BP, gainfield_bandpass_apply,
            gain_tables_BP_dict, gaintables_apply_BP_dict, gainfields_apply_BP_dict)


def cal_phases_amplitudes(gaintables_apply_BP, gainfield_bandpass_apply, i=1, overwrite=False):
    spw_skip_edge, spw_central = get_chan_spws_map(vis=vis_for_cal)

    gain_tables_phases_dict = {}

    """
    First, lets compute the short phases for all complex calibrators.
    """
    table_stage_all_p_short = '_allcal_p_short_'
    gaintables_temp_calibrators_p_short = run_gaincal(vis=vis_for_cal,
                                                      field=calibrators_all,
                                                      gaintables=gaintables_apply_BP,
                                                      scan='', refant=ref_antenna,
                                                      spw=spw_central,
                                                      calmode='p', gaintype='G',
                                                      solint=all_solint_short_p,
                                                      overwrite=overwrite,
                                                      i=i, table_stage=table_stage_all_p_short,
                                                      minsnr=minsnr
                                                      )

    gain_tables_phases_dict['allcals_p_short'] = gaintables_temp_calibrators_p_short[-1]

    calibration_table_plot(table=gain_tables_phases_dict['allcals_p_short'],
                           stage='calibration',
                           table_type=str(i) + table_stage_all_p_short + all_solint_short_p,
                           kind='', xaxis='time', yaxis='phase', fields='')

    """
    We should also compute longer phase solution for all calibrators. 
    Usually, these longer phase solutions will be the ones transferred to the science sources. 
    """
    table_stage_all_p_inf = '_allcal_p_inf_'
    gaintables_temp_calibrators_p_inf = run_gaincal(vis=vis_for_cal,
                                                    field=calibrators_all, combine='',
                                                    gaintables=gaintables_apply_BP,
                                                    scan='', refant=ref_antenna,
                                                    spw=spw_central,
                                                    calmode='p', gaintype='G',
                                                    solint=all_solint_long_p, overwrite=overwrite,
                                                    i=i, table_stage=table_stage_all_p_inf,
                                                    minsnr=minsnr
                                                    )

    gain_tables_phases_dict['allcals_p_inf'] = gaintables_temp_calibrators_p_inf[-1]

    calibration_table_plot(table=gain_tables_phases_dict['allcals_p_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage_all_p_inf + all_solint_long_p,
                           kind='', xaxis='time', yaxis='phase', fields='')

    """
    We compute now the amplitude solutions for the complex calibrators.
    This one uses a short solution interval (but should not be smaller than 32s). 
    Note that this uses the previous shorter phase solutions.
    """
    table_stage_all_ap_short = '_allcal_ap_short_'
    gaintables_temp_calibrators_amp_short = run_gaincal(vis=vis_for_cal,
                                                        field=calibrators_all,
                                                        gaintables=gaintables_temp_calibrators_p_short,
                                                        scan='', refant=ref_antenna,
                                                        spw=spw_central, calmode='ap', gaintype='G',
                                                        solint=all_solint_short_ap,
                                                        i=i, table_stage=table_stage_all_ap_short,
                                                        minsnr=minsnr
                                                        )
    gain_tables_phases_dict['allcals_ap_short'] = gaintables_temp_calibrators_amp_short[-1]

    calibration_table_plot(table=gain_tables_phases_dict['allcals_ap_short'],
                           stage='calibration',
                           table_type=str(i) + table_stage_all_ap_short + all_solint_short_ap,
                           kind='', xaxis='time', yaxis='phase', fields='')
    calibration_table_plot(table=gain_tables_phases_dict['allcals_ap_short'],
                           stage='calibration',
                           table_type=str(i) + table_stage_all_ap_short + all_solint_short_ap,
                           kind='', xaxis='time', yaxis='amp', fields='')

    ##CONTINUE HEREEEEEE

    """
    We compute now the amplitude solutions for the complex calibrators, but using 
    an infinite solution interval. 
    Note that this still uses the previous shorter phase solutions.
    """
    table_stage_allcal_ap_inf = '_allcal_ap_inf_'
    gaintables_temp_calibrators_amp_inf = run_gaincal(vis=vis_for_cal,
                                                      field=calibrators_all,
                                                      gaintables=gaintables_temp_calibrators_p_short,
                                                      scan='', refant=ref_antenna,
                                                      spw=spw_central, calmode='ap', gaintype='G',
                                                      solint=all_solint_inf_ap,
                                                      i=i, table_stage=table_stage_allcal_ap_inf,
                                                      minsnr=minsnr
                                                      )
    gain_tables_phases_dict['allcals_ap_inf'] = gaintables_temp_calibrators_amp_inf[-1]

    calibration_table_plot(table=gain_tables_phases_dict['allcals_ap_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage_allcal_ap_inf + all_solint_inf_ap,
                           kind='', xaxis='time', yaxis='phase', fields='')
    calibration_table_plot(table=gain_tables_phases_dict['allcals_ap_inf'],
                           stage='calibration',
                           table_type=str(i) + table_stage_allcal_ap_inf + all_solint_inf_ap,
                           kind='', xaxis='time', yaxis='amp', fields='')

    ## Flux Scale

    """
    We now apply the flux scale on the amplitude gains with the longer solution intervals. 
    """
    try:
        fluxtable_short = gain_tables_phases_dict['allcals_ap_short'].replace('.tb','_flux_scale.tb')
        listfluxfile_short = fluxtable_short.replace('.tb', '_fluxinfo.txt')

        fluxtable = gain_tables_phases_dict['allcals_ap_inf'].replace('.tb', '_flux_scale.tb')
        listfluxfile = fluxtable.replace('.tb', '_fluxinfo.txt')

        flux_bp_short = fluxscale(vis=vis_for_cal,
                            caltable=gain_tables_phases_dict['allcals_ap_short'],
                            fluxtable=fluxtable_short, reference=flux_calibrator,
                            transfer=calibrators_all, incremental=True,
                            listfile=listfluxfile_short, fitorder=1)

        flux_bp = fluxscale(vis=vis_for_cal,
                            caltable=gain_tables_phases_dict['allcals_ap_inf'],
                            fluxtable=fluxtable, reference=flux_calibrator,
                            transfer=calibrators_all, incremental=True,
                            listfile=listfluxfile, fitorder=1)
        """
        The following lines are commented out as an example of a workaround when fluxscale 
        fails for observations with duplicated fields, where one is completely flagged.
        This can happen in early EVLA observations (~2010-2012).
        Manually set the correct field ID for the flux calibrator and the valid (unflagged, 
        with solutions) field IDs for the phase calibrators.
        """
        # flux_bp_short = fluxscale(vis=vis_for_cal,
        #                           caltable=gain_tables_phases_dict['allcals_ap_short'],
        #                           fluxtable=fluxtable_short,
        #                           transfer='0,1,3,5,7,9,11,13,15,17,19,21,23,25', reference='0',
        #                           incremental=True, display=True,
        #                           listfile=listfluxfile_short, fitorder=1)

        # flux_bp = fluxscale(vis=vis_for_cal,
        #                     caltable=gain_tables_phases_dict['allcals_ap_inf'],
        #                     fluxtable=fluxtable,
        #                     transfer='0,1,3,5,7,9,11,13,15,17,19,21,23,25', reference='0',
        #                     incremental=True, display=True,
        #                     listfile=listfluxfile, fitorder=1)
    except:
        print('WARNING: Fluxscale tables were not generated!')
        pass

    # allcals_ap_inf

    if os.path.exists(fluxtable):
        """
        If fluxscale fails (e.g. older observations), the table fluxtable will not be created.
        """
        #
        gain_tables_phases_dict['allcals_ap_fluxscale'] = fluxtable
        gain_tables_phases_dict['allcals_ap_fluxscale_short'] = fluxtable_short

        flux_phase_cals_scaled = setjy(vis=vis_for_cal, field=calibrators_all,
                                       scalebychan=True, standard='fluxscale',
                                       fluxdict=flux_bp)

        calibration_table_plot(table=fluxtable_short,
                               stage='calibration',
                               table_type=str(
                                   i) + table_stage_all_ap_short + all_solint_short_ap + '_flux_scale',
                               kind='', xaxis='time', yaxis='phase', fields='')
        calibration_table_plot(table=fluxtable_short,
                               stage='calibration',
                               table_type=str(
                                   i) + table_stage_all_ap_short + all_solint_short_ap + '_flux_scale',
                               kind='', xaxis='time', yaxis='amp', fields='')

        calibration_table_plot(table=fluxtable,
                               stage='calibration',
                               table_type=str(
                                   i) + table_stage_allcal_ap_inf + all_solint_inf_ap + '_flux_scale',
                               kind='', xaxis='time', yaxis='phase', fields='')
        calibration_table_plot(table=fluxtable,
                               stage='calibration',
                               table_type=str(
                                   i) + table_stage_allcal_ap_inf + all_solint_inf_ap + '_flux_scale',
                               kind='', xaxis='time', yaxis='amp', fields='')

        msmd.open(vis_for_cal)
        bandwidth = msmd.bandwidths()
        nspw = len(bandwidth)

        chan_freqs_all = np.empty(nspw, dtype=object)
        spws_freq = np.zeros(nspw)

        for nch in range(nspw):
            chan_freqs_all[nch] = msmd.chanfreqs(nch)
            spws_freq[nch] = np.mean(chan_freqs_all[nch])

        msmd.done()

        plots_dir = os.path.join(working_directory).rstrip('/') + '/' + 'plots'
        try:
            spws_phasecals = {}
            fluxes_phasecals = {}
            for kk in range(len(phase_calibrator.split(','))):
                spws_phasecals[f"{kk}"] = []
                fluxes_phasecals[f"{kk}"] = []
                for spw_id in range(nspw):
                    spws_phasecals[f"{kk}"].append(spw_id)
                    fluxes_phasecals[f"{kk}"].append(
                        flux_phase_cals_scaled[f"{kk + 1}"][str(spw_id)]['fluxd'][0])

            logging.info(f"Plotting the bootstrap fluxes against frequency.")
            plt.figure(figsize=(8, 5))
            for kk in range(len(phase_calibrator.split(','))):
                plt.plot(spws_freq * 1e-9, fluxes_phasecals[f"{kk}"], 'o', color='black',
                         label=f"{phase_calibrator.split(',')[kk]}")

            plt.xlabel('Frequency [GHz]')
            plt.ylabel(f"'Flux Density [Jy]")
            plt.grid()
            plt.legend()
            plt.title('Flux Density Bootstrap For Phase Calibrators from Fluxscale')
            plt.semilogx()
            plt.semilogy()
            flux_plot = os.path.join(plots_dir, 'phasecals_flux_density_bootstrap.pdf')
            plt.savefig(flux_plot, dpi=600, bbox_inches='tight')
            plt.clf()
            plt.close()
        except Exception as e:
            logging.warning(f"Flux plot not generated due to: {e}")

        # gaintables_temp_calibrators_amp_fluxscale = gaintables_temp_calibrators_amp_short.copy()
        gaintables_temp_calibrators_amp_fluxscale = gaintables_temp_calibrators_amp_inf.copy()
        gaintables_temp_calibrators_amp_fluxscale.append(fluxtable)

        gain_tables_ampphase_for_all_cals = [gain_tables_phases_dict['allcals_p_short'],
                                             gain_tables_phases_dict['allcals_ap_short'],
                                             # care with this one
                                             # gain_tables_phases_dict['allcals_ap_inf'],
                                             gain_tables_phases_dict['allcals_ap_fluxscale']
                                             ]

        gain_tables_ampphase_for_science = [gain_tables_phases_dict['allcals_p_inf'],
                                            gain_tables_phases_dict['allcals_ap_inf'],
                                            gain_tables_phases_dict['allcals_ap_fluxscale']
                                            ]

        # gain_tables_ampphase = [gaintables_temp_calibrators_amp[-2],
        #                         gaintables_temp_calibrators_amp[-1], fluxtable]
        flag_FLUX_SCALE = False

    else:
        logging.warning(f"No fluxscale table generated.")
        gaintables_temp_calibrators_amp_fluxscale = gaintables_temp_calibrators_amp_short.copy()
        # gaintables_temp_calibrators_amp_fluxscale.append(fluxtable)
        gain_tables_ampphase_for_all_cals = [gain_tables_phases_dict['allcals_p_short'],
                                             gain_tables_phases_dict['allcals_ap_inf']
                                             ]

        gain_tables_ampphase_for_science = [gain_tables_phases_dict['allcals_p_inf'],
                                            gain_tables_phases_dict['allcals_ap_inf']
                                            ]

        flux_phase_cals_scaled = None
        flag_FLUX_SCALE = True

    logging.info(f"Creating flag-backup before applycal to calibrators iteration {i}")
    flagmanager(vis=vis_for_cal, mode='save', versionname='before_applycal_' + str(i),
                comment='Flags before applycal, iteraction' + str(i) + '.')

    logging.info(f"Reporting flags before applycal to calibrators iteration {i}")
    summary_before_applycal_to_calibrators = flagdata(vis=vis_for_cal, mode='summary',
                                                      field=calibrators_all)
    report_flag(summary_before_applycal_to_calibrators, 'field')

    """
    Aggregating the tables and fields for the applycal to the calibrators. These contain shorter
    phase and amplitude solutions.
    """
    gain_tables_to_apply_all_cals = gaintables_apply_BP.copy()
    gain_tables_to_apply_all_cals.extend(gain_tables_ampphase_for_all_cals)
    """
    Aggregating the tables for the applycal to the science sources. These contain longer or inf 
    phase and amplitude solutions.
    """
    gain_tables_to_apply_science = gaintables_apply_BP.copy()
    gain_tables_to_apply_science.extend(gain_tables_ampphase_for_science)

    """
    This needs a fix when a phase calibrator is used for multiple science sources. 
    We need to track properly the gainfields. 
    """
    for calibrator_field in calibrators_all_arr:
        ext_cal_fields = [calibrator_field] * len(gain_tables_ampphase_for_all_cals)
        gainfield_to_apply_all_cals = gainfield_bandpass_apply.copy()
        gainfield_to_apply_all_cals.extend(ext_cal_fields)

        logging.info(f"Appplying calibration to: {calibrator_field}")
        logging.info(f"     => Gainfields are: {gainfield_to_apply_all_cals}")
        logging.info(f"     => Gaintables are: {gain_tables_to_apply_all_cals}")
        applycal(vis=vis_for_cal,
                 field=calibrator_field,
                 applymode=ph_ap_applymode,
                 gaintable=gain_tables_to_apply_all_cals, flagbackup=False,
                 gainfield=gainfield_to_apply_all_cals, calwt=False)

    logging.info(f"Reporting flags after applycal to calibrators iteration {i}")
    summary_after_applycal_to_calibrators = flagdata(vis=vis_for_cal, mode='summary',
                                                     field=calibrators_all)
    report_flag(summary_after_applycal_to_calibrators, 'field')

    make_plots_stages(vis=vis_for_cal, stage='after', kind=f"after_allcals_apply_iter_{i}",
                      FIELDS=calibrators_all.split(','))

    """
    We need to return the tables 
    """
    return (
        gain_tables_phases_dict,
        gain_tables_ampphase_for_science, gain_tables_to_apply_science,
        flag_FLUX_SCALE)


def apply_cal_to_science(vis, gain_tables_to_apply_science_final,
                         gainfield_bandpass_apply_final,
                         gain_tables_ampphase_for_science_final):
    logging.info("Applying calibration to science source(s).")
    # logging.info("Aggregating gaintables  and gainfields.")

    if not os.path.exists(vis + '.flagversions/flags.before_applycal_science/'):
        logging.info(f"Creating flag-backup before applycal to science sources.")
        flagmanager(vis=vis, mode='save', versionname='before_applycal_science',
                    comment='Flags before applycal to science sources.')
    else:
        logging.info(f"Flag-backup before applycal to science sources already exists.")
        flagmanager(vis=vis, mode='restore', versionname='before_applycal_science')

    logging.info("     => Reporting data flagged before applycal.")
    summary_cal_before = flagdata(vis=vis,
                                  mode='summary', field='', datacolumn='data')
    report_flag(summary_cal_before, 'field')

    for n in range(len(target_fields_arr)):
        # gainfields_final = (gainfield_bandpass_apply_final +
        #                     [phase_calibrator.split(',')[n]] * len(
        #             gain_tables_ampphase_for_science_final))
        gainfields_final = (gainfield_bandpass_apply_final +
                            ['nearest'] * len(
                    gain_tables_ampphase_for_science_final))
        logging.info(f"Applying calibration to: {target_fields_arr[n]}")
        logging.info(f"Gaintables: {gain_tables_to_apply_science_final}")
        logging.info(f"Gainfields: {gainfields_final}")
        applycal(vis=vis,
                 field=target_fields_arr[n],
                 gaintable=gain_tables_to_apply_science_final,
                 flagbackup=False,
                 gainfield=gainfields_final, calwt=False)

    print('     => Reporting data flagged after applycal.')
    summary_cal_after = flagdata(vis=vis,
                                 mode='summary', field='', datacolumn='data')
    report_flag(summary_cal_after, 'field')

    make_plots_stages(vis=vis,
                      stage='after',
                      kind='after_calibration',
                      FIELDS=target_fields_arr)

    pass
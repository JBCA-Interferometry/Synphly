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

    try:
        logging.info("Clearing model column")
        casatasks.delmod(vis, otf=True, scr=False)
        logging.info("Successfully deleted model column")
    except Exception as e:
        logging.critical(f"Exception {e} while deleting model column")

    try:
        logging.info("Re-initialize the calibration")
        casatasks.clearcal(vis)
        logging.info("Successfully cleared the calibration")
    except Exception as e:
        logging.critical(f"Exception {e} while clearing calibrations")

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

    mean_freq = np.mean(np.mean(chan_freqs_all[0]))*1e-9

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

    for range_,band in freq_ranges.items():
        if mean_freq>=range_[0] and mean_freq<=range_[1]:
            logging.info(f"Observations done in band: {band}")
            logging.info(f"Will use model {model} for absolute flux calibration")
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





def get_chan_spws_map(vis):
    msmd = casatools.msmetadata()
    msmd.open(vis)
    bandwidth = msmd.bandwidths()
    nspw = len(bandwidth)

    chan_spw_skip_edge_map = np.empty(nspw, dtype=object)
    for spw_id in range(nspw):
        chan_spw_skip_edge_map[spw_id] = f"{spw_id}:{int(edge_channel_frac*msmd.nchan(spw_id))}~{int(((1-edge_channel_frac)*msmd.nchan(spw_id)))}"
    spw_skip_edge = ','.join(chan_spw_skip_edge_map)

    chan_spw_central_map = np.empty(nspw, dtype=object)
    for spw_id in range(nspw):
        chan_spw_central_map[spw_id] = (f"{spw_id}:"
                                        f"{int(0.3*msmd.nchan(spw_id))}~{int(0.7*msmd.nchan(spw_id))}")
    spw_central = ','.join(chan_spw_central_map)
    msmd.done()
    return(spw_skip_edge,spw_central)
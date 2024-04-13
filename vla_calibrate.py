def initial_corrections():
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
    
    try:
        logging.info("Generating cal solutions for antenna positions")
        caltable = vis.replace('.ms','_antpos.tb')
        os.system(f"rm -r {caltable}")
        casatasks.gencal(vis=vis,caltable=caltable, caltype='antpos')
        init_tables.append(caltable)
    except Exception as e:
        logging.critical(f"Exception {e} while generating {caltable}")

    # gain curves
    # try:
    #     logging.info("Generating cal solutions for gaincurves")
    #     caltable = vis.replace('.ms','_gaincurve.tb')
    #     os.system(f"rm -r {caltable}")
    #     casatasks.gencal(vis=vis,caltable=caltable, caltype='gc')
    #     init_tables.append(caltable)
    # except Exception as e:
    #     logging.critical(f"Exception {e} while generating {caltable}")



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
        os.system(f"rm -r {weather_plot}")
        myTau = casatasks.plotweather(vis=vis, seasonal_weight=0.5, doPlot=True, plotName=weather_plot)
        os.system(f'mv {weather_plot} {plots_dir}')
        try:
            caltable = vis.replace('.ms','_opacity.tb')
            logging.info(f"Generating weather caltable {caltable}")
            # fix the spw here
            casatasks.gencal(vis=vis,caltable=caltable,caltype='opac', spw=all_spw, parameter=myTau) 
            init_tables.append(caltable)
        except Exception as e:
            logging.critical(f"Exception {e} while generating cal for opacity")      
    except Exception as e:
        logging.critical(f"Exception {e} while running plotweather")


    # requantisation corrections

    try:
        logging.info("Generating cal solutions for rq")
        caltable = vis.replace('.ms','_rq.tb')
        os.system(f"rm -r {caltable}")
        casatasks.gencal(vis=vis,caltable=caltable, caltype='rq')
        init_tables.append(caltable)
    except Exception as e:
        logging.critical(f"Exception {e} while generating {caltable}")

    #  switched power

    try:
        logging.info("Generating cal solutions for spwpow")
        caltable = vis.replace('.ms','_spwpow.tb')
        os.system(f"rm -r {caltable}")
        casatasks.gencal(vis=vis,caltable=caltable, caltype='swpow')
        init_tables.append(caltable)
    except Exception as e:
        logging.critical(f"Exception {e} while generating {caltable}")



    initial_corrections_endtime = time.time() 
    initial_corrections_time = initial_corrections_endtime- initial_corrections_starttime
    logging.info(f"Initial calibrations took {initial_corrections_time/ 60:.2f} minutes")
    
def flux_scale_setjy():

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
    spw = 0
    spw0_freq = msmd.chanfreqs(0)*1e-9
    
    model = "3C286" 
    freq_ranges = {
        (4, 8): "C",
        (8, 12): "X",
        (12, 18): "Ku",
        (18,26.5):"K",
            }
    
    for range_,band in freq_ranges.items():
        if spw0_freq>=range_[0] and spw0_freq<=range_[1]:
            logging.info(f"Observations done in band: {band}")
            logging.info("Will use model {model} for absolute flux calibration")
            model = model+f'_{band}.im'
    try:
        logging.info(f"Performing absolute flux calibration using {model}")
        flux_density_data = casatasks.setjy(vis=vis, field=flux_calibrator, 
                                    spw='',model=model, scalebychan=True,
                                    standard='Perley-Butler 2017',listmodels=False, usescratch=True)
    except Exception as e:
        logging.critical(f"Exception {e} while running setjy")

    plots_dir = os.path.join(working_directory).rstrip('/')+'/'+ 'plots'
    spws = []
    fluxes = []
    for key in list(flux_density_data['0'].keys())[:-1]:
        spws.append(int(key))
        fluxes.append(flux_density_data['0'][key]['fluxd'][0])
    spws = np.asarray(spws)
    fluxes = np.asarray(fluxes)
    
    try:
        logging.info(f"Plotting the fluxes for each spw")
        plt.figure(figsize=(8, 5))
        plt.plot(spws, fluxes, 'o', color='black')
        plt.xlabel('SPWids')
        plt.ylabel(f"'Flux Density {flux_calibrator} [Jy]")
        plt.grid()
        plt.title('Flux density from setjy model')
        flux_plot = os.path.join(plots_dir,flux_calibrator+'_flux_density_model.pdf')
        plt.savefig(flux_plot, dpi=600)
        plt.clf()

    except Exception as e:
        logging.warning(f"Flux plot not generated due to: {e}")




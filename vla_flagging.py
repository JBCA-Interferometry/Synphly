def run_aoflagger_sif(vis):

    """
    Executes singularity containers from python

    """
    

    try:
        container = aoflagger_sif
        if os.path.exists(container):
            logging.info(f"Found {container}")
            singularity_bind = os.path.join(os.path.dirname(os.path.dirname(aoflagger_sif)))
            logging.info(f"You are binding singularity to {singularity_bind}")

    except FileNotFoundError:
        logging.critical(f"AOflagger singularity container not found")
 
    
    strategy = ['aoflagger', '-v', '-indirect-read', '-fields', '', '-strategy', aoflagger_strategy, vis]

    command_to_execute = ['singularity', 'exec', '-B', singularity_bind, container] + strategy
    try:
        logging.info("Executing: %s", ' '.join(command_to_execute))
        process = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate()
        logging.info("stdout: %s", stdout)
        logging.info("stderr: %s", stderr)

        return_code = process.returncode
        if return_code == 0:
            logging.info(f"Strategy executed successfully. Output:\n{stdout}")
        else:
            logging.critical(f"Error executing strategy. Return code: {return_code}\nError message: {stderr}")  

    except Exception as e:
        logging.critical(f"An error occurred: {e}")


def run_aoflagger_nat(vis):
    """
    Executes aoflagger in native mode (this is for debugging purposes only).

    """

    if report_verbosity >= 2:
        logging.info('Reporting data flagged before running aoflagger ...')
        summary_before_aoflagger = casatasks.flagdata(vis=vis, mode='summary')
        report_flag(summary_before_aoflagger, 'field')

    strategy = (['aoflagger', '-v', '-j','6', '-direct-read', '-fields', '', '-strategy',
                aoflagger_strategy,vis])

    command_to_execute =  strategy
    try:
        logging.info("Executing: %s", ' '.join(command_to_execute))
        process = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate()
        logging.info("stdout: %s", stdout)
        logging.info("stderr: %s", stderr)

        return_code = process.returncode
        if return_code == 0:
            logging.info(f"Strategy executed successfully. Output:\n{stdout}")
        else:
            logging.critical(
                f"Error executing strategy. Return code: {return_code}\nError message: {stderr}")

        if report_verbosity >= 2:
            logging.info('Reporting data flagged after running aoflagger ...')
            summary_after_aoflagger = casatasks.flagdata(vis=vis, mode='summary')
            report_flag(summary_after_aoflagger, 'field')

    except Exception as e:
        logging.critical(f"An error occurred: {e}")


def report_flag(summary, axis):
    logging.info("REPORTING FLAGGING STATS")
    try:
        for id, stats in summary[axis].items():
            logging.info('%s %s: %5.1f percent flagged' % (axis, id, 100. * stats['flagged'] / stats['total']))
    except Exception as e:
        logging.info(f"Exception {e} while reporting flags")
    

def run_rflag(i, field):
    logging.info("Running rflag")
    summary_before_apply_cal = casatasks.flagdata(vis=vis, mode='summary')
    report_flag(summary_before_apply_cal, 'field')
    # report_flag(summary_before_apply_cal,'antenna')
    # report_flag(summary_before_apply_cal,'spw')

    # if extended_flag_backups >= 1:
    #     try:
    #         logging.info('    ** Creating flag backup before rflag...')
    #         casatasks.flagmanager(vis=vis, mode='save', versionname='pre_calibration_before_rflag_iteraction_' + str(i),
    #                     comment='Flagbackup before rflag/pre-calibration iteration ' + str(i))
    #     except Exception as e:
    #         logging.error("")

    summary_before_rflag = casatasks.flagdata(vis=vis, mode='summary')
    report_flag(summary_before_rflag, 'field')
    # report_flag(summary_before_rflag,'antenna')
    # report_flag(summary_before_rflag,'spw')

    datacolumn_to_flag = 'corrected'
    
    try:
        logging.info(f"Flagging column {datacolumn_to_flag}")
        casatasks.flagdata(vis=vis, mode='rflag', field=field, spw='', display='report',
                datacolumn=datacolumn_to_flag, ntime='scan', combinescans=False,
                extendflags=False, winsize=7, timedevscale=3.0, freqdevscale=3.0,
                flagnearfreq=False, flagneartime=False, growaround=True,
                action='apply', flagbackup=False, savepars=True
                )

        casatasks.flagdata(vis=vis, field=field, spw='',
                datacolumn=datacolumn_to_flag,
                mode='extend', action='apply', display='report',
                flagbackup=False, growtime=75.0,
                growfreq=75.0, extendpols=False)
    except Exception as e:
        logging.error(f"Exception {e} occured while running casatasks.flagdata")
    # make_plots_stages(stage='after',kind='after_rflag',FIELDS=fields_test_plot)
    summary_after_rflag = casatasks.flagdata(vis=vis, mode='summary')
    report_flag(summary_after_rflag, 'field')

    # fast_check_cal(FIELDS=calibrators_all_arr,
    #     stage='after_rflag',type=solint)
    # report_flag(summary_after_rflag,'antenna')
    # report_flag(summary_after_rflag,'spw')
    #
    # if extended_flag_backups >= 1:
    #     print('    ** Saving flags backup after rflag...')
    #     casatasks.flagmanager(vis=vis, mode='save', versionname='pre_calibration_after_rflag_iteraction_' + str(i),
    #                 comment='Flagbackup after rflag/pre-calibration iteration ' + str(i))


def manual_flagging():
    
    logging.info(f'Flagging using user supplied flagging file {manual}')
    try:
        casatasks.flagdata(vis=vis, mode='list',inpfile=manual_file, flagbackup=False)
        versionname = 'manual_flagging_1'
        logging.info(f'Creating new flagbackup file version {manual_flagging_1}')
        casatasks.flagmanager(vis=vis, mode='save', versionname=versionname,
                    comment='First run of manual flagging.')
        if report_verbosity >= 1:
            summary_after_manual = casatasks.flagdata(vis=vis, mode='summary')
            report_flag(summary_after_manual, 'field')
            # report_flag(summary_after_manual,'scan')
            # report_flag(summary_after_manual,'antenna')
    except:
        logging.warning('Supply a manual flagging file')




def pre_flagging(vis):

    """
    Pre-flagging to the data.
    """
    flags_dir = os.path.join(working_directory).rstrip('/')+'/'+'flags'
    plots_dir = os.path.join(working_directory).rstrip('/')+'/'+ 'plots'

    pre_flagging_starttime = time.time()

    try:
        logging.info('Creating flagbackup file for original ms')
        casatasks.flagmanager(vis=vis, mode='save', versionname='original_flags_import',
                    comment='Original flags from import.')
    except Exception as e:
        logging.warning("Exception {e} when saving flags")

    logging.info('Starting pre-flagging to the data.')

    if report_verbosity >= 2:
        logging.info('Reporting data flagged at start ...')
        summary_0 = casatasks.flagdata(vis=vis, mode='summary')
        report_flag(summary_0, 'field')
        # report_flag(summary_0,'scan')
        # report_flag(summary_0,'antenna')

    casatasks.plotants(vis=vis, logpos=True, figfile=plots_dir.rstrip('/')+'/'+'_plotant_log.pdf')
    casatasks.plotants(vis=vis, logpos=False, figfile=plots_dir.rstrip('/')+'/'+'_plotant.pdf')

    # if report_verbosity >= 2:
    #     print('     ## Reporting data flagged after online flagging...')
    #     summary_online = casatasks.flagdata(vis=vis, mode='summary')
    #     report_flag(summary_online,'field')
    #     # report_flag(summary_online,'scan')
    #     # report_flag(summary_online,'antenna')

    try:
        logging.info('Flagging autocorrelations')
        casatasks.flagdata(vis=vis, mode='manual', autocorr=True,
                reason='autocorr', flagbackup=False, action='apply',
                name='autocorr')
    except Exception as e:
        logging.error(f"Exception {e} while flagging autocorrelations")

    if report_verbosity >= 2:
        logging.info('Reporting flagged data after autocorr flagging...')
        summary_autocorr = casatasks.flagdata(vis=vis, mode='summary')
        report_flag(summary_autocorr, 'field')
        # report_flag(summary_autocorr,'scan')
        # report_flag(summary_autocorr,'antenna')
    try:   
        logging.info('Shadow flagging the data')
        casatasks.flagdata(vis=vis, mode='shadow', reason='shadow', tolerance=0.0,
             flagbackup=False, name='shadow', action='apply')
    except Exception as e:
        logging.error(f"Exception {e} while shadow flagging")

    if report_verbosity >= 2:
        logging.info('Reporting data flagged after shadow flagging...')
        summary_2 = casatasks.flagdata(vis=vis, mode='summary')
        report_flag(summary_2, 'field')
        # report_flag(summary_2,'scan')

    # flag zeros data (flagm data with zero values/amplitudes)
    try:
        print('Clipping the data')
        casatasks.flagdata(vis=vis, mode='clip', correlation='ABS_ALL', clipzeros=True,
                reason='clip', flagbackup=False, action='apply', name='clip')
    except Exception as e:
        logging.error(f"Exception {e} while clipping")

    if report_verbosity >= 2:
        logging.info('Reporting data flagged after clipping')
        summary_4 = casatasks.flagdata(vis=vis, mode='summary')
        report_flag(summary_4, 'field')
        # report_flag(summary_4,'scan')

    # quack flagging (time to the telescope to go to the source)
    #  get scan length -- change the quack

    try:
        logging.info('Quacking the data')
        casatasks.flagdata(vis=vis, mode='quack', quackinterval=5.0, quackmode='beg',
                reason='quack', flagbackup=False, action='apply', name='quack')
    except Exception as e:
        logging.error(f"Exception {e} while quacking")

    if report_verbosity >= 2:
        logging.info('Reporting data flagged after quack flagging...')
        summary_5 = casatasks.flagdata(vis=vis, mode='summary')
        report_flag(summary_5, 'field')
        # report_flag(summary_5,'scan')

    try:
        logging.info('Creating new flagbackup file after pre-flagging.')
        casatasks.flagmanager(vis=vis, mode='save', versionname='pre_flagging',
                    comment='Pre-flags applied: Autocorr,clipping, quack, shadow.')
    except Exception as e:
        logging.error(f"Exception {e} encountered while backing up flags")

    # Further flagging (manual inspections)

    # if apply_tfcrop_init == True:
    #     print(' >> Performing tfcrop on raw data...')

    #     summary_before_tfcrop = casatasks.flagdata(vis=vis, mode='summary')
    #     if report_verbosity >= 1:
    #         print('     => Reporting flags before tfcrop')
    #         report_flag(summary_before_tfcrop, 'field')
    #         # report_flag(summary_before_tfcrop,'scan')
    #         # report_flag(summary_before_tfcrop,'antenna')
    #         # report_flag(summary_before_tfcrop,'spw')
    #     casatasks.flagmanager(vis=vis, mode='save', versionname='flags_before_tfcrop_init',
    #                 comment='Flags beforet tfcrop on raw flagged data')
    #     # casatasks.flagdata(vis=vis, mode='tfcrop',datacolumn='data',
    #     #     action='apply',display='',reason='tfcrop',
    #     #     name='tfcrop',flagbackup=False,outfile='tfcrop_flag')
    #     casatasks.flagdata(vis=vis, mode='tfcrop', field=calibrators_all, display='', spw='',
    #              datacolumn='data', ntime='scan', combinescans=False,
    #              extendflags=False, flagnearfreq=False, flagneartime=False,
    #              growaround=False,
    #              timecutoff=3.0, freqcutoff=3.0, maxnpieces=5, winsize=7,
    #              action='apply', flagbackup=False, savepars=True
    #              )

    #     casatasks.flagdata(vis=vis, mode='extend', field=calibrators_all, spw='', display='report',
    #              action='apply', datacolumn='data', combinescans=False, flagbackup=False,
    #              growtime=75.0, growfreq=75.0, extendpols=True)

    #     casatasks.flagmanager(vis=vis, mode='save', versionname='flags_after_tfcrop_init',
    #                 comment='Flags after tfcrop on raw flagged data')

    #     print('     => Reporting flags after applied tfcrop')
    #     summary_after_tfcrop = casatasks.flagdata(vis=vis, mode='summary')
    #     report_flag(summary_after_tfcrop, 'field')
    #     report_flag(summary_after_tfcrop, 'scan')
        # report_flag(summary_after_tfcrop,'antenna')
        # report_flag(summary_after_tfcrop,'spw')
    # summary_7 = casatasks.flagdata(vis=vis, mode='summary',field='')



    logging.info('Total data after initial flagging')
    summary_pre_cal = casatasks.flagdata(vis=vis, mode='summary')
    report_flag(summary_pre_cal, 'field')
    report_flag(summary_pre_cal, 'scan')
    # report_flag(summary_pre_cal,'antenna')

    pre_flagging_endtime = time.time() 
    pre_flagging_time = pre_flagging_endtime - pre_flagging_starttime 
    
    logging.info(f"Initial flagging took {pre_flagging_time/ 60:.2f} minutes")
    
    """Remember to flag edge channels in each spw"""
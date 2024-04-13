import argparse
import os
# from casaplotms import plotms
# from casatasks import *


from sys import argv
import time

startTime = time.time()

solint_long = '60s'
calculate_long_solint = True

solint_mid = '30s'
calculate_mid_solint = True

solint_bandpass_phase_short = '6s'
solint_phase_short = '15s'
solint_amp_phase = 'inf'



# flagging settings
manual_file_flag = True
fields_to_report_flag = ''  # leavy empty to report all fields, but takes longer

# this is for the beginning, raw data
apply_tfcrop_init = True

# this is at the end, for calibrated data (rflag) or uncalibrated data (tfcrop)
auto_flag_data = True
flag_with_rflag = True
flag_with_tfcrop = False

# calibration settings
additional_gain_tables = False
minsnr = 2.0
combine = ''

# Create additional flagbackups along the way.
# 0 > none additional, but still do important ones;
# 1 > secondary important backups (e.g. rflag, tfcrop, etc)
# 2 > everything;
extended_flag_backups = 0

# controls the level of plotting.
plotting_level = 1

# control the level of terminal verbosity output.
report_verbosity = 2

# return()

# Include any override variables in the config file.
exec(open('./config_input.py').read())
# select some fields (or all) to make visibility plots along the way.
# the more, the longer is the time, though....
# useful to see how calibration and automatic flagging performs.
fields_test_plot = calibrators_all_arr


def data_handle():
    '''
    Handle importint the data, asdm to ms file.


        Need to be done:
            - if ms file already exists, validade a resume point
            to start to work.

    '''
    data_handle_starttime = time.time()
    do_hanning = True
    if not os.path.exists(base_path+name + '.ms'):
        importasdm(asdm=base_path + name, vis=base_path+name + '.ms',
                   process_syspower=True, process_caldevice=True, process_pointing=True,
                   process_flags=True, applyflags=True, savecmds=True, flagbackup=True,
                   verbose=True, with_pointing_correction=True,
                   outfile=output_vis_path + name + '.flagonline.txt')
    else:
        print('MS file already exists. Skipping...')

    listobs(vis=base_path+name + '.ms',
            listfile=vis.replace('.ms','.listobs'),
            overwrite=True)
    if do_hanning == True:
        vis_hs = vis.replace('.ms', '_hs.ms')
        if not os.path.exists(vis_hs):
            print(' >> Applying Hanning smoothing to the data...')
            hanningsmooth(vis=base_path+name + '.ms',
                          outputvis=vis_hs)
        vis_to_use = vis_hs
        print('     => Setting vis file to Hanning smoothed version [*_hs.ms]')
        print(vis_to_use)
    else:
        vis_to_use = vis
    # if os.path.exists(vis_hs):
    #     print('     => Setting vis file to Hanning smoothed version [*_hs.ms]')
    #     vis_to_use = vis_hs
    #     print(vis_to_use)

    if not os.path.exists(base_path + 'flags/'):
        os.makedirs(base_path + 'flags/')
    if not os.path.exists(base_path + 'calibration/'):
        os.makedirs(base_path + 'calibration/')
    if not os.path.exists(base_path + 'plots/'):
        os.makedirs(base_path + 'plots/')

    data_handle_time = time.time() - data_handle_starttime
    print('Exec time for data handle/conversion=', data_handle_time)
    return (vis_to_use)



def report_flag(summary, axis):
    for id, stats in summary[axis].items():
        print('%s %s: %5.1f percent flagged' % (axis, id, 100. * stats['flagged'] / stats['total']))
    pass


def fast_check_cal(FIELDS=['0', '1', '3', '5'], stage='', type=''):
    if not os.path.exists(base_path + 'plots/calibration/check_cal/'):
        os.makedirs(base_path + 'plots/calibration/check_cal/')

    for f in FIELDS:
        plotms(vis=vis_to_use, xaxis='freq', yaxis='amp', showgui=False,
               coloraxis='spw', ydatacolumn='corrected', field=f, avgtime='20',
               plotfile=base_path + 'plots/calibration/check_cal/' + type + '_freq_amp_' + f + '_' + stage + '.jpg',
               title='Field ' + str(f), plotrange=[-1, -1, 0, 8])
        plotms(vis=vis_to_use, xaxis='time', yaxis='phase', showgui=False,
               coloraxis='spw', ydatacolumn='corrected', field=f, avgchannel='16',
               plotfile=base_path + 'plots/calibration/check_cal/' + type + '_time_phase_' + f + '_' + stage + '.jpg',
               title='Field ' + str(f), plotrange=[-1, -1, -180, 180])
    pass


def split_calibrators():
    print('  >> Spliting calibrators to separated ms file...')
    split(vis=vis_to_use,
          outputvis=str(i) + '_calibrators_' + name + '.ms', keepmms=True,
          field=calibrators_all,
          datacolumn='corrected', keepflags=True)


def make_plots_stages(stage='before', kind='',
                      plots=None, FIELDS=calibrators_all_arr, plot_all_uv=False, avgantenna=True):
    """
    Make standard plots given a stage (before or after) of calibration.
    This can be useful to compare how calibration performs on the data.

    PS. This function takes a long time to complete if all plots are asked.
    """
    # Amplitude vs channel; Amplitude vs time; Amplitude vs Frequency;
    # phase vs time;
    make_plots_starttime = time.time()

    if not os.path.exists(base_path + 'plots/'):
        os.makedirs(base_path + 'plots/')
    if not os.path.exists(base_path + 'plots/' + stage):
        os.makedirs(base_path + 'plots/' + stage)

    if not os.path.exists(base_path + 'plots/' + stage + '/chan_amp/'):
        os.makedirs(base_path + 'plots/' + stage + '/chan_amp/')
    if not os.path.exists(base_path + 'plots/' + stage + '/time_amp/'):
        os.makedirs(base_path + 'plots/' + stage + '/time_amp/')
    if not os.path.exists(base_path + 'plots/' + stage + '/freq_amp/'):
        os.makedirs(base_path + 'plots/' + stage + '/freq_amp/')
    if not os.path.exists(base_path + 'plots/' + stage + '/time_phase/'):
        os.makedirs(base_path + 'plots/' + stage + '/time_phase/')
    if not os.path.exists(base_path + 'plots/' + stage + '/amp_phase/'):
        os.makedirs(base_path + 'plots/' + stage + '/amp_phase/')
    if not os.path.exists(base_path + 'plots/' + stage + '/chan_phase/'):
        os.makedirs(base_path + 'plots/' + stage + '/chan_phase/')

    if stage == 'before':
        ydatacolumn = 'data'
    if stage == 'after':
        ydatacolumn = 'corrected'

    # if plot_all_uv==True:
    #     plotms(vis=vis_to_use, xaxis='U', yaxis='V',field='',
    #         avgchannel='32', avgtime='60',
    #         width=800,height=540,showgui=False,overwrite=True,
    #         plotfile=base_path+'plots/'+stage+'/uv_plane_all_data_'+kind+'.jpg')

    # All antenas, plot each field
    average_strong = True
    average_few = False

    if plotting_level >= 1:
        for FIELD in FIELDS:
            # print('Plotting Chan vs Amp: Field')
            plotms(vis=vis_to_use, xaxis='time', yaxis='amp', ydatacolumn=ydatacolumn,
                   avgchannel='9999', coloraxis='spw', field=FIELD,
                   xselfscale=True, yselfscale=True, correlation='RR,LL',
                   title='Time vs Amp, ' + str(FIELD), avgantenna=avgantenna,
                   gridrows=1, gridcols=1, width=2000, height=800, showgui=False, overwrite=True, dpi=1200,
                   highres=True,
                   plotfile=base_path + 'plots/' + stage + '/time_amp/time_amp_avg_' + ydatacolumn + '_field_' + str(
                       FIELD) + '_' + kind + '.jpg')

            plotms(vis=vis_to_use, xaxis='freq', yaxis='amp', ydatacolumn=ydatacolumn,
                   avgtime='9999', coloraxis='spw', field=FIELD,
                   xselfscale=True, yselfscale=True, correlation='RR,LL',
                   title='Freq vs Amp, ' + str(FIELD), avgantenna=avgantenna,
                   # width=800,height=540,dpi=600,overwrite=True,showgui=False,
                   gridrows=1, gridcols=1, width=2000, height=800, showgui=False, overwrite=True, dpi=1200,
                   highres=True,
                   plotfile=base_path + 'plots/' + stage + '/freq_amp/freq_amp_avg_' + ydatacolumn + '_field_' + str(
                       FIELD) + '_' + kind + '.jpg')

            plotms(vis=vis_to_use, xaxis='time', yaxis='phase', ydatacolumn=ydatacolumn, correlation='RR,LL',
                   avgchannel='9999', coloraxis='spw', field=FIELD,
                   title='Time vs Phase, ' + str(FIELD), avgantenna=avgantenna,
                   gridrows=1, gridcols=1, width=2000, height=800, showgui=False, overwrite=True,
                   dpi=1200, highres=True,
                   plotrange=[-1, -1, -180, 180],
                   plotfile=base_path + 'plots/' + stage + '/time_phase/time_phase_avg_' + ydatacolumn + '_field_' + str(
                       FIELD) + '_' + kind + '.jpg')

            # plotms(vis=vis_to_use, xaxis='U', yaxis='V',ydatacolumn=ydatacolumn,xdatacolumn=ydatacolumn,
            #     avgchannel='16',avgtime='20',coloraxis='',field=FIELD,
            #     title='u vs v, AvgChan=16,AvgTime=20'+str(FIELD),
            #     gridrows=1,gridcols=1,width=800,height=540,showgui=False,overwrite=True,
            #     # plotrange=[-1,-1,-180,180],
            #     plotfile=base_path+'plots/'+stage+'/u_v_avg_'+ydatacolumn+'_field_'+str(FIELD)+'_'+kind+'.jpg')

            plotms(vis=vis_to_use, xaxis='uvwave', yaxis='amp', field=FIELD,
                   coloraxis='spw', correlation='RR,LL',
                   xselfscale=True, yselfscale=True,
                   ydatacolumn=ydatacolumn, avgchannel='9999', avgtime='9999',
                   width=2000, height=800, showgui=False, overwrite=True, dpi=1200, highres=True,
                   plotfile=base_path + 'plots/' + stage + '/uvwave_amp_' + ydatacolumn + '_' + str(
                       FIELD) + '_' + kind + '.jpg')

            # plotms(vis=vis_to_use, xaxis='uvdist', yaxis='amp',field=FIELD,
            #     ydatacolumn=ydatacolumn, avgchannel='16', avgtime='20',
            #     width=800,height=540,showgui=False,overwrite=True,
            #     plotfile=base_path+'plots/'+stage+'/uvwave_amp_'+ydatacolumn+'_'+str(FIELD)+'_'+kind+'.jpg')
            # plotms(vis=vis_to_use, xaxis='uvdist', yaxis='amp',field=FIELD,
            #     ydatacolumn=ydatacolumn, avgchannel='16', avgtime='20',
            #     width=800,height=540,showgui=False,overwrite=True,
            #     plotfile=base_path+'plots/'+stage+'/uvdist_amp_data_'+str(FIELD)+'_'+kind+'.jpg')
            #
            # plotms(vis=vis_to_use, xaxis='UVwave', yaxis='amp',field=FIELD,
            #     ydatacolumn=ydatacolumn, avgchannel='16', avgtime='20',
            #     width=800,height=540,showgui=False,overwrite=True,
            #     plotfile=base_path+'plots/'+stage+'/uvwave_amp_data_'+str(FIELD)+'_'+kind+'.jpg')

        # for FIELD in calibrators_all:
        #     plotms(vis=vis_to_use, xaxis='time', yaxis='phase',ydatacolumn=ydatacolumn,
        #         avgchannel='16',coloraxis='spw',field=FIELD,
        #         title='Time vs Phase, AvgChan=16,'+str(FIELD),
        #         gridrows=1,gridcols=1,width=800,height=540,showgui=False,overwrite=True,
        #         plotrange=[-1,-1,-180,180],
        #         plotfile=base_path+'plots/'+stage+'/time_phase/time_phase_avg_field_'+str(FIELD)+'_'+kind+'.jpg')

    make_plots_time = time.time() - make_plots_starttime
    print('Exec time for plotting regarding', kind, '=', make_plots_time)
    pass


def find_refant(msfile, field, tablename):
    """
    This function comes from the e-MERLIN CASA Pipeline.
    https://github.com/e-merlin/eMERLIN_CASA_pipeline/blob/master/functions/eMCP_functions.py#L1501
    """
    # Find phase solutions per scan:
    # tablename = calib_dir +
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
    # if 'Lo' in antenna_names:
    #     priorities = ['Pi','Da','Kn','De','Cm']
    # else:
    #     priorities = ['Mk2','Pi','Da','Kn', 'Cm', 'De']
    # refant = ','.join([a for a in pref_ant if a in priorities])
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

    if not os.path.exists(base_path + 'plots/' + stage):
        os.makedirs(base_path + 'plots/' + stage)

    if yaxis == 'phase':
        plotrange = [-1, -1, -180, 180]
    else:
        plotrange = [-1, -1, -1, -1]

    if fields == '':
        plotfile = base_path + 'plots/' + stage + '/' + table_type + '_' + xaxis + '_' + yaxis + '_field_' + str(
            'all') + '_ant_' + antenna + '_spw_' + spw + '.jpg'
        if not os.path.exists(plotfile):
            plotms(vis=table, xaxis=xaxis, yaxis=yaxis, field='',
                   gridcols=1, gridrows=1, coloraxis='spw', antenna=antenna, spw=spw, plotrange=plotrange,
                   width=2000, height=800, showgui=False, overwrite=True, dpi=1200, highres=True,
                   plotfile=plotfile)
    else:
        try:
            for FIELD in fields:
                plotfile = base_path + 'plots/' + stage + '/' + table_type + '_' + xaxis + '_' + yaxis + '_field_' + str(
                    FIELD) + '_ant_' + antenna + '_spw_' + spw + '.jpg'
                if not os.path.exists(plotfile):
                    plotms(vis=table, xaxis=xaxis, yaxis=yaxis, field=FIELD,
                           # gridcols=4,gridrows=4,coloraxis='spw',antenna='',iteraxis='antenna',
                           # width=2048,height=1280,dpi=256,overwrite=True,showgui=False,
                           gridcols=1, gridrows=1, coloraxis='spw', antenna=antenna, spw=spw, plotrange=plotrange,
                           width=2000, height=800, showgui=False, overwrite=True, dpi=1200, highres=True,
                           plotfile=plotfile)
        except:
            print('     => Not going to plot calibration tables... Check your input fields list.  ')
    pass


def apply_precal(tables_to_apply, i):
    """
        Apply initial calibration.

        The sole purpose of applying this is to check how the initial
        tables (phase&ampphase, bandpass) are performing on calibrating
        the data. This should be used in case of
        running rflag to the data later.
    """
    ## Apply calibration, flagging bad solutions.
    print(' >> Creating new flagbackup file before applying pre-calibration ', str(i))
    flagmanager(vis=vis_to_use, mode='save', versionname='before_pre_calibration_iteraction_' + str(i),
                comment='Flagbackup before pre-calibration iteration ' + str(i))

    print('     => Reporting data flagged before pre-calibration...')
    summary_pre_cal = flagdata(vis=vis_to_use,
                               mode='summary', field=calibrators_all)
    report_flag(summary_pre_cal, 'field')

    applycal(vis=vis_to_use,
             field=calibrators_all, selectdata=True,
             gaintable=tables_to_apply,
             gainfield=[''],
             interp=[''],
             calwt=True, flagbackup=False)

    print('     => Reporting data flagged after pre-calibration...')
    summary_pre_cal_after = flagdata(vis=vis_to_use,
                                     mode='summary', field=calibrators_all)
    report_flag(summary_pre_cal_after, 'field')

    pass


def apply_rflag(i, field):
    print('  >> Applying rflag...')
    summary_before_apply_cal = flagdata(vis=vis_to_use, mode='summary')
    report_flag(summary_before_apply_cal, 'field')
    # report_flag(summary_before_apply_cal,'antenna')
    # report_flag(summary_before_apply_cal,'spw')

    if extended_flag_backups >= 1:
        print('    ** Creating flag backup before rflag...')
        flagmanager(vis=vis_to_use, mode='save', versionname='pre_calibration_before_rflag_iteraction_' + str(i),
                    comment='Flagbackup before rflag/pre-calibration iteration ' + str(i))

    summary_before_rflag = flagdata(vis=vis_to_use, mode='summary')
    report_flag(summary_before_rflag, 'field')
    # report_flag(summary_before_rflag,'antenna')
    # report_flag(summary_before_rflag,'spw')

    datacolumn_to_flag = 'corrected'
    flagdata(vis=vis_to_use, mode='rflag', field=field, spw='', display='report',
             datacolumn=datacolumn_to_flag, ntime='scan', combinescans=False,
             extendflags=False, winsize=7, timedevscale=3.0, freqdevscale=3.0,
             flagnearfreq=False, flagneartime=False, growaround=True,
             action='apply', flagbackup=False, savepars=True
             )

    flagdata(vis=vis_to_use, field=field, spw='',
             datacolumn=datacolumn_to_flag,
             mode='extend', action='apply', display='report',
             flagbackup=False, growtime=75.0,
             growfreq=75.0, extendpols=False)

    # make_plots_stages(stage='after',kind='after_rflag',FIELDS=fields_test_plot)
    summary_after_rflag = flagdata(vis=vis_to_use, mode='summary')
    report_flag(summary_after_rflag, 'field')

    # fast_check_cal(FIELDS=calibrators_all_arr,
    #     stage='after_rflag',type=solint)
    # report_flag(summary_after_rflag,'antenna')
    # report_flag(summary_after_rflag,'spw')
    #
    if extended_flag_backups >= 1:
        print('    ** Saving flags backup after rflag...')
        flagmanager(vis=vis_to_use, mode='save', versionname='pre_calibration_after_rflag_iteraction_' + str(i),
                    comment='Flagbackup after rflag/pre-calibration iteration ' + str(i))


def apply_tfcrop(tables_to_apply, i, applied_cal=False):
    print('  >> Applying tfcrop...')
    summary_before_apply_cal = flagdata(vis=vis_to_use, mode='summary')
    report_flag(summary_before_apply_cal, 'field')

    if extended_flag_backups >= 1:
        print('    ** Creating flag backup before tfcrop...')
        flagmanager(vis=vis_to_use, mode='save', versionname='pre_calibration_before_tfcrop_iteraction_' + str(i),
                    comment='Flagbackup before tfcrop/pre-calibration iteration ' + str(i))

    summary_before_tfcrop = flagdata(vis=vis_to_use, mode='summary')
    report_flag(summary_before_tfcrop, 'field')
    # report_flag(summary_before_rflag,'antenna')
    # report_flag(summary_before_rflag,'spw')

    # fast_check_cal(FIELDS=calibrators_all_arr,
    #     stage='before_tfcrop',type=solint)
    datacolumn_to_flag = 'corrected'
    flagdata(vis=vis_to_use, mode='tfcrop', field=calibrators_all, spw='',
             datacolumn='residual', ntime='scan', combinescans=False,
             extendflags=False, winsize=7,
             flagnearfreq=False,
             flagneartime=False, growaround=True, timecutoff=2.5, freqcutoff=2.5,
             action='apply', flagbackup=False, savepars=False,
             )

    flagdata(vis=vis_to_use, field=calibrators_all, spw='',
             datacolumn=datacolumn_to_flag,
             mode='extend', action='apply', display='report',
             flagbackup=False, growtime=75.0,
             growfreq=75.0, extendpols=False)

    summary_after_tfcrop = flagdata(vis=vis_to_use, mode='summary')
    report_flag(summary_after_tfcrop, 'field')
    # report_flag(summary_after_rflag,'antenna')
    # report_flag(summary_after_rflag,'spw')
    #
    if extended_flag_backups >= 1:
        print('    ** Saving flags backup after tfcrop...')
        flagmanager(vis=vis_to_use, mode='save', versionname='pre_calibration_after_tfcrop_iteraction_' + str(i),
                    comment='Flagbackup after tfcrop/pre-calibration iteration ' + str(i))


# def restore_flags():


def manual_flagging():
    ## Apply the flags from the flag commands list.
    if manual_file_flag == True:
        print(' >> Performing instructions from manual flag file.')
        try:
            flagdata(vis=vis_to_use, mode='list',
                     inpfile=base_path + 'flags/' + name + '.flagcmds', flagbackup=False)
            print('     => Creating new flagbackup file after manual flagging file.')
            flagmanager(vis=vis_to_use, mode='save', versionname='manual_flagging_1',
                        comment='First run of manual flagging.')
            if report_verbosity >= 1:
                summary_after_manual = flagdata(vis=vis_to_use, mode='summary')
                report_flag(summary_after_manual, 'field')
                # report_flag(summary_after_manual,'scan')
                # report_flag(summary_after_manual,'antenna')
        except:
            print(' **==>> Please, create a manual file flag inside ', base_path + 'flags/')
            print(' **==>> under the name ', name + '.flagcmds')
            print('     ** No manual flags applied....')


def initial_flagging():
    """
    Init initial flagging to the data.
    """

    initial_flagging_starttime = time.time()

    #
    # delmod(vis)
    # clearcal(vis)

    print('Creating flagbackup file for original MS.')
    flagmanager(vis=vis_to_use, mode='save', versionname='original_flags_import',
                comment='Original flags from import.')

    print('Starting pre-flagging to the data.')

    if report_verbosity >= 2:
        print('     => Reporting data flagged at start ...')
        summary_0 = flagdata(vis=vis_to_use, mode='summary')
        report_flag(summary_0, 'field')
        # report_flag(summary_0,'scan')
        # report_flag(summary_0,'antenna')

    print(' >> Applying online flags...')
    flagcmd(vis=vis_to_use, inpmode='table', reason='any', action='plot',
            plotfile=base_path + 'plots/' + name + '_flaggingreason_vs_time.pdf',
            useapplied=True, overwrite=True)

    flagcmd(vis=vis_to_use, inpmode='table', reason='any', action='apply',
            flagbackup=False, useapplied=True)

    # online flags can take long run times.
    # flagmanager(vis=vis_to_use,mode='save',versionname='after_online_flags',
    #     comment='Backup point for restoring after online flags.')

    plotants(vis=vis_to_use, logpos=True, figfile=base_path + 'plots/' + name + '_plotant_log.pdf')
    plotants(vis=vis_to_use, logpos=False, figfile=base_path + 'plots/' + name + '_plotant.pdf')

    # if report_verbosity >= 2:
    #     print('     ## Reporting data flagged after online flagging...')
    #     summary_online = flagdata(vis=vis_to_use, mode='summary')
    #     report_flag(summary_online,'field')
    #     # report_flag(summary_online,'scan')
    #     # report_flag(summary_online,'antenna')

    print(' >> Applying autocorr flagging...')
    flagdata(vis=vis_to_use, mode='manual', autocorr=True,
             reason='autocorr', flagbackup=False, action='apply',
             name='autocorr')

    if report_verbosity >= 2:
        print('     => Reporting data flagged after autocorr flagging...')
        summary_autocorr = flagdata(vis=vis_to_use, mode='summary')
        report_flag(summary_autocorr, 'field')
        # report_flag(summary_autocorr,'scan')
        # report_flag(summary_autocorr,'antenna')

    print(' >> Applying shadow flagging...')
    flagdata(vis=vis_to_use, mode='shadow', reason='shadow', tolerance=0.0,
             flagbackup=False, name='shadow', action='apply')

    if report_verbosity >= 2:
        print('     ## Reporting data flagged after shadow flagging...')
        summary_2 = flagdata(vis=vis_to_use, mode='summary')
        report_flag(summary_2, 'field')
        # report_flag(summary_2,'scan')

    # flag zeros data (flagm data with zero values/amplitudes)
    print(' >> Applying clipping...')
    flagdata(vis=vis_to_use, mode='clip', correlation='ABS_ALL', clipzeros=True,
             reason='clip', flagbackup=False, action='apply', name='clip')

    if report_verbosity >= 2:
        print('     ## Reporting data flagged after clip flagging...')
        summary_4 = flagdata(vis=vis_to_use, mode='summary')
        report_flag(summary_4, 'field')
        # report_flag(summary_4,'scan')

    # quack flagging (time to the telescope to go to the source)
    print(' >> Applying quack flagging...')
    flagdata(vis=vis_to_use, mode='quack', quackinterval=5.0, quackmode='beg',
             reason='quack', flagbackup=False, action='apply', name='quack')

    if report_verbosity >= 2:
        print('     => Reporting data flagged after quack flagging...')
        summary_5 = flagdata(vis=vis_to_use, mode='summary')
        report_flag(summary_5, 'field')
        # report_flag(summary_5,'scan')

    print('     => Creating new flagbackup file after pre-flagging.')
    flagmanager(vis=vis_to_use, mode='save', versionname='pre_flagging',
                comment='Pre-flags applied: Autocorr,clipping, quack, shadow.')

    # Further flagging (manual inspections)

    if apply_tfcrop_init == True:
        print(' >> Performing tfcrop on raw data...')

        summary_before_tfcrop = flagdata(vis=vis_to_use, mode='summary')
        if report_verbosity >= 1:
            print('     => Reporting flags before tfcrop')
            report_flag(summary_before_tfcrop, 'field')
            # report_flag(summary_before_tfcrop,'scan')
            # report_flag(summary_before_tfcrop,'antenna')
            # report_flag(summary_before_tfcrop,'spw')
        flagmanager(vis=vis_to_use, mode='save', versionname='flags_before_tfcrop_init',
                    comment='Flags beforet tfcrop on raw flagged data')
        # flagdata(vis=vis_to_use, mode='tfcrop',datacolumn='data',
        #     action='apply',display='',reason='tfcrop',
        #     name='tfcrop',flagbackup=False,outfile='tfcrop_flag')
        flagdata(vis=vis_to_use, mode='tfcrop', field=calibrators_all, display='', spw='',
                 datacolumn='data', ntime='scan', combinescans=False,
                 extendflags=False, flagnearfreq=False, flagneartime=False,
                 growaround=False,
                 timecutoff=3.0, freqcutoff=3.0, maxnpieces=5, winsize=7,
                 action='apply', flagbackup=False, savepars=True
                 )

        flagdata(vis=vis_to_use, mode='extend', field=calibrators_all, spw='', display='report',
                 action='apply', datacolumn='data', combinescans=False, flagbackup=False,
                 growtime=75.0, growfreq=75.0, extendpols=True)

        flagmanager(vis=vis_to_use, mode='save', versionname='flags_after_tfcrop_init',
                    comment='Flags after tfcrop on raw flagged data')

        print('     => Reporting flags after applied tfcrop')
        summary_after_tfcrop = flagdata(vis=vis_to_use, mode='summary')
        report_flag(summary_after_tfcrop, 'field')
        report_flag(summary_after_tfcrop, 'scan')
        # report_flag(summary_after_tfcrop,'antenna')
        # report_flag(summary_after_tfcrop,'spw')
    # summary_7 = flagdata(vis=vis_to_use, mode='summary',field='')

    print('     => Reporting amount of data flagged after initial flagging:')
    summary_pre_cal = flagdata(vis=vis_to_use, mode='summary')
    report_flag(summary_pre_cal, 'field')
    report_flag(summary_pre_cal, 'scan')
    # report_flag(summary_pre_cal,'antenna')

    initial_flagging_time = time.time() - initial_flagging_starttime
    print('###  Exec time for initial flagging=', initial_flagging_time, '    ###')
    return


def initial_corrections():
    """
    Init first corrections to the data, e.g. opacity, gain curve, etc.
    """
    if not os.path.exists(base_path + 'calibration/'):
        os.makedirs(base_path + 'calibration/')
    # Initial Flux Density Scaling
    ##check flux calibrator models
    # setjy(vis=vis_to_use, listmodels=True)
    initial_corrections_starttime = time.time()

    ## Initial corrections
    ### Antenna positions
    print(' >> Initial corrections:')
    init_tables = []
    print('     => Antenna positions...')
    if not os.path.exists(base_path + 'calibration/antpos_' + name + '.tb'):
        gencal(vis=vis_to_use,
               caltable=base_path + 'calibration/antpos_' + name + '.tb', caltype='antpos')

    if os.path.exists(base_path + 'calibration/antpos_' + name + '.tb'):
        init_tables.append(base_path + 'calibration/antpos_' + name + '.tb')

    ### Gain curve correction.
    print('     => Gain curve...')
    if not os.path.exists(base_path + 'calibration/gaincurve_gc_' + name + '.tb'):
        gencal(vis=vis_to_use,
               caltable=base_path + 'calibration/gaincurve_gc_' + name + '.tb',
               caltype='gc')

    if os.path.exists(base_path + 'calibration/gaincurve_gc_' + name + '.tb'):
        init_tables.append(base_path + 'calibration/gaincurve_gc_' + name + '.tb')

    ## Correct atmospheric/weather conditions (opacity)
    a = np.arange(0, int(all_spws.split(',')[-1]) + 1)
    all_spw_opacity = ",".join(str(x) for x in list(a.astype(str)))

    print('     => Opacity...')
    myTau = plotweather(vis=vis_to_use, seasonal_weight=0.5, doPlot=True,
                        plotName=base_path + 'plots/weather_' + name + '.pdf')

    if not os.path.exists(base_path + 'calibration/opacity_' + name + '.tb'):
        gencal(vis=vis_to_use,
               caltable=base_path + 'calibration/opacity_' + name + '.tb',
               caltype='opac', spw=all_spw_opacity, parameter=myTau)

    if os.path.exists(base_path + 'calibration/opacity_' + name + '.tb'):
        init_tables.append(base_path + 'calibration/opacity_' + name + '.tb')

    ### Corrections to (rq)
    print('     => rq...')
    if not os.path.exists(base_path + 'calibration/rq_' + name + '.tb'):
        gencal(vis=vis_to_use,
               caltable=base_path + 'calibration/rq_' + name + '.tb', caltype='rq')

    if os.path.exists(base_path + 'calibration/rq_' + name + '.tb'):
        init_tables.append(base_path + 'calibration/rq_' + name + '.tb')

    ### Corrections to switched power (swpow)
    print('     => swpower...')
    if not os.path.exists(base_path + 'calibration/swpow_' + name + '.tb'):
        gencal(vis=vis_to_use,
               caltable=base_path + 'calibration/swpow_' + name + '.tb', caltype='swpow')

    if os.path.exists(base_path + 'calibration/swpow_' + name + '.tb'):
        init_tables.append(base_path + 'calibration/swpow_' + name + '.tb')

    initial_corrections_time = time.time() - initial_corrections_starttime
    print('Exec time for initial flagging=', initial_corrections_time)
    return (init_tables)


def flux_scale_setjy(flux_density=None):
    print('--==> Clearing model and cal visibilities.')
    delmod(vis, otf=True, scr=False)
    # delmod(vis)
    clearcal(vis)
    print('Setting the model for the flux calibrator...')
    if flux_density is None:
        flux_density_data = setjy(vis=vis_to_use, field=flux_calibrator, spw=all_spws,
                                  # selectdata=False,
                                  model=model_setjy, scalebychan=True,
                                  standard='Perley-Butler 2017',
                                  listmodels=False, usescratch=True)

        spws = []
        fluxes = []
        for key in list(flux_density_data['0'].keys())[:-1]:
            spws.append(int(key))
            fluxes.append(flux_density_data['0'][key]['fluxd'][0])
        spws = np.asarray(spws)
        fluxes = np.asarray(fluxes)
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(8, 5))
            plt.plot(spws, fluxes, 'o', color='black')
            plt.xlabel('SPWids')
            plt.ylabel(f"'Flux Density {flux_calibrator} [Jy]")
            plt.grid()
            plt.title('Flux density from setjy model')
            plt.savefig(f"{base_path}plots/{flux_calibrator}_flux_density_model.pdf", dpi=600)
            plt.clf()
        except:
            print('     => No matplotlib installed. No plots will be created.')
    else:
        flux_density_data = setjy(vis=vis_to_use, field=flux_calibrator, spw=all_spws,
                                  scalebychan=True,
                                  standard='manual', fluxdensity=flux_density,
                                  listmodels=False, usescratch=True)
        fluxes = flux_density
        spws = np.asarray(get_spwids(vis))
    return (flux_density_data, spws, fluxes)


def get_spwids(vis):
    lobs = listobs(vis=vis_to_use)
    extract_spwids = {key: lobs[key] for key in lobs if 'scan_' in key}

    unique_spwids = set()

    for key in extract_spwids:
        nested_dict = extract_spwids[key]
        for inner_key in nested_dict:
            spwids = nested_dict[inner_key]['SpwIds']
            # Convert the array to a sorted tuple and add to the set
            unique_spwids.add(tuple(sorted(spwids)))

    # Convert the set of tuples back to a sorted list of lists
    unique_spwids_lists = sorted([list(t) for t in unique_spwids])
    # Flatten the list and then convert to a set to get unique elements
    unique_elements = set(element for sublist in unique_spwids_lists for element in sublist)

    # Convert the set back to a list and sort it
    unique_elements_sorted = sorted(list(unique_elements))
    return unique_elements_sorted


def check_bandpass_plots(ref_antenna_list, field, spws=None):
    if spws is None:
        _spws = np.asarray(get_spwids(vis))
        n_spws = _spws.shape[0]
        spws = _spws[[int(n_spws * 0.2), int(n_spws * 0.5), -2]]

    if not os.path.exists(base_path + 'plots/bandpass'):
        os.makedirs(base_path + 'plots/bandpass')

    for i in range(len(ref_antenna_list)):
        for spwid in spws:
            plotms(vis=vis_to_use, field=field,
                   xaxis='chan', yaxis='phase',
                   correlation='RR',
                   plotrange=[-1, -1, -180, 180],
                   antenna=f"{ref_antenna_list[0]}&{ref_antenna_list[i]}",
                   spw=str(spwid),
                   width=1000, height=440, showgui=False, overwrite=True,
                   dpi=1200, highres=True,
                   plotfile=f"{base_path}plots/bandpass/{name}_chan_phase_fluxcal_ant_{ref_antenna_list[0]}&{ref_antenna_list[i]}_spw_{spwid}.jpg")

            plotms(vis=vis_to_use, field=field, avgchannel='8',
                   xaxis='time', yaxis='phase',
                   correlation='RR',
                   plotrange=[-1, -1, -180, 180],
                   antenna=f"{ref_antenna_list[0]}&{ref_antenna_list[i]}",
                   spw=str(spwid),
                   width=1000, height=440, showgui=False, overwrite=True,
                   dpi=1200, highres=True,
                   plotfile=f"{base_path}plots/bandpass/{name}_time_phase_fluxcal_ant_{ref_antenna_list[0]}&{ref_antenna_list[i]}_spw_{spwid}.jpg")


def run_gaincal(vis, field, scan,
                refant, spw, calmode, solint, minsnr,
                gaintype, gaintables, i, table_stage, combine='',
                refantmode='strict', overwrite=False):
    print(f" >> Performing gaincal for {table_stage};  with solint of {solint}.")
    caltable = base_path + 'calibration/' + str(i) + table_stage + solint + '_' + name + '.tb'
    print('     => Caltable will be:', caltable)
    if not os.path.exists(caltable):
        gaincal(vis=vis_to_use, caltable=caltable,
                field=field, refant=refant, spw=spw, combine=combine,
                calmode=calmode, solint=solint, minsnr=minsnr, gaintype=gaintype,
                refantmode=refantmode,
                # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                gaintable=gaintables)
    else:
        print('     => Caltable already exists. Skipping gaincal...')
    _gaintables_temp = gaintables.copy()
    _gaintables_temp.append(caltable)
    # print(_gaintables_temp)
    # calibration_table_plot(table=base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint+'_'+name+'.tb',
    #                        stage='calibration',
    #                        table_type=str(i)+'_initial_phase_cal_solint_'+solint,
    #                        kind='',xaxis='time',yaxis='phase',fields='')
    # return(gaintables.copy().append(caltable))
    return (_gaintables_temp)


def run_bandpass(vis, field, scan,
                 refant, spw, solint, minsnr,
                 gaintables, i, table_stage, combine, bandtype,
                 solnorm=False,
                 refantmode='strict', overwrite=False):
    print(f" >> Performing bandpass for {table_stage};  with solint of {solint}.")
    caltable = base_path + 'calibration/' + str(i) + table_stage + solint + '_' + name + '.tb'
    print('     => Caltable will be:', caltable)
    if not os.path.exists(caltable):
        bandpass(vis=vis_to_use, caltable=caltable,
                 field=field, refant=refant, spw=spw,
                 combine=combine, bandtype=bandtype,
                 solint=solint, minsnr=minsnr, solnorm=solnorm,
                 # refantmode=refantmode,
                 # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                 gaintable=gaintables)
    else:
        print('     => Caltable already exists. Skipping bandpass...')
    _gaintables_temp = gaintables.copy()
    _gaintables_temp.append(caltable)
    # print(_gaintables_temp)
    # calibration_table_plot(table=base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint+'_'+name+'.tb',
    #                        stage='calibration',
    #                        table_type=str(i)+'_initial_phase_cal_solint_'+solint,
    #                        kind='',xaxis='time',yaxis='phase',fields='')
    # return(gaintables.copy().append(caltable))
    return (_gaintables_temp)


def bandpass_cal(i=1, do_plots=False):
    if do_plots:
        check_bandpass_plots(ref_antenna_list=ref_antenna_list,
                             field=bandpass_calibrator, spws=None)

    table_stage = '_delay_calibration_scan_'
    solint = 'inf'
    gaintables_temp_K = run_gaincal(vis=vis_to_use,
                                    field=bandpass_calibrator,
                                    gaintables=init_tables,
                                    scan='', refant=ref_antenna,
                                    spw=spw_skip_edge, calmode='p', gaintype='K',
                                    solint=solint,
                                    i=i, table_stage=table_stage,
                                    minsnr=minsnr
                                    )

    calibration_table_plot(table=gaintables_temp_K[-1],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='ant1', yaxis='delay', fields='')

    table_stage = '_initial_bandpass_short_phase_'
    solint = solint_bandpass_phase_short
    gaintables_temp_BP_PH = run_gaincal(vis=vis_to_use,
                                        field=bandpass_calibrator,
                                        gaintables=gaintables_temp_K,
                                        scan='', refant=ref_antenna,
                                        spw=spw_central, calmode='p', gaintype='G',
                                        solint=solint,
                                        i=i, table_stage=table_stage,
                                        minsnr=minsnr
                                        )

    # for k in range(len(ref_antenna_list)):
    #     calibration_table_plot(table=gaintables_temp_BP_PH[-1],
    #                            stage='calibration', antenna=f"{ref_antenna_list[k]}",
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='time', yaxis='phase', fields='')
    #
    # for k in range(len(spws)):
    #     calibration_table_plot(table=gaintables_temp_BP_PH[-1],
    #                            stage='calibration', spw=str(spws[k]),
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='time', yaxis='phase', fields='')

    # table_stage='_initial_bandpass_long_phase_'
    # solint='inf'
    # gaintables_temp_BP_PH_inf = run_gaincal(vis=vis_to_use,
    #             field=bandpass_calibrator,
    #             gaintables = gaintables_temp_BP_PH,
    #             scan='',refant=ref_antenna,
    #             spw='',calmode='p', gaintype='G',
    #             solint=solint,
    #             i=i,table_stage=table_stage,
    #             minsnr=minsnr
    #             )

    # for k in (range(len(ref_antenna_list))):
    #     calibration_table_plot(table=gaintables_temp_BP_PH_inf[-1],
    #                         stage='calibration',antenna=f"{ref_antenna_list[k]}",
    #                         table_type=str(i)+table_stage+solint,
    #                         kind='',xaxis='time',yaxis='phase',fields='')

    # for k in (range(len(spws))):
    #     calibration_table_plot(table=gaintables_temp_BP_PH_inf[-1],
    #                         stage='calibration',spw=str(spws[k]),
    #                         table_type=str(i)+table_stage+solint,
    #                         kind='',xaxis='time',yaxis='phase',fields='')

    # for k in range(len(ref_antenna_list)):
    #     for l in range(len(spws)):
    #         calibration_table_plot(table=gaintables_temp_BP_PH[-1],
    #                             stage='calibration',
    #                             antenna=f"{ref_antenna_list[k]}",
    #                             spw=str(spws[l]),
    #                             table_type=str(i)+table_stage+solint,
    #                             kind='',xaxis='time',yaxis='phase',fields='')

    table_stage = '_initial_bandpass_BP_inf_phase_'
    solint = 'inf'
    gaintables_temp_BP_PH_inf = run_bandpass(vis=vis_to_use,
                                             field=bandpass_calibrator,
                                             gaintables=gaintables_temp_BP_PH,
                                             combine='scan', bandtype='B',
                                             scan='', refant=ref_antenna,
                                             spw='',
                                             solint=solint, solnorm=False,
                                             i=i, table_stage=table_stage,
                                             minsnr=minsnr
                                             )

    calibration_table_plot(table=gaintables_temp_BP_PH_inf[-1],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='chan', yaxis='phase', fields='')

    calibration_table_plot(table=gaintables_temp_BP_PH_inf[-1],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='freq', yaxis='phase', fields='')

    calibration_table_plot(table=gaintables_temp_BP_PH_inf[-1],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='chan', yaxis='amp', fields='')

    calibration_table_plot(table=gaintables_temp_BP_PH_inf[-1],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='freq', yaxis='amp', fields='')

    # for k in (range(len(ref_antenna_list))):
    #     calibration_table_plot(table=gaintables_temp_BP_PH_inf[-1],
    #                            stage='calibration', antenna=f"{ref_antenna_list[k]}",
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='chan', yaxis='phase', fields='')
    #     calibration_table_plot(table=gaintables_temp_BP_PH_inf[-1],
    #                            stage='calibration', antenna=f"{ref_antenna_list[k]}",
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='chan', yaxis='amp', fields='')
    #     calibration_table_plot(table=gaintables_temp_BP_PH_inf[-1],
    #                            stage='calibration', antenna=f"{ref_antenna_list[k]}",
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='freq', yaxis='phase', fields='')
    #     calibration_table_plot(table=gaintables_temp_BP_PH_inf[-1],
    #                            stage='calibration', antenna=f"{ref_antenna_list[k]}",
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='freq', yaxis='amp', fields='')

    # for k in (range(len(spws))):
    #     calibration_table_plot(table=gaintables_temp_BP_PH_inf[-1],
    #                            stage='calibration', spw=str(spws[k]),
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='chan', yaxis='phase', fields='')
    #     calibration_table_plot(table=gaintables_temp_BP_PH_inf[-1],
    #                            stage='calibration', spw=str(spws[k]),
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='chan', yaxis='amp', fields='')

    pre_cal_tables_temp = [gaintables_temp_K[-1], gaintables_temp_BP_PH_inf[-1]]
    gainfield_init = [''] * len(init_tables)
    gainfield_bandpass = [bandpass_calibrator] * len(pre_cal_tables_temp)
    gainfield_bandpass_apply = gainfield_init.copy()
    gainfield_bandpass_apply.extend(gainfield_bandpass)

    gaintables_apply_BP = init_tables.copy()
    gaintables_apply_BP.extend(pre_cal_tables_temp)

    print('Creating flag-backup before applying initial bandpass.')
    flagmanager(vis=vis_to_use, mode='save', versionname='before_bandpass_init_' + str(i),
                comment='Flags before apply bandpass init, iteraction' + str(i) + '.')

    print('     ++==>> Reporting flags before applycal to bandpass:', i)
    summary_before_applycal_to_bandpass = flagdata(vis=vis_to_use, mode='summary',
                                                   field=bandpass_calibrator)
    report_flag(summary_before_applycal_to_bandpass, 'field')

    applycal(vis=vis_to_use, field=bandpass_calibrator,
             gaintable=gaintables_apply_BP,
             gainfield=gainfield_bandpass_apply,
             calwt=False, flagbackup=False)

    if flux_calibrator != bandpass_calibrator:
        table_stage = '_initial_bandpass_flux_short_phase_'
        solint = '16s'
        gaintables_temp_BP_FLX_PH = run_gaincal(vis=vis_to_use,
                                                field=bandpass_calibrator + ',' + flux_calibrator,
                                                gaintables=gaintables_apply_BP,
                                                scan='', refant=ref_antenna,
                                                spw='', calmode='p', gaintype='G',
                                                solint=solint,
                                                i=i, table_stage=table_stage,
                                                minsnr=minsnr
                                                )

    print('     ++==>> Reporting flags after applycal to bandpass:', i)
    summary_after_applycal_to_bandpass = flagdata(vis=vis_to_use, mode='summary',
                                                  field=bandpass_calibrator)
    report_flag(summary_after_applycal_to_bandpass, 'field')

    return (gaintables_apply_BP, gainfield_bandpass_apply)


def cal_phases_amplitudes(gaintables_apply_BP, gainfield_bandpass_apply, i=1):
    table_stage = '_calibrators_phase_short_'
    solint = solint_phase_short
    gaintables_temp_calibrators_short = run_gaincal(vis=vis_to_use,
                                                    field=calibrators_all,
                                                    gaintables=gaintables_apply_BP,
                                                    scan='', refant=ref_antenna,
                                                    spw=spw_central, calmode='p', gaintype='G',
                                                    solint=solint,
                                                    i=i, table_stage=table_stage,
                                                    minsnr=minsnr
                                                    )

    calibration_table_plot(table=gaintables_temp_calibrators_short[-1],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='time', yaxis='phase', fields='')

    # for k in (range(len(ref_antenna_list))):
    #     calibration_table_plot(table=gaintables_temp_calibrators_short[-1],
    #                            stage='calibration', antenna=f"{ref_antenna_list[k]}",
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='time', yaxis='phase', fields='')
    #
    # for k in (range(len(spws))):
    #     calibration_table_plot(table=gaintables_temp_calibrators_short[-1],
    #                            stage='calibration', spw=str(spws[k]),
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='time', yaxis='phase', fields='')

    table_stage = '_calibrators_phase_scaninf_'
    solint = 'inf'
    gaintables_temp_calibrators_scaninf = run_gaincal(vis=vis_to_use,
                                                      field=calibrators_all,
                                                      gaintables=gaintables_apply_BP,
                                                      scan='', refant=ref_antenna,
                                                      spw=spw_central, calmode='p', gaintype='G', combine='',
                                                      solint=solint,
                                                      i=i, table_stage=table_stage,
                                                      minsnr=minsnr
                                                      )

    calibration_table_plot(table=gaintables_temp_calibrators_scaninf[-1],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='time', yaxis='phase', fields='')

    # for k in (range(len(ref_antenna_list))):
    #     calibration_table_plot(table=gaintables_temp_calibrators_scaninf[-1],
    #                            stage='calibration', antenna=f"{ref_antenna_list[k]}",
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='time', yaxis='phase', fields='')
    #
    # for k in (range(len(spws))):
    #     calibration_table_plot(table=gaintables_temp_calibrators_scaninf[-1],
    #                            stage='calibration', spw=str(spws[k]),
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='time', yaxis='phase', fields='')

    table_stage = '_calibrators_ampphase_'
    solint = solint_amp_phase
    gaintables_temp_calibrators_amp = run_gaincal(vis=vis_to_use,
                                                  field=calibrators_all,
                                                  gaintables=gaintables_temp_calibrators_short,
                                                  scan='', refant=ref_antenna,
                                                  spw=spw_central, calmode='ap', gaintype='G',
                                                  solint=solint,
                                                  i=i, table_stage=table_stage,
                                                  minsnr=minsnr
                                                  )

    calibration_table_plot(table=gaintables_temp_calibrators_amp[-1],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='time', yaxis='phase', fields='')
    calibration_table_plot(table=gaintables_temp_calibrators_amp[-1],
                           stage='calibration',
                           table_type=str(i) + table_stage + solint,
                           kind='', xaxis='time', yaxis='amp', fields='')

    # for k in (range(len(ref_antenna_list))):
    #     calibration_table_plot(table=gaintables_temp_calibrators_amp[-1],
    #                            stage='calibration', antenna=f"{ref_antenna_list[k]}",
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='time', yaxis='phase', fields='')
    #     calibration_table_plot(table=gaintables_temp_calibrators_amp[-1],
    #                            stage='calibration', antenna=f"{ref_antenna_list[k]}",
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='time', yaxis='amp', fields='')
    #
    # for k in (range(len(spws))):
    #     calibration_table_plot(table=gaintables_temp_calibrators_amp[-1],
    #                            stage='calibration', spw=str(spws[k]),
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='time', yaxis='phase', fields='')
    #     calibration_table_plot(table=gaintables_temp_calibrators_amp[-1],
    #                            stage='calibration', spw=str(spws[k]),
    #                            table_type=str(i) + table_stage + solint,
    #                            kind='', xaxis='time', yaxis='amp', fields='')

    ## Flux Scale

    fluxtable = gaintables_temp_calibrators_amp[-1].replace(table_stage + solint,
                                                            table_stage + solint + '_flux_scale')
    listfluxfile = fluxtable.replace('.tb', '_fluxinfo.txt')

    flux_bp = fluxscale(vis=vis_to_use,
                        caltable=gaintables_temp_calibrators_amp[-1],
                        fluxtable=fluxtable, reference=flux_calibrator,
                        transfer=calibrators_all, incremental=True,
                        listfile=listfluxfile, fitorder=1)

    if os.path.exists(fluxtable):
        #

        setjy(vis=vis_to_use, field=calibrators_all, scalebychan=True,
              standard='fluxscale', fluxdict=flux_bp)

        calibration_table_plot(table=fluxtable,
                               stage='calibration',
                               table_type=str(i) + table_stage + solint + '_flux_scale',
                               kind='', xaxis='time', yaxis='phase', fields='')
        calibration_table_plot(table=fluxtable,
                               stage='calibration',
                               table_type=str(i) + table_stage + solint + '_flux_scale',
                               kind='', xaxis='time', yaxis='amp', fields='')

        # for k in (range(len(ref_antenna_list))):
        #     calibration_table_plot(table=fluxtable,
        #                            stage='calibration', antenna=f"{ref_antenna_list[k]}",
        #                            table_type=str(i) + table_stage + solint + '_flux_scale',
        #                            kind='', xaxis='time', yaxis='phase', fields='')
        #     calibration_table_plot(table=fluxtable,
        #                            stage='calibration', antenna=f"{ref_antenna_list[k]}",
        #                            table_type=str(i) + table_stage + solint + '_flux_scale',
        #                            kind='', xaxis='time', yaxis='amp', fields='')
        #
        # for k in (range(len(spws))):
        #     calibration_table_plot(table=fluxtable,
        #                            stage='calibration', spw=str(spws[k]),
        #                            table_type=str(i) + table_stage + solint + '_flux_scale',
        #                            kind='', xaxis='time', yaxis='phase', fields='')
        #     calibration_table_plot(table=fluxtable,
        #                            stage='calibration', spw=str(spws[k]),
        #                            table_type=str(i) + table_stage + solint + '_flux_scale',
        #                            kind='', xaxis='time', yaxis='amp', fields='')

        gaintables_temp_calibrators_amp_fluxscale = gaintables_temp_calibrators_amp.copy()
        gaintables_temp_calibrators_amp_fluxscale.append(fluxtable)

        gain_tables_ampphase = [gaintables_temp_calibrators_amp[-2],
                                gaintables_temp_calibrators_amp[-1], fluxtable]
        flag_FLUX_SCALE = False

    else:
        print('No fluxscale talbe generated.')
        gaintables_temp_calibrators_amp_fluxscale = gaintables_temp_calibrators_amp.copy()
        # gaintables_temp_calibrators_amp_fluxscale.append(fluxtable)

        gain_tables_ampphase = [gaintables_temp_calibrators_amp[-2],
                                gaintables_temp_calibrators_amp[-1]]
        flag_FLUX_SCALE = True

    print('     ++==>> Creating flag-backup before applycal to calibrators iteration:', i)
    flagmanager(vis=vis_to_use, mode='save', versionname='before_applycal_' + str(i),
                comment='Flags before applycal, iteraction' + str(i) + '.')

    print('     ++==>> Reporting flags before applycal to calibrators iteration:', i)
    summary_before_applycal_to_calibrators = flagdata(vis=vis_to_use, mode='summary',
                                                      field=calibrators_all)
    report_flag(summary_before_applycal_to_calibrators, 'field')

    for calibrator_field in calibrators_all_arr:
        ext_cal_fields = [calibrator_field] * len(gain_tables_ampphase)
        gainfield_ampphase = gainfield_bandpass_apply.copy()
        gainfield_ampphase.extend(ext_cal_fields)

        print('Appplying calibration to:', calibrator_field)
        print('     => Gainfields are:', gainfield_ampphase)
        print('     => Gaintables are:', gaintables_temp_calibrators_amp_fluxscale)
        applycal(vis=vis_to_use,
                 field=calibrator_field,
                 gaintable=gaintables_temp_calibrators_amp_fluxscale, flagbackup=False,
                 gainfield=gainfield_ampphase, calwt=False)

    # print(gaintables_temp_calibrators_amp_fluxscale)
    # print(gaintables_temp_calibrators_scaninf)

    print('     ++==>> Reporting flags after applycal to calibrators iteration:', i)
    summary_after_applycal_to_calibrators = flagdata(vis=vis_to_use, mode='summary', field=calibrators_all)
    report_flag(summary_after_applycal_to_calibrators, 'field')

    return (
        gaintables_temp_calibrators_amp_fluxscale, gaintables_temp_calibrators_scaninf, flag_FLUX_SCALE)


def apply_cal_to_science(init_tables, gain_tables_BP_final, gain_tables_amps_phases):
    print('Applying calibration to science targets.')
    gain_tables_final = init_tables.copy()
    gain_tables_final.extend(gain_tables_BP_final)
    gain_tables_final.extend(gain_tables_amps_phases)

    print('     => Reporting data flagged before applycal.')
    summary_cal_before = flagdata(vis=vis_to_use,
                                  mode='summary', field='', datacolumn='data')
    report_flag(summary_cal_before, 'field')

    for n in range(len(target_fields_arr)):
        gainfields_final = [''] * len(init_tables)
        gainfields_final.extend([bandpass_calibrator] * len(gain_tables_BP_final))
        gainfields_final_ext = [phase_calibrators_all_arr[n]] * len(gain_tables_amps_phases)
        gainfields_final.extend(gainfields_final_ext)
        print(gainfields_final)
        print('Applying calibration to:', target_fields_arr[n])
        applycal(vis=vis_to_use,
                 field=target_fields_arr[n],
                 gaintable=gain_tables_final,
                 gainfield=gainfields_final, calwt=False)

    print('     => Reporting data flagged after applycal.')
    summary_cal_after = flagdata(vis=vis_to_use,
                                 mode='summary', field='', datacolumn='data')
    report_flag(summary_cal_after, 'field')
    return (gain_tables_final, gainfields_final)


def final_auto_flag():
    print(
        '     => Saving flags before final flagging.')
    flagmanager(vis=vis_to_use, mode='save',
                versionname='after_final_cal',
                comment='Flags after apply calibration. This is before any \
                 additional flagging to the full target corrected data.')

    print('     => Reporting data flagged after final cal and before final flagging...')
    summary_after_final_cal = flagdata(vis=vis_to_use, mode='summary')
    report_flag(summary_after_final_cal, 'field')

    flagdata(vis=vis_to_use, mode='rflag', field=target_fields, spw='', display='report',
             datacolumn='corrected', ntime='scan', combinescans=False,
             extendflags=False, winsize=7, timedevscale=3.5, freqdevscale=3.5,
             flagnearfreq=False, flagneartime=False, growaround=True,
             timecutoff=2.5, freqcutoff=2.5,
             action='apply', flagbackup=False, savepars=True
             )

    # flagdata(vis=vis_to_use,mode='tfcrop',field=all_fields,spw='',display='both',
    #     datacolumn='corrected', ntime='scan', combinescans=False,
    #     extendflags=False,winsize=7, timedevscale=4.5, freqdevscale=4.5,
    #     flagnearfreq=False,
    #     flagneartime=False,growaround=True,timecutoff=2.0,freqcutoff=1.0,
    #     action='calculate', flagbackup=False, savepars=True,
    #     )

    flagdata(vis=vis_to_use, mode='extend', field=target_fields, spw='', display='report',
             action='apply', datacolumn='corrected', combinescans=False, flagbackup=False,
             growtime=75.0, growfreq=75.0, extendpols=True)
    flagmanager(vis=vis_to_use, mode='save',
                versionname='after_final_cal_flags',
                comment='Flags after apply calibration. \
        This is after any additional flagging to the full target corrected data.')

    print('     => Reporting data flagged after final cal and after final flagging...')
    summary_after_final_cal_flag = flagdata(vis=vis_to_use, mode='summary')
    report_flag(summary_after_final_cal_flag, 'field')

    pass


# Split
def split_fields():
    print('Spliting measurement file into separated fields...')
    if not os.path.exists(base_path + 'fields/'):
        os.makedirs(base_path + 'fields/')

    def split_ms(field):
        if not os.path.exists(base_path + 'fields/' + field):
            os.makedirs(base_path + 'fields/' + field)

        g_name = base_path + 'fields/' + field + '/' + field + '.calibrated'
        g_vis = g_name + '.ms'
        split(vis=vis_to_use, outputvis=g_vis, field=field, datacolumn='corrected')
        statwt(vis=g_vis, datacolumn='data')

        flagmanager(vis=g_vis, mode='save', versionname='Original',
                    comment='Original flags from split after calibration.')

    # targets_to_split = ['UGC08387','MCG+07-23-019','IRASF08572+391','UGC05101',
    #     'UGC08058','VV340a','VV250a','UGC08696','NGC3690','VV705','UGC04881',
    #     'UGC09913','IRASF15250+360','IRASF17132+531']
    targets_to_split = target_fields_arr

    for TT in targets_to_split:
        print(' >> Spliting field', TT)
        split_ms(TT)


def split_fields_new():
    ms_amp = listobs(vis=vis_to_use, intent='*CALIBRATE_AMPLI*')
    ms_ph = listobs(vis=vis_to_use, intent='*CALIBRATE_PHASE*')
    ms_flux = listobs(vis=vis_to_use, intent='*CALIBRATE_FLUX*')
    ms_bp = listobs(vis=vis_to_use, intent='*BANDPASS*')
    ms_all = listobs(vis=vis_to_use)

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

    fids, targets = get_fields(ms_all, 'field')
    # if not os.path.exists(base_path + 'fields/' + field):
    #     os.makedirs(base_path + 'fields/' + field)
    if not os.path.exists(base_path + 'fields/'):
        os.makedirs(base_path + 'fields/')
    # os.system(f'mkdir fields')
    for target in targets:
        # os.system(f'mkdir fields/{target}')
        formated_target = target.replace(' ', '').replace('/', '')
        os.system(f'mkdir {base_path}fields/{formated_target}')
        # if not os.path.exists(base_path + 'fields/' + formated_target):
        print(f"Splitting field {target} into fields/{formated_target}.")
        split(vis=vis_to_use,
              outputvis=f'{base_path}fields/{formated_target}'
                        f'/{formated_target}.calibrated.avg12s.ms',
              datacolumn='corrected', field=target, timebin='12s')
        split(vis=vis_to_use,
              outputvis=f'{base_path}fields/{formated_target}/{formated_target}.calibrated.ms',
              datacolumn='corrected', field=target)


def basic_imaging(threshold='1.0e-4Jy', niter=10000,
                  cell='0.03arcsec', SIZE=3072,
                  deconvolver='multiscale', scales=[0, 2, 5, 10, 20, 50],
                  smallscalebias=0.9):
    imaging_starttime = time.time()
    print('Performing basic imaging on data fields...')
    if not os.path.exists(base_path + 'imaging/'):
        os.makedirs(base_path + 'imaging/')

    def image_calibrators():
        for F in calibrators_all:
            print(' >> Imaging calibrator field', F)
            SIZE = 1024
            imagename = base_path + 'imaging/field_' + F + '_' + str(SIZE) + '_3K.0.05arcsec.natural'
            tclean(vis=vis_to_use, imagename=imagename, imsize=SIZE,
                   cell='0.05arcsec', pblimit=-0.01, niter=3000, stokes='I',
                   savemodel='none', field=F, datacolumn='corrected', weighting='natural',
                   antenna='', spw='')
            exportfits(imagename=imagename + '.image', fitsimage=imagename + '.fits',
                       velocity=True)

    def image_targets():
        unit = 'mJy'
        rms_std_factor = 3
        # rms_level = 0.037 #Natural
        rms_level = 0.044  # Robust
        rms_std = str(rms_level / rms_std_factor) + unit
        # threshold =  rms_std

        for F in target_fields_arr:
            g_name = base_path + 'fields/' + F + '/' + F + '.calibrated'
            g_vis = g_name + '.ms'
            print(' >> Imaging target field', F)

            imagename = base_path + 'imaging/field_' + F + '_' + str(SIZE) + '_30K.0.03arcsec.multiscale.natural'
            tclean(vis=g_vis, imagename=imagename, imsize=SIZE,
                   cell=cell, pblimit=-0.01, niter=niter, stokes='I',
                   savemodel='none', field=F, datacolumn='corrected',
                   weighting='briggs', robust=1.0,
                   antenna='', spw='',
                   deconvolver=deconvolver, scales=scales,
                   smallscalebias=smallscalebias, pbcor=True, threshold=threshold)

            exportfits(imagename=imagename + '.image', fitsimage=imagename + '.fits',
                       velocity=True)

            imagename = base_path + 'imaging/field_' + F + '_' + str(SIZE) + '_3K.0.03arcsec.multiscale.briggs'
            tclean(vis=g_vis, imagename=imagename, imsize=SIZE,
                   cell=cell, pblimit=-0.01, niter=niter, stokes='I',
                   savemodel='none', field=F, datacolumn='corrected',
                   weighting='briggs', robust=1.0,
                   antenna='', spw='',
                   deconvolver=deconvolver, scales=scales,
                   smallscalebias=smallscalebias, pbcor=True, threshold=threshold)

            exportfits(imagename=imagename + '.image', fitsimage=imagename + '.fits',
                       velocity=True)

    image_calibrators()
    image_targets()
    imaging_time = time.time() - imaging_starttime
    print('Exec time for basic imaging=', imaging_time, 's')


# config()



steps = [
    'startup',
    'initial_flagging',
    'manual_flagging',
    'initial_corrections',
    'flux_scale_setjy',
    'select_refant',
    # 'calibration',
    # 'run_statwt',
    # 'split_fields'
]
#  'split_fields'


# try:
#     steps_performed
# except NameError:
#     steps_performed = []
# steps_performed = []
# steps_performed = []

try:
    if 'startup' in steps and 'startup' not in steps_peformed:
        vis_to_use = data_handle()
        spws = np.asarray(get_spwids(vis=vis_to_use))
        steps_peformed.append('startup')
except:
    if 'startup' in steps and 'startup':
        steps_peformed = []
        vis_to_use = data_handle()
        spws = np.asarray(get_spwids(vis=vis_to_use))
        steps_peformed.append('startup')

# if 'average_in_time' in steps and 'average_in_time' not in steps_peformed:
#     split(vis=vis, outputvis=name + '.RR_LL.ms', datacolumn='data', keepflags=False,
#           correlation='RR,LL')
#     steps_peformed.append('average_in_time')

if 'initial_flagging' in steps and 'initial_flagging' not in steps_peformed:
    initial_flagging()
    steps_peformed.append('initial_flagging')

if 'manual_flagging' in steps and 'manual_flagging' not in steps_peformed:
    manual_flagging()
    steps_peformed.append('manual_flagging')

if 'initial_corrections' in steps and 'initial_corrections' not in steps_peformed:
    init_tables = initial_corrections()
    steps_peformed.append('initial_corrections')

if 'flux_scale_setjy' in steps and 'flux_scale_setjy' not in steps_peformed:
    flux_density_data, spws, fluxes = flux_scale_setjy()
    # flux_density_data, spws, fluxes = flux_scale_setjy(flux_density=[1.92, 0, 0, 0])
    steps_peformed.append('flux_scale_setjy')

if 'select_refant' in steps and 'select_refant' not in steps_peformed:
    if refant is None:
        tablename_refant = base_path + '/calibration/find_refant.phase'
        ref_antenna = find_refant(msfile=vis_to_use, field=calibrators_all,
                                  tablename=tablename_refant)
        ref_antenna_list = ref_antenna.split(',')
    else:
        ref_antenna = refant
    steps_peformed.append('select_refant')

if 'calibration' in steps and 'calibration' not in steps_peformed:
    gaintables_apply_BP_1, gainfield_bandpass_apply_1 = bandpass_cal(i=1, do_plots=False)

    gaintables_temp_calibrators_amp_fluxscale_1, gaintables_temp_calibrators_scaninf_1, flag_FLUX_SCALE_1 = \
        cal_phases_amplitudes(gaintables_apply_BP_1, gainfield_bandpass_apply_1, i=1)

    make_plots_stages(stage='after', kind='after_calibration_iter_1', FIELDS=calibrators_all_arr)

    apply_rflag(i=1, field=calibrators_all)

    make_plots_stages(stage='after', kind='after_calibration_iter_1_after_rflag',
                      FIELDS=calibrators_all_arr)

    gaintables_apply_BP_2, gainfield_bandpass_apply_2 = bandpass_cal(i=2, do_plots=False)

    gaintables_temp_calibrators_amp_fluxscale_2, gaintables_temp_calibrators_scaninf_2, flag_FLUX_SCALE_2 = (
        cal_phases_amplitudes(gaintables_apply_BP_2, gainfield_bandpass_apply_2, i=2))

    make_plots_stages(stage='after', kind='after_calibration_iter_2', FIELDS=calibrators_all_arr)

    if flag_FLUX_SCALE_2 == False:
        gain_tables_amps_phases = [gaintables_temp_calibrators_scaninf_2[-1],
                                   gaintables_temp_calibrators_amp_fluxscale_2[-2],
                                   gaintables_temp_calibrators_amp_fluxscale_2[-1]]
    else:
        gain_tables_amps_phases = [gaintables_temp_calibrators_scaninf_2[-1],
                                   gaintables_temp_calibrators_amp_fluxscale_2[-1]]

    gain_tables_BP_final = [gaintables_apply_BP_2[-2], gaintables_apply_BP_2[-1]]

    print('Creating flag-backup before applying calibration.')
    flagmanager(vis=vis_to_use, mode='save', versionname='before_final_cal',
                comment='Flags before apply calibration.')

    _gain_tables_final, _gainfields_final = apply_cal_to_science(init_tables, gain_tables_BP_final,
                                                                 gain_tables_amps_phases)

    make_plots_stages(stage='after', kind='after_calibration_iter_2', FIELDS=target_fields_arr)

    steps_peformed.append('calibration')

if 'run_statwt' in steps and 'run_statwt' not in steps_peformed:
    statwt(vis=vis_to_use, preview=False,
           datacolumn='corrected',
           timebin='16s', statalg='chauvenet')
    steps_peformed.append('run_statwt')

if 'split_fields' in steps and 'split_fields' not in steps_peformed:
    split_fields_new()
    steps_peformed.append('split_fields')

# if 'calibration' in steps and 'calibration' not in steps_peformed:
#     calibration()
#     steps_peformed.append('calibration')

# make_plots_stages(stage='before',kind='before_tfcrop_init',FIELDS=fields_test_plot,plot_all_uv=False)
# # # # #
# initial_flagging()
# /nvme1/scratch/lucatelli/lirgi/emerlin/casa-release-5.8.0-109.el6/bin/casa -c eMERLIN_CASA_pipeline/eMERLIN_CASA_pipeline.py -r restore_flags flag_manual_avg init_models bandpass initial_gaincal fluxscale bandpass_final gaincal_final applycal_all flag_target plot_corrected split_fields
# # #
# make_plots_stages(stage='before',kind='after_tfcrop_init',FIELDS=fields_test_plot,plot_all_uv=False)
# initial_corrections()
# # #
# # #
# # """


# # calibration()
# #
# #
# # # make_plots_stages(stage='after',kind='after_rflag_and_cal',FIELDS=fields_test_plot)
# # """
# make_plots_stages(stage='after',kind='after_cal_before_rflag',FIELDS=target_fields)

# add_final_auto_flags = True
# if add_final_auto_flags == True:
#     '''
#         Apply autoflag to target fields.
#     '''
#     final_auto_flag()

# split_fields()

# make_plots_stages(stage='after',kind='final',FIELDS=target_fields_arr,plot_all_uv=False)
# # # basic_imaging()

# exec_time = time.time() - startTime
# print('Exec time for pipeline=',exec_time,'s')

# exit()


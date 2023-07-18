import argparse
import os
# from casaplotms import plotms
# from casatasks import *


from sys import argv
import time
startTime = time.time()


solint_long = '64s'
calculate_long_solint = True

solint_mid = '32s'
calculate_mid_solint = True


solint_short = '16s'
calculate_short_solint = True
#Some tables will be calculated for this, no matter true of false.
# E.G. short phases for the bandpass and delay need to be short.

calculate_extra_tables = False # not implemented yet.

main_setjy_solint = solint_mid #which solution interval to use to set the flux scalling.

solint_main = solint_mid # which solution interval to be used as a reference


#flagging settings
manual_file_flag = True
fields_to_report_flag = '' # leavy empty to report all fields, but takes longer

#this is for the beginning, raw data
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

#control the level of terminal verbosity output.
report_verbosity = 2

    # return()

# Include any override variables in the config file.
exec(open('./config_input_23A-324_X.py').read())
#select some fields (or all) to make visibility plots along the way.
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

    if not os.path.exists(vis):
        importasdm(asdm=base_path+name,vis=vis,
            process_syspower=True,process_caldevice=True, process_pointing=True,
            process_flags=True,applyflags=True, savecmds=True, flagbackup=True,
            verbose=True,with_pointing_correction=True,
            outfile=output_vis_path+name+'.flagonline.txt')
        listobs(vis=vis,listfile=base_path+name+'.listobs')
    else:
        print('MS file already exists. Skipping...')

    if not os.path.exists(base_path+'flags/'):
        os.makedirs(base_path+'flags/')
    if not os.path.exists(base_path+'calibration/'):
        os.makedirs(base_path+'calibration/')
    if not os.path.exists(base_path+'plots/'):
        os.makedirs(base_path+'plots/')

    data_handle_time = time.time() - data_handle_starttime
    print('Exec time for data handle/conversion=',data_handle_time)
    return()


def report_flag(summary,axis):
    for id, stats in summary[ axis ].items():
        print('%s %s: %5.1f percent flagged' % ( axis, id, 100. * stats[ 'flagged' ] / stats[ 'total' ] ))
    pass


def fast_check_cal(FIELDS=['0','1','3','5'],stage='',type=''):
    if not os.path.exists(base_path+'plots/calibration/check_cal/'):
        os.makedirs(base_path+'plots/calibration/check_cal/')

    for f in FIELDS:
        plotms(vis=vis,xaxis='freq',yaxis='amp',showgui=False,
            coloraxis='spw',ydatacolumn='corrected',field=f,avgtime='20',
            plotfile = base_path+'plots/calibration/check_cal/'+type+'_freq_amp_'+f+'_'+stage+'.jpg',
            title='Field '+str(f),plotrange=[-1,-1,0,8])
        plotms(vis=vis,xaxis='time',yaxis='phase',showgui=False,
            coloraxis='spw',ydatacolumn='corrected',field=f,avgchannel='16',
            plotfile = base_path+'plots/calibration/check_cal/'+type+'_time_phase_'+f+'_'+stage+'.jpg',
            title='Field '+str(f),plotrange=[-1,-1,-180,180])
    pass



def split_calibrators():
    print('  >> Spliting calibrators to separated ms file...')
    split(vis=vis,
        outputvis=str(i)+'_calibrators_'+name+'.ms', keepmms=True,
        field=calibrators_all,
        datacolumn='corrected', keepflags=True)


def make_plots_stages(stage='before',kind='',
        plots=None,FIELDS=calibrators_all_arr,plot_all_uv=False):
    """
    Make standard plots given a stage (before or after) of calibration.
    This can be useful to compare how calibration performs on the data.

    PS. This function takes a long time to complete if all plots are asked.
    """
    # Amplitude vs channel; Amplitude vs time; Amplitude vs Frequency;
    # phase vs time;
    make_plots_starttime = time.time()

    if not os.path.exists(base_path+'plots/'):
        os.makedirs(base_path+'plots/')
    if not os.path.exists(base_path+'plots/'+stage):
        os.makedirs(base_path+'plots/'+stage)

    if not os.path.exists(base_path+'plots/'+stage+'/chan_amp/'):
        os.makedirs(base_path+'plots/'+stage+'/chan_amp/')
    if not os.path.exists(base_path+'plots/'+stage+'/time_amp/'):
        os.makedirs(base_path+'plots/'+stage+'/time_amp/')
    if not os.path.exists(base_path+'plots/'+stage+'/freq_amp/'):
        os.makedirs(base_path+'plots/'+stage+'/freq_amp/')
    if not os.path.exists(base_path+'plots/'+stage+'/time_phase/'):
        os.makedirs(base_path+'plots/'+stage+'/time_phase/')
    if not os.path.exists(base_path+'plots/'+stage+'/amp_phase/'):
        os.makedirs(base_path+'plots/'+stage+'/amp_phase/')
    if not os.path.exists(base_path+'plots/'+stage+'/chan_phase/'):
        os.makedirs(base_path+'plots/'+stage+'/chan_phase/')

    if stage=='before':
        ydatacolumn = 'data'
    if stage=='after':
        ydatacolumn = 'corrected'


    if plot_all_uv==True:
        plotms(vis=vis, xaxis='U', yaxis='V',field='',
            avgchannel='32', avgtime='60',
            width=800,height=540,showgui=False,overwrite=True,
            plotfile=base_path+'plots/'+stage+'/uv_plane_all_data_'+kind+'.jpg')


    # All antenas, plot each field
    average_strong=True
    average_few=False

    if plotting_level>=1:
        for FIELD in FIELDS:
            # print('Plotting Chan vs Amp: Field')
            plotms(vis=vis, xaxis='time', yaxis='amp',ydatacolumn=ydatacolumn,
                avgchannel='16',coloraxis='spw',field=FIELD,
                title='Time vs Amp, AvgChan=16,'+str(FIELD),
                gridrows=1,gridcols=1,width=800,height=540,showgui=False,overwrite=True,
                plotfile=base_path+'plots/'+stage+'/time_amp/time_amp_avg_'+ydatacolumn+'_field_'+str(FIELD)+'_'+kind+'.jpg')

            plotms(vis=vis, xaxis='freq', yaxis='amp',ydatacolumn=ydatacolumn,
                avgtime='20',coloraxis='spw',field=FIELD,
                title='Freq vs Amp, AvgTime=20,'+str(FIELD),
                # width=800,height=540,dpi=600,overwrite=True,showgui=False,
                gridrows=1,gridcols=1,width=800,height=540,showgui=False,overwrite=True,
                plotfile=base_path+'plots/'+stage+'/freq_amp/freq_amp_avg_'+ydatacolumn+'_field_'+str(FIELD)+'_'+kind+'.jpg')

            plotms(vis=vis, xaxis='time', yaxis='phase',ydatacolumn=ydatacolumn,
                avgchannel='16',coloraxis='spw',field=FIELD,
                title='Time vs Phase, AvgChan=16,'+str(FIELD),
                gridrows=1,gridcols=1,width=800,height=540,showgui=False,overwrite=True,
                plotrange=[-1,-1,-180,180],
                plotfile=base_path+'plots/'+stage+'/time_phase/time_phase_avg_'+ydatacolumn+'_field_'+str(FIELD)+'_'+kind+'.jpg')

            plotms(vis=vis, xaxis='U', yaxis='V',ydatacolumn=ydatacolumn,xdatacolumn=ydatacolumn,
                avgchannel='16',avgtime='20',coloraxis='',field=FIELD,
                title='u vs v, AvgChan=16,AvgTime=20'+str(FIELD),
                gridrows=1,gridcols=1,width=800,height=540,showgui=False,overwrite=True,
                # plotrange=[-1,-1,-180,180],
                plotfile=base_path+'plots/'+stage+'/u_v_avg_'+ydatacolumn+'_field_'+str(FIELD)+'_'+kind+'.jpg')

            plotms(vis=vis, xaxis='UVwave', yaxis='amp',field=FIELD,
                ydatacolumn=ydatacolumn, avgchannel='16', avgtime='20',
                width=800,height=540,showgui=False,overwrite=True,
                plotfile=base_path+'plots/'+stage+'/uvwave_amp_'+ydatacolumn+'_'+str(FIELD)+'_'+kind+'.jpg')

            plotms(vis=vis, xaxis='uvdist', yaxis='amp',field=FIELD,
                ydatacolumn=ydatacolumn, avgchannel='16', avgtime='20',
                width=800,height=540,showgui=False,overwrite=True,
                plotfile=base_path+'plots/'+stage+'/uvwave_amp_'+ydatacolumn+'_'+str(FIELD)+'_'+kind+'.jpg')
            # plotms(vis=vis, xaxis='uvdist', yaxis='amp',field=FIELD,
            #     ydatacolumn=ydatacolumn, avgchannel='16', avgtime='20',
            #     width=800,height=540,showgui=False,overwrite=True,
            #     plotfile=base_path+'plots/'+stage+'/uvdist_amp_data_'+str(FIELD)+'_'+kind+'.jpg')
            #
            # plotms(vis=vis, xaxis='UVwave', yaxis='amp',field=FIELD,
            #     ydatacolumn=ydatacolumn, avgchannel='16', avgtime='20',
            #     width=800,height=540,showgui=False,overwrite=True,
            #     plotfile=base_path+'plots/'+stage+'/uvwave_amp_data_'+str(FIELD)+'_'+kind+'.jpg')

            if plotting_level>=2:

                plotms(vis=vis, xaxis='chan', yaxis='amp',ydatacolumn=ydatacolumn,
                    avgtime='20',coloraxis='spw',field=FIELD,
                    title='Chan vs Amp, AvgTime=20,'+str(FIELD),
                    gridrows=1,gridcols=1,width=800,height=540,showgui=False,overwrite=True,
                    plotfile=base_path+'plots/'+stage+'/chan_amp/chan_amp_avg_'+ydatacolumn+'_field_'+str(FIELD)+'_'+kind+'.jpg')

                plotms(vis=vis, xaxis='chan', yaxis='phase',ydatacolumn=ydatacolumn,
                    avgtime='20',coloraxis='spw',field=FIELD,
                    title='Chan vs Amp, AvgTime=20,'+str(FIELD),
                    gridrows=1,gridcols=1,width=800,height=540,showgui=False,overwrite=True,
                    plotfile=base_path+'plots/'+stage+'/chan_phase/chan_phase_avg_'+ydatacolumn+'_field_'+str(FIELD)+'_'+kind+'.jpg')

            if plotting_level>=3:
                plotms(vis=vis, xaxis='freq', yaxis='amp',ydatacolumn='model',
                    avgtime='20',coloraxis='spw',field=FIELD,
                    title='Freq vs Amp Model, AvgTime=20,'+str(FIELD),
                    # width=800,height=540,dpi=600,overwrite=True,showgui=False,
                    gridrows=1,gridcols=1,width=800,height=540,showgui=False,overwrite=True,
                    plotfile=base_path+'plots/'+stage+'/freq_amp/freq_amp_model_avg_'+ydatacolumn+'_field_'+str(FIELD)+'_'+kind+'.jpg')



        # for FIELD in calibrators_all:
        #     plotms(vis=vis, xaxis='time', yaxis='phase',ydatacolumn=ydatacolumn,
        #         avgchannel='16',coloraxis='spw',field=FIELD,
        #         title='Time vs Phase, AvgChan=16,'+str(FIELD),
        #         gridrows=1,gridcols=1,width=800,height=540,showgui=False,overwrite=True,
        #         plotrange=[-1,-1,-180,180],
        #         plotfile=base_path+'plots/'+stage+'/time_phase/time_phase_avg_field_'+str(FIELD)+'_'+kind+'.jpg')

    make_plots_time = time.time() - make_plots_starttime
    print('Exec time for plotting regarding',kind,'=',make_plots_time)
    pass

def calibration_table_plot(table,stage='calibration',
    table_type='gain_phase',kind='',
    xaxis='time',yaxis='phase',
    fields=['0']):
    '''
    fields: if a string of fields, will plot data for all fields together.
                e.g. fields='0,1,2'
            if a list of fields, will plot the data for each field separated.
                e.g. fields=['0','1','2']
    '''

    if not os.path.exists(base_path+'plots/'+stage):
     os.makedirs(base_path+'plots/'+stage)

    if yaxis == 'phase':
     plotrange=[-1,-1,-180,180]
    else:
     plotrange=[-1,-1,-1,-1]

    if fields=='':
         plotms(vis=table,xaxis=xaxis,yaxis=yaxis,field='',
             gridcols=1,gridrows=1,coloraxis='spw',antenna='',plotrange=plotrange,
             width=800,height=540,dpi=600,overwrite=True,showgui=False,
             plotfile=base_path+'plots/'+stage+'/'+table_type+'_'+xaxis+'_'+yaxis+'_field_'+str('all')+'.jpg')
    else:
        try:
            for FIELD in fields:
                plotms(vis=table,xaxis=xaxis,yaxis=yaxis,field=FIELD,
                    # gridcols=4,gridrows=4,coloraxis='spw',antenna='',iteraxis='antenna',
                    # width=2048,height=1280,dpi=256,overwrite=True,showgui=False,
                    gridcols=1,gridrows=1,coloraxis='spw',antenna='',plotrange=plotrange,
                    width=800,height=540,dpi=600,overwrite=True,showgui=False,
                         plotfile=base_path+'plots/'+stage+'/'+table_type+'_'+xaxis+'_'+yaxis+'_field_'+str(FIELD)+'.jpg')
        except:
            print('     => Not going to plot calibration tables... Check your input fields list.  ')
    pass


def apply_precal(tables_to_apply,i):
    """
        Apply initial calibration.

        The sole purpose of applying this is to check how the initial
        tables (phase&ampphase, bandpass) are performing on calibrating
        the data. This should be used in case of
        running rflag to the data later.
    """
    ## Apply calibration, flagging bad solutions.
    print(' >> Creating new flagbackup file before applying pre-calibration ',str(i))
    flagmanager(vis=vis,mode='save',versionname='before_pre_calibration_iteraction_'+str(i),
        comment='Flagbackup before pre-calibration iteration '+str(i))

    print('     => Reporting data flagged before pre-calibration...')
    summary_pre_cal = flagdata(vis=vis,
        mode='summary',field=calibrators_all)
    report_flag(summary_pre_cal,'field')

    applycal(vis=vis,
        field=calibrators_all,selectdata=True,
        gaintable=tables_to_apply,
        gainfield=[''],
        interp=[''],
        calwt=True,flagbackup=False)

    print('     => Reporting data flagged after pre-calibration...')
    summary_pre_cal_after = flagdata(vis=vis,
        mode='summary',field=calibrators_all)
    report_flag(summary_pre_cal_after,'field')

    pass


def apply_rflag(tables_to_apply,i,applied_cal=False):
    print('  >> Applying rflag...')
    summary_before_apply_cal = flagdata(vis=vis,mode='summary')
    report_flag(summary_before_apply_cal,'field')
    # report_flag(summary_before_apply_cal,'antenna')
    # report_flag(summary_before_apply_cal,'spw')

    if extended_flag_backups>=1:
        print('    ** Creating flag backup before rflag...')
        flagmanager(vis=vis,mode='save',versionname='pre_calibration_before_rflag_iteraction_'+str(i),
            comment='Flagbackup before rflag/pre-calibration iteration '+str(i))


    if applied_cal==False:
        print('      => Applying pre-calibration before running rflag...')
        apply_precal(tables_to_apply=tables_to_apply,i=i)
        # fast_check_cal(FIELDS=calibrators_all_arr,
        #     stage='before_rflag',type=solint_mid)

    summary_before_rflag = flagdata(vis=vis,mode='summary')
    report_flag(summary_before_rflag,'field')
    # report_flag(summary_before_rflag,'antenna')
    # report_flag(summary_before_rflag,'spw')
    make_plots_stages(stage='after',kind='before_rflag',FIELDS=fields_test_plot)
    datacolumn_to_flag = 'corrected'
    flagdata(vis=vis,mode='rflag',field=calibrators_all,spw='',display='report',
        datacolumn=datacolumn_to_flag, ntime='scan', combinescans=False,
        extendflags=False,winsize=7, timedevscale=3.0, freqdevscale=3.0,
        flagnearfreq=False,flagneartime=False,growaround=True,
        action='apply', flagbackup=False, savepars=True
        )

    flagdata(vis=vis,field=calibrators_all,spw='',
        datacolumn=datacolumn_to_flag,
        mode='extend', action='apply', display='report',
        flagbackup=False,growtime=75.0,
        growfreq=75.0,extendpols=False)

    make_plots_stages(stage='after',kind='after_rflag',FIELDS=fields_test_plot)
    summary_after_rflag = flagdata(vis=vis,mode='summary')
    report_flag(summary_after_rflag,'field')

    # fast_check_cal(FIELDS=calibrators_all_arr,
    #     stage='after_rflag',type=solint)
    # report_flag(summary_after_rflag,'antenna')
    # report_flag(summary_after_rflag,'spw')
    #
    if extended_flag_backups>=1:
        print('    ** Saving flags backup after rflag...')
        flagmanager(vis=vis,mode='save',versionname='pre_calibration_after_rflag_iteraction_'+str(i),
            comment='Flagbackup after rflag/pre-calibration iteration '+str(i))


def apply_tfcrop(tables_to_apply,i,applied_cal=False):
    print('  >> Applying tfcrop...')
    summary_before_apply_cal = flagdata(vis=vis,mode='summary')
    report_flag(summary_before_apply_cal,'field')

    if extended_flag_backups>=1:
        print('    ** Creating flag backup before tfcrop...')
        flagmanager(vis=vis,mode='save',versionname='pre_calibration_before_tfcrop_iteraction_'+str(i),
            comment='Flagbackup before tfcrop/pre-calibration iteration '+str(i))


    summary_before_tfcrop = flagdata(vis=vis,mode='summary')
    report_flag(summary_before_tfcrop,'field')
    # report_flag(summary_before_rflag,'antenna')
    # report_flag(summary_before_rflag,'spw')

    # fast_check_cal(FIELDS=calibrators_all_arr,
    #     stage='before_tfcrop',type=solint)
    datacolumn_to_flag = 'corrected'
    flagdata(vis=vis,mode='tfcrop',field=calibrators_all,spw='',
        datacolumn='residual', ntime='scan', combinescans=False,
        extendflags=False, winsize=7,
        flagnearfreq=False,
        flagneartime=False,growaround=True,timecutoff=2.5,freqcutoff=2.5,
        action='apply', flagbackup=False, savepars=False,
        )

    flagdata(vis=vis,field=calibrators_all,spw='',
        datacolumn=datacolumn_to_flag,
        mode='extend', action='apply', display='report',
        flagbackup=False,growtime=75.0,
        growfreq=75.0,extendpols=False)


    summary_after_tfcrop = flagdata(vis=vis,mode='summary')
    report_flag(summary_after_tfcrop,'field')
    # report_flag(summary_after_rflag,'antenna')
    # report_flag(summary_after_rflag,'spw')
    #
    if extended_flag_backups>=1:
        print('    ** Saving flags backup after tfcrop...')
        flagmanager(vis=vis,mode='save',versionname='pre_calibration_after_tfcrop_iteraction_'+str(i),
            comment='Flagbackup after tfcrop/pre-calibration iteration '+str(i))


# def restore_flags():



def initial_flagging():
    """
    Init initial flagging to the data.
    """

    initial_flagging_starttime = time.time()

    #
    # delmod(vis)
    # clearcal(vis)

    print('Creating flagbackup file for original MS.')
    flagmanager(vis=vis,mode='save',versionname='original_flags_import',
        comment='Original flags from import.')

    print('Starting pre-flagging to the data.')

    if report_verbosity >= 2:
        print('     => Reporting data flagged at start ...')
        summary_0 = flagdata(vis=vis, mode='summary')
        report_flag(summary_0,'field')
        # report_flag(summary_0,'scan')
        # report_flag(summary_0,'antenna')

    print(' >> Applying online flags...')
    flagcmd(vis=vis, inpmode='table', reason='any', action='plot',
            plotfile=base_path+'plots/'+name+'_flaggingreason_vs_time.pdf',
            useapplied=True,overwrite=True)

    flagcmd(vis=vis, inpmode='table', reason='any', action='apply',
        flagbackup=False,useapplied=True)

    # online flags can take long run times.
    # flagmanager(vis=vis,mode='save',versionname='after_online_flags',
    #     comment='Backup point for restoring after online flags.')


    plotants(vis=vis,logpos=True,figfile=base_path+'plots/'+name+'_plotant_log.pdf')
    plotants(vis=vis,logpos=False,figfile=base_path+'plots/'+name+'_plotant.pdf')


    # if report_verbosity >= 2:
    #     print('     ## Reporting data flagged after online flagging...')
    #     summary_online = flagdata(vis=vis, mode='summary')
    #     report_flag(summary_online,'field')
    #     # report_flag(summary_online,'scan')
    #     # report_flag(summary_online,'antenna')


    print(' >> Applying autocorr flagging...')
    flagdata(vis=vis,mode='manual',autocorr=True,
            reason='autocorr',flagbackup=False,action='apply',
            name='autocorr')

    if report_verbosity >= 2:
        print('     => Reporting data flagged after autocorr flagging...')
        summary_autocorr = flagdata(vis=vis, mode='summary')
        report_flag(summary_autocorr,'field')
        # report_flag(summary_autocorr,'scan')
        # report_flag(summary_autocorr,'antenna')


    print(' >> Applying shadow flagging...')
    flagdata(vis=vis,mode='shadow',reason='shadow',tolerance=0.0,
            flagbackup=False,name='shadow',action='apply')

    if report_verbosity >= 2:
        print('     ## Reporting data flagged after shadow flagging...')
        summary_2 = flagdata(vis=vis, mode='summary')
        report_flag(summary_2,'field')
        # report_flag(summary_2,'scan')

    #flag zeros data (flagm data with zero values/amplitudes)
    print(' >> Applying clipping...')
    flagdata(vis=vis,mode='clip',correlation = 'ABS_ALL',clipzeros=True,
            reason='clip',flagbackup=False,action='apply',name='clip')

    if report_verbosity >= 2:
        print('     ## Reporting data flagged after clip flagging...')
        summary_4 = flagdata(vis=vis, mode='summary')
        report_flag(summary_4,'field')
        # report_flag(summary_4,'scan')

    #quack flagging (time to the telescope to go to the source)
    print(' >> Applying quack flagging...')
    flagdata(vis=vis, mode='quack', quackinterval=5.0, quackmode='beg',
            reason='quack',flagbackup=False,action='apply',name='quack')

    if report_verbosity >=2:
        print('     => Reporting data flagged after quack flagging...')
        summary_5 = flagdata(vis=vis, mode='summary')
        report_flag(summary_5,'field')
        # report_flag(summary_5,'scan')


    print('     => Creating new flagbackup file after pre-flagging.')
    flagmanager(vis=vis,mode='save',versionname='pre_flagging',
        comment='Pre-flags applied: Autocorr,clipping, quack, shadow.')

    # Further flagging (manual inspections)
    ## Apply the flags from the flag commands list.
    if manual_file_flag==True:
        print(' >> Performing instructions from manual flag file.')
        try:
            flagdata(vis=vis,mode='list',
                inpfile=base_path+'flags/'+name+'.flagcmds',flagbackup=False)
            print('     => Creating new flagbackup file after manual flagging file.')
            flagmanager(vis=vis,mode='save',versionname='manual_flagging_1',
                comment='First run of manual flagging.')
            if report_verbosity >=1:
                summary_after_manual = flagdata(vis=vis, mode='summary')
                report_flag(summary_after_manual,'field')
                # report_flag(summary_after_manual,'scan')
                # report_flag(summary_after_manual,'antenna')
        except:
            print(' **==>> Please, create a manual file flag inside ',base_path+'flags/')
            print(' **==>> under the name ',name+'.flagcmds')
            print('     ** No manual flags applied....')

    if apply_tfcrop_init == True:
        print(' >> Performing tfcrop on raw data...')

        summary_before_tfcrop = flagdata(vis=vis, mode='summary')
        if report_verbosity >=1:
            print('     => Reporting flags before tfcrop')
            report_flag(summary_before_tfcrop,'field')
            # report_flag(summary_before_tfcrop,'scan')
            # report_flag(summary_before_tfcrop,'antenna')
            # report_flag(summary_before_tfcrop,'spw')
        flagmanager(vis=vis,mode='save',versionname='flags_before_tfcrop_init',
            comment='Flags beforet tfcrop on raw flagged data')
        # flagdata(vis=vis, mode='tfcrop',datacolumn='data',
        #     action='apply',display='',reason='tfcrop',
        #     name='tfcrop',flagbackup=False,outfile='tfcrop_flag')
        flagdata(vis=vis,mode='tfcrop',field=all_fields_str,display='',spw='',
            datacolumn='data', ntime='scan', combinescans=False,
            extendflags=False,flagnearfreq=False,flagneartime=False,
            growaround=False,
            timecutoff=2.5,freqcutoff=2.5,maxnpieces=5,winsize=7,
            action='apply', flagbackup=False, savepars=True
            )

        flagdata(vis=vis,mode='extend',field=all_fields_str,spw='',display='report',
            action='apply',datacolumn='data', combinescans=False,flagbackup=False,
            growtime=75.0,growfreq=75.0,extendpols=True)

        flagmanager(vis=vis,mode='save',versionname='flags_after_tfcrop_init',
            comment='Flags after tfcrop on raw flagged data')

        print('     => Reporting flags after applied tfcrop')
        summary_after_tfcrop = flagdata(vis=vis, mode='summary')
        report_flag(summary_after_tfcrop,'field')
        report_flag(summary_after_tfcrop,'scan')
        # report_flag(summary_after_tfcrop,'antenna')
        # report_flag(summary_after_tfcrop,'spw')
    # summary_7 = flagdata(vis=vis, mode='summary',field='')

    print('     => Reporting amount of data flagged after initial flagging:')
    summary_pre_cal = flagdata(vis=vis, mode='summary')
    report_flag(summary_pre_cal,'field')
    report_flag(summary_pre_cal,'scan')
    # report_flag(summary_pre_cal,'antenna')


    initial_flagging_time = time.time() - initial_flagging_starttime
    print('###  Exec time for initial flagging=',initial_flagging_time,'    ###')
    return


def initial_corrections():
    """
    Init first corrections to the data, e.g. opacity, gain curve, etc.
    """
    if not os.path.exists(base_path+'calibration/'):
        os.makedirs(base_path+'calibration/')
    #Initial Flux Density Scaling
    ##check flux calibrator models
    # setjy(vis=vis, listmodels=True)
    initial_corrections_starttime = time.time()

    ## Initial corrections
    ### Antenna positions
    print(' >> Initial corrections:')
    init_tables = []
    print('     => Antenna positions...')
    gencal(vis=vis,
        caltable=base_path+'calibration/antpos_'+name+'.tb',caltype='antpos')

    if  os.path.exists(base_path+'calibration/antpos_'+name+'.tb'):
        init_tables.append(base_path+'calibration/antpos_'+name+'.tb')


    ### Gain curve correction.
    print('     => Gain curve...')
    gencal(vis=vis,
           caltable=base_path+'calibration/gaincurve_gc_'+name+'.tb',
           caltype='gc')

    if  os.path.exists(base_path+'calibration/gaincurve_gc_'+name+'.tb'):
        init_tables.append(base_path+'calibration/gaincurve_gc_'+name+'.tb')


    ## Correct atmospheric/weather conditions (opacity)
    a = np.arange(0,int(all_spws.split(',')[-1])+1)
    all_spw_opacity = ",".join(str(x) for x in list(a.astype(str)))

    print('     => Opacity...')
    myTau = plotweather(vis=vis,seasonal_weight=0.5, doPlot=True,
        plotName=base_path+'plots/weather_'+name+'.pdf')

    gencal(vis=vis,
        caltable=base_path+'calibration/opacity_'+name+'.tb',
        caltype='opac',spw=all_spw_opacity,parameter=myTau)

    if  os.path.exists(base_path+'calibration/opacity_'+name+'.tb'):
        init_tables.append(base_path+'calibration/opacity_'+name+'.tb')


    ### Corrections to (rq)
    print('     => rq...')
    gencal(vis=vis,
           caltable=base_path+'calibration/rq_'+name+'.tb',caltype='rq')

    if  os.path.exists(base_path+'calibration/rq_'+name+'.tb'):
        init_tables.append(base_path+'calibration/rq_'+name+'.tb')


    ### Corrections to switched power (swpow)
    print('     => swpower...')
    gencal(vis=vis,
           caltable=base_path+'calibration/swpow_'+name+'.tb', caltype='swpow')

    if  os.path.exists(base_path+'calibration/swpow_'+name+'.tb'):
        init_tables.append(base_path+'calibration/swpow_'+name+'.tb')

    initial_corrections_time = time.time() - initial_corrections_starttime
    print('Exec time for initial flagging=',initial_corrections_time)


def calibration():
    """
        Main function to handle calibration operations.
    """
    calibration_starttime = time.time()
    # delmod(vis)
    # clearcal(vis)
    if not os.path.exists(base_path+'calibration/'):
        os.makedirs(base_path+'calibration/')

    def gain_calibration(vis,calibrators_all,flux_calibrator,phase_calibrators_all,
                i,refant,spw_central,spw_skip_edge,auto_flag_data=False):
        '''
            This is a support function to perform i times the calibration step.

            As is indicated in the vla casa pipeline, calibration are performed
            multiple times. I will be using this function for a better understanding
            of how these operations are organized and executed.

        '''




        print('Performing initial gains/corrections for iteraction',i)
        additional_flagging = False
        
        if additional_flagging==True:
            ## Useful in case we need to do more flagging (e.g. after
            ## inspecting plots, etc....)
            print('     ** Performing additional flagging....')
            flagdata(vis=vis,mode='manual',antenna='ea17',flagbackup=False,action='apply')

        print('Setting the model for the flux calibrator...')

        setjy(vis=vis, field=flux_calibrator,spw=all_spws,
            # selectdata=False,
            model=model_setjy,scalebychan=True,
            standard='Perley-Butler 2017',
            listmodels=False, usescratch=False)

        # if calculate_short_solint==True:
        print(' >> Performing initial gain phases...; solint,',solint_short)
        gaincal(vis=vis,
        caltable=base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_short+'_'+name+'.tb',
            field=bandpass_calibrator, refant=refant, spw=spw_central,
            calmode='p', solint=solint_short, minsnr=minsnr,gaintype='G',
            # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
            gaintable=[
                base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb'
            ]
            )
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_short+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_initial_phase_cal_solint_'+solint_short,
            kind='',xaxis='time',yaxis='phase',fields=[bandpass_calibrator])


        print(' >> Performing delay calibraton: bandpass/flux calibrator;... solint=',solint_short)
        gaincal(vis=vis,caltable=base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
            field=bandpass_calibrator,refant=refant,spw=spw_skip_edge,gaintype='K',
            solint='inf',combine=combine,minsnr=minsnr,calmode='p',
            gaintable=[
                base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_short+'_'+name+'.tb'
            ])

        print(' >> Performing initial gain phase>ampphases for flux calibrator; solint,',solint_short)
        gaincal(vis=vis,
        caltable=base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
            field=bandpass_calibrator, refant=refant, spw=spw_central,
            calmode='ap', solint=solint_short, minsnr=minsnr,gaintype='G',
            # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
            gaintable=[
                base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+solint_short+'_'+name+'.tb',   #K
                base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_short+'_'+name+'.tb'
            ]
            )
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_initial_phase_ampphase_cal_solint_'+solint_short,
            kind='',xaxis='time',yaxis='phase',fields=[bandpass_calibrator])
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_initial_phase_ampphase_cal_solint_'+solint_short,
            kind='',xaxis='time',yaxis='amp',fields=[bandpass_calibrator])

        # print(' >> Performing initial gain phase>ampphases for flux calibrator; solint,',solint_short,'+',solint_long)
        # gaincal(vis=vis,
        # caltable=base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_short+'_'+solint_long+'_'+name+'.tb',
        #     field=bandpass_calibrator, refant=refant, spw=spw_central,
        #     calmode='ap', solint=solint_long, minsnr=minsnr,gaintype='G',
        #     # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
        #     gaintable=[
        #         base_path+'calibration/antpos_'+name+'.tb',
        #         base_path+'calibration/gaincurve_gc_'+name+'.tb',
        #         base_path+'calibration/opacity_'+name+'.tb',
        #         base_path+'calibration/rq_'+name+'.tb',
        #         base_path+'calibration/swpow_'+name+'.tb',
        #         base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+solint_short+'_'+name+'.tb',   #K
        #         base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_short+'_'+name+'.tb'
        #     ]
        #     )
        # calibration_table_plot(table=base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_short+'_'+solint_long+'_'+name+'.tb',
        #     stage='calibration',
        #     table_type=str(i)+'_initial_phase_ampphase_cal_solint_'+solint_short+'_'+solint_long,
        #     kind='',xaxis='time',yaxis='phase',fields=[bandpass_calibrator])
        # calibration_table_plot(table=base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_short+'_'+solint_long+'_'+name+'.tb',
        #     stage='calibration',
        #     table_type=str(i)+'_initial_phase_ampphase_cal_solint_'+solint_short+'_'+solint_long,
        #     kind='',xaxis='time',yaxis='amp',fields=[bandpass_calibrator])

        if calculate_mid_solint==True:
            print(' >> Performing initial gain phases...; solint=',solint_mid)
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
                field=bandpass_calibrator, refant=refant, spw=spw_central,
                calmode='p', solint=solint_mid, minsnr=minsnr,gaintype='G',
                # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_initial_phase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='phase',fields=[bandpass_calibrator])

            ## Delay Calibration
            print(' >> Performing delay calibraton: bandpass/flux calibrator;... solint=',solint_mid)
            gaincal(vis=vis,caltable=base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+solint_mid+'_'+name+'.tb',
                field=bandpass_calibrator,refant=refant,spw=spw_skip_edge,gaintype='K',
                solint='inf',combine=combine,minsnr=minsnr,calmode='p',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_mid+'_'+name+'.tb'
                ])

            print(' >> Performing initial gain phase>ampphases for flux calibrator; solint,',solint_mid)
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                field=bandpass_calibrator, refant=refant, spw=spw_central,
                calmode='ap', solint=solint_mid, minsnr=minsnr,gaintype='G',
                # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+solint_mid+'_'+name+'.tb',   #K
                    base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_mid+'_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_initial_phase_ampphase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='phase',fields=[bandpass_calibrator])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_initial_phase_ampphase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='amp',fields=[bandpass_calibrator])

        if calculate_long_solint==True:
            print(' >> Performing initial gain phases...; solint,',solint_long)
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_long+'_'+name+'.tb',
                field=bandpass_calibrator, refant=refant, spw=spw_central,
                calmode='p', solint=solint_long, minsnr=minsnr,gaintype='G',
                # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_initial_phase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='phase',fields=[bandpass_calibrator])


            ## Delay Calibration
            print(' >> Performing delay calibraton: bandpass/flux calibrator;... solint=',solint_long)
            gaincal(vis=vis,caltable=base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+solint_long+'_'+name+'.tb',
                field=bandpass_calibrator,refant=refant,spw=spw_skip_edge,gaintype='K',
                solint='inf',combine=combine,minsnr=minsnr,calmode='p',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_long+'_'+name+'.tb'
                ])

            print(' >> Performing initial gain phase>ampphases for flux calibrator; solint,',solint_long)
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                field=bandpass_calibrator, refant=refant, spw=spw_central,
                calmode='ap', solint=solint_long, minsnr=minsnr,gaintype='G',
                # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+solint_long+'_'+name+'.tb',   #K
                    base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_long+'_'+name+'.tb'
                ]
                )

            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_initial_phase_ampphase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='phase',fields=[bandpass_calibrator])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_initial_phase_ampphase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='amp',fields=[bandpass_calibrator])



        if calculate_mid_solint==True:
            print('     => Using gains from solint,',solint_mid)
            bandpass(vis=vis,caltable=base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
                field=bandpass_calibrator,refant=refant,combine='scan', minsnr=minsnr,
                solint='inf',bandtype='B',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_mid+'_'+name+'.tb', #G0
                    base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+solint_mid+'_'+name+'.tb',   #K
                    base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb'
                ])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_bandpass_calibration_'+solint_mid,
                kind='',xaxis='chan',yaxis='amp',fields=[bandpass_calibrator])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_bandpass_calibration_'+solint_mid,
                kind='',xaxis='chan',yaxis='phase',fields=[bandpass_calibrator])


        if calculate_long_solint==True:
            ## Bandpass
            print(' >> Performing bandpass calibraton...')
            print('     => Using gains from solint,',solint_long)
            bandpass(vis=vis,caltable=base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_long+'_'+name+'.tb',
                field=bandpass_calibrator,refant=refant,combine='scan', minsnr=minsnr,
                solint='inf',bandtype='B',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_long+'_'+name+'.tb', #G0
                    base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+solint_long+'_'+name+'.tb',   #K
                    base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb'
                ])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_bandpass_calibration_'+solint_long,
                kind='',xaxis='chan',yaxis='amp',fields=[bandpass_calibrator])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_bandpass_calibration_'+solint_long,
                kind='',xaxis='chan',yaxis='phase',fields=[bandpass_calibrator])

        bandpass(vis=vis,caltable=base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_short+'_'+name+'.tb',
            field=bandpass_calibrator,refant=refant,combine='scan', minsnr=minsnr,
            solint='inf',bandtype='B',
            gaintable=[
                base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_initial_phase_cal_solint_'+solint_short+'_'+name+'.tb', #G0
                base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+solint_short+'_'+name+'.tb',   #K
                base_path+'calibration/'+str(i)+'_initial_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb'
            ])
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_short+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_bandpass_calibration_'+solint_short,
            kind='',xaxis='chan',yaxis='amp',fields=[bandpass_calibrator])
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_short+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_bandpass_calibration_'+solint_short,
            kind='',xaxis='chan',yaxis='phase',fields=[bandpass_calibrator])




        # Second pass of gains, for all calibrators)

        print(' >> Performing second gain phases for all calibrators; solint=',solint_short,'...')
        gaincal(vis=vis,
        caltable=base_path+'calibration/'+str(i)+'_second_phase_cal_solint_'+solint_short+'_'+name+'.tb',
            field=calibrators_all, refant=refant, spw=spw_central,
            calmode='p', solint=solint_short, minsnr=minsnr,gaintype='G',
            # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
            gaintable=[
                base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                # base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+name+'.tb',   #K
                base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_short+'_'+name+'.tb'
            ]
            )
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_second_phase_cal_solint_'+solint_short+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_second_phase_cal_solint_'+solint_short,
            kind='',xaxis='time',yaxis='phase',fields='')

        ## Delay Calibration
        print(' >> Performing delay calibraton: all calibrators ...')
        gaincal(vis=vis,caltable=base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
            field=calibrators_all,refant=refant,spw=spw_skip_edge,gaintype='K',
            solint='inf',combine=combine,minsnr=minsnr,calmode='p',
            gaintable=[
                base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                # base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_second_phase_cal_solint_'+solint_short+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_short+'_'+name+'.tb'
            ])


        if calculate_short_solint==True:

            print(' >> Performing second gain phases>ampphase for all calibrators; solint=',solint_short,'...')
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                field=calibrators_all, refant=refant, spw=spw_central,
                calmode='ap', solint=solint_short, minsnr=minsnr,gaintype='G',
                # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_short+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_second_phase_cal_solint_'+solint_short+'_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_second_phase_ampphase_cal_solint_'+solint_short,
                kind='',xaxis='time',yaxis='phase',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_second_phase_ampphase_cal_solint_'+solint_short,
                kind='',xaxis='time',yaxis='amp',fields='')

            print('  >> Performing fluxscale scalling, from flux calibrator',flux_calibrator)
            print('     => Fluxscale from second phase > ampphase; solint= ',solint_short,' ...')
            flux_scale_phase_ampphase_short = fluxscale(vis=vis,
                caltable=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                fluxtable=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                reference=flux_calibrator,
                listfile=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.fluxinfo',
                transfer=[''],#not sure if using all ph cals
                incremental=False)
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_short,
                kind='',xaxis='time',yaxis='phase',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_short,
                kind='',xaxis='time',yaxis='amp',fields='')


        if calculate_mid_solint==True:
            print(' >> Performing second gain phases for all calibrators; solint=',solint_mid,'...')
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_second_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
                field=calibrators_all, refant=refant, spw=spw_central,
                calmode='p', solint=solint_mid, minsnr=minsnr,gaintype='G',
                # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    # base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+name+'.tb',   #K
                    base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_mid+'_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_second_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_second_phase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='phase',fields='')

            ## Delay Calibration
            print(' >> Performing delay calibraton: all calibrators ...')
            gaincal(vis=vis,caltable=base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_mid+'_'+name+'.tb',
                field=calibrators_all,refant=refant,spw=spw_skip_edge,gaintype='K',
                solint='inf',combine=combine,minsnr=minsnr,calmode='p',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    # base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_second_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_mid+'_'+name+'.tb'
                ])

            print(' >> Performing second gain phases>ampphase for all calibrators; solint=',solint_mid,'...')
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                field=calibrators_all, refant=refant, spw=spw_central,
                calmode='ap', solint=solint_mid, minsnr=minsnr,gaintype='G',
                # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_mid+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_second_phase_cal_solint_'+solint_mid+'_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_second_phase_ampphase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='phase',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_second_phase_ampphase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='amp',fields='')

            print('     => Fluxscale from second phase > ampphase; solint= ',solint_mid,' ...')
            flux_scale_phase_ampphase_mid = fluxscale(vis=vis,
                caltable=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                fluxtable=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                reference=flux_calibrator,
                listfile=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.fluxinfo',
                transfer=[''],#not sure if using all ph cals
                incremental=False)
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='phase',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='amp',fields='')

        
        if calculate_long_solint==True:
            ### Second pass of bandpass (for all calibrators)
            print(' >> Performing second gain phases for all calibrators; solint=',solint_long,'...')
            
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_second_phase_cal_solint_'+solint_long+'_'+name+'.tb',
                field=calibrators_all, refant=refant, spw=spw_central,
                calmode='p', solint=solint_long, minsnr=minsnr,gaintype='G',
                # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    # base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+name+'.tb',   #K
                    base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_long+'_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_second_phase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_second_phase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='phase',fields='')


            ## Delay Calibration
            print(' >> Performing delay calibraton: all calibrators ...')
            gaincal(vis=vis,caltable=base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_long+'_'+name+'.tb',
                field=calibrators_all,refant=refant,spw=spw_skip_edge,gaintype='K',
                solint='inf',combine=combine,minsnr=minsnr,calmode='p',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    # base_path+'calibration/'+str(i)+'_delay_calibration_scan_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_second_phase_cal_solint_'+solint_long+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_long+'_'+name+'.tb'
                ])

            print(' >> Performing second gain phases>ampphase for all calibrators; solint=',solint_long,'...')
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                field=calibrators_all, refant=refant, spw=spw_central,
                calmode='ap', solint=solint_long, minsnr=minsnr,gaintype='G',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_bandpass_calibration_'+solint_long+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_long+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_second_phase_cal_solint_'+solint_long+'_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_second_phase_ampphase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='phase',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_second_phase_ampphase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='amp',fields='')
            
            print('     => Fluxscale from second phase > ampphase; solint= ',solint_long,' ...')
            flux_scale_phase_ampphase_long = fluxscale(vis=vis,
                caltable=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                fluxtable=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                reference=flux_calibrator,
                listfile=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.fluxinfo',
                transfer=[''],#not sure if using all ph cals
                incremental=False)
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='phase',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='amp',fields='')



        if main_setjy_solint==solint_short:
            setjy(vis=vis, field=calibrators_all, scalebychan=True,
                standard = 'fluxscale', fluxdict=flux_scale_phase_ampphase_short)

        if main_setjy_solint==solint_mid:
            flux_scale_phase_ampphase_mid = fluxscale(vis=vis,
                caltable=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                fluxtable=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                reference=flux_calibrator,
                listfile=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.fluxinfo',
                transfer=[''],#not sure if using all ph cals
                incremental=False)
            setjy(vis=vis, field=calibrators_all, scalebychan=True,
                standard = 'fluxscale', fluxdict=flux_scale_phase_ampphase_mid)

        if main_setjy_solint==solint_long:
            setjy(vis=vis, field=calibrators_all, scalebychan=True,
                standard = 'fluxscale', fluxdict=flux_scale_phase_ampphase_long)


        '''
            Now, since we have update the model information with fluxscale,
            lets re-calculate the gains for the bandpass calibrator.

            The letters 'up' in the tables, mean 'update', so they may
            differ slightly from the previous tables. Previous tables are not
            used anymore.
        '''


        # if calculate_short_solint==True:
        print(' >> Performing updated initial gain phases...; solint=',solint_short)
        gaincal(vis=vis,
        caltable=base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_short+'_'+name+'.tb',
            field=bandpass_calibrator, refant=refant, spw=spw_central,
            calmode='p', solint=solint_short, minsnr=minsnr,gaintype='G',
            gaintable=[
                base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb'
            ]
            )
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_short+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_up_initial_phase_cal_solint_'+solint_short,
            kind='',xaxis='time',yaxis='phase',fields=[bandpass_calibrator])

        ## Delay Calibration
        print(' >> Performing updated delay calibraton: bandpass/flux calibrator;... solint=',solint_short)
        gaincal(vis=vis,caltable=base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
            field=bandpass_calibrator,refant=refant,spw=spw_skip_edge,gaintype='K',
            solint='inf',combine=combine,minsnr=minsnr,calmode='p',
            gaintable=[
                base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_short+'_'+name+'.tb'
            ])

        print(' >> Performing updated initial gain phase>ampphases for flux calibrator; solint,',solint_short)
        gaincal(vis=vis,
        caltable=base_path+'calibration/'+str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
            field=bandpass_calibrator, refant=refant, spw=spw_central,
            calmode='ap', solint=solint_short, minsnr=minsnr,gaintype='G',
            gaintable=[
                base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',   #K
                base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_short+'_'+name+'.tb'
            ]
            )
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_short,
            kind='',xaxis='time',yaxis='phase',fields=[bandpass_calibrator])
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_short,
            kind='',xaxis='time',yaxis='amp',fields=[bandpass_calibrator])

        print('     => Update bandpass for bandpass calibrator, from gains with solint=,',solint_short)
        bandpass(vis=vis,caltable=base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_short+'_'+name+'.tb',
            field=bandpass_calibrator,refant=refant,combine='scan', minsnr=minsnr,
            solint='inf',bandtype='B',
            gaintable=[
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_short+'_'+name+'.tb', #G0
                base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',   #K
                base_path+'calibration/'+str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb'
            ])
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_short+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_up_bandpass_calibration_'+solint_short,
            kind='',xaxis='chan',yaxis='amp',fields=[bandpass_calibrator])
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_short+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_up_bandpass_calibration_'+solint_short,
            kind='',xaxis='chan',yaxis='phase',fields=[bandpass_calibrator])

        if calculate_mid_solint==True:
            print(' >> Performing updated initial gain phases...; solint=',solint_mid)
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
                field=bandpass_calibrator, refant=refant, spw=spw_central,
                calmode='p', solint=solint_mid, minsnr=minsnr,gaintype='G',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_initial_phase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='phase',fields=[bandpass_calibrator])

            ## Delay Calibration
            print(' >> Performing updated delay calibraton: bandpass/flux calibrator;... solint=',solint_mid)
            gaincal(vis=vis,caltable=base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_mid+'_'+name+'.tb',
                field=bandpass_calibrator,refant=refant,spw=spw_skip_edge,gaintype='K',
                solint='inf',combine=combine,minsnr=minsnr,calmode='p',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_mid+'_'+name+'.tb'
                ])

            print(' >> Performing updated initial gain phase>ampphases for flux calibrator; solint,',solint_mid)
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                field=bandpass_calibrator, refant=refant, spw=spw_central,
                calmode='ap', solint=solint_mid, minsnr=minsnr,gaintype='G',
                # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_mid+'_'+name+'.tb',   #K
                    base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_mid+'_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='phase',fields=[bandpass_calibrator])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='amp',fields=[bandpass_calibrator])

            print('     => Update bandpass for bandpass calibrator, from gains with solint=,',solint_mid)
            bandpass(vis=vis,caltable=base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
                field=bandpass_calibrator,refant=refant,combine='scan', minsnr=minsnr,
                solint='inf',bandtype='B',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_mid+'_'+name+'.tb', #G0
                    base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_mid+'_'+name+'.tb',   #K
                    base_path+'calibration/'+str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb'
                ])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_bandpass_calibration_'+solint_mid,
                kind='',xaxis='chan',yaxis='amp',fields=[bandpass_calibrator])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_bandpass_calibration_'+solint_mid,
                kind='',xaxis='chan',yaxis='phase',fields=[bandpass_calibrator])

        if calculate_long_solint==True:
            print(' >> Performing updated initial gain phases...; solint=',solint_long)
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_long+'_'+name+'.tb',
                field=bandpass_calibrator, refant=refant, spw=spw_central,
                calmode='p', solint=solint_long, minsnr=minsnr,gaintype='G',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_initial_phase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='phase',fields=[bandpass_calibrator])

            ## Delay Calibration
            print(' >> Performing updated delay calibraton: bandpass/flux calibrator;... solint=',solint_long)
            gaincal(vis=vis,caltable=base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_long+'_'+name+'.tb',
                field=bandpass_calibrator,refant=refant,spw=spw_skip_edge,gaintype='K',
                solint='inf',combine=combine,minsnr=minsnr,calmode='p',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_long+'_'+name+'.tb'
                ])

            print(' >> Performing updated initial gain phase>ampphases for flux calibrator; solint,',solint_long)
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                field=bandpass_calibrator, refant=refant, spw=spw_central,
                calmode='ap', solint=solint_long, minsnr=minsnr,gaintype='G',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_long+'_'+name+'.tb',   #K
                    base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_long+'_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='phase',fields=[bandpass_calibrator])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='amp',fields=[bandpass_calibrator])

            print('     => Update bandpass for bandpass calibrator, from gains with solint=,',solint_long)
            bandpass(vis=vis,caltable=base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_long+'_'+name+'.tb',
                field=bandpass_calibrator,refant=refant,combine='scan', minsnr=minsnr,
                solint='inf',bandtype='B',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_initial_phase_cal_solint_'+solint_long+'_'+name+'.tb', #G0
                    base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',   #K
                    base_path+'calibration/'+str(i)+'_up_initial_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb'
                ])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_bandpass_calibration_'+solint_long,
                kind='',xaxis='chan',yaxis='amp',fields=[bandpass_calibrator])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_bandpass_calibration_'+solint_long,
                kind='',xaxis='chan',yaxis='phase',fields=[bandpass_calibrator])


        '''
        Now, do the same for all calibrators, with the new update tables
        for the bandpass.

        Now the solint will be calculated as it is requested by the user
        in the config session.
        '''


        # Short solution for phases should be calculated. Needed later...
        print(' >> Performing second gain phases for all calibrators (all cals); solint=',solint_short,'...')
        gaincal(vis=vis,
        caltable=base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_short+'_'+name+'.tb',
            field=calibrators_all, refant=refant, spw=spw_central,
            calmode='p', solint=solint_short, minsnr=minsnr,gaintype='G',
            gaintable=[
                base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                # base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_short+'_'+name+'.tb'
            ]
            )
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_short+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_up_second_phase_cal_solint_'+solint_short,
            kind='',xaxis='time',yaxis='phase',fields='')

        if calculate_short_solint==True:
            print(' >> Performing second gain phases>ampphase for all calibrators; solint=',solint_short,'...')
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                field=calibrators_all, refant=refant, spw=spw_central,
                calmode='ap', solint=solint_short, minsnr=minsnr,gaintype='G',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_short+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',   #K
                    # base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_short+'_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_short,
                kind='',xaxis='time',yaxis='phase',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_short,
                kind='',xaxis='time',yaxis='amp',fields='')


            print('     => Update bandpass for all calibrators, from gains with solint=,',solint_short)
            bandpass(vis=vis,caltable=base_path+'calibration/'+str(i)+'_up_second_bandpass_calibration_'+solint_short+'_'+name+'.tb',
                field=calibrators_all,refant=refant,combine='scan', minsnr=minsnr,
                solint='inf',bandtype='B',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_short+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                    # base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_short+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb'
                ])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_bandpass_calibration_'+solint_short+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_bandpass_calibration_'+solint_short,
                kind='',xaxis='chan',yaxis='amp',fields=[bandpass_calibrator])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_bandpass_calibration_'+solint_short+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_bandpass_calibration_'+solint_short,
                kind='',xaxis='chan',yaxis='phase',fields='')


            print('     => Fluxscale update from second phase > ampphase; solint= ',solint_short,' ...')
            flux_scale_phase_ampphase_short_up = fluxscale(vis=vis,
                caltable=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                fluxtable=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                reference=flux_calibrator,
                listfile=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.fluxinfo',
                transfer=[''],#not sure if using all ph cals
                incremental=False)
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_short,
                kind='',xaxis='time',yaxis='phase',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_short,
                kind='',xaxis='time',yaxis='amp',fields='')

        if calculate_mid_solint==True:

            print(' >> Performing second gain phases for all calibrators (all cals); solint=',solint_mid,'...')
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
                field=calibrators_all, refant=refant, spw=spw_central,
                calmode='p', solint=solint_mid, minsnr=minsnr,gaintype='G',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_mid+'_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_phase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='phase',fields='')

            print(' >> Performing second gain phases>ampphase for all calibrators; solint=',solint_mid,'...')
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                field=calibrators_all, refant=refant, spw=spw_central,
                calmode='ap', solint=solint_mid, minsnr=minsnr,gaintype='G',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                    # base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_mid+'_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='phase',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='amp',fields='')


            print('     => Update bandpass for all calibrators, from gains with solint=,',solint_mid)
            bandpass(vis=vis,caltable=base_path+'calibration/'+str(i)+'_up_second_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
                field=calibrators_all,refant=refant,combine='scan', minsnr=minsnr,
                solint='inf',bandtype='B',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_mid+'_'+name+'.tb',
                    # base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_mid+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb'
                ])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_bandpass_calibration_'+solint_mid,
                kind='',xaxis='chan',yaxis='amp',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_bandpass_calibration_'+solint_mid,
                kind='',xaxis='chan',yaxis='phase',fields='')

            print('     => Fluxscale update from second phase > ampphase; solint= ',solint_mid,' ...')
            flux_scale_phase_ampphase_mid_up = fluxscale(vis=vis,
                caltable=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                fluxtable=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                reference=flux_calibrator,
                listfile=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.fluxinfo',
                transfer=[''],#not sure if using all ph cals
                incremental=False)
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='phase',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_mid,
                kind='',xaxis='time',yaxis='amp',fields='')



        if calculate_long_solint==True:
            print(' >> Performing second gain phases for all calibrators (all cals); solint=',solint_long,'...')
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_long+'_'+name+'.tb',
                field=calibrators_all, refant=refant, spw=spw_central,
                calmode='p', solint=solint_long, minsnr=minsnr,gaintype='G',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_short+'_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_phase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='phase',fields='')

            print(' >> Performing second gain phases>ampphase for all calibrators; solint=',solint_long,'...')
            gaincal(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                field=calibrators_all, refant=refant, spw=spw_central,
                calmode='ap', solint=solint_long, minsnr=minsnr,gaintype='G',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_short+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                    # base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_long+'_'+name+'.tb'
                ]
                )
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='phase',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='amp',fields='')

            print('     => Update bandpass for all calibrators, from gains with solint=,',solint_long)
            bandpass(vis=vis,caltable=base_path+'calibration/'+str(i)+'_up_second_bandpass_calibration_'+solint_long+'_'+name+'.tb',
                field=calibrators_all,refant=refant,combine='scan', minsnr=minsnr,
                solint='inf',bandtype='B',
                gaintable=[
                    base_path+'calibration/antpos_'+name+'.tb',
                    base_path+'calibration/gaincurve_gc_'+name+'.tb',
                    base_path+'calibration/opacity_'+name+'.tb',
                    base_path+'calibration/rq_'+name+'.tb',
                    base_path+'calibration/swpow_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_long+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_long+'_'+name+'.tb',
                    # base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_long+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_long+'_'+name+'.tb',
                    base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb'
                ])
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_bandpass_calibration_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_bandpass_calibration_'+solint_long,
                kind='',xaxis='chan',yaxis='amp',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_bandpass_calibration_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_up_second_bandpass_calibration_'+solint_long,
                kind='',xaxis='chan',yaxis='phase',fields='')

            print('     => Fluxscale update from second phase > ampphase; solint= ',solint_mid,' ...')
            flux_scale_phase_ampphase_long_up = fluxscale(vis=vis,
                caltable=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                fluxtable=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                reference=flux_calibrator,
                listfile=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.fluxinfo',
                transfer=[''],#not sure if using all ph cals
                incremental=False)
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='phase',fields='')
            calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_long+'_'+name+'.tb',
                stage='calibration',
                table_type=str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_long,
                kind='',xaxis='time',yaxis='amp',fields='')

        # apply_precal()
        # split_calibrators()
        summary_cal_init = flagdata(vis=vis,mode='summary')
        print('Finished calibrations...')
        return(summary_cal_init,i)



    def final_scan_averaged_gains(i,solint_main,solint_final='inf'):
        ## Scan averaged gains
        print(' >> Performing final avaraged gain phases (all cals); solint=inf ...')
        gaincal(vis=vis,
        caltable=base_path+'calibration/'+str(i)+'_up_second_phase_cal_average_solint_'+solint_final+'_'+name+'.tb',
            field=calibrators_all, refant=refant, spw=spw_central,combine=combine,
            calmode='p', solint=solint_final, minsnr=minsnr,gaintype='G',
            gaintable=[
                base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                # base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_main+'_'+name+'.tb'
            ]
            )
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_cal_average_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_up_second_phase_cal_average_solint_'+solint_final,
            kind='',xaxis='time',yaxis='phase',fields='')



        print(' >> Performing final averaged gain phases>ampphase (from inf phases gains); solint=inf...')
        gaincal(vis=vis,
        caltable=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_average_solint_'+solint_final+'_'+name+'.tb',
            field=calibrators_all, refant=refant, spw=spw_central,combine=combine,
            calmode='ap', solint=solint_final, minsnr=minsnr,gaintype='G',
            gaintable=[
                base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_second_phase_cal_average_solint_'+solint_final+'_'+name+'.tb'
            ]
            )
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_average_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_up_second_phase_ampphase_cal_average_solint_'+solint_final,
            kind='',xaxis='time',yaxis='phase',fields='')
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_average_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_up_second_phase_ampphase_cal_average_solint_'+solint_final,
            kind='',xaxis='time',yaxis='amp',fields='')


        print(' >> Performing final averaged gain phases>ampphase (from short phases gains); solint=inf...')
        gaincal(vis=vis,
        caltable=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_short_average_solint_'+solint_final+'_'+name+'.tb',
            field=calibrators_all, refant=refant, spw=spw_central,combine=combine,
            calmode='ap', solint=solint_final, minsnr=minsnr,gaintype='G',
            gaintable=[
                base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_main+'_'+name+'.tb'
            ]
            )
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_short_average_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_up_second_phase_ampphase_cal_short_average_solint_'+solint_final,
            kind='',xaxis='time',yaxis='phase',fields='')
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_short_average_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_up_second_phase_ampphase_cal_short_average_solint_'+solint_final,
            kind='',xaxis='time',yaxis='amp',fields='')

        print('     => Fluxscale update from final averaged phase(inf) > ampphase(inf); solint=inf ...')
        flux_scale_phase_ampphase_inf = fluxscale(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_average_solint_'+solint_final+'_'+name+'.tb',
            fluxtable=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_average_solint_'+solint_final+'_'+name+'.tb',
            reference=flux_calibrator,
            listfile=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_average_solint_'+solint_final+'_'+name+'.fluxinfo',
            transfer=[''],#not sure if using all ph cals
            incremental=False)
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_average_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_flux_scale_up_second_phase_ampphase_cal_average_solint_'+solint_final,
            kind='',xaxis='time',yaxis='phase',fields='')
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_average_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_flux_scale_up_second_phase_ampphase_cal_average_solint_'+solint_final,
            kind='',xaxis='time',yaxis='amp',fields='')


        print('     => Fluxscale update from final averaged phase(short) > ampphase(inf); solint=inf ...')
        flux_scale_phase_ampphase_inf = fluxscale(vis=vis,
            caltable=base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_short_average_solint_'+solint_final+'_'+name+'.tb',
            fluxtable=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_short_average_solint_'+solint_final+'_'+name+'.tb',
            reference=flux_calibrator,
            listfile=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_short_average_solint_'+solint_final+'_'+name+'.fluxinfo',
            transfer=[''],#not sure if using all ph cals
            incremental=False)
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_short_average_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_flux_scale_up_second_phase_ampphase_cal_short_average_solint_'+solint_final,
            kind='',xaxis='time',yaxis='phase',fields='')
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_short_average_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_flux_scale_up_second_phase_ampphase_cal_short_average_solint_'+solint_final,
            kind='',xaxis='time',yaxis='amp',fields='')

        print('     =>  Ended calculation of final averaged gains....')
        pass



    def final_gain_calibration(i,solint_main,solint_final):
        """
            Calculate gains calibration after obtained bandpass and corrections for
            iteraction i.
        """

        print('Performing final gains calibration for phase and amplitude.')
        # print('  >> This gain refers to iteration',j,' of intial gains computations.')
        # print('  >> Setting the model for the flux calibrator...')
        # print('     -> Model is',model_setjy)
        # setjy(vis=vis,
        #     field=flux_calibrator,spw='',
        #     selectdata=False,
        #     model=model_setjy,scalebychan=True,
        #     standard='Perley-Butler 2017',
        #     listmodels=False, usescratch=False)
        # print('  >> Calibrators to work with:',calibrators_all)


        print(' >> Performing second gain phases for all calibrators (all cals); solint=',solint_final,'...')
        gaincal(vis=vis,
        caltable=base_path+'calibration/'+str(i)+'_final_phases_cal_solint_'+solint_final+'_'+name+'.tb',
            field=calibrators_all, refant=refant, spw=spw_central,combine='',
            calmode='p', solint=solint_final, minsnr=minsnr,gaintype='G',
            gaintable=[
                # base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
                # base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_main+'_'+name+'.tb'
            ]
            )
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_final_phases_cal_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_final_phases_cal_solint_'+solint_final,
            kind='',xaxis='time',yaxis='phase',fields='')


        print(' >> Performing second gain phases for all calibrators (all cals); solint=',solint_main,'...')
        gaincal(vis=vis,
        caltable=base_path+'calibration/'+str(i)+'_final_phases_cal_solint_'+solint_main+'_'+name+'.tb',
            field=calibrators_all, refant=refant, spw=spw_central,combine='',
            calmode='p', solint=solint_main, minsnr=minsnr,gaintype='G',
            gaintable=[
                # base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_main+'_'+name+'.tb',
                # base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_main+'_'+name+'.tb'
            ]
            )
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_final_phases_cal_solint_'+solint_main+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_final_phases_cal_solint_'+solint_main,
            kind='',xaxis='time',yaxis='phase',fields='')


        print(' >> Performing second gain phases>ampphase for all calibrators; solint=',solint_final,'...')
        gaincal(vis=vis,
        caltable=base_path+'calibration/'+str(i)+'_final_phases_amplitudes_cal_solint_'+solint_final+'_'+name+'.tb',
            field=calibrators_all, refant=refant, spw=spw_central,combine='',
            calmode='ap', solint=solint_final, minsnr=minsnr,gaintype='G',
            # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
            gaintable=[
                # base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_main+'_'+name+'.tb',
                # base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_final_phases_cal_solint_'+solint_main+'_'+name+'.tb',
            ]
            )
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_final_phases_amplitudes_cal_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_final_phases_amplitudes_cal_solint_'+solint_final,
            kind='',xaxis='time',yaxis='phase',fields='')
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_final_phases_amplitudes_cal_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_final_phases_amplitudes_cal_solint_'+solint_final,
            kind='',xaxis='time',yaxis='amp',fields='')


        print(' >> Performing second gain phases>ampphase for all calibrators; solint=',solint_final,'...')
        gaincal(vis=vis,
        caltable=base_path+'calibration/'+str(i)+'_final_average_phases_amplitudes_cal_solint_'+solint_final+'_'+name+'.tb',
            field=calibrators_all, refant=refant, spw=spw_central,combine='',
            calmode='ap', solint=solint_final, minsnr=minsnr,gaintype='G',
            # gaintable=[base_path+'calibration/'+'antpos_'+name+'.tb']
            gaintable=[
                # base_path+'calibration/antpos_'+name+'.tb',
                base_path+'calibration/gaincurve_gc_'+name+'.tb',
                base_path+'calibration/opacity_'+name+'.tb',
                base_path+'calibration/rq_'+name+'.tb',
                base_path+'calibration/swpow_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_main+'_'+name+'.tb',
                # base_path+'calibration/'+str(i)+'_second_delay_calibration_scan_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_main+'_'+name+'.tb',
                base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_main+'_'+name+'.tb',
                # base_path+'calibration/'+str(i)+'_final_phases_cal_solint_'+solint_main+'_'+name+'.tb',
            ]
            )
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_final_average_phases_amplitudes_cal_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_final_average_phases_amplitudes_cal_solint_'+solint_final,
            kind='',xaxis='time',yaxis='phase',fields='')
        calibration_table_plot(table=base_path+'calibration/'+str(i)+'_final_average_phases_amplitudes_cal_solint_'+solint_final+'_'+name+'.tb',
            stage='calibration',
            table_type=str(i)+'_final_average_phases_amplitudes_cal_solint_'+solint_final,
            kind='',xaxis='time',yaxis='amp',fields='')
        #
        #
        # print('  >> Performing fluxscale scalling, from flux calibrator',flux_calibrator)
        #
        # print('     => Fluxscale from final phase > ampphase; solint= ',solint,' ...')
        # flux_scale_phase_ampphase = fluxscale(vis=vis,
        #     caltable=base_path+'calibration/'+str(i)+'_phase_ampphase_gain_calibration_scan_'+solint+'_'+name+'.tb',
        #     fluxtable=base_path+'calibration/'+str(i)+'_flux_scale_phase_ampphase_scan_'+solint+'_'+name+'.tb',
        #     reference=flux_calibrator,
        #     listfile=base_path+'calibration/'+str(i)+'_flux_scale_phase_ampphase_scan_'+solint+'_'+str(flux_calibrator)+'_'+name+'.fluxinfo',
        #     transfer=[''],#not sure if using all ph cals
        #     incremental=False)
        #
        #
        # print('     => Fluxscale from initial phase > ampphase; solint= ',solint,' ...')
        # flux_scale_phase_ampphase = fluxscale(vis=vis,
        #     caltable=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint+'_'+name+'.tb',
        #     fluxtable=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_scan_'+solint+'_'+name+'.tb',
        #     reference=flux_calibrator,
        #     listfile=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_scan_'+solint+'_'+str(flux_calibrator)+'_'+name+'.fluxinfo',
        #     transfer=[''],#not sure if using all ph cals
        #     incremental=False)
        #
        #
        # print('     => Fluxscale from initial phase > ampphase; solint= ',solint_mid,' ...')
        # flux_scale_phase_ampphase = fluxscale(vis=vis,
        #     caltable=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
        #     fluxtable=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_scan_'+solint_mid+'_'+name+'.tb',
        #     reference=flux_calibrator,
        #     listfile=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_scan_'+solint_mid+'_'+str(flux_calibrator)+'_'+name+'.fluxinfo',
        #     transfer=[''],#not sure if using all ph cals
        #     incremental=False)
        #
        #
        # print('     => Fluxscale from initial phase > ampphase; solint= ',solint_short,' ...')
        # flux_scale_phase_ampphase = fluxscale(vis=vis,
        #     caltable=base_path+'calibration/'+str(i)+'_second_phase_ampphase_cal_solint_'+solint_short+'_'+name+'.tb',
        #     fluxtable=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_scan_'+solint_short+'_'+name+'.tb',
        #     reference=flux_calibrator,
        #     listfile=base_path+'calibration/'+str(i)+'_flux_scale_second_phase_ampphase_scan_'+solint_short+'_'+str(flux_calibrator)+'_'+name+'.fluxinfo',
        #     transfer=[''],#not sure if using all ph cals
        #     incremental=False)
        pass



    def apply_calibration(i,solint_main,solint_final='inf'):
        """
            Apply calibration tables.

            DEV: Need to fix cases where there are multiple calibrators.
            Should apply to each calibrator < - > target per time, not all
            of them at once.
        """

        print('Creating flag-backup before applying calibration.')
        flagmanager(vis=vis,mode='save',versionname='before_final_cal_'+str(i),
            comment='Flags before apply calibration, iteraction'+str(i)+'.')

        print('Applying calibration tables to data.')
        # setjy(vis=vis, field=flux_calibrator, scalebychan=True,
              # standard = 'fluxscale', fluxdict=myscale)
        # print(' >> Applying calibration on flux calibrator',flux_calibrator,' ...')

        print('     => Reporting calibrators data flagged before calibration.')
        summary_calibrators_before = flagdata(vis=vis,
            mode='summary',field=calibrators_all,datacolumn='data')
        report_flag(summary_calibrators_before,'field')
        #
        # tables_to_apply = [
        #     base_path+'calibration/gaincurve_gc_'+name+'.tb',
        #     base_path+'calibration/opacity_'+name+'.tb',
        #     base_path+'calibration/rq_'+name+'.tb',
        #     base_path+'calibration/swpow_'+name+'.tb',
        #     base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_short+'_'+name+'.tb',
        #     base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_short+'_'+name+'.tb',
        #     base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
        #     base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
        #     # base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+'inf_scan'+'_'+name+'.tb'
        # ]

        # tables_to_apply = [
        #     #base_path+'calibration/antpos_'+name+'.tb',
        #     base_path+'calibration/gaincurve_gc_'+name+'.tb',
        #     base_path+'calibration/opacity_'+name+'.tb',
        #     base_path+'calibration/rq_'+name+'.tb',
        #     base_path+'calibration/swpow_'+name+'.tb',
        #     base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_mid+'_'+name+'.tb',
        #     base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
        #     # base_path+'calibration/'+str(i)+'_up_second_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
        #     base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
        #     base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
        #     # base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+'inf'+'_'+name+'.tb'
        #     # base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
        #     base_path+'calibration/'+str(i)+'_final_phases_cal_solint_'+'inf'+'_'+name+'.tb',
        #     base_path+'calibration/'+str(i)+'_final_phases_amplitudes_cal_solint_'+'inf'+'_'+name+'.tb'
        #     ]

        tables_to_apply_calibrators = [
            base_path+'calibration/antpos_'+name+'.tb',
            base_path+'calibration/gaincurve_gc_'+name+'.tb',
            base_path+'calibration/opacity_'+name+'.tb',
            base_path+'calibration/rq_'+name+'.tb',
            base_path+'calibration/swpow_'+name+'.tb',
            base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_main+'_'+name+'.tb',
            base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_main+'_'+name+'.tb',
            base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_main+'_'+name+'.tb',
            base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_main+'_'+name+'.tb'
            ]

        applycal(vis=vis,
            field=calibrators_all,
            gaintable=tables_to_apply_calibrators,
            gainfield=[''],
            interp=[''],
            calwt=True,flagbackup=False,applymode='calflag')

        print('     => Reporting calibrators data flagged after calibration.')
        summary_calibrators_after = flagdata(vis=vis,
            mode='summary',field=calibrators_all,datacolumn='data')
        report_flag(summary_calibrators_after,'field')

        print('     => Reporting targets data flagged before calibration.')
        summary_targets_before = flagdata(vis=vis,
            mode='summary',field=target_fields,datacolumn='data')
        report_flag(summary_targets_before,'field')

        tables_to_apply_targets = [
            base_path+'calibration/antpos_'+name+'.tb',
            base_path+'calibration/gaincurve_gc_'+name+'.tb',
            base_path+'calibration/opacity_'+name+'.tb',
            base_path+'calibration/rq_'+name+'.tb',
            base_path+'calibration/swpow_'+name+'.tb',
            base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_main+'_'+name+'.tb',
            base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_main+'_'+name+'.tb',
            # base_path+'calibration/'+str(i)+'_up_second_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
            # base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
            # base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
            base_path+'calibration/'+str(i)+'_up_second_phase_cal_average_solint_'+solint_final+'_'+name+'.tb',
            base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_average_solint_'+solint_final+'_'+name+'.tb'
            ]

        #now do the same for the target fields.
        for k in range(len(target_fields_arr)):
            TARGET_FIELD = target_fields_arr[k]
            PHASE_CAL_TO_TARGET = phase_calibrators_all_arr[k]
            print(' >> Applying calibration on target field',TARGET_FIELD,' ...')

            applycal(vis=vis,
                field=TARGET_FIELD,
                gaintable=tables_to_apply_targets,
                gainfield=['','','','','',
                    bandpass_calibrator,bandpass_calibrator,
                    PHASE_CAL_TO_TARGET,PHASE_CAL_TO_TARGET],
                interp=['','','','','','','','',''],#not sure about nearest
                calwt=True,flagbackup=False
                # flagbackup=False,applymode='calflagstrict'
                )

        print('     => Reporting targets data flagged after calibration.')
        summary_targets_after = flagdata(vis=vis,
            mode='summary',field=target_fields,datacolumn='data')
        report_flag(summary_targets_after,'field')

        print('Creating flag-backup after applying calibration.')
        flagmanager(vis=vis,mode='save',versionname='after_final_cal_'+str(i),
            comment='Flags after apply calibration, iteraction'+str(i)+'.')


        print(' >> Finished to apply calibration.')

    i=1
    summary_1st_cal,j = gain_calibration(vis,calibrators_all,
        flux_calibrator,phase_calibrators_all,i,
        refant,spw_central,spw_skip_edge,
        auto_flag_data = True)




    '''
    Now that we performed two iteractions, lets use the most recent tables
    to calculate the last and final gain calibration tables (incremental).
    These should be around unity for amplitude and zero for phases.
    So, check them. If that is not the case you must look for bad data, manually,
    and evaluate if one more iteraction is needed, or if that data must be removed.
    '''

    j=i

    tables_to_apply = [
        base_path+'calibration/antpos_'+name+'.tb',
        base_path+'calibration/gaincurve_gc_'+name+'.tb',
        base_path+'calibration/opacity_'+name+'.tb',
        base_path+'calibration/rq_'+name+'.tb',
        base_path+'calibration/swpow_'+name+'.tb',
        base_path+'calibration/'+str(i)+'_up_delay_calibration_scan_'+solint_mid+'_'+name+'.tb',
        base_path+'calibration/'+str(i)+'_up_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
        # base_path+'calibration/'+str(i)+'_up_second_bandpass_calibration_'+solint_mid+'_'+name+'.tb',
        base_path+'calibration/'+str(i)+'_up_second_phase_cal_solint_'+solint_mid+'_'+name+'.tb',
        base_path+'calibration/'+str(i)+'_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
        # base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+'inf'+'_'+name+'.tb'
        # base_path+'calibration/'+str(i)+'_flux_scale_up_second_phase_ampphase_cal_solint_'+solint_mid+'_'+name+'.tb',
        # base_path+'calibration/'+str(i)+'_final_phases_cal_solint_'+'inf'+'_'+name+'.tb',
        # base_path+'calibration/'+str(i)+'_final_average_phases_amplitudes_cal_solint_'+'inf'+'_'+name+'.tb'
        ]

    if auto_flag_data == True:
        if extended_flag_backups==1:
            print('    ** Creating flag backup before autoflagging...')
            flagmanager(vis=vis,mode='save',versionname='pre_calibration_before_autoflag_iteraction_'+str(i),
                comment='Flagbackup before autoflag/pre-calibration iteration '+str(i))
        # flag_with_rflag = False
        if flag_with_rflag == True:
            apply_rflag(tables_to_apply=tables_to_apply,i=i,applied_cal=False)
        if flag_with_tfcrop == True:
            apply_tfcrop(i=i,applied_cal=False)

        if extended_flag_backups==1:
            print('    ** Creating flag backup after autoflagging...')
            flagmanager(vis=vis,mode='save',versionname='pre_calibration_after_autoflag_iteraction_'+str(i),
                comment='Flagbackup after autoflag/pre-calibration iteration '+str(i))

    """
        If using rflag to flag the data, we should perform
        one more iteraction, so that new gains and calibration
        tables are computed according to the new data that was flagged, which
        in principle may result in better calibrations, but it is not
        specifically true for all the cases.

        Initial tests should be made by applying rflag and inspecting results,
        without the need of recomputing the tables.

    """
    # Uncomment the block bellow if you would like to perform all calibration
    # again after the first pass of calibration and automatic flagging. This
    # should improve the calibration a little, not guarantee, but take care
    # to not flagging to much data. Target fields are not affected though.
    '''
    i=2 #should not run rflag or tfcrop again. Might flag more data than needed.
    summary_2nd_cal,j = gain_calibration(vis,calibrators_all,
        flux_calibrator,phase_calibrators_all,i,
        refant,spw_central,spw_skip_edge,
        auto_flag_data = False)
    '''

    solint_final = solint_long
    final_scan_averaged_gains(i=j,solint_main=solint_main,solint_final=solint_final)
    # # final_gain_calibration(i=j,solint_main=solint_main,solint_final=solint_final)
    apply_calibration(i=j,solint_main=solint_main,solint_final=solint_final)
    calibration_time = time.time() - calibration_starttime
    print('Exec time for calibration =',calibration_time,'s')
    return(j)
    pass

def final_auto_flag():
    print(
        '     => Saving flags before final flagging.')
    flagmanager(vis=vis,mode='save',
        versionname='after_final_cal',
        comment='Flags after apply calibration. This is before any \
                 additional flagging to the full target corrected data.')

    print('     => Reporting data flagged after final cal and before final flagging...')
    summary_after_final_cal = flagdata(vis=vis, mode='summary')
    report_flag(summary_after_final_cal,'field')

    flagdata(vis=vis,mode='rflag',field=target_fields,spw='',display='report',
        datacolumn='corrected', ntime='scan', combinescans=False,
        extendflags=False,winsize=7, timedevscale=3.5, freqdevscale=3.5,
        flagnearfreq=False,flagneartime=False,growaround=True,
        timecutoff=2.5,freqcutoff=2.5,
        action='apply', flagbackup=False, savepars=True
        )

    # flagdata(vis=vis,mode='tfcrop',field=all_fields,spw='',display='both',
    #     datacolumn='corrected', ntime='scan', combinescans=False,
    #     extendflags=False,winsize=7, timedevscale=4.5, freqdevscale=4.5,
    #     flagnearfreq=False,
    #     flagneartime=False,growaround=True,timecutoff=2.0,freqcutoff=1.0,
    #     action='calculate', flagbackup=False, savepars=True,
    #     )

    flagdata(vis=vis,mode='extend',field=target_fields,spw='',display='report',
        action='apply',datacolumn='corrected', combinescans=False,flagbackup=False,
        growtime=75.0,growfreq=75.0,extendpols=True)
    flagmanager(vis=vis,mode='save',
        versionname='after_final_cal_flags',
        comment='Flags after apply calibration. \
        This is after any additional flagging to the full target corrected data.')

    print('     => Reporting data flagged after final cal and after final flagging...')
    summary_after_final_cal_flag = flagdata(vis=vis, mode='summary')
    report_flag(summary_after_final_cal_flag,'field')

    pass


# Split
def split_fields():
    print('Spliting measurement file into separated fields...')
    if not os.path.exists(base_path+'fields/'):
        os.makedirs(base_path+'fields/')

    def split_ms(field):
        if not os.path.exists(base_path+'fields/'+field):
            os.makedirs(base_path+'fields/'+field)

        g_name = base_path+'fields/'+field+'/'+field+'.calibrated'
        g_vis = g_name + '.ms'
        split(vis=vis,outputvis=g_vis,field=field,datacolumn='corrected')
        statwt(vis=g_vis,datacolumn='data')

        flagmanager(vis=g_vis,mode='save',versionname='Original',
            comment='Original flags from split after calibration.')

    # targets_to_split = ['UGC08387','MCG+07-23-019','IRASF08572+391','UGC05101',
    #     'UGC08058','VV340a','VV250a','UGC08696','NGC3690','VV705','UGC04881',
    #     'UGC09913','IRASF15250+360','IRASF17132+531']
    targets_to_split = target_fields_arr

    for TT in targets_to_split:
        print(' >> Spliting field',TT)
        split_ms(TT)

def basic_imaging(threshold='1.0e-4Jy',niter=10000,
    cell='0.03arcsec',SIZE = 3072,
    deconvolver='multiscale',scales=[0,2,5,10,20,50],
    smallscalebias=0.9):
    imaging_starttime = time.time()
    print('Performing basic imaging on data fields...')
    if not os.path.exists(base_path+'imaging/'):
        os.makedirs(base_path+'imaging/')

    def image_calibrators():
        for F in calibrators_all:
            print(' >> Imaging calibrator field',F)
            SIZE = 1024
            imagename=base_path+'imaging/field_'+F+'_'+str(SIZE)+'_3K.0.05arcsec.natural'
            tclean(vis=vis, imagename=imagename,imsize=SIZE,
                cell='0.05arcsec', pblimit=-0.01, niter=3000,stokes='I',
                savemodel='none',field=F,datacolumn='corrected',weighting='natural',
                antenna='',spw='')
            exportfits(imagename=imagename+'.image',fitsimage=imagename+'.fits',
                velocity=True)

    def image_targets():
        unit = 'mJy'
        rms_std_factor = 3
        #rms_level = 0.037 #Natural
        rms_level = 0.044 #Robust
        rms_std = str(rms_level/rms_std_factor)+unit
        # threshold =  rms_std

        for F in target_fields_arr:
            g_name = base_path+'fields/'+F+'/'+F+'.calibrated'
            g_vis = g_name + '.ms'
            print(' >> Imaging target field',F)

            imagename=base_path+'imaging/field_'+F+'_'+str(SIZE)+'_30K.0.03arcsec.multiscale.natural'
            tclean(vis=g_vis, imagename=imagename,imsize=SIZE,
                cell=cell, pblimit=-0.01, niter=niter,stokes='I',
                savemodel='none',field=F,datacolumn='corrected',
                weighting='briggs',robust=1.0,
                antenna='',spw='',
                deconvolver=deconvolver,scales=scales,
                smallscalebias=smallscalebias,pbcor=True,threshold=threshold)

            exportfits(imagename=imagename+'.image',fitsimage=imagename+'.fits',
                velocity=True)

            imagename=base_path+'imaging/field_'+F+'_'+str(SIZE)+'_3K.0.03arcsec.multiscale.briggs'
            tclean(vis=g_vis, imagename=imagename,imsize=SIZE,
                cell=cell, pblimit=-0.01, niter=niter,stokes='I',
                savemodel='none',field=F,datacolumn='corrected',
                weighting='briggs',robust=1.0,
                antenna='',spw='',
                deconvolver=deconvolver,scales=scales,
                smallscalebias=smallscalebias,pbcor=True,threshold=threshold)

            exportfits(imagename=imagename+'.image',fitsimage=imagename+'.fits',
                velocity=True)


    image_calibrators()
    image_targets()
    imaging_time = time.time() - imaging_starttime
    print('Exec time for basic imaging=',imaging_time,'s')

# config()

data_handle()

make_plots_stages(stage='before',kind='before_tfcrop_init',FIELDS=fields_test_plot,plot_all_uv=False)
# #
initial_flagging()
#
make_plots_stages(stage='before',kind='after_tfcrop_init',FIELDS=fields_test_plot,plot_all_uv=False)
initial_corrections()
# #
# #
# """
# calibration()
#
#
# # make_plots_stages(stage='after',kind='after_rflag_and_cal',FIELDS=fields_test_plot)
# """
# make_plots_stages(stage='after',kind='after_cal_before_rflag',FIELDS=target_fields)
#
# add_final_auto_flags = True
# if add_final_auto_flags == True:
#     '''
#         Apply autoflag to target fields.
#     '''
#     final_auto_flag()
#
# split_fields()
#
# # make_plots_stages(stage='after',kind='final',FIELDS=target_fields_arr,plot_all_uv=False)
# # basic_imaging()

exec_time = time.time() - startTime
print('Exec time for pipeline=',exec_time,'s')

# exit()


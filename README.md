           '                                                
           '                                 .;okOk;        
                                         .;xKWMMMMMMc.      
                .                     .:ONMMMMMMMMMM0:.     
                                    'xNMMMMMMMMMMMMWOO;     
                                 .cKMMMMMMWNNXWMMMMK0Xo.    
                               .dNMMNXXOdx,;..'lXMKWNOk,    
                           ..'l0K0x::.. ,.. . .. 00NWWk;    
                    ,cl,;;';0WXx;.. . .;.  . . .kNX0N0Ol    
                   lKMXxod0Koc::;c;',.;.  . . lN0NWKWKx,    
                  'o :x;k0lo,. . ...clc:.. ..oNNONXKdc,.    
                  k  :xKk.  .,::,..,. ..::ccXWKMWKNKo;;.    
                 d. ,ol.'d    .;00kl,. . lkXNKKkXKNok::     
                :c':.o, .,c  ,oxxc':ldodWNNNXWKMK0;.k''     
               .0c...k . .l,.;x:';:ccO0NNKKNXxKNKllOl'      
               O' . 'd. . :c'. ':::kWMMXNXNXNMK0c.;l'.      
             .k..  .:c ,', . . ..kNOKNNNXx0NNKk .o:'.       
           .dO,. . .k;;.. . . ;OMMMKMXXNN0XNd.X0xc'.        
          ,KXl..,,,,x. . . 'dNKNNNWKNNNXNKXc  0XWX,.        
         lWMMMNNxo;;x . .c0NNMKMMNXOXNWN0;l0c00NK::         
       .xMMMMMMMMMMMWKdo0XWWWXO0XNNMN0o;X..XONWN;;          
      .kMMMMMMMMMMX0KKNMN0NNNNN0NXOddl,.kxk00dxKOx.         
      '0MMMMWNKKK0XX0KKNN0NNNXXx;.;dd,;coKMMMxOMMM0.        
       .,cccx0x0WNKOKXX00xo;co,;c:'..  ;XMMMMxOMMMMX,       
           ...,;'',loc;;.c,'...       lWMMMMMxOMMMMMNc      
                  .                 .xMMMMMMMxOMMMMMMMd.    
                                 .',lddddddddoxddxxxxxxl;,, 
                                           ..',;clodxkO0.   
                             ..',:codkO0XNWMMMMMMMMMMMMM'   
                    .';ldOKWMMMMMMMMMMMMMMMMMMMMMMMMMMMW0do,

# Synphly
`Synphly` is a simple CASA-EVLA pipeline for radio Interferometric standard data calibration, 
plotting and basic imaging. This pipeline was motivated by the need for calibrating early EVLA 
observations, where the official EVLA pipeline fails. `Synphly` can be used, in principle, for 
any EVLA observations. 

WARNING: This code and documentation is under development. Calibration may or may not work 
depending on your data. It has been tested in EVLA visibilities ONLY. 
We have been using it to calibrate observations for all bands in the EVLA, and it is performing 
well. 

## Configuration file
The configuration file [`config.ini`](./config.ini) contains all the necessary information to be 
completed by the user. Below, we provide some practical cases to get the pipeline running.


### Standard Usage: Recent EVLA observations
In general, only three options are required to be completed:
1) `experiment_name` - the name of the experiment, it will be the observation name, plus `.ms` 
   extension. For example, `experiment_name = '11A-231_sb4455680_2.55806.745764444444'`. Note: 
   do not use the `.ms` extension here. 
2) `working_directory` - the path to the working directory.
3) `asdm_file` - the path to the ASDM file. If you do not have the ASDM file, but instead you 
   have the `.ms` file, set this option as equal as the name of the measurement set (buth 
   without the `.ms` extension). See examples below.

A typical example is:
```python
experiment_name = '11A-231_sb4455680_2.55806.745764444444'
working_directory = '/data/directory/'
asdm_file = '/data/directory/11A-231_sb4455680_2.55806.745764444444'
```
If you do not have the ASDM file, just provide the ASDM file as the same as the measurement set 
(experiment name), in our case `11A-231_sb4455680_2.55806.745764444444`.

For recent EVLA obvservations, that is all you need to run the pipeline.
It will use the default options already set in the configuration file (see below more more details).

### Standard Usage: Early EVLA observations
For early EVLA observations, things are not direct. We need to know some prior information from 
the observations. 

1. In early observations, scan intents are wrongly defined (e.g. flux calibration 
cang have `OBSERVE_TARGET` intent instead of `CALIBRATE_FLUX`). 
2. Also, some fields have unique names but duplicated field IDs. For example, to the same field 
   name (e.g. `3C48`) there are two field IDs (e.g. `0` and `1`). Usually one corresponds to 
   pointing calibration (or some observational setup) and the other corresponds to the actual 
   flux calibrator scans. This may also happen to phase calibrators. Later on, the `fluxscale` 
   task will fail because of this.

For these cases, we need to complete six variables in the configuration file. 
Lets consider that our flux calibrator is `3C48`, bandpass calibrator is `3C48`, phase 
calibrator is `J0410+7656` and the science source is `VIIZw031`. Our flux calibrator has two 
fields IDs, `0` and `1`. The field ID `1` corresponds to some setup scans while the field ID `0` 
contains the valid scans for flux calibration. The same happens to the phase calibrator,
`J0410+7656` has two field IDs, `2` and `3`. The field ID `3` corresponds to some setup scans
while the field ID `2` contains the valid scans for phase calibration. 

For the first issue mentioned previously (of wrong scan intents), we need to specify the following 
information manually:

```python
flux_calibrator = '3C48'
bandpass_calibrator = '3C48'
phase_calibrator = 'J0410+7656'
target = 'VIIZw031'
```
For the second issue, we need to specify the VALID field IDs corresponding to the flux 
calibrator, bandpass calibrator and phase calibrators.  
```python
transfer = 0,2
reference = 0
```
The variable `reference` is the referent field ID from where the flux scalling solutions should 
be taken. In this case, the flux calibrator is the reference. The variable `transfer` sets the 
field IDs in which transfer solutions should be applied. In this case, the flux calibrator 
(itself) and the phase calibrator. All these information can be obtained from the `listobs` file.

If you do not know any of this information, the first thing to do is just to run the data 
import step of the pipeline, which will generate a listobs file. For that, use the variable 
`run_only_ms_info = True` in the configuration file, so that just the data import step will be excuted. 
Then, you can check the listobs file and get the necessary information.


### Customisation
Now, we describe other arguments that can be changed in the configuration file.

#### Hanniging Smoothing
To run the Hanniging smoothing, set the variable `do_hanning = True`.

#### Flagging
In the section `flagging`, you can find options related to flagging. In particular:
- `do_tfcrop_raw` - if `True`, the pipeline will run the task `flagdata` with the `tfcrop` 
  algorithm on the native data (`data` data column).
- `edge_channel_frac` - the fraction of edge channels to be ignored during calibration. This is a 
  way to choose just the central channels of each spectral window. For example, 
  `edge_channel_frac = 0.3` will ignore 30% of the channels in the edges of the spectral windows, so a total of 40% 
  of central channels will be used for calibration (e.g. bandpass).
- `edge_channel_flag_frac_cals` - the fraction of channels to be flagged in the edges of the 
  spectral windows for the calibrators. For example, if `edge_channel_flag_frac_cals = 0.1`, 
  10% of the channels will be flagged in the edges of the spectral windows for the calibrators.
- `edge_channel_flag_frac_science` - the fraction of channels to be flagged in the edges of the 
  spectral windows for the science source. For example, if `edge_channel_flag_frac_science = 0.1`, 
  10% of the channels will be flagged in the edges of the spectral windows for the science target.
- These two last options will be performed if the arguments `do_flag_edge_channels_cals` and 
  `do_flag_edge_channels_science` are set to True, respectively.
- `cals_flag_mode_strategy` - the strategy to be used in the `flagdata` task when flagging 
  calibrated data of calibrator fields. The options are `rflag` and `tfcrop`.
- `cals_datacolumn_to_flag` - the data column to be flagged in the `flagdata` task when flagging 
  calibrated data of calibrator fields. The options can be `corrected`, `residual` or `data`. 
  `corrected` or `residual` are good cases.
- `science_flag_mode_strategy` - the strategy to be used in the `flagdata` task when flagging 
  calibrated data of science fields. The options are `rflag` and `tfcrop`.
- `science_datacolumn_to_flag` - the data column to be flagged in the `flagdata` task when flagging 
  calibrated data of science fields. Usually, `corrected` is a good option. See the 
  documentation of `flagdata` task in CASA for more information.
- `do_clip` - if `True`, the pipeline will run the `flagdata` task with the `clip` mode 
  on the `corrected` data column. This is a way to remove outliers in the data. Please, make 
  sure that you know the flux density of the sources, so that the clip range will not completely 
  flag the data. 

##### Manual Flagging
In the manual flag file, you can input all the commands you would like to so that 
the data will be flagged. The manual flag file is set with the variable `manual_file = `.  

The basics of a file like this is: 
```python
mode='manual' scan='1' reason='Config Scan'
mode='manual' spw='0~15:0~2;61~63' reason='Flag chan edges'
# etc ...
``` 
See the CASA documentation for more information.



#### Average
Options related to averaging are in the section `averaging`. Note that it is not advised to run 
flagging on averaged data. Therefore, all previous steps (e.g. flagging) are made on the native 
data. Current averaging options are:
- `do_average` - if `True`, the pipeline will average the data.
- `time_avg` - if True, the pipeline will average the data in time.
- `timebin_avg` - the time bin to be used in the time averaging, for example, `timebin_avg = '6s'`.
- `channel_avg` - if True, the pipeline will average the data in frequency (channel average).
- `chan_out_avg` - the number of output channels to be averaged. For example, if your 
  observation has 128 channels, `chan_out_avg = 64` will average the channels by a factor of 2. 
  In the most extreme case, `chan_out_avg = 1` will average all channels into one. 


#### Calibration
The calibration strategy consists of running a firs pass of full calibration, then run 
autoflagging on `corrected` data column to remove possible bad data. Then, a second pass of
complete calibration is performed. There are significant calibration improvements when adopting 
this strategy. The basic options are:
```python
do_initial_cal = True
do_setjy = True
do_refant = True
do_bandpass_1st_run = True
do_gain_calibration_1st_run = True
do_apply_science_1st_run = True

do_bandpass_2nd_run = True
do_gain_calibration_2nd_run = True
```

If the option `do_apply_science_1st_run` is set to `True`, the pipeline will apply the 
1st-pass calibrations to the science sources and will split each science source into separated 
measurement sets. This is useful to check the quality of the calibration with the final stage. 

##### Reference Antenna
The reference antenna will be computed automatically by the pipeline if `refant = None`. 

##### Solution Intervals
Current options are:
```python
minsnr = 2.0
bp_solint_K = inf
bp_solint_G_p = 16s
bp_solint_G_ap = 32s
bp_solint_BP = inf

all_solint_short_p = 16s
all_solint_short_ap = 32s
all_solint_long_p = inf
all_solint_inf_ap = inf
bp_applymode = calflagstrict
ph_ap_applymode = calflagstrict
```

##### Apply final calibration.
Options related to the final calibration are:
```python
do_apply_science = True
do_flag_science = True
do_run_statwt = True
calwt = True
statwt_timebin = 8s
statwt_statalg = chauvenet
do_split = True
timebin_longer = 8s
```

- `do_apply_science` - if `True`, the pipeline will apply the final calibration to the science 
  sources.
- `do_flag_science` - if `True`, the pipeline will run the `flagdata` task on the science sources 
  after the final calibration.
- `do_run_statwt` - if `True`, the pipeline will run the `statwt` task on the final calibrated 
  data.
- `calwt` - if `True`, the weights will be calibrated during `applycal`.
- `statwt_timebin` - the time bin to be used in the `statwt` task.
- `statwt_statalg` - the statistical algorithm to be used in the `statwt` task.
- `do_split` - if `True`, the pipeline will split the final calibrated data into separated 
  measurement sets for each field (both calibrators and science sources).
- `timebin_longer` - Timebin to be used to generate additional measurement sets for each field.

##### Imaging (WARNING: EXPERIMENTAL)
If one want to run basic imaging, set the variable `do_imaging = True`. It will run `tclean` for 
basic imaging, using the auto-masking implementation in CASA (enabled with `usemask = 
'auto-multithresh'` in `tclean`). See function `run_imaging_tclean` in the script 
[`data_calibration/helper_functions.py`](./data_calibration/helper_functions.py) for more details.

NOTE: To display the images after imaging, you will need to install `astropy` inside the CASA environment.
For example, enter casa (`$ casa`) and then run:
```python
CASA <1>: %pip install astropy
```

#### 3.5 How to run the script?

1. Open casa: `$ casa`
2. Then, execute:
```python
CASA <1>: exec(open('./calibration_script.py').read())
```
3. Wait... can take hours...

Another way to run the pipeline is to do:
```bash
casa -c main.py
````

If you want to run the imaging step at the end (`do_imaging`) with `tclean`, it will be better to 
use`mpicasa` instead. Hence, you can run the script as:
```bash
$ mpicasa -n 8 casa --nogui -c main.py
```
If running with `mpicasa`, in section `imaging` of the configuration file, set the variable
`parallel = True`. If not running with `mpicasa`, set `parallel = False` to avoid errors in the end.

[//]: # (#### 3.6 Known issues)

### Basic plotting for reports.
Some basic plotting are made to check the quality of the calibration.

#### Gain Plots
These plots can be found in: `working_directory/plots/calibration/`.

#### Corrected Visibility Plots
These plots can be found in: `working_directory/plots/after/`. 

#### Flagging statistics plots
These plots can be found in: `working_directory/plots/`.





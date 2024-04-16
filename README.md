# radintCAL
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


A CASA-JVLA based pileline for radio Interferometric data reduction, calibration, 
plotting and basic imaging.

This is a CASA's helper script, which handles many function call to deal with 
data calibration.

WARNING: This code is under development and it may not work depending on your data.
It has been tested in EVLA visibilities ONLY. 
Currently, I am using it to reduce C-BAND data and it is performing well, however I 
HAVE not checked how it performs on other frequencies (something that I am going 
to do later this year), so be aware that the automated flagging (using `tfcrop` and `rflag` 
may encounter issues when using it for L-BAND data, for example), since RFIs are more frequent. 


Before running the code, there are two main points to pay attention: 
1) The header of the file
2) The configuration file

I am going to explain both.
### 1 Configuration file
First, you the paths where the data is located must be set: 

1) Where your data is stored: <br>`base_path = '/data/directory/`
2) Name of the `.ms` file: <br> `name = 'data_vis.ms/'`
3) The name of the manual file having the list of manual flag instructions: <br> `flag_cmds_file`
   <br>
   The default option for this command is to use the previous options, 
   and have this file located inside a folder named `flags/` under 
   the name `data_vis.flagcmds`. Then, it results in: <br>
   `flag_cmds_file = base_path+'flags/'+name+'.flagcmds'`
4) The default input visibility file is not actually a `.ms`, but instead a SMBD file
   which will be converted to a `ms` file. But, the code checks if the `.ms` file 
   exists, which is located in: <br> `output_vis_path = base_path`

Now, we need to know relevant information from the observation file
(generated with `listobs`) which must be inputed into the configuration file.
At the current momment, these information must be written mannualy (next plans is to have it created 
automatically). Moreover, you should know/have in hands the listobs file in order to input some
of the required information. They are: fields and calibrators and other arguments that are listed in full bellow: 

```python
flux_calibrator = '3C286'
bandpass_calibrator = '3C48'
# amplitude_calibrator = '0521+166=3C138' # not implemented, assumes to be the same as the phase calibrator.
model_setjy = '3C286_C.im'
spw_skip_edge = '0~15:5~59'
spw_central = '0~15:12~52'
refant='ea10,ea25,ea28'
all_spws = '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15'#only SPWs for C band.


phase_calibrators_all = 'J2011-1546,J2236+2828,J2330+1100' #
target_fields = 'Mrk509,Ark564,NGC7469'
```
The arguments `spw_skip_edge` and `spw_central` are used to perform a 
selection in channels across spectral windows.
The argument `spw_skip_edge` is used for the `K` corrections (delays), 
where edge channels should be avoided. The argument `spw_central` is used to select 
central channels only, to be used with the `G` gaintype 
(modes `p` and `ap` -- amplitudes and phases). 

Also, the `refant` should be used to specify which antenna is going to be used
as reference when computing the calibration tables. 

Finally, `phase_calibrators_all` and `target_fields` are the names 
of the fields related to phase calibrators and target fields. The number of fields in both must be the same, 
each target must have an phase calibrator associated, even if it is repeated. For example: 
```python
target_fields = 'TARGET1, TARGET2, TARGET3'
phase_calibrators_all = 'CALIBRATOR_X, CALIBRATOR_Y, CALIBRATOR_X'
``` 
In this example, `CALIBRATOR_X` is used FOR both `TARGET1` and `TARGET3`.

NOTE: Be aware that the I have not tested the code in case the measurement set 
contain multiple frequencies, e.g. observations for more than one band. 
For now, I would like to recommend to split the data into each individual frequency. 

### 2. Manual flag file
In the manual flag file, you can input all the commands you would like to so that 
the data will be flagged. 
The basics of a file like this is: 
```python
mode='manual' scan='1' reason='Config Scan'
mode='manual' spw='0~15:0~2;61~63' reason='Flag chan edges'
# etc ...
``` 
In this example, the first scan is flagged; and also the edge channels of each 
spectral window, in this case 2 channels each side.

NOTE: In this example, I assumed that the number of spectral windows was 16 
(from 0 to 15) and the number of channels was 65 (from 0 to 64).
### 3. File's header
The header of the file `calibration_script.py` contain critical arguments to be 
used. Among them,  flagging options, solution intervals, etc. Lets go in detail.

#### 3.1 Solution intervals
```python
solint_long = '48s'
calculate_long_solint = True

solint_mid = '32s'
calculate_mid_solint = True

solint_short = '16s'
calculate_short_solint = True
```
The code will compute ***all tables*** for three solution intervals, a shorter 
solution interval, `solint_short `, a intermediate `solint_mid` and a longer 
solution interval, `solint_long`. 

Then, we should set which one we are going to use as the main solution interval:
```python
calculate_extra_tables = False # not implemented yet.

main_setjy_solint = solint_mid #which solution interval to use to set the flux scalling.

solint_main = solint_mid # which solution interval to be used as a reference
```
as well the one to be used as the reference to the flux scalling when calling 
the CASA task `setjy`. 


#### 3.2 Flagging options

```python
#flagging settings
manual_file_flag = True
fields_to_report_flag = '' # leavy empty to report all fields, but takes longer

#this is for the beginning, raw data
apply_tfcrop_init = True

# this is at the end, for calibrated data (rflag) or uncalibrated data (tfcrop)
auto_flag_data = True
flag_with_rflag = True
flag_with_tfcrop = False
```

#### 3.3 Calibration Options
```python
# calibration settings
additional_gain_tables = False
minsnr = 3.0
combine = ''
```

#### 3.4 Function Calls 
At the end of the code, function calls are organized as follows: 

```python
data_handle()

make_plots_stages(stage='before',
                  kind='before_tfcrop_init',
                  FIELDS=fields_test_plot,
                  plot_all_uv=True)

initial_flagging()

make_plots_stages(stage='before',
                  kind='after_tfcrop_init',
                  FIELDS=fields_test_plot)
initial_corrections()


calibration()


make_plots_stages(stage='after',
                  kind='after_rflag_and_cal',
                  FIELDS=fields_test_plot)
add_final_auto_flags = True
if add_final_auto_flags == True:
    '''
        Apply autoflag to target fields.
    '''
    final_auto_flag()
split_fields()
make_plots_stages(stage='after',kind='final',FIELDS=target_fields_arr,plot_all_uv=True)
# basic_imaging()
```
#### 3.5 How to run the script?

1. Open casa: `$ casa`
2. Then, execute:
   ```python
   CASA <1>: exec(open('./calibration_script.py').read())
   ```
3. Wait... can take hours...

#### 3.6 Known issues
There are some issues with CASA-6.4> that results in `core dumped` when starting 
computing the calibration tables.
I think that is an issue with CASA's end. So, please use `CASA 6.2`. 

### 4. Data products
If asked, the code will perform multiple plots during the calibration process,
before initial flagging, after, etc (but see item 5. bellow about runtime).
The folder structure to those plots are: 
```
plots > before
plots > after
```
In each one of these folders, there will be plots such as `amp_phase`, `freq_amp`, etc. 

### 5. General Comments
Since the code calculates multiple gain tables (for three solution interval), the runtime can be quite long. 
But also what makes it slow is the plotting functions, which perform multiple plots in between different steps 
(e.g. before and after initial flagging, before and after calibration; before and after rflag during calibration; before and after final
flagging with rflag.)

If you do not want to do those plots, comment all the function calls of the function 
`make_plots_stages`.


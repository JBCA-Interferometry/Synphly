
import os, glob, subprocess
from casatasks import *
from casaplotms import *
import bdsf

from astropy.io import fits
from matplotlib import pyplot as plt

# define globals 
# vis = '/home/kelvin/Desktop/vla/working_directory/selfcal/M15X-2.calibrated.ms'
# vis = '/home/kelvin/Desktop/vla/working_directory/selfcal/2123+1007.ms'
# vis = '/home/kelvin/Desktop/vla/working_directory/selfcal/luca_split.ms'
vis = '/home/kelvin/Desktop/vla/working_directory/selfcal/luca.ms'
working_directory = '/home/kelvin/Desktop/vla/working_directory/selfcal'
outlierfile = '/home/kelvin/Desktop/Synphly/selfcal/outlier_fields.txt'
basename = os.path.splitext(os.path.basename(vis))[0]

# imaging and selfcal globals

cell = '60mas'
imsize = [256,256] # has to be[x,y] otherwise wsclean in function peeling will fail
niter = [1000,10000,30000] # the number of iterations for each loop -- needs to be arbitrarily large
threshold = ['0.1mJy','0.05mJy','0.025mJy'] # in mJy
nterms = 2
gridder = 'standard'
deconvolver = 'mtmfs'
weighting='briggs'
robust = -0.5
wprojplanes = 1
outlier_file = '/home/kelvin/Desktop/Synphly/selfcal/outlier_fields.txt'
pblimit = -0.1 # avoid 1,-1 or 0

# selfcal
refant = 'ea28'
nloops = 3 # number of selfcal loops
loop = 0 # large image for selfcal part 1
calmode = ['p','p','ap']
gaintype= ['G','G','G']
solint = ['60s','30s','180s']
minsnr = [1,1,1]

# pybdsf
detection_threshold = 5.0

# final image and peeling
niter_final = 1000000
threshold_final = '0.01mJy'
wsclean_sif= '/home/kelvin/Desktop/singularity/wsclean-v3.3-no-cuda.sif'
singularity_bind = '/home/kelvin/Desktop/'

spw = 17 # wsclean chan out
abs_mem = 4 # mem to use in GB

def set_working_dir():

    if not os.path.exists(working_directory):
        # logging.info(f"{working_directory} does not exist, making one")
        os.makedirs(working_directory)
    else:
        # logging.info(f"Working directory {working_directory} already exists")
        pass

    os.chdir(working_directory)





def pybdsf(input_image):

    # The input image is a casa .image that then gets exported to a FITS
    imagename = input_image.replace('.image.tt0','')
    fitsname = imagename+'.fits'
    exportfits(imagename = input_image, fitsimage=fitsname, overwrite=True)

    img = bdsf.process_image(fitsname,adaptive_rms_box=True, thresh='hard',
                            thresh_isl=True, thresh_pix = detection_threshold, advanced_opts=True,
                            mean_map='map', rms_map =True, group_by_isl=True)
    # adaptive_rms_box=False, spline_rank=4, thresh='hard', thresh_isl=True, thresh_pix = detection_threshold
    # Write out island mask and FITS catalog -- for the large map
    img.export_image(outfile=imagename+'.maskfile.fits',img_type='island_mask',img_format='fits',clobber=True)
    img.write_catalog(outfile=imagename+'.cat', format='fits', clobber=True, catalog_type ='gaul')
    
    regionfile = imagename+'.casabox'
    ascii_file = imagename+'.ascii'
    rmsfile = imagename+'.rmsfile'

    img.write_catalog(outfile=regionfile,format='casabox',clobber=True,catalog_type='srl')
    img.write_catalog(outfile=ascii_file, format='ascii', clobber=True, catalog_type='gaul')
    img.export_image(outfile=rmsfile, img_type='rms', img_format='fits', clobber=True)

    return regionfile

def selfcal_part1():

    """
    Creates an (a large) an image that is used to create a casa region file using pybdsf 
    for masking
    """
    
    global first_part_imagename
    first_part_imagename = basename + '_first_masking'

    if not os.path.exists(first_part_imagename):
        print(f"Making {first_part_imagename}")
        tclean(
            vis = vis, imagename=first_part_imagename, imsize=imsize, cell=cell,
            gridder = gridder, wprojplanes = wprojplanes, deconvolver = deconvolver,
            weighting = weighting, robust = robust, niter=1000, threshold = '0.5mJy',
            nterms = nterms, pblimit = pblimit
        )

    regionfile = pybdsf(input_image=first_part_imagename+'.image.tt0')


def selfcal_part2():

    if os.path.exists(outlier_file) and open(outlier_file).read() == '':
        outlierfile = ''

    regionfile = basename + '_first_masking.casabox'

    print("Deleting model column before selfcal")
    delmod(vis=vis,otf=True)

    for selfcal_loop in range(nloops):
        caltable = f'caltable_{selfcal_loop}.gcal'
        prev_caltables = sorted(glob.glob('*.gcal'))
        if len(prev_caltables) >0 and calmode[selfcal_loop] !='':
            applycal(vis=vis, gaintable = prev_caltables, parang=False )
    
        imagename = f'target_selfcal_{selfcal_loop}'
        if os.path.exists(imagename):
            print("Continuing to the next image")
        
        else:
            # imagename = f'target_selfcal_{selfcal_loop}'
            print(f"Making image {imagename}")
            tclean(
                vis = vis, imagename=imagename, imsize=imsize, cell=cell,
                parallel=False,
                gridder = gridder, wprojplanes = wprojplanes, deconvolver = deconvolver,
                weighting = weighting, robust = robust, niter=niter[selfcal_loop], threshold = threshold[selfcal_loop],
                nterms = nterms, pblimit = -1,interactive=False, usemask='user', mask=regionfile
            )

            ## NB: The problem was niter -- there was a space in the list []

            print("Adding modelcolumn to data")
            # model images from the MTMFS images,
            ft(vis = vis, model=[imagename+'.model.tt0',imagename+'.model.tt1'], nterms=2,usescratch=True)

            # plot the model column
            plotms(
                vis=vis, xaxis='UVwave', yaxis='amp', ydatacolumn='model',avgchannel='64',avgtime='300',
                showgui=False, plotfile=imagename+'_modelcolumn.png', overwrite=True, width=1500, height=750,
            )

            gaincal( vis =vis, caltable = caltable, refant = refant, solint = solint[selfcal_loop],
                    gaintype = gaintype[selfcal_loop], gaintable=prev_caltables,  minsnr = minsnr[selfcal_loop],
                    calmode = calmode[selfcal_loop], append=False, parang=False
                    )
            coloraxis = ['corr','spw']
            for color in coloraxis:
                if calmode[selfcal_loop] =='p':
                    plotms(
                        vis = caltable, xaxis='time', yaxis='phase', gridcols=3, gridrows=3,
                        iteraxis='antenna', coloraxis = color, showgui=False, overwrite=True,
                        plotfile=caltable.replace('.gcal',f'_{color}.png'), dpi=300, width=1500, height=750,
                    )
                else:
                    plotms(
                            vis = caltable, xaxis='time', yaxis='amp', gridcols=3, gridrows=3,
                            iteraxis='antenna', coloraxis = color, showgui=False, overwrite=True,
                            plotfile=caltable.replace('.gcal',f'_{color}.png'), dpi=300, width=1500, height=750
                        )

            if selfcal_loop == nloops-1:
                prev_caltables = sorted(glob.glob('*.gcal'))
                print("Applying the caltable derived from last gaincal iteration")
                applycal(vis=vis, gaintable = prev_caltables, parang=False )
        
        # ### Get the last imagename from the loop and generate a final mask
        
    imagename = basename +f'_{nloops-1}'+'.final'
    ##  tclean here to make the final image
    print("Make final image with all selfcal corrections applied")
    tclean(
        vis = vis, imagename = imagename, imsize=imsize, cell=cell, gridder=gridder,
        wprojplanes = wprojplanes, deconvolver = deconvolver, weighting = weighting,
        robust = robust, niter=niter_final, threshold = threshold_final, nterms=nterms,
        pblimit=pblimit, interactive=False, usemask = 'user', mask=regionfile,
    )
    ### Use the output here to peel -- wsclean predict should work
    ## implement using wsclean -- also no need to create a large image



def run_wsclean(command):

    """
    Runs wsclean commands 
    """

    container = wsclean_sif
    if os.path.exists(container):
        singularity_bind = os.path.join(os.path.dirname(os.path.dirname(wsclean_sif)))

    command_to_execute = ['singularity', 'exec', '-B', singularity_bind, container] + command
    try:
        print("Executing: %s", ' '.join(command_to_execute))
        process = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate()
        print("stdout: %s", stdout)
        print("stderr: %s", stderr)

        return_code = process.returncode
        if return_code == 0:
            print(f"Strategy executed successfully. Output:\n{stdout}")
        else:
            print(f"Error executing strategy. Return code: {return_code}\nError message: {stderr}")  

    except Exception as e:
        print(f"An error occurred: {e}")


def peeling():

    """
    Subtract all the sources in the field such that you are left with a blank

    Use wsclean and pybdsf casa region from the final iterations 

    Then perform uvsub in CASA

    """

    # Make a region file of the final self calibrated image and use it to peel the sources
    imagename = basename +f'_{nloops-1}'+'.final.image.tt0'
    regionfile_to_peel = pybdsf(input_image=imagename)
    fitsmask = imagename.replace('.image.tt0','')+'.maskfile.fits'
    model_fits = imagename.replace('.final.image.tt0','.final.image.tt0-model.fits')
    os.rename(fitsmask,model_fits )


    threshold_cmd = ['wsclean', '-auto-threshold','3', '-size', f'{imsize[0]}', f'{imsize[1]}','-scale', f'{cell}',\
                    '-mgain', '0.8', '-niter', '0',f'{vis}']
    
    predict_cmd = ['wsclean', '-log-time', '-predict', '-field', '', '-reorder' ,'-name', f'{imagename}', '-abs-mem',f'{abs_mem}', vis]


    run_wsclean(predict_cmd)

    ## NB: wsclean needs to find an image named my-image-model.fits or reg 
    ## works by replacing model column with model for the problem sources using

    
    
    ## Subtract the models put in the model column from the data and make an image
        
    print("Running uvsub")
    uvsub(vis=vis)

    ## Run wsclean to check if the subtraction has been successful -- make dirty map

    run_wsclean(threshold_cmd)



def pb_corrections():

    """
    Performs the primary beam correction after imaging -- performs wideband primary beam correction
    """

    # NB: Check which imagename is to be used here -- probably should be the one after the source subtraction or before?
    imagename = basename +f'_{nloops-1}'+'.final.image'

    widebandpbcor(
        vis = vis, imagename = [imagename+'.tt0', imagename+'.tt1'], nterms=2, action = 'pbcor'
    )



def direction_string(ra, dec, frame):
  
  """helper function for often needed string"""
  return ' '.join([frame, ra, dec])


def get_im_stats(imagename):
    
    """
    Gets the statistics for either a 256x256 pix image and writes
    them to a logfile
    """


    rms=imstat(imagename=imagename,box='51,7,247,76')['rms'][0]  # for 256x256 px
    peak=imstat(imagename=imagename,box='124,122,133,134')['max'][0]
    print('For %s, the peak %.3f mJy/beam, rms %.3f mJy/beam, S/N %6.0f\n\n' %
                (imagename, peak*1e3, rms*1e3, peak/rms))
    
    # snr = peak/rms

    # if snr >= 5:
    #     casa_imstat = casatasks.imstat(imagename)
    #     imfit_box = '124,122,133,134'
    #     imfit_results = casatasks.imfit(imagename,box=imfit_box)

        # results = cl.fromrecord(imfit_results['results'])
        # print(results)


        # fit_file = 'imfit.txt'
        # with open(fit_file, "a") as txt_file:
        #     txt_file.write(f"For {imagename}\n\n, the maximum pos for imstat is {casa_imstat['maxposf']}\n\nand the fit results are {imfit_results}")


    logfile = 'imstat.txt'
    casa_imstat = imstat(imagename)
    with open(logfile,"a") as txt_file:
        txt_file.write('For %s, the peak %.3f mJy/beam, rms %.3f mJy/beam, S/N %6.0f\n\n' %
                    (imagename, peak*1e3, rms*1e3, peak/rms))

        txt_file.write(f"For {imagename}, the maximum pos for imstat is {casa_imstat['maxposf']}\n")



def plot_fits(fitsname):
    """
    Plots fitsfiles using astropy
    """
    fitsfile = fits.open(fitsname)
    image_data = fitsfile[0].data[0,0,:,:]
    ny, nx = image_data.shape
    x_center = nx // 2
    y_center = ny // 2
    x_new = np.arange(nx) - x_center
    y_new = np.arange(ny) - y_center

    fig, ax = plt.subplots()

    # image_plot = ax.imshow(image_data, origin='lower', 
    #                    extent=[x_new.min(), x_new.max(), y_new.min(), y_new.max()],cmap='viridis')
    image_plot = ax.imshow(image_data, origin='lower', 
                       extent=[-32, 32, -32, 32],cmap='viridis')
    cbar = plt.colorbar(image_plot,ax=ax,orientation='vertical')
    # ax.set_title(sources_to_image,fontsize=16)
    plt.savefig(fitsname.replace('.fits','.pdf'))



phasecenter = 'J2000 322.4932710322deg +12.1629471549deg'
msname = '/home/kelvin/Downloads/M15X-2/M15X-2.calibrated.ms'

import numpy as np
coords = np.loadtxt('/home/kelvin/Desktop/gv020/hst_cuts_notebook/hacks_hb_coords.txt')
ra = coords[:,0]
dec = coords[:,1]

ra_str = ', '.join([str(val) for val in ra])


def phaseshift_image():

    for i in range(len(ra)):
        
        # ra_dir,dec_dir = phasecenter[i].split(' ')
        ra_str = str(ra[i]); dec_str = str(dec[i])
        phasecenter = 'J2000' +' ' + ra_str + 'deg' + '+ ' +dec_str + 'deg'
        print(f"Phaseshifting to {phasecenter}")

        
        phaseshifted_ms = f"phaseshifted_ms_{phasecenter.replace(' ','_')}"
        if not os.path.exists(phaseshifted_ms):
            # subprocess.run(['rm','-r',phaseshifted_ms])
            phaseshift(
                vis=msname,outputvis=phaseshifted_ms,datacolumn='corrected',
                phasecenter=phasecenter
            )

        split_ms = f"split_ms_{phasecenter.replace(' ','_')}"

        print(f"Splitting to {split_ms}")
        if not os.path.exists(split_ms):
            # subprocess.run(['rm','-r',split_ms])
            split(
                vis=phaseshifted_ms,outputvis=split_ms,
                datacolumn='data', timebin='30s', width=16
                # createmms = True, 
            )
        ## Delete the phaseshifted_ms after averaging to save space
        print(f"Deleting {phaseshifted_ms}")
        subprocess.run(['rm','-r',phaseshifted_ms])
        print(f"Successfully deleted {phaseshifted_ms}")

        imagename = f"image_{phasecenter.replace(' ','_')}"
        os.system(f'rm -r {imagename}.*')

        print(f"Imaging {phasecenter[i]}")

        tclean(
            vis=split_ms, imagename=imagename,cell=cell, niter=0,
            imsize=[256],parallel=False, deconvolver='mtmfs', nterms=2,
            weighting='briggs', robust=-0.5, datacolumn='data',
            )
        exportfits(imagename=imagename+'.image.tt0',fitsimage=imagename+'.fits',overwrite=True)
        get_im_stats(imagename+'.image.tt0')
        plot_fits(imagename+'.fits')

        print(f"Finished {phasecenter}")


set_working_dir()
# selfcal_part1()
# selfcal_part2()
# peeling()

import time
start = time.time()
phaseshift_image()
end = time.time()
print(f"Phaseshifting, splitting and imaging took {(end-start) / 3600:.2f} hours")


import os, glob, subprocess
from casatasks import *
from casaplotms import *
import bdsf


# define globals 
# vis = '/home/kelvin/Desktop/vla/working_directory/selfcal/M15X-2.calibrated.ms'
# vis = '/home/kelvin/Desktop/vla/working_directory/selfcal/2123+1007.ms'
vis = '/home/kelvin/Desktop/vla/working_directory/selfcal/luca_split.ms'
working_directory = '/home/kelvin/Desktop/vla/working_directory/selfcal'
outlierfile = '/home/kelvin/Desktop/Synphly/selfcal/outlier_fields.txt'
basename = os.path.splitext(os.path.basename(vis))[0]

# imaging and selfcal globals

cell = '200mas'
imsize = [320,320]
niter = [1,2,3] # the number of iterations for each loop -- needs to be arbitrarily large
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
threshold_final = '10e-6mJy'
wsclean_sif= '/home/kelvin/Desktop/singularity/wsclean-v3.3-no-cuda.sif'

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
            weighting = weighting, robust = robust, niter=10000, threshold = '0.5mJy',
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
        
    imagename = basename +f'_{nloops-1}'
    ##  tclean here to make the final image
    print("Make final image with all selfcal corrections applied")
    imagename = imagename+'.final' 
    tclean(
        vis = vis, imagename = imagename, imsize=imsize, cell=cell, gridder=gridder,
        wprojplanes = wprojplanes, deconvolver = deconvolver, weighting = weighting,
        robust = robust, niter=niter_final, threshold = threshold_final, nterms=nterms,
        pblimit=pblimit, interactive=False, usemask = 'user', mask=regionfile,
    )
    ### Use the output here to peel -- wsclean predict should work
    ## implement using wsclean -- also no need to create a large image

        

def peeling():

    """
    Subtract all the sources in the field such that you are left with a blank

    Use wsclean and pybdsf casa region from the final iterations 

    Then perform uvsub in CASA

    """

    # Make a region file of the final self calibrated image and use it to peel the sources
    imagename = basename +f'_{nloops-1}'
    regionfile_to_peel = pybdsf(input_image=imagename+'.image.tt0')

    
    container = wsclean_sif
    if os.path.exists(container):
        singularity_bind = os.path.join(os.path.dirname(os.path.dirname(wsclean_sif)))

    ## NB: wsclean needs to find an image named my-image-model.fits or reg 
    ## works by replacing model column with model for the problem sources using


    cmd = ['wsclean', '-log-time', '-predict', '-field', '', '-channels-out', '16' '-name','image', '-abs-mem','2', vis]

    command_to_execute = ['singularity', 'exec', '-B', singularity_bind, container] + cmd
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



set_working_dir()
selfcal_part1()
selfcal_part2()


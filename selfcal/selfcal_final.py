
import os, glob
from casatasks import *
from casaplotms import *
import bdsf


# define globals 
# vis = '/home/kelvin/Desktop/vla/working_directory/fields/M15X-2/M15X-2.calibrated.ms'
# vis = '/home/kelvin/Desktop/vla/working_directory/selfcal/2123+1007.ms'
vis = '/home/kelvin/Desktop/vla/working_directory/selfcal/luca.ms'
working_directory = '/home/kelvin/Desktop/vla/working_directory/selfcal'
outlierfile = '/home/kelvin/Desktop/Synphly/selfcal/outlier_fields.txt'


# imaging and selfcal globals

cell = '300mas'
imsize = [320,320]
niter = [10000,10000,500000] # the number of iterations for each loop -- needs to be arbitrarily large
threshold = ['0.5mJy','0.05mJy','0.005mJy'] # in mJy
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
niter_final = 100000
threshold_final = '100e-6mJy'

def set_working_dir():

    if not os.path.exists(working_directory):
        # logging.info(f"{working_directory} does not exist, making one")
        os.makedirs(working_directory)
    else:
        # logging.info(f"Working directory {working_directory} already exists")
        pass

    os.chdir(working_directory)





def pybdsf(imagename):

    # The input image is a casa .image that then gets exported to a FITS
    imagename = imagename.replace('.image.tt0','')
    fitsname = imagename+'.fits'
    exportfits(imagename = imagename+'.tt0', fitsimage=fitsname, overwrite=True)

    img = bdsf.process_image(fitsname,adaptive_rms_box=False, spline_rank=4, thresh='hard',
                            thresh_isl=True, thresh_pix = detection_threshold, advanced_opts=True,
                            mean_map='map', rms_map =True)
    
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
    
    imagename = 'large_map'

    if not os.path.exists(imagename):
        print("Making large image")
        tclean(
            vis = vis, imagename=imagename, imsize=[320], cell=cell,
            gridder = gridder, wprojplanes = 1, deconvolver = deconvolver,
            weighting = weighting, robust = robust, niter=100000, threshold = '0.5mJy',
            nterms = nterms, pblimit = pblimit
        )




def selfcal_part2():

    if os.path.exists(outlier_file) and open(outlier_file).read() == '':
        outlierfile = ''

    print("Deleting model column before selfcal")
    delmod(vis=vis,otf=True)

    for selfcal_loop in range(nloops):
        caltable = f'caltable_{selfcal_loop}.gcal'
        prev_caltables = sorted(glob.glob('*.gcal'))

        if len(prev_caltables) >0 and calmode[selfcal_loop] !='':
            applycal(vis=vis, gaintable = prev_caltables, parang=False )
    
        # imagename = f'target_selfcal_{selfcal_loop}'
        # if os.path.exists(imagename):
        #     print("Continuing to the next image")
        
        else:
            
            print(f"Making image {imagename}")
            tclean(
                vis = vis, imagename=imagename, imsize=imsize, cell=cell,
                gridder = gridder, wprojplanes = wprojplanes, deconvolver = deconvolver,
                weighting = weighting, robust = robust, niter=niter[selfcal_loop], threshold = threshold[selfcal_loop],
                nterms = nterms, pblimit = pblimit, interactive=False
            )

            ## NB: The problem was niter -- there was a space in the list []

            print("Adding modelcolumn to data")
            # model images from the MTMFS images,
            ft(vis = vis, model=[imagename+'.model.tt0',imagename+'.model.tt1'], nterms=2,usescratch=True)

            # Plot the model column
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
            # Plot the corrected/model column to check quality of selfcal 
            plotms(
                vis = vis, xaxis = 'UVwave',yaxis='amp', ydatacolumn='corrected/model', avgchannel='64',
                avgtime='300', showgui=False, plotfile = imagename+'_corrected_model.png',overwrite=True, width=1500, height=750,
            )

            if selfcal_loop == nloops-1:
                prev_caltables = sorted(glob.glob('*.gcal'))
                print("Applying the caltable derived from last gaincal iteration")
                applycal(vis=vis, gaintable = prev_caltables, parang=False )

        # tclean here to make the final image
        print("Make final image with all sefcal corrections applied")
        imagename = imagename+'.final' 
        tclean(
            vis = vis, imagename = imagename, imsize=imsize, cell=cell, gridder=gridder,
            wprojplanes = wprojplanes, deconvolver = deconvolver, weighting = weighting,
            robust = robust, niter=niter_final, threshold = threshold_final, nterms=nterms,
            pblimit=pblimit, interactive=False
        )

  



set_working_dir()
# large_map()
# selfcal()
# pybdsf(imagename='large_map.image.tt0')

imagename = 'masking_trial'
imagename='large_map.image.tt0'
imagename = imagename.replace('.tt0','')
maskfile = imagename+'.maskfile.fits'

tclean(
    vis = vis, imagename=imagename, imsize=[320], cell=cell,
    gridder = gridder, wprojplanes = 1, deconvolver = deconvolver,
    weighting = weighting, robust = robust, niter=100000, threshold = '0.01mJy',
    nterms = nterms, pblimit = pblimit, usemask='user', mask='large_map.image.casabox',
    interactive=True
)




import casatasks
import casatools
import casaplotms

import os


vis = '/home/kelvin/Desktop/vla/working_directory/fields/M15X-2/M15X-2.calibrated.ms'
working_directory = '/home/kelvin/Desktop/vla/working_directory/selfcal'
outlierfile = '/home/kelvin/Desktop/Synphly/selfcal/outlier_fields.txt'

refant = 'ea28'

def set_working_dir():

    if not os.path.exists(working_directory):
        # logging.info(f"{working_directory} does not exist, making one")
        os.makedirs(working_directory)
    else:
        # logging.info(f"Working directory {working_directory} already exists")
        pass

    os.chdir(working_directory)

def tclean(imagename,gridder,wprojplanes,imsize,outlierfile,niter,weighting,robust,datacolumn):

    casatasks.tclean(
        vis = vis, imagename=imagename, datacolumn=datacolumn,cell='0.2arcsec',
        pblimit = -0.1, gridder=gridder,wprojplanes=wprojplanes, imsize=imsize, outlierfile=outlierfile,
        niter = niter, weighting= weighting, robust=robust, interactive=True,
        savemodel='modelcolumn', deconvolver='mtmfs',nterms=2
    )

    peak = casatasks.imstat(imagename=imagename+'.image')['max'][0]
    rms = casatasks.imstat(imagename=imagename+'.image')['rms'][0]

    dynamic_range = peak/rms
    print(f"The dynamic range of the image is {dynamic_range}")


gaintables = []

def gaincal(caltable, solint,calmode,gaintype,minsnr):

    if not os.path.exists(caltable):
        casatasks.gaincal(
            vis = vis, caltable = caltable, solint = solint, refant = refant,
            calmode = calmode, gaintype= gaintype, minsnr = minsnr
        )

        gaintables.append(caltable)

        casaplotms.plotms(
            vis = caltable, xaxis='time', yaxis='phase', iteraxis='antenna',
            gridcols=3, gridrows=3, coloraxis='corr',
        )
    else:
        print(f"{caltable} exists -- will not create a new one")

def applycal():
    
    print(gaintables)
    casatasks.applycal(
        vis = vis, gaintable = gaintables
    )


set_working_dir()

# tclean(imagename='obj_prelim_clean.3arcmin',gridder='standard',wprojplanes=1,imsize=1280,outlierfile='',niter=1000,weighting='briggs',robust=0,datacolumn='data')
# gaincal(caltable='selfcal_initial.tb', solint='int',calmode='p',gaintype='G',minsnr=0)

# gaincal(caltable='selfcal_combine_pol_solint_30s',solint='30s',calmode='p',gaintype='T',minsnr=3)
# applycal()
# tclean(imagename='obj_first_clean.3arcmin',gridder='standard',wprojplanes=1,imsize=1280,outlierfile='',niter=1000,weighting='briggs',robust=0,datacolumn='corrected')


import bdsf

def make_bdsf_catalogue(input_image, detection_threshold):

    casabox = True
    ## Adaptive rms box -- rms box is reduced in size near bright sources and enlarged far from them
    ## scaling attempts to account for possible strong artifacts around bright sources

    ## thresh=hard -- hard thresh is assumed given by thresh_pix
    ## thresh_isl -- determines the region to which the fitting is done
    img = bdsf.process_image(input_image,adaptive_rms_box=True, thresh='hard', thresh_isl=True, thresh_pix = detection_threshold)

    # write the source catalog list

    if casabox == True:
        img.write_catalog(format='csv',catalog_type='srl',clobber=True)

    # write the residual image
    img.export_image(outfile=input_image.replace('.image','_pybdsf.fits'),img_type='gaus_resid',clobber=True)

    # write the model image
    img.export_image(outfile=input_image.replace('.image','_gaus.model.fits'),img_type='gaus_model',clobber=True)

    # write the rms image
    img.export_image(outfile=input_image.replace('.image','_rms.fits'),img_type='rms',clobber=True)


input_image = '/home/kelvin/Desktop/vla/working_directory/selfcal/obj_prelim_clean.3arcmin.pb.tt0'
make_bdsf_catalogue(input_image,detection_threshold=5.0)
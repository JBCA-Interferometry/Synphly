
import os, glob
from casatasks import *
from casaplotms import *


# define globals 
vis = '/home/kelvin/Desktop/vla/working_directory/fields/M15X-2/M15X-2.calibrated.ms'
# vis = '/home/kelvin/Desktop/vla/working_directory/fields/J2139+1423/J2139+1423.calibrated.ms'
working_directory = '/home/kelvin/Desktop/vla/working_directory/selfcal'
outlierfile = '/home/kelvin/Desktop/Synphly/selfcal/outlier_fields.txt'


# imaging and selfcal globals

cell = '200mas'
imsize = [320,320]
niter = [ 1,1,1] # the number of iterations for each loop -- needs to be arbitrarily large
threshold = ['0.5mJy','0.5mJy','0.5mJy'] # in mJy
nterms = 2
gridder = 'standard'
deconvolver = 'mtmfs'
weighting='briggs'
robust = -0.5
wprojplanes = 1
outlier_file = '/home/kelvin/Desktop/Synphly/selfcal/outlier_fields.txt'

# selfcal
refant = 'ea28'
nloops = 1 # number of selfcal loops
loop = 0 # large image for selfcal part 1
calmode = ['p','p','ap']
gaintype= ['G','G','G']
solint = ['30s','20s','60s']
minsnr = [0,0,0]



def set_working_dir():

    if not os.path.exists(working_directory):
        # logging.info(f"{working_directory} does not exist, making one")
        os.makedirs(working_directory)
    else:
        # logging.info(f"Working directory {working_directory} already exists")
        pass

    os.chdir(working_directory)


def large_map():
    
    imagename = 'large_map'

    if not os.path.exists(imagename):
        print("Making large image")
        tclean(
            vis = vis, imagename=imagename, imsize=[5120,5120], cell=cell,
            gridder = gridder, wprojplanes = 18, deconvolver = deconvolver,
            weighting = weighting, robust = robust, niter=10000, threshold = '0.01mJy',
            nterms = nterms, pblimit = -1
        )


def selfcal():

    if os.path.exists(outlier_file) and open(outlier_file).read() == '':
        outlierfile = ''

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
                gridder = gridder, wprojplanes = wprojplanes, deconvolver = deconvolver,
                weighting = weighting, robust = robust, niter=niter[selfcal_loop], threshold = threshold[selfcal_loop],
                nterms = nterms, pblimit = -1,interactive=False
            )


            print("Adding modelcolumn to data")
            # model images from the MTMFS images,
            ft(vis = vis, model=[imagename+'.model.tt0',imagename+'.model.tt1'], nterms=2,usescratch=True)

            # plot the model column
            plotms(
                vis=vis, xaxis='UVwave', yaxis='amp', ydatacolumn='model',avgchannel='64',avgtime='300',
                showgui=False, plotfile=imagename+'_modelcolumn.png'
            )

            # gaincal( vis =vis, caltable = caltable, refant = refant, solint = solint[selfcal_loop],
            #         gaintype = gaintype[selfcal_loop], gaintable=prev_caltables,  minsnr = minsnr[selfcal_loop],
            #         calmode = calmode[selfcal_loop], append=False, parang=False
            #         )
            # coloraxis = ['corr','spw']
            # for color in coloraxis:
            #     if calmode[selfcal_loop] =='p':
            #         plotms(
            #             vis = caltable, xaxis='time', yaxis='phase', gridcols=3, gridrows=3,
            #             iteraxis='antenna', coloraxis = color, showgui=False, 
            #             plotfile=caltable.replace('.gcal',f'_{color}.png'), dpi=300
            #         )
            #     else:
            #         plotms(
            #                 vis = caltable, xaxis='time', yaxis='amp', gridcols=3, gridrows=3,
            #                 iteraxis='antenna', coloraxis = color, showgui=False, 
            #                 plotfile=caltable.replace('.gcal',f'_{color}.png'), dpi=300
            #             )

            # if selfcal_loop == nloops-1:
            #     prev_caltables = sorted(glob.glob('*.gcal'))
            #     print("Applying the caltable derived from last gaincal iteration")
            #     applycal(vis=vis, gaintable = prev_caltables, parang=False )

  



set_working_dir()
# large_map()
selfcal()



# imagename='target_trial'
# tclean(
#     vis = vis, imagename=imagename, imsize=imsize, cell=cell,
#     gridder = gridder, wprojplanes = wprojplanes, deconvolver = deconvolver,
#     weighting = weighting, robust = robust, niter=1, threshold = '0.25mJy',
#     nterms = nterms, pblimit = -1, savemodel= 'modelcolumn',interactive=False
# )

# plotms(
#     vis=vis, xaxis='UVwave', yaxis='amp', ydatacolumn='model',avgchannel='64',avgtime='300',
#     showgui=False, plotfile=imagename+'.png'
# )


# caltable='target_trial.gcal'
# gaincal(vis =vis, caltable = caltable, refant = refant, solint = '30s',
#                     gaintype = 'G', gaintable='',  minsnr = 3,
#                     calmode = 'p', append=False, parang=False)
#!/usr/bin/env python
import sys
import threading
import numpy as np
from collections import deque
import hcipy
from configobj import ConfigObj
import time
import matplotlib.pyplot as plt
from pathlib import Path

from ..common import plotting_funcs as pf
from ..common import classes as ff_c
from ..common import fake_hardware as fhw
from ..common import support_functions as sf

def run_fastandfurious_test(camera=None, aosystem=None, config=None, configspec=None,
        my_deque=None, my_event=None, plotter=None):
    if my_deque is None:
        my_deque = deque()

    if my_event is None:
        my_event = threading.Event()
    settings = sf.validate_config(config, configspec)

    #----------------------------------------------------------------------
    # Control Loop parameters
    #----------------------------------------------------------------------
    Niter             = settings['LOOP_SETTINGS']['N iter']
    gain              = settings['LOOP_SETTINGS']['gain']
    leak_factor       = settings['LOOP_SETTINGS']['leak factor']
    chosen_mode_basis = settings['LOOP_SETTINGS']['Used mode basis']
    Nmodes            = settings['LOOP_SETTINGS']['Number of modes']
    Nimg_avg          = settings['LOOP_SETTINGS']['N images averaged']
    control_even      = settings['LOOP_SETTINGS']['control even modes']
    control_odd       = settings['LOOP_SETTINGS']['control odd modes']

    #----------------------------------------------------------------------
    # Optical model parameters
    #----------------------------------------------------------------------
    # Optical properties
    wavelength = settings['MODELLING']['wavelength (m)']
    mas_pix = settings['MODELLING']['pixel scale (mas/pix)']

    # Pupil and focal plane sampling
    Npix_pup = settings['MODELLING']['N pix pupil']
    Npix_foc = settings['MODELLING']['N pix focal']

    # Aperture and DM configuration
    chosen_aperture = settings['MODELLING']['aperture']
    rotation_angle_aperture = settings['MODELLING']['rotation angle aperture (deg)']
    rotation_angle_dm = settings['MODELLING']['rotation angle dm (deg)']

    # Image orientation settings
    rotation_angle_deg = settings['MODELLING']['rotation angle im (deg)']
    flip_x = settings['MODELLING']['flip_x']
    flip_y = settings['MODELLING']['flip_y']

    # Reference PSF settings
    oversampling_factor = settings['MODELLING']['ref PSF oversampling factor']
    #----------------------------------------------------------------------
    # F&F parameters
    #----------------------------------------------------------------------
    xcen                = settings['FF_SETTINGS']['xcen']
    ycen                = settings['FF_SETTINGS']['ycen']
    #WILBY SMOOTHIN IS NOT IMPLEMENTED YET!!!
    apply_smooth_filter = settings['FF_SETTINGS']['Apply smooth filter']
    epsilon             = settings['FF_SETTINGS']['epsilon']
    SNR_cutoff          = settings['FF_SETTINGS']['SNR cutoff']
    #automatically sub the background in the camera frame
    #this is not used right now anywhere in this script
    auto_background     = settings['FF_SETTINGS']['auto_background']

    #----------------------------------------------------------------------
    # Simulation parameters
    #----------------------------------------------------------------------
    flux                = settings['SIMULATION']['flux']
    exptime             = settings['SIMULATION']['exptime']
    rms_wfe             = settings['SIMULATION']['rms_wfe']
    seed                = settings['SIMULATION']['seed']
    #----------------------------------------------------------------------
    # Load the classes
    #----------------------------------------------------------------------
   


    Aperture = ff_c.Aperture(Npix_pup=Npix_pup,
                             aperturename=chosen_aperture,
                             rotation_angle_aperture=rotation_angle_aperture)

    OpticalModel = ff_c.SystemModel(aperture=Aperture,
                                    Npix_foc=Npix_foc,
                                    mas_pix=mas_pix,
                                    wavelength=wavelength)
    

    FnF = ff_c.FastandFurious(SystemModel=OpticalModel,
                              leak_factor=leak_factor,
                              gain=gain,
                              epsilon=epsilon,
                              chosen_mode_basis=chosen_mode_basis,
                              #apply_smoothing_filter=apply_smooth_filter,
                              number_of_modes=Nmodes)
    #----------------------------------------------------------------------
    # Load instruments
    #----------------------------------------------------------------------
    if camera == 'Sim' and aosystem == 'Sim':
        Camera = fhw.FakeDetector(opticalsystem=OpticalModel,
                                  flux = flux,
                                  exptime=exptime,
                                  dark_current_rate=0,
                                  read_noise=10,
                                  flat_field=0,
                                  include_photon_noise=True,
                                  xsize=1024,
                                  ysize=1024,
                                  field_center_x=330,
                                  field_center_y=430)

        AOsystem = fhw.FakeAOSystem(OpticalModel, modebasis=FnF.mode_basis,
                                    initial_rms_wfe=rms_wfe, seed=seed)
                                    #rotation_angle_dm = rotation_angle_dm)
    else:
        Camera = camera
        AOsystem = aosystem
    # generating the first reference image
    data_raw = Camera.take_image()
    data_ref = sf.reduce_images(data_raw, xcen=xcen, ycen=ycen,
                                          npix=Npix_foc,
                                          refpsf=OpticalModel.ref_psf.shaped,
                                          )
    # Take first image
    FnF.initialize_first_image(data_ref)
    #MAIN LOOP SETUP AND RUNNING
    #----------------------------------------------------------------------

    SRA_measurements = np.zeros(Niter)
    VAR_measurements = np.zeros(Niter)

    SRA_measurements[SRA_measurements==0] = np.nan
    VAR_measurements[VAR_measurements==0] = np.nan
    t0 = time.time()

    test_rot = np.arange(100)
    rotation_angle_threshold = 5
    rotation_angle_deg_pre = rotation_angle_aperture

    #create zernike mode
    mode_basis = hcipy.make_zernike_basis(5, 11.3, Aperture.pupil_grid, 5)
    mode_basis = sf.orthonormalize_mode_basis(mode_basis, Aperture.aperture)
    amplitude = 1.


    for mode, i in zip(mode_basis, np.arange(len(mode_basis))):
        
        # creating the phase that will be introduced
        phase_rad = mode * amplitude

        # ipdb.set_trace()
        microns = phase_rad * FnF.wavelength / (2 * np.pi) * 1e6
        #move the dm and get the dm_microns map
        _,dm_microns = AOsystem.set_dm_data(microns)

    

        image = Camera.take_image()

        pupil_wf = hcipy.Wavefront(Aperture.aperture * np.exp(1j * phase_rad),
                             wavelength=FnF.wavelength)
        focal_wf = OpticalModel.propagator(pupil_wf)

        # getting the images by theory and practice
        image_theory = focal_wf.power

        image_bench = sf.reduce_images(image, xcen=xcen, ycen=ycen, npix=Npix_foc,
                                refpsf=OpticalModel.ref_psf.shaped,
                                )
        
        ipdb.set_trace()
        plt.ion()
        fig, ax = plt.subplots(1)
        ax.imshow(np.log10(image_theory.shaped / image_theory.max()), vmin=-5)
        plt.draw()
        plt.pause(0.02)
        for i in range(3):
            ax.imshow(np.log10(image_theory.shaped / image_theory.max()), vmin=-5, alpha = 0.5)
            plt.pause(1)
            ax.imshow(np.log10(np.abs(image_bench) / image_bench.max()), vmin=-3, alpha=0.5)
            plt.pause(1)
        plt.ioff()
        plt.close(fig)
        plt.figure(figsize=(8, 8))

        plt.subplot(2, 2, 1)
        hcipy.imshow_field(np.log10(image_theory / image_theory.max()), vmin=-5)
        plt.colorbar()
        plt.title('theory')

        plt.subplot(2, 2, 2)
        plt.imshow(np.log10(np.abs(image_bench) / image_bench.max()), vmin=-3, origin='lower')
        plt.colorbar()
        plt.title('bench')

        max_theory = np.max(np.abs(phase_rad))

        plt.subplot(2, 2, 3)
        hcipy.imshow_field(phase_rad, cmap='bwr', vmin=-max_theory, vmax=max_theory)
        plt.colorbar()

        plt.title('theory')

        max_bench = np.max(np.abs(dm_microns))

        plt.subplot(2, 2, 4)
        plt.imshow(dm_microns, origin='lower', cmap='bwr',
                   vmin=-max_bench, vmax=max_bench)

        plt.colorbar()

        plt.title('Applied command')

        plt.show()
        # converting the volt


if __name__ == "__main__":
    run_fastandfurious_test()
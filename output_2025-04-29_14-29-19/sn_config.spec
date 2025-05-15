[SN_SETTINGS]
    #x and y setpoints
    xcen = integer
    ycen = integer
    cropsize = integer_or_none
    IWA = float(min=1)
    OWA = float(max=11)
    THETA1 = float
    THETA2 = float
    FULL_DARKHOLE = boolean
    DM_AMPLITUDE_VOLTS = float(max=7)
    NUM_ITERATIONS = integer

[CAMERA_CALIBRATION]
    bgddir = string

[DM_REGISTRATION]
    calspot_kx = float
    calspot_ky = float
    calspot_amp = float(min=0)

    [[MEASURED_PARAMS]]    
        centerx = float
        centery = float
        angle = float
        lambdaoverd = float

    [[INTENSITY_CAL]]
        stepsize = float(min=0)
        min = float(min=0)
        max = float
        ical_dm_amplitude = float(min=0)
        aperture_radius = float(min=0)

[SIMULATION]
    [[OPTICAL_PARAMS]]
        wavelength (m)                        = float(min=0, max=10e-6)
        N pix pupil                       = integer
        N pix focal                       = integer
        pixel scale (mas/pix)             = float(min=0)
        rotation angle im (deg)           = float(min=0)
        #flips are applied last, not first
        flip_x                             = boolean
        flip_y                             = boolean
        [[[APERTURE]]]
            aperture                      = option('keck', 'subaru')
            rotation angle aperture (deg) = float
        [[[CORONAGRAPH_MASK]]]
            IWA_mas                       = float(min=0)
        [[[LYOT_STOP]]]
            lyot stop                     = option('NIRC2_incircle_mask', 'NIRC2_large_hexagonal_mask', 'NIRC2_Lyot_Stop')
            rotation angle lyot (deg)     = float


    [[CAMERA_PARAMS]]
        flux                 = float(min=0)
        exptime              = float(min=0)
        read_noise           = float(min=0)
        dark_current_rate    = float(min=0)
        flat_field           = float
        include_photon_noise = boolean
        xsize                = integer(min=0)
        ysize                = integer(min=0)
        field_center_x       = integer(min=0)
        field_center_y       = integer(min=0)
        bad_pixel_mask       = string_or_none
        output_directory     = string_or_none

    [[AO_PARAMS]]
        modebasis               = option_or_none('zernike', 'pixel', 'disk_harmonics', 'fourier')
        initial_rms_wfe         = float(min=0)
        seed                    = integer_or_none
        rotation_angle_dm       = float
        flip_x_dm               = boolean
        flip_y_dm               = boolean
        num_actuators_across    = integer_or_none
        actuator_spacing        = float_or_none

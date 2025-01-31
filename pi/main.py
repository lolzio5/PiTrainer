import numpy as np
import time
from filtering import MovingAverage
import accelerometer
import magnet
from rep_analysis import SetData, Exercise, analyse_set, isolate_axis
from kalman import KalmanFilter3D


def main() -> None:
    # accelx_filter = MovingAverage(15)
    # accely_filter = MovingAverage(15)
    # accelz_filter = MovingAverage(15)

    # magnetx_filter = MovingAverage(15)
    # magnety_filter = MovingAverage(15)
    # magnetz_filter = MovingAverage(15)

    accelx_filter = KalmanFilter3D(0.01)
    accely_filter = KalmanFilter3D(0.01)
    accelz_filter = KalmanFilter3D(0.01)

    accelerometer.lis3dh_init()
    # magnet.Mag_init()

    accel_filtered: list[ tuple[float, float, float] ] = []
    vel_filtered: list[ tuple[float, float, float ]] = []
    pos_filtered: list[ tuple[float, float, float ]] = []

    try:
        while True:
            accelx, accely, accelz = accelerometer.lis3dh_read_xyz()
            # current_magn = magnet.Mag_Read()

            # accel_filtered.append((accelx_filter.update(current_accel[0]),
            #                    accely_filter.update(current_accel[1]),
            #                    accelz_filter.update(current_accel[2]),))

            accelx_filter.step(accelx)
            accely_filter.step(accely)
            accelz_filter.step(accelz)

            accel_filtered.append((accelx_filter.acceleration, 
                                   accely_filter.acceleration,
                                   accelz_filter.acceleration))
            
            vel_filtered.append((accelx_filter.velocity, 
                                   accely_filter.velocity,
                                   accelz_filter.velocity))
            
            pos_filtered.append((accelx_filter.position, 
                                   accely_filter.position,
                                   accelz_filter.position)) 
                               

            # rep counter

            time.sleep(0.01)

    except KeyboardInterrupt:
        print('Exiting...')
        print('You followed this displacement:\n')
        print(f'\nACCELERATION\n: {isolate_axis(accel_filtered, 0)}')
        print(f'\nVELOCITY\n: {isolate_axis(accel_filtered, 1)}')
        print(f'\nDISPLACEMENT\n: {isolate_axis(accel_filtered, 2)}')


if __name__ == '__main__':
    main()
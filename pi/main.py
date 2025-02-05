import numpy as np
import time
import json
import requests
import asyncio

from filtering import MovingAverage, KalmanFilter3D
import accelerometer
import magnet
from rep_analysis import SetData, Exercise, analyse_set, isolate_axis

## ---- CONSTANTS ---- ##
workout_states = [
    'Tricep Extension',
    'Cable Row',
    'Idle'
]

BACKEND_URL = "http://18.134.249.18:80/api"

## ---- UTILS FUNCTIONS ---- ##

def poll_workout_state() -> str:
    r = requests.get(url=BACKEND_URL + "/pipoll")
    data = r.json()
    return data
    

def send_rep_data(workout_name, rep_nb, timestamp, accel, vel, pos, magn) -> str:
    data = {
        'Name': workout_name ,
        'Rep Number': rep_nb ,
        'Timestamp': timestamp ,
        'Acceleration 3D': accel ,
        'Velocity 3D': vel ,
        'Position 3D': pos ,
        'Magnetometer 3D': magn,
        'User': "lv322"
    }
    r = requests.post(url=f"{BACKEND_URL}/process", data=data)
    return r.text

def send_rep(workout_name, rep_nb, timestamp) -> str:
    data = {
        'Name': workout_name ,
        'Rep Number': rep_nb ,
        'Timestamp': timestamp ,
        'User': "lv322"
    }
    r = requests.post(url=f"{BACKEND_URL}/rep", data=data)
    return r.text



def main() -> None:
    ts = 0.01
    M = 50

    accelx_filter = KalmanFilter3D(ts)
    accely_filter = KalmanFilter3D(ts)
    accelz_filter = KalmanFilter3D(ts)

    magnetx_filter = MovingAverage(M)
    magnety_filter = MovingAverage(M)
    magnetz_filter = MovingAverage(M)

    accelerometer.lis3dh_init()
    magnet.Mag_init()

    accel_filtered: list[ tuple[float, float, float ] ] = []
    vel_filtered:   list[ tuple[float, float, float ] ] = []
    pos_filtered:   list[ tuple[float, float, float ] ] = []

    mag_filtered:   list[ tuple[float, float, float ] ] = []

    workout_state = workout_states[-1]
    current_rep = 0

    init_time = time.time()
    g = 9.81

    print('All ready! Sampling now...')
    i = 0
    try:
        while True:
            # Get workout State
            if i % 1/ts == 0:
                workout_state = poll_workout_state()

            # Timeout check
            if time.time() - init_time > 300: # 5 min workout timeout
                workout_state = workout_states[-1]
                accel_filtered.clear()
                vel_filtered.clear()
                pos_filtered.clear()
                mag_filtered.clear()

            # Do nothing if in Idle mode, check every 0.5s
            if workout_state == workout_states[-1]: # IF IDLE
                time.sleep(0.5/ts)
                continue

            accelx, accely, accelz = accelerometer.lis3dh_read_xyz()
            if i % 2 == 0: # 50 Hz for ts = 0.01 / fs = 100Hz
                magx, magy, magz = magnet.Mag_Read()

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
                               
            mag_filtered.append((
                magnetx_filter.update(magx),
                magnety_filter.update(magy),
                magnetz_filter.update(magz)
            ))

        

            # current_rep, rep_counted = ... # rep counter

            # if rep_counted:
            #     send_rep_data(workout_state, current_rep, 
            #                   time.time(), accel_filtered, 
            #                   vel_filtered, pos_filtered, 
            #                   mag_filtered)
                # current_rep = 0

            time.sleep(ts)

    except (KeyboardInterrupt, Exception) as e:
        print(e)
        print(accel_filtered)
        print('\n\n\n\n')
        print(mag_filtered)
        print('Restarting...')
        # main()
        pass


if __name__ == '__main__':
    main()

    # print(poll_workout_state())
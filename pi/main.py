import numpy as np
import time
import json
import requests

from filtering import MovingAverage, KalmanFilter3D
import accelerometer
import magnet
from rep_analysis import SetData, Exercise, analyse_set, isolate_axis

## ---- CONSTANTS ---- ##
exercises = [
    'Tricep Pulldown',
    'Cable Row',
    'Other'
]

workout_states = [
    'Idle',
    'Working Out',
]

BACKEND_URL = "http://pastebin.com/api/api_post.php" # ??

## ---- UTILS FUNCTIONS ---- ##

def poll_workout_state() -> str:
    r = requests.get(url=BACKEND_URL, params=['Workout State', 'Workout Name'])
    data = r.json()
    return data['Workout State'], data['Workout Name']
    


def send_rep_data(workout_name, rep_nb, timestamp, accel, vel, pos, magn) -> str:
    data = {
        'Name': workout_name ,
        'Rep Number': rep_nb ,
        'Timestamp': timestamp ,
        'Acceleration 3D': accel ,
        'Velocity 3D': vel ,
        'Position 3D': pos ,
        'Magnetometer 3D': magn ,
    }
    r = requests.post(url=BACKEND_URL, data=data)
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
    # magnet.Mag_init()

    accel_filtered: list[ tuple[float, float, float ] ] = []
    vel_filtered:   list[ tuple[float, float, float ] ] = []
    pos_filtered:   list[ tuple[float, float, float ] ] = []

    mag_filtered:   list[ tuple[float, float, float ] ] = []

    workout_state = workout_states[0]
    workout_name = exercises[-1]
    current_rep = 0

    init_time = time.time()
    g = 9.81

    try:
        while True:
            # Get workout State
            workout_state, workout_name = poll_workout_state()

            # Timeout check
            if time.time() - init_time > 300: # 5 min workout timeout
                workout_state = workout_states[-1]
                accel_filtered.clear()
                vel_filtered.clear()
                pos_filtered.clear()
                mag_filtered.clear()

            # Do nothing if in Idle mode
            if workout_state == workout_states[-1]: # IF IDLE
                time.sleep(ts)
                continue

            accelx, accely, accelz = accelerometer.lis3dh_read_xyz()
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

            current_rep, rep_counted = ... # rep counter

            if rep_counted:
                send_rep_data(workout_name, current_rep, 
                              time.time(), accel_filtered, 
                              vel_filtered, pos_filtered, 
                              mag_filtered)
                current_rep = 0

            time.sleep(ts)

    except:
        print('Restarting...')
        main()
        pass


if __name__ == '__main__':
    main()
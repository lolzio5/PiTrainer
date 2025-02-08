import numpy as np
import time
import json
import requests

from filtering import MovingAverage, KalmanFilter3D
import accelerometer
import magnet
from workout import Workout
from model_preprocessing import process_data_to_dict
# from rep_analysis import SetData, Exercise, analyse_set, isolate_axis
from rep_analysis import sort_reps_by_pt, SetData

## ---- CONSTANTS ---- ##
workout_states = [
    'Tricep Extension',
    'Cable Row',
    'Idle'
]

BACKEND_URL = "http://18.134.249.18:80/api"
USER = "lv322"

## ---- UTILS FUNCTIONS ---- ##

def get_workout_state() -> str:
    # r = requests.get(url=BACKEND_URL + "/pipoll" + f"?user={USER}")
    r = requests.get(url=BACKEND_URL + "/pipoll" + f"/{USER}")
    data = r.json()
    return data
    

def send_rep_data(data, current_rep_sent) -> str:
    json_data = data
    json_data['Rep Number'] = current_rep_sent
    json_data['User'] = USER

    r = requests.post(url=f"{BACKEND_URL}/process", data=json_data)
    return r.text


def send_rep_number(workout_name, rep_nb, timestamp) -> str:
    data = {
        'Name': workout_name ,
        'Rep Number': rep_nb ,
        'Timestamp': timestamp ,
        'User': USER
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

    data = SetData()

    current_workout_state = workout_states[-1]
    previous_workout_state = workout_states[-1]
    current_workout = Workout("Rows")
    current_rep = 0

    init_time = time.time()
    g = 9.81

    print('All ready! Sampling now...')
    i = 0
    try:
        while True:
            # Get workout State
            if i % 1/ts == 0:
                previous_workout_state = current_workout_state
                current_workout_state = get_workout_state()

            # Timeout check
            if time.time() - init_time > 300: # 5 min workout timeout
                current_workout_state = workout_states[-1]
                data = SetData()

            # STATE MACHINE
            match current_workout_state:
                case "Rows":
                    if previous_workout_state != current_workout_state:
                        current_workout = Workout("Rows")

                case "Tricep Extensions":
                    if previous_workout_state != current_workout_state:
                        current_workout = Workout("Tricep Extensions")

                case "Idle":
                    if previous_workout_state == current_workout_state:
                        # poll every 0.5s
                        time.sleep(0.5/ts)
                        
                    else:
                        # Sort Reps
                        accel_sorted, vel_sorted, pos_sorted, mag_sorted = sort_reps_by_pt(data, current_workout.select, current_workout_state)
                            
                        for i in range(current_workout.count):
                            # Package Rep Data
                            rep_features = process_data_to_dict( 
                                        accel_sorted[i], vel_sorted[i], 
                                        pos_sorted[i], mag_sorted[i])
                            # Send rep data
                            send_rep_data(rep_features, i+1)

                case _: # default case is working out
                    accelx, accely, accelz = accelerometer.lis3dh_read_xyz()
                    if i % 2 == 0: # 50 Hz for ts = 0.01 / fs = 100Hz
                        magx, magy, magz = magnet.Mag_Read()

                    accelx_filter.step(accelx)
                    accely_filter.step(accely)
                    accelz_filter.step(accelz)

                    data.accel.append((accelx_filter.acceleration, 
                                        accely_filter.acceleration,
                                        accelz_filter.acceleration))
                    
                    data.vel.append((accelx_filter.velocity, 
                                        accely_filter.velocity,
                                        accelz_filter.velocity))
                    
                    data.pos.append((accelx_filter.position, 
                                        accely_filter.position,
                                        accelz_filter.position)) 
                                    
                    data.magn.append((
                        magnetx_filter.update(magx),
                        magnety_filter.update(magy),
                        magnetz_filter.update(magz)
                    ))

                    counted, rep_nb = current_workout.update([accelx_filter.velocity, accely_filter.velocity, accelz_filter.velocity],
                                        [magnetx_filter.output, magnety_filter.output, magnetz_filter.output])
                    
                    if counted:
                        send_rep_number(current_workout.workout, rep_nb, time.time())

        
            time.sleep(ts)

    except (KeyboardInterrupt, Exception) as e:
        # print(e)
        # print(accel_filtered)
        # print('\n\n\n\n')
        # print(mag_filtered)
        print('Restarting...')
        # main()
        pass


if __name__ == '__main__':
    main()

    # print(poll_workout_state())
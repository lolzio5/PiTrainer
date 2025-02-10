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
    'Lat Pulldowns',
    'Seated Cable Rows',
    'Idle'
]

BACKEND_URL = "http://18.134.249.18:80/api"
USER = "pi"

## ---- UTILS FUNCTIONS ---- ##

def get_workout_state() -> str:
    # data = json.dumps({"pi_id": USER})
    PI_ID = USER
    r = requests.post(f"{BACKEND_URL}/pipoll", json=PI_ID)
    # print(r)
    # print(r.text)
    data = r.json()
    return data["response"]
    

## MODIFIY
def send_rep_data(data, current_rep_sent) -> str:
    json_data = data
    json_data['Rep Number'] = current_rep_sent
    json_data['User'] = USER

    r = requests.post(url=f"{BACKEND_URL}/process", data=json_data)
    return r.text


def send_rep_number(workout_name, rep_nb) -> str:
    data = {
        'reps': rep_nb ,
        'pi_id': USER
    }
    r = requests.post(url=f"{BACKEND_URL}/rep", json=data)
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

    data = SetData([], [], [], [], [], ts)

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
            i += 1
            time.sleep(ts)

            # Get workout State
            previous_workout_state = current_workout_state
            if (i % 50) == 0:
                # previous_workout_state = current_workout_state
                current_workout_state = get_workout_state()
                print(f'Polled State: {current_workout_state} {i}')

            # # Timeout check
            # if time.time() - init_time > 300: # 5 min workout timeout
            #     current_workout_state = workout_states[-1]
            #     data = SetData([], [], [], [], [], ts)

            # STATE MACHINE
            match current_workout_state:
                case 'Seated Cable Rows':
                    if previous_workout_state != current_workout_state:
                        print('Starting Seated Cable Rows...')
                        current_workout = Workout("Rows")
                        accelx_filter.clear()
                        accely_filter.clear()
                        accelz_filter.clear()
                        magnetx_filter.clear()
                        magnety_filter.clear()
                        magnetz_filter.clear()
                        data = SetData([], [], [], [], [], ts)

                case "Lat Pulldowns":
                    if previous_workout_state != current_workout_state:
                        print('Starting Lat Pulldowns...')
                        current_workout = Workout("Tricep Extensions")
                        accelx_filter.clear()
                        accely_filter.clear()
                        accelz_filter.clear()
                        magnetx_filter.clear()
                        magnety_filter.clear()
                        magnetz_filter.clear()
                        data = SetData([], [], [], [], [], ts)

                case "Idle":
                    if previous_workout_state == current_workout_state:
                        continue
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

                        accelx_filter.clear()
                        accely_filter.clear()
                        accelz_filter.clear()
                        magnetx_filter.clear()
                        magnety_filter.clear()
                        magnetz_filter.clear()
                        data = SetData([], [], [], [], [], ts)

                case "Pseudo Idle":
                    continue

                case _:
                    continue

            if current_workout_state in ["Idle", "Pseudo Idle"]:
                # time.sleep(ts)
                continue

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
                send_rep_number(current_workout.workout, rep_nb)
                data.sample_time.append(time.time())
                print(f'Rep {rep_nb} counted!')

    except (KeyboardInterrupt, Exception) as e:
        print(e)
        # print(accel_filtered)
        # print('\n\n\n\n')
        # print(mag_filtered)
        print('Restarting...')
        # main()
        pass


if __name__ == '__main__':
    main()
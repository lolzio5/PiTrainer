import numpy as np
import time
import json
import requests

from filtering import MovingAverage, KalmanFilter3D
import accelerometer
import magnet
from workout import Workout
from model_preprocessing import process_rep_to_dict
# from rep_analysis import SetData, Exercise, analyse_set, isolate_axis
from rep_analysis import give_feedback, SetData, separate_reps, workout_feedback, sort_reps

## ---- CONSTANTS ---- ##
workout_states = [
    'Lat Pulldowns',
    'Seated Cable Rows',
    'Idle'
]

BACKEND_URL = "http://3.10.117.27:80/api"
USER = "pi"

## ---- UTILS FUNCTIONS ---- ##

def get_workout_state() -> str:
    PI_ID = USER
    r = requests.post(f"{BACKEND_URL}/pipoll", json=PI_ID)
    j = r.json()
    return r.text if 'response' not in j.keys() else j['response']

## MODIFIY
def send_workout_data(all_sets_data: list[dict], workout_name: str) -> str:
    json_data = {}
    json_data['sets_data'] = all_sets_data
    json_data['pi_id'] = USER
    json_data['name'] = workout_name

    r = requests.post(url=f"{BACKEND_URL}/process", json=json_data)
    return r.text

def send_set_data(feedback: dict[str, float|str], set_count: int) -> str:
    json_data = feedback
    json_data['set_count'] = set_count
    json_data['pi_id'] = USER

    r = requests.post(url=f'{BACKEND_URL}/anal', json=json_data)
    return r.text


def send_rep_number(rep_nb) -> str:
    data = {
        'reps': rep_nb ,
        'pi_id': USER
    }
    r = requests.post(url=f"{BACKEND_URL}/rep", json=data)
    return r.text



def main() -> None:
    print('Starting...')
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

    data = SetData([], [], [], [], [], [], ts)

    current_workout_state = workout_states[-1]
    previous_workout_state = workout_states[-1]
    current_workout = Workout("Rows")
    set_count: int = 0
    current_workout_feedbacks: list[ dict[str, float] ] = []
    workout_features_per_rep = []


    init_time = time.time()
    g = 9.81

    print('All ready! Sampling now...')
    i = 0
    # try:
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
        #     data = SetData([], [], [], [], [], [], ts)

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
                    data = SetData([], [], [], [], [], [], ts)

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
                    data = SetData([], [], [], [], [], [], ts)

            case "Idle":
                if previous_workout_state == current_workout_state:
                    continue
                if previous_workout_state != 'Pseudo Idle':
                    # package last set
                    # Sort Reps
                    accel_reps, vel_reps, pos_reps, mag_reps, data = separate_reps(data, current_workout.select)
                    # DATA.REP_INDICES ARE NOW UPDATED!! 
                    num_reps = len(accel_reps)
                    print(f'num_reps: {num_reps}')
                    for i in range(num_reps):
                        workout_features_per_rep.append(
                            process_rep_to_dict(accel_reps[i], vel_reps[i], pos_reps[i], mag_reps[i])
                        )

                    feedback = give_feedback(accel_reps, vel_reps, pos_reps, mag_reps, 
                                            data.sample_times, data.rep_indices)
                    print(f'feedback calculated: {feedback}')
                    current_workout_feedbacks.append(feedback)

                    send_set_data(feedback, set_count)
                
                # Send WORKOUT DATA (multiple sets)
                # overall_feedback = workout_feedback(current_workout_feedbacks)
                print(f'features per rep shape: {np.shape(workout_features_per_rep)}')
                print(workout_features_per_rep)
                response = send_workout_data(workout_features_per_rep, current_workout.workout)
                print(response)
                set_count = 0
                workout_features_per_rep.clear()
                current_workout_feedbacks.clear()
                accelx_filter.clear()
                accely_filter.clear()
                accelz_filter.clear()
                magnetx_filter.clear()
                magnety_filter.clear()
                magnetz_filter.clear()
                data = SetData([], [], [], [], [], [], ts)

            case "Pseudo Idle":
                if previous_workout_state == current_workout_state or previous_workout_state == 'Idle':
                    continue
                # Sort Reps
                accel_reps, vel_reps, pos_reps, mag_reps, data = separate_reps(data, current_workout.select)
                # DATA.REP_INDICES ARE NOW UPDATED!! 
                num_reps = len(accel_reps)
                print(f'num_reps: {num_reps}')
                for i in range(num_reps):
                    workout_features_per_rep.append(
                        process_rep_to_dict(accel_reps[i], vel_reps[i], pos_reps[i], mag_reps[i])
                    )

                feedback = give_feedback(accel_reps, vel_reps, pos_reps, mag_reps, 
                                         data.sample_times, data.rep_indices)
                print(f'feedback calculated: {feedback}')
                current_workout_feedbacks.append(feedback)

                print(f'feedback: {feedback}')

                set_count += 1
                send_set_data(feedback, set_count)

                accelx_filter.clear()
                accely_filter.clear()
                accelz_filter.clear()
                magnetx_filter.clear()
                magnety_filter.clear()
                magnetz_filter.clear()
                data = SetData([], [], [], [], [], [], ts)
                # Send SET data
                continue

            case _:
                set_count = 0
                accelx_filter.clear()
                accely_filter.clear()
                accelz_filter.clear()
                magnetx_filter.clear()
                magnety_filter.clear()
                magnetz_filter.clear()
                data = SetData([], [], [], [], [], [], ts)
                continue

        if current_workout_state in ["Idle", "Pseudo Idle"]:
            # time.sleep(ts)
            continue

        accelx, accely, accelz = accelerometer.lis3dh_read_xyz()
        # print(accelx, accely, accelz)
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

        data.sample_times.append(time.time())

        counted, rep_nb = current_workout.update([accelx_filter.velocity, accely_filter.velocity, accelz_filter.velocity],
                            [magnetx_filter.output, magnety_filter.output, magnetz_filter.output])
        
        if counted:
            send_rep_number(rep_nb)
            data.rep_indices.append(len(data.sample_times)-1)
            print(f'Rep {rep_nb} counted!')

    # except (KeyboardInterrupt, Exception) as e:
    #     print(e)
    #     # print(accel_filtered)
    #     # print('\n\n\n\n')
    #     # print(mag_filtered)
    #     print('Restarting...')
    #     # main()
    #     pass


if __name__ == '__main__':
    main()
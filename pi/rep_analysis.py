# import smbus2
# import gpiozero
import json
import time

from dataclasses import dataclass
from enum import Enum
import numpy as np
from scipy import signal
from scipy.signal import find_peaks
from scipy.stats import linregress
import pandas as pd
import ast
import re

import matplotlib.pyplot as plt
from filtering import MovingAverage
from workout import Workout

# import magnet as mag
# import accelerometer

"""
NOTE:
For this, the data will be packaged as such:
all points correspond to an entry in the list:

eg. SetData.accel = [   
                        [x0, y0, z0],
                        [x1, y1, z2],
                        [x2, y2, z2],
                        ...
                        ...
                    ]

"""

"""
NOTE:
    THIS WAS MEANT AS A BACKUP FOR THE MACHINE LEARNING MODEL
    RUNNING ON THE SERVER.

    THIS CAN BE USED ON THE PI. but it currently IS NOT
"""

## CLASSES
@dataclass
class SetData:
    accel: list[ list[ float, float, float] ]
    vel : list[ list[float,float,float]]
    pos : list[ list[float,float,float]]
    magn: list[ list[float, float, float] ]
    sample_time: list[ float]
    ts : float

## UTILS FUNCTIONS
def isolate_axis(points: list[list[float]], axis: int) -> list[float]:
    return [point[axis] for point in points]

    
#CUMSUM DOESN'T WORK (See graphs below)
def integrate(data: list [list[float, float, float]], dt: float=1):
    #Gonna leave plots in here so you can see the issue
    plt.figure()
    intx = np.cumsum(isolate_axis(data, 0)) * dt
    inty = np.cumsum(isolate_axis(data, 1)) * dt
    intz = np.cumsum(isolate_axis(data, 2)) * dt
    plt.plot(intx)
    plt.title("Cum Sum")
    # return [(float(intx[i]), float(inty[i]), float(intz[i])) for i in range(len(intx))]

    posx = [data[0][0]]
    posy = [data[0][1]]
    posz = [data[0][2]]
    for i in range(1,len(data)):
        posx.append(posx[-1] + (data[i][0] - data[i-1][0]) * dt)
        posy.append(posy[-1] + (data[i][1]- data[i-1][0]) * dt)
        posz.append(posz[-1] + (data[i][2] - data[i-1][0]) * dt)

    plt.figure()
    plt.plot(posx)
    plt.title("Manual Integration")
    plt.show()
    plt.close()#Put a breakpoint here to see graphs
    output = []
    [output.append([posx[i],posy[i],posz[i]]) for i in range(len(posx))]
    return output


def package_ax_by_ax(data: SetData):
    accel = [isolate_axis(data.accel, 0), isolate_axis(data.accel, 1), isolate_axis(data.accel, 2)]
    vel = [isolate_axis(data.vel, 0), isolate_axis(data.vel, 1), isolate_axis(data.vel, 2)]
    pos = [isolate_axis(data.pos, 0), isolate_axis(data.pos, 1), isolate_axis(data.pos, 2)]
    mag = [isolate_axis(data.magn, 0), isolate_axis(data.magn, 1), isolate_axis(data.magn, 2)]

    return accel, vel, pos, mag


def package_ax_by_ax(points):
    return [isolate_axis(points, 0), isolate_axis(points, 1), isolate_axis(points, 2)]


def package_points(x, y, z):
    return [ (x[i], y[i], z[i]) for i in range(len(x)) ] if len(x) == len(y) == len(z) else None



def remove_repeat_peaks(peaks : list[float], peak_times: list[float], timeout : float):
    new_peaks = [peaks[0]]
    new_peak_times = [peak_times[0]]
    for i in range(1,len(peak_times)-2):
        if  (peak_times[i] - new_peak_times[-1] > timeout):
            new_peaks.append(peaks[i])
            new_peak_times.append(peak_times[i])
    
    return new_peaks, new_peak_times

# CHECKKKKK / REWORK
def thresholds_for_peaks(sig: list[float],percentile : float = 0.75, std_multiplier : float = 1.5) -> float:
    naive_peaks, _ = find_peaks(sig)
    peak_values = [sig[naive_peaks[i]] for i in range(len(naive_peaks))]
    percentile_threshold = np.percentile(peak_values, percentile)
    mean_peak = np.mean(peak_values)
    std_peak = np.std(peak_values)
    std_threshold = mean_peak + std_multiplier * std_peak
    threshold = (percentile_threshold + std_threshold) / 2
    print(f'threshold = {threshold}, nb_peaks = {len(naive_peaks)}')
    return threshold


## ACTUAL FUNCTIONS
#Is this still used??
def sort_reps_by_ax(data: SetData, sel: tuple[int, int], exercise_name: str):
    # (3D axis needed, mag axis needed)

    vel_smoothed = MovingAverage(50)
    vel_smoothed = [vel_smoothed.update(val[sel[0]]) for val in data.vel]#smoothed velocity 

    pos_peaks = find_peaks(vel_smoothed,0.125)[0]
    neg_peaks = find_peaks(np.multiply(vel_smoothed,-1),0.02)[0]

    t_p = [data.sample_time[val] for val in pos_peaks]
    t_n = [data.sample_time[val] for val in neg_peaks]
    pos_peaks, t_p = remove_repeat_peaks(pos_peaks,t_p,1)
    neg_peaks,t_n = remove_repeat_peaks(neg_peaks,t_n,1)

    print(f"LP = {len(pos_peaks)} LN = {len(neg_peaks)}")
    if (len(pos_peaks) > len(neg_peaks)):
        pos_peaks = pos_peaks[:len(neg_peaks)]
    else:
        neg_peaks = neg_peaks[:len(pos_peaks)]
    
    reps = []
    for i in range(0,len(pos_peaks)):
        reps.append(np.sort([pos_peaks[i],neg_peaks[i]]).tolist())
    print(reps)
    
    accel_temp, vel_temp, pos_temp, mag_temp = package_ax_by_ax(data)
    accel = [[], [], []]
    vel = [[], [], []]
    pos = [[], [], []]
    mag = [[], [], []]

    match exercise_name:
        case "Rows":
            accel[0] = [accel_temp[0] [rep[0] : rep[1]] for rep in reps]
            accel[1] = [accel_temp[1] [rep[0] : rep[1]] for rep in reps]
            accel[2] = [accel_temp[2] [rep[0] : rep[1]] for rep in reps]
            vel[0] = [vel_temp[0] [rep[0] : rep[1]] for rep in reps]
            vel[1] = [vel_temp[1] [rep[0] : rep[1]] for rep in reps]
            vel[2] = [vel_temp[2] [rep[0] : rep[1]] for rep in reps]
            pos[0] = [pos_temp[0] [rep[0] : rep[1]] for rep in reps]
            pos[1] = [pos_temp[1] [rep[0] : rep[1]] for rep in reps]
            pos[2] = [pos_temp[2] [rep[0] : rep[1]] for rep in reps]
            mag[0] = [mag_temp[0] [rep[0] : rep[1]] for rep in reps]
            mag[1] = [mag_temp[1] [rep[0] : rep[1]] for rep in reps]
            mag[2] = [mag_temp[2] [rep[0] : rep[1]] for rep in reps]
            
        case "Tricep Extension":
            ...

        case _:
            # By default, separate between the positive peaks
            accel[0] = [accel_temp [reps[j][0] : reps[j+1][0]] for j in range(len(reps)-1)]
            accel[1] = [accel_temp [reps[j][0] : reps[j+1][0]] for j in range(len(reps)-1)]
            accel[2] = [accel_temp [reps[j][0] : reps[j+1][0]] for j in range(len(reps)-1)]
            vel[0] = [vel_temp [reps[j][0] : reps[j+1][0]] for j in range(len(reps)-1)]
            vel[1] = [vel_temp [reps[j][0] : reps[j+1][0]] for j in range(len(reps)-1)]
            vel[2] = [vel_temp [reps[j][0] : reps[j+1][0]] for j in range(len(reps)-1)]
            pos[0] = [pos_temp [reps[j][0] : reps[j+1][0]] for j in range(len(reps)-1)]
            pos[1] = [pos_temp [reps[j][0] : reps[j+1][0]] for j in range(len(reps)-1)]
            pos[2] = [pos_temp [reps[j][0] : reps[j+1][0]] for j in range(len(reps)-1)]
            mag[0] = [mag_temp [reps[j][0] : reps[j+1][0]] for j in range(len(reps)-1)]
            mag[1] = [mag_temp [reps[j][0] : reps[j+1][0]] for j in range(len(reps)-1)]
            mag[2] = [mag_temp [reps[j][0] : reps[j+1][0]] for j in range(len(reps)-1)]
            
    # if package_to_points:
    #     accel = [ [accel[0][i], accel[1], accel[2]] ]

    # they are now in an AXES BY AXES BASIS
    return accel, vel, pos, mag


"""This works more or less. Tested on rep data 8, and 50 reps, and it seems to work well. The issue I ran into was
the timeout for rep removal needing to be changed (from 1 to 0.2). This shouldn't have too much of an effect in the future (since
timestamp data was not included in 50 reps, the time was approximated)

It does still miss around 1-2 reps, but it should be fine for the most part. We can compare the reps counted here, to the reps counted
during the workout, and if this sees less, the extra are counted as average reps, and if there are more, we truncate this?

Also, since negative peaks is very innacurate, we may need to adjust the truncating, in order to pick values closest to the positive peaks"""
def sort_reps_by_pt(data: SetData, sel: tuple[int, int], exercise_name: str=""):
    # (3D axis needed, mag axis needed)

    vel_smoothed = MovingAverage(50)
    vel_smoothed = [vel_smoothed.update(val[sel[0]]) for val in data.vel] #smoothed velocity)

    #This tends to be more accurate
    pthreshold = thresholds_for_peaks(vel_smoothed,0.75,3)
    
    #Tend to be a lot more noisy
    nthreshold = thresholds_for_peaks(np.multiply(vel_smoothed,-1),0.75,2.75) *-1


    pos_peaks = find_peaks(vel_smoothed, pthreshold)[0]
    neg_peaks = find_peaks(np.multiply(vel_smoothed,-1), nthreshold)[0]
    print(f"Before removal : LP = {len(pos_peaks)} LN = {len(neg_peaks)}")

    t_p = [data.sample_time[val] for val in pos_peaks]
    t_n = [data.sample_time[val] for val in neg_peaks]
    
    #The time here may need to be adjusted based on exercise type
    pos_peaks, t_p = remove_repeat_peaks(pos_peaks,t_p,0.2)
    neg_peaks,t_n = remove_repeat_peaks(neg_peaks,t_n,0.2)

    print(f"After Removal : LP = {len(pos_peaks)} LN = {len(neg_peaks)}")
    #Likely need to change this
    if (len(pos_peaks) > len(neg_peaks)):
        pos_peaks = pos_peaks[:len(neg_peaks)]
    else:
        neg_peaks = neg_peaks[:len(pos_peaks)]
    
    reps = []
    for i in range(0,len(pos_peaks)):
        reps.append(np.sort([pos_peaks[i],neg_peaks[i]]).tolist())
    print(reps)
    
    match exercise_name:
        case "Rows":
            accel = [data.accel[ rep[0] : rep[1] ] for rep in reps]
            vel = [data.vel[ rep[0] : rep[1] ] for rep in reps]
            pos = [data.pos[ rep[0] : rep[1] ] for rep in reps]
            mag = [data.magn[ rep[0] : rep[1] ] for rep in reps]
            times = [data.sample_time[rep[1]] - data.sample_time[rep[0]] for rep in reps]

        case _:
            # By default, count from peak to peak 
            accel = [data.accel[ pos_peaks[i] : pos_peaks[i+1] ] for i in range(len(pos_peaks)-1)] 
            vel = [data.vel[ pos_peaks[i] : pos_peaks[i+1] ] for i in range(len(pos_peaks)-1)]
            pos = [data.pos[ pos_peaks[i] : pos_peaks[i+1] ] for i in range(len(pos_peaks)-1)]
            mag = [data.magn[ pos_peaks[i] : pos_peaks[i+1] ] for i in range(len(pos_peaks)-1)]
            times = [data.sample_time[pos_peaks[i+1]] - data.sample_time[pos_peaks[i]] for i in range(len(pos_peaks)-1)]

    return accel, vel, pos, mag, times, reps

#Returns percnetage score of how consistent the distance travelled in reps is
def distance_analysis(pos,reps) -> float:
    dist = [pos[rep[1]] - pos[rep[0]] for rep in reps]
    score = 1 - (np.var(dist) / (max(dist) - min(dist))) #Normalised variance
    return score*100

#Not sure how accurate this would be?
def time_consistency_analysis(t,Y):
    #Assuming here t is a list of time taken for each rep (Independent X)
    #Could use either a quality score (if we have one here), or variance of velocity for dependent Y
    #These two things can be extracted from sort_reps_by_pt above

    var = [np.var(y) for y in Y]
    _, _, r_value, _, _ = linregress(t, var)
    #_, _, r_value, _, _ = linregress(t, range(len(t)))
    return 100*r_value**2

# def get_pos_score(sd, dist_range, min_dists):
    # the tighter it is, the better
    # the shorter range of distances, the better
    # score = dist_range / sd 
    # # normalize to some known value, make integer
    # if score in range(80, 100):
    #     # Perfect
    #     ...
    # if score in range(70, 80):
    #     # Great
    #     ...
    # elif score in range(60, 70):
    #     # Good
    #     ...
    # elif score in range(50, 60):
    #     # Fair
    #     ...
    # elif score in range(40, 50):
    #     # Needs improvement
    #     ...
    # else:
    #     # Fail!
    #     ...
    # return ...

## REWORK
def analyse_set(data: SetData, exercise: Workout, exercise_name: str):
    accel = [isolate_axis(data.accel, 0), isolate_axis(data.accel, 1), isolate_axis(data.accel, 2)]
    vel = [isolate_axis(data.vel, 0), isolate_axis(data.vel, 1), isolate_axis(data.vel, 2)]
    pos = [isolate_axis(data.pos, 0), isolate_axis(data.pos, 1), isolate_axis(data.pos, 2)]
    mag = [isolate_axis(data.magn, 0), isolate_axis(data.magn, 1), isolate_axis(data.magn, 2)]

    accel, vel, pos, mag = sort_reps_by_pt(data, exercise.select, exercise_name)


    # accel_based_qualities = [] # probably not used
    vel_based_quality = []
    mag_based_quality = []

    pos_based_quality = get_pos_scores(pos)
    # vel metrics
    # mag metrics

    return overall_score(vel_based_quality, pos_based_quality, mag_based_quality)

def parse_list_string(list_string):
        return ast.literal_eval(list_string)    

#################################################

def join_rep_data(df):
    accel = []
    vel = []
    pos = []
    mag = []

    for _, row in df.iterrows():
        accel_x = row['accel_x']
        accel_y = row['accel_y']
        accel_z = row['accel_z']
        
        vel_x = row['vel_x']
        vel_y = row['vel_y']
        vel_z = row['vel_z']
        
        pos_x = row['pos_x']
        pos_y = row['pos_y']
        pos_z = row['pos_z']
        
        mag_x = row['mag_x']
        mag_y = row['mag_y']
        mag_z = row['mag_z']
        
        # Combine the x, y, z components into [x, y, z] lists
        accel.extend([[x, y, z] for x, y, z in zip(accel_x, accel_y, accel_z)])
        vel.extend([[x, y, z] for x, y, z in zip(vel_x, vel_y, vel_z)])
        pos.extend([[x, y, z] for x, y, z in zip(pos_x, pos_y, pos_z)])
        mag.extend([[x, y, z] for x, y, z in zip(mag_x, mag_y, mag_z)])
    
    t = [0]
    [t.append(t[-1] + 0.01) for _ in range(1,len(accel))]
    return SetData(accel, vel, pos, mag, t, 0.01)
              

def main() -> None:
    file = open("rep_data_8.txt","r")
    file_data = file.read().split("\n")
    file.close()
    file_data = [line.split(" ") for line in file_data] #Time | Vel xyz | Mag xyz
    file_data.remove(file_data[-1])
    vel = [ [float(file_data[i][j]) for j in range(1, 4)] for i in range(len(file_data))]
    # vel = []
    # [vel.append([float(file_data[i][1]),float(file_data[i][2]),float(file_data[i][3])]) for i in range(len(file_data))]
    pos = integrate(vel)
    mag = [ [float(file_data[i][j]) for j in range(4, 7)] for i in range(len(file_data))]
    # [mag.append([float(file_data[i][4]),float(file_data[i][5]),float(file_data[i][6])]) for i in range(len(file_data))]
    t = [float(file_data[i][0]) for i in range(len(file_data))]
    # [t.append(float(file_data[i][0])) for i in range(len(file_data))]
    data = SetData([], vel, pos, mag, t, 0.01)
    exercise = Workout("Rows")
    accel_sorted, vel_sorted, pos_sorted, mag_sorted, times_sorted, reps= sort_reps_by_pt(data, exercise.select, exercise.workout)
    rval = time_consistency_analysis(times_sorted, isolate_axis(vel_sorted, 0))
    print(rval)

    dist_score = distance_analysis(isolate_axis(pos,0), reps)
    print(dist_score)

    #av = average_line(pos)


    # f = plt.figure()
    # f.add_subplot(projection='3d')

    # # plt.plot(isolate_axis(vel, 0), isolate_axis(vel, 1), isolate_axis(vel, 2), '-b')
    # plt.plot(isolate_axis(pos, 0), isolate_axis(pos, 1), isolate_axis(pos, 2), '-b')
    # plt.plot(isolate_axis(av, 0), isolate_axis(av, 1), isolate_axis(av, 2), '-r')
    # plt.xlabel('x')
    # plt.ylabel('y')
    # plt.legend(['Vel', "Average Vel"])

    # f = plt.figure()
    # f.add_subplot(projection='3d')

    # for i in range(len(pos_sorted)):
    #     plt.plot(isolate_axis(pos_sorted[i], 0), isolate_axis(pos_sorted[i], 1), isolate_axis(pos_sorted[i], 2), '-b')
    
    # f = plt.figure()
    # plt.plot(isolate_axis(vel, 0), '-b')

    # try:
    #     plt.show()
    #     while(1):
    #         pass
    # except KeyboardInterrupt:
    #     plt.close()

#A main to test the 50 rep data
def main_50() -> None:
    array_columns = ['rep_nb','accel_x', 'accel_y', 'accel_z', 'vel_x', 'vel_y', 'vel_z', 'pos_x', 'pos_y', 'pos_z', 'mag_x', 'mag_y', 'mag_z']

    # Open the file and read the lines
    with open("seated_cable_rows.csv", "r") as file:
        lines = file.readlines()

    # Manually process rows
    data = []
    for line in lines[1:]:
        # Strip newline and split by commas using the regular expression
        parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line.strip())
        data.append(parts)

    # Convert to DataFrame
    df = pd.DataFrame(data)
    df.columns = array_columns

    for column in df.columns:
        # Apply ast.literal_eval only to columns that contain list-like strings
        df[column] = df[column].apply(lambda x:ast.literal_eval(x))
        df[column] = df[column].apply(lambda x:ast.literal_eval(x) if type(x) == str else x)

    labels = [93, 78, 87, 78, 84, 85, 78, 89, 67, 89,
        78, 56, 78, 89, 56, 57, 65, 78, 87, 78,
        79, 78, 67, 65, 73, 86, 68, 68, 76, 54,
        36, 78, 68, 64, 89, 87, 67, 67, 77, 68,
        90, 87, 69, 87, 84, 84, 81, 59, 75, 76
    ]
    df['quality_score'] = labels
    workout_data = join_rep_data(df)
    workout = Workout("Rows")
    accel_sorted, vel_sorted, pos_sorted, mag_sorted = sort_reps_by_pt(workout_data, workout.select, workout.workout)
    print(len(pos_sorted))

if __name__ == '__main__':
    main()
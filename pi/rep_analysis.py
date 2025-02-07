# import smbus2
# import gpiozero
import json
import time

from dataclasses import dataclass
from enum import Enum
import numpy as np
from scipy import signal

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


def distance_pnt2pnt(p1: tuple[float, float, float], p2: tuple[float, float, float]) -> float:
    return np.linalg.norm(np.array(p1) - np.array(p2))
    # return np.sqrt( (p1[0] - p2[0])**2 + (p1[1] - p1[1])**2 + (p1[2] - p2[2])**2 )


def closest_point_on_line(point: tuple[float, float, float], line: list[tuple[float, float, float]]):
    min_dist: float = np.inf
    closest_point: tuple[float, float, float] = None
    for linept in line:
        dist: float = distance_pnt2pnt(point, linept)
        if dist < min_dist:
            min_dist = dist
            closest_point = linept

    return closest_point, min_dist
    

def integrate(data: list [list[float, float, float]], dt: float=1):
    intx = np.cumsum(isolate_axis(data, 0)) * dt
    inty = np.cumsum(isolate_axis(data, 1)) * dt
    intz = np.cumsum(isolate_axis(data, 2)) * dt

    return [(intx[i], inty[i], intz[i]) for i in range(len(intx))]

    # posx = [data[0][0]]
    # posy = [data[0][1]]
    # posz = [data[0][2]]
    # for i in range(1,len(data)):
    #     posx.append(posx[-1] + (data[i][0] - data[i-1][0]) * dt)
    #     posy.append(posy[-1] + (data[i][1]- data[i-1][0]) * dt)
    #     posz.append(posz[-1] + (data[i][2] - data[i-1][0]) * dt)

    # output = []
    # [output.append([posx[i],posy[i],posz[i]]) for i in range(len(posx))]
    # return output


def remove_repeat_peaks(peaks : list[float], peak_times: list[float],timeout : float):
    for i in range(1,len(peak_times)-2):
        if peak_times[i] - peak_times[i-1] < timeout:
            peak_times.remove(peak_times[i])
            peaks = np.delete(peaks,i)
    
    return peaks,peak_times


def thresholds_for_peaks(sig: list[float]): ## CHECKKKKK
    naive_peaks = signal.find_peaks(sig)
    mean_peak = np.mean(naive_peaks)
    return signal.find_peaks(sig, heaight=mean_peak)


def average_line(points, num_points=120):
    avx = MovingAverage(num_points)
    avy = MovingAverage(num_points)
    avz = MovingAverage(num_points)

    return [ 
        (
            avx.update(points[i][0]),
            avy.update(points[i][1]),
            avz.update(points[i][2])
        )
        for i in range(len(points))
     ]


## ACTUAL FUNCTIONS
# First part of code is peak analysis for rep count
def sort_reps_by_ax(data: SetData, sel: tuple[int, int], exercise_name: str, package_to_points:bool=False):
    # (3D axis needed, mag axis needed)

    vel_smoothed = MovingAverage(50)
    vel_smoothed = [vel_smoothed.update(val[sel[0]]) for val in data.vel]#smoothed velocity 

    pos_peaks = signal.find_peaks(vel_smoothed,0.125)[0]
    neg_peaks = signal.find_peaks(np.multiply(vel_smoothed,-1),0.02)[0]

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
    
    accel_temp = [isolate_axis(data.accel,0), isolate_axis(data.accel,1), isolate_axis(data.accel,2)]
    vel_temp = [isolate_axis(data.vel,0), isolate_axis(data.vel,1), isolate_axis(data.vel,2)]
    pos_temp = [isolate_axis(data.pos,0), isolate_axis(data.pos,1), isolate_axis(data.pos,2)]
    mag_temp = [isolate_axis(data.magn,0), isolate_axis(data.magn,1), isolate_axis(data.magn,2)]

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


def sort_reps_by_pt(data: SetData, sel: tuple[int, int], exercise_name: str, package_to_points:bool=False):
    # (3D axis needed, mag axis needed)

    vel_smoothed = MovingAverage(50)
    vel_smoothed = [vel_smoothed.update(val[sel[0]]) for val in data.vel]#smoothed velocity 

    # pthreshold = thresholds_for_peaks(vel_smoothed)
    pthreshold = 0.125

    # nthreshold = thresholds_for_peaks(np.multiply(vel_smoothed,-1))
    nthreshold = 0.02

    pos_peaks = signal.find_peaks(vel_smoothed,pthreshold)[0]
    neg_peaks = signal.find_peaks(np.multiply(vel_smoothed,-1),0.02)[0]

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
    
    match exercise_name:
        case "Rows":
            accel = [data.accel[ rep[0] : rep[1] ] for rep in reps]
            vel = [data.vel[ rep[0] : rep[1] ] for rep in reps]
            pos = [data.pos[ rep[0] : rep[1] ] for rep in reps]
            mag = [data.magn[ rep[0] : rep[1] ] for rep in reps]

        case _:
            # By default, count from peak to peak 
            accel = [data.accel[ pos_peaks[i] : pos_peaks[i+1] ] for i in range(len(pos_peaks)-1)] 
            vel = [data.vel[ pos_peaks[i] : pos_peaks[i+1] ] for i in range(len(pos_peaks)-1)]
            pos = [data.pos[ pos_peaks[i] : pos_peaks[i+1] ] for i in range(len(pos_peaks)-1)]
            mag = [data.magn[ pos_peaks[i] : pos_peaks[i+1] ] for i in range(len(pos_peaks)-1)]

    return accel, vel, pos, mag



def distance_analysis(pos: list[ list[float, float, float] ]):
    av_line = average_line(pos, num_points=100)

    min_dists = []
    for point in pos:
        _, dist = closest_point_on_line(point=point, line=av_line)
        min_dists.append(dist)

    sd = np.std(min_dists)
    dist_range = np.max(min_dists) - np.min(min_dists)
    mean = np.mean(min_dists)
    median = np.median(min_dists)

    return min_dists, sd, dist_range


def get_pos_score(sd, dist_range, min_dists):
    # the tighter it is, the better
    # the shorter range of distances, the better
    score = dist_range / sd 
    # normalize to some known value, make integer
    if score in range(80, 100):
        # Perfect
        ...
    if score in range(70, 80):
        # Great
        ...
    elif score in range(60, 70):
        # Good
        ...
    elif score in range(50, 60):
        # Fair
        ...
    elif score in range(40, 50):
        # Needs improvement
        ...
    else:
        # Fail!
        ...

    return ...


def overall_score(vel_based_scores, pos_based_scores, mag_based_scores):
    final_score = []
    # CHECK SAME LENGTH
    if len(vel_based_scores) == len(pos_based_scores) == len(mag_based_scores):

        # coefficients may be adjusted
        for i in range(vel_based_scores):
            final_score.append(
                0.6*pos_based_scores[i] + 0.3*vel_based_scores[i] + 0.1*mag_based_scores[i]
            )

        return final_score
    else:
        return "Invalid Input"


def analyse_set(data: SetData, exercise: Workout, exercise_name: str):
    accel = [isolate_axis(data.accel, 0), isolate_axis(data.accel, 1), isolate_axis(data.accel, 2)]
    vel = [isolate_axis(data.vel, 0), isolate_axis(data.vel, 1), isolate_axis(data.vel, 2)]
    pos = [isolate_axis(data.pos, 0), isolate_axis(data.pos, 1), isolate_axis(data.pos, 2)]
    mag = [isolate_axis(data.magn, 0), isolate_axis(data.magn, 1), isolate_axis(data.magn, 2)]

    _, vel, pos, mag = sort_reps_by_pt(data, exercise.select, exercise_name)


    # accel_based_qualities = [] # probably not used
    vel_based_quality = []
    pos_based_quality = []
    mag_based_quality = []

    nb_reps = len(accel[0])
    for i in range(nb_reps):
        pos_metrics = distance_analysis(pos[i])
        pos_based_quality.append(get_pos_score(pos_metrics))


    return overall_score(vel_based_quality, pos_based_quality, mag_based_quality)
        

def package_ax_by_ax(data: SetData):
    accel = [isolate_axis(data.accel, 0), isolate_axis(data.accel, 1), isolate_axis(data.accel, 2)]
    vel = [isolate_axis(data.vel, 0), isolate_axis(data.vel, 1), isolate_axis(data.vel, 2)]
    pos = [isolate_axis(data.pos, 0), isolate_axis(data.pos, 1), isolate_axis(data.pos, 2)]
    mag = [isolate_axis(data.magn, 0), isolate_axis(data.magn, 1), isolate_axis(data.magn, 2)]

    return accel, vel, pos, mag

def package_ax_by_ax(points):
    return [isolate_axis(points, 0), isolate_axis(points, 1), isolate_axis(points, 2)]



#################################################

def main() -> None:
    file = open("pi/rep_data_8.txt","r")
    file_data = file.read().split("\n")
    file.close()
    file_data = [line.split(" ") for line in file_data] #Time | Vel xyz | Mag xyz
    file_data.remove(file_data[-1])
    vel = [ [float(file_data[i][j]) for j in range(3)] for i in range(len(file_data))]
    # [vel.append([float(file_data[i][1]),float(file_data[i][2]),float(file_data[i][3])]) for i in range(len(file_data))]
    pos = integrate(vel)
    mag = [ [float(file_data[i][j]) for j in range(4, 7)] for i in range(len(file_data))]
    # [mag.append([float(file_data[i][4]),float(file_data[i][5]),float(file_data[i][6])]) for i in range(len(file_data))]
    t = [float(file_data[i][0]) for i in range(len(file_data))]
    # [t.append(float(file_data[i][0])) for i in range(len(file_data))]
    data = SetData([], vel, pos, mag, t, 0.01)
    exercise = Workout("Rows")
    _ = sort_reps_by_pt(data, exercise.select, 'Rows')

    av = average_line(pos)



    f = plt.figure()
    f.add_subplot(projection='3d')

    # plt.plot(isolate_axis(vel, 0), isolate_axis(vel, 1), isolate_axis(vel, 2), '-b')
    plt.plot(isolate_axis(pos, 0), isolate_axis(pos, 1), isolate_axis(pos, 2), '-b')
    plt.plot(isolate_axis(av, 0), isolate_axis(av, 1), isolate_axis(av, 2), '-r')
    
    plt.xlabel('x')
    plt.ylabel('y')
    # plt.zlabel('z')
    plt.legend(['Vel', "Average Vel"])
    plt.show()

import matplotlib.pyplot as plt

if __name__ == '__main__':
    main()

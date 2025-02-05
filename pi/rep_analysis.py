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


class Exercise(Enum):
    TRICEP_PULLDOWN = 1,
    OTHERS = 999


## FNS
def contains_nan(dataset) -> bool:
    dataset = np.array(dataset)
    dataset.flatten()
    # print(dataset)
    for i in dataset:
        if i is np.nan or i == np.nan: 
            return True
    return False


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
    


def get_SetData_pos_vel(data: SetData) -> list[ tuple[float, float, float] ]:
    sample_time = data.sample_time

    pos = []
    vel = []

    current_x_vel = 0.0
    current_y_vel = 0.0
    current_z_vel = 0.0

    current_x_pos = 0.0
    current_y_pos = 0.0
    current_z_pos = 0.0

    for acc in data.accel:
        current_x_vel += acc[0] * sample_time
        current_y_vel += acc[1] * sample_time
        current_z_vel += acc[2] * sample_time

        vel.append((current_x_vel, current_y_vel, current_z_vel))

        current_x_pos += current_x_vel * sample_time
        current_y_pos += current_y_vel * sample_time
        current_z_pos += current_z_vel * sample_time

        pos.append((current_x_pos, current_y_pos, current_z_pos))

    return pos, vel

def remove_repeats(peaks : list[float],peak_times: list[float],timeout : float):
    for i in range(1,len(peak_times)-2):
        if peak_times[i] - peak_times[i-1] < timeout:
            peak_times.remove(peak_times[i])
            peaks = np.delete(peaks,i)
    
    return peaks,peak_times

# First part of code is peak analysis
def sort_reps(data: SetData, exercise: Workout):
    sel = exercise.select #Returns a tuple (velocity axis needed, mag axis needed)
    vel_smoothed = MovingAverage(50)
    vel_smoothed = [vel_smoothed.update(val[sel[0]]) for val in data.vel]#smoothed velocity 
    pos_peaks = signal.find_peaks(vel_smoothed,0.125)[0]
    neg_peaks = signal.find_peaks(np.multiply(vel_smoothed,-1),0.02)[0]
    t_p = []
    [t_p.append(data.sample_time[val]) for val in pos_peaks]
    pos_peaks,t_p = remove_repeats(pos_peaks,t_p,1)
    

    t_n = []
    [t_n.append(data.sample_time[val]) for val in neg_peaks]
    neg_peaks,t_n = remove_repeats(neg_peaks,t_n,1)

    print(f"LP = {len(pos_peaks)} LN = {len(neg_peaks)}")
    if (len(pos_peaks) > len(neg_peaks)):
        pos_peaks = pos_peaks[:len(neg_peaks)]
    else:
        neg_peaks = neg_peaks[:len(pos_peaks)]
    
    dists = []
    for i in range(0,len(pos_peaks)):
        dists.append(abs(vel_smoothed[neg_peaks[i]]) + abs(vel_smoothed[pos_peaks[i]]))

    #Analysis of the peaks has been cancelled :()
    reps = []
    for i in range(0,len(pos_peaks)):
        reps.append(np.sort([pos_peaks[i],neg_peaks[i]]).tolist())
    print(reps)


    accel_temp = [isolate_axis(data.accel,0),isolate_axis(data.accel,1),isolate_axis(data.accel,2)]
    vel_temp = [isolate_axis(data.vel,0),isolate_axis(data.vel,1),isolate_axis(data.vel,2)]
    pos_temp = [isolate_axis(data.pos,0),isolate_axis(data.pos,1),isolate_axis(data.pos,2)]
    mag_temp = [isolate_axis(data.magn,0),isolate_axis(data.magn,1),isolate_axis(data.magn,2)]

    accelx = []
    accely = []
    accelz = []
    velx = []
    vely = []
    velz = []
    posx = []
    posy = []
    posz = []
    magx = []
    magy = []
    magz = []

    for i in reps:
        L = i[0]
        R = i[1]
        accelx.append(accel_temp[0][L:R])
        accely.append(accel_temp[1][L:R])
        accelz.append(accel_temp[2][L:R])
        velx.append(vel_temp[0][L:R])
        vely.append(vel_temp[1][L:R])
        velz.append(vel_temp[2][L:R])
        posx.append(pos_temp[0][L:R])
        posy.append(pos_temp[1][L:R])
        posz.append(pos_temp[2][L:R])
        magx.append(mag_temp[0][L:R])
        magy.append(mag_temp[1][L:R])
        magz.append(mag_temp[2][L:R])


    return accelx,accely,accelz,velx,vely,velz,posx,posy,posz,magx,magy,magz





    

    

def analyse_set(data: SetData, exercise: Exercise, cal_rep: SetData):
    # check same length data
    # if len(data.accel) != len(data.magn):
    #     print('Different size datasets were passed in! \nExiting...')
    #     return
    
    time_elapsed = len(data.accel) / data.sample_time

    # get positions and velocities from SetDatas
    cal_pos, cal_vel = get_SetData_pos_vel(cal_rep)
    set_pos, set_vel = get_SetData_pos_vel(data)

    # use RHR: X: in front (facing same way), Z: pointing up, Y: follows RHR
    # x:0, y:1, Z:2 - constant axis - want little variation there
    accel_constant_ax: int = -1
    magnet_constant_ax: int = -1
    accel_matters: bool = True
    magnet_matters: bool = False

    # match exercise:
    match exercise:
        case Exercise.TRICEP_PULLDOWN:
            accel_constant_ax = 2 
            accel_matters = True
            magnet_constant_ax = 1
            magnet_matters = True

        case _:
            print('Choose a Valid Exercise!')
            return

    # print(f'set_pos: {set_pos}')

    dists_to_cal: list[float] = []
    for point in set_pos:
        # print(point)
        closest_point, dist_to_closest = closest_point_on_line(point, cal_pos)
        dists_to_cal.append(dist_to_closest)

    dists_var = np.var(dists_to_cal)

    if(contains_nan(dists_to_cal)):
        print('CONTAINS NANSS!!')

    # do sth with it

    return dists_to_cal, set_pos, set_vel

def integrate(data: list [list[float, float, float]],dt : float):
    posx = [data[0][0]]
    posy = [data[0][1]]
    posz = [data[0][2]]
    for i in range(1,len(data)):
        posx.append(posx[-1] + (data[i][0] - data[i-1][0]) * dt)
        posy.append(posy[-1] + (data[i][1]- data[i-1][0]) * dt)
        posz.append(posz[-1] + (data[i][2] - data[i-1][0]) * dt)

    output = []
    [output.append([posx[i],posy[i],posz[i]]) for i in range(len(posx))]
    return output

def main() -> None:
    file = open("rep_data_8.txt","r")
    file_data = file.read().split("\n")
    file.close()
    file_data = [line.split(" ") for line in file_data] #Time | Vel xyz | Mag xyz
    file_data.remove(file_data[-1])
    vel = []
    [vel.append([float(file_data[i][1]),float(file_data[i][2]),float(file_data[i][3])]) for i in range(len(file_data))]
    pos = integrate(vel,1)
    mag = []
    [mag.append([float(file_data[i][4]),float(file_data[i][5]),float(file_data[i][6])]) for i in range(len(file_data))]
    t = []
    [t.append(float(file_data[i][0])) for i in range(len(file_data))]
    data = SetData([],vel,pos,mag,t,0.01)
    exercise = Workout("Rows")
    sort_reps(data,exercise)

def main_H() -> None:
    ts = 0.01
    t = np.arange(0, 10, ts)

    perfect = np.array([(np.cos(i), i, 0) for i in t])
    noise = np.array([( (np.random.random() - 0.5), i, 0) for i in t])
    # noise = np.array([( (np.cos(2*i)), i, 0) for i in t])

    zeros_3d = [(0,0,0) for _ in t]

    calibration = SetData(perfect, zeros_3d, 0.01)

    set = SetData(None,  zeros_3d, ts)
    # set.accel = (perfect[0] + noise[0] - 0.5, np.zeros(len(t)), np.zeros(len(t)))
    set.accel = np.array([(perfect[i][0] + 3*noise[i][0], t[i], 0) for i in range( len(t) )])

    print(len(set.accel))
    
    min_dists, set_pos, set_vel = analyse_set(set, Exercise.TRICEP_PULLDOWN, calibration)

    cal_pos, cal_vel = get_SetData_pos_vel(calibration)

    # print(min_dists)

    # plt.figure()
    # plt.plot(t, isolate_axis(perfect, 0), '--r')
    # plt.plot(t, isolate_axis(set.accel, 0), '-b')
    # plt.plot(t, min_dists, '-k')
    # plt.legend(["Calibration Rep", "Our Rep", "Min Dists"])
    # plt.grid(True)

    plt.figure()
    plt.plot(t, isolate_axis(cal_vel, 0), '--r')
    plt.plot(t, isolate_axis(set_vel, 0), '-b')
    plt.legend(['Cal Velocity', 'Set Velocity'])
    plt.grid(True)

    plt.figure()
    plt.plot(t, isolate_axis(cal_pos, 0), '--r')
    plt.plot(t, isolate_axis(set_pos, 0), '-b')
    plt.plot(t, min_dists, '-m')
    plt.legend(['Cal Displacement', 'Set Displacement', 'Minimum Distance'])

    # plt.figure()
    # plt.plot(t, isolate_axis(set.accel, 0))
    # plt.plot(t, isolate_axis(set_pos, 0))
    # plt.plot(t, isolate_axis(set_vel, 0))
    # plt.legend(["Accel", "Pos", "Vel"])
    # plt.grid(True)


    filter = MovingAverage(50)
    filtered = [filter.update(val) for val in isolate_axis(set.accel, 0)]

    plt.figure()
    plt.plot(t, isolate_axis(set.accel, 0))
    plt.plot(t, filtered)
    plt.legend(['raw', 'filtered'])


    ax = plt.figure().add_subplot(projection='3d')
    ax.plot(isolate_axis(perfect, 0),
             isolate_axis(perfect, 1),
             isolate_axis(perfect, 2), '--r', linewidth=2)
    ax.plot(isolate_axis(set.accel, 0),
             isolate_axis(set.accel, 1),
             isolate_axis(set.accel, 2), '-b', alpha=0.5)
    plt.grid(True)


    plt.show()


if __name__ == '__main__':
    main()

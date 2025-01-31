# import smbus2
# import gpiozero
import json
import time

from dataclasses import dataclass
from enum import Enum
import numpy as np

import matplotlib.pyplot as plt
from filtering import MovingAverage

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
    magn: list[ list[float, float, float] ]
    sample_time: float


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


def main() -> None:
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

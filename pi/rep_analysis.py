# import smbus2
# import gpiozero
import json
import time

from dataclasses import dataclass
from enum import Enum
import numpy as np

import matplotlib.pyplot as plt

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
    accel: list[list]
    magn: list[list]
    sample_time: float


class Exercise(Enum):
    TRICEP_PULLDOWN = 1,
    OTHERS = 999


## FNS
def distance_pnt2pnt(p1, p2) -> float:
    return np.sqrt( (p1[0] - p2[0])**2 + (p1[1] - p1[1])**2 + (p1[2] - p2[2])**2 )


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


def closest_point_on_line(point: list[float], line: list[list[float]]):
    min_dist = np.inf
    closest_point = None
    for linept in line:
        dist = distance_pnt2pnt(point, linept)
        if dist < min_dist:
            min_dist = dist
            closest_point = linept

    return closest_point, min_dist
    

    # Use linear algebra to find closest point
    point = np.array(point)
    closest_point = 0, 0, 0
    min_distance = np.inf
    
    for i in range(len(line) - 1):
        # Define the segment endpoints
        A = np.array(line[i])
        B = np.array(line[i + 1])
        
        # Vector from A to B and from A to the point
        AB = B - A
        AP = point - A
        
        # Project AP onto AB, get the parameter t
        t = np.dot(AP, AB) / np.dot(AB, AB)

        # print(t)
        
        # Clamp t to the range [0, 1]
        t = max(0, min(1 , t))
        
        # Compute the closest point on the segment
        Q = A + t * AB
        
        # Compute the distance to the point
        distance = np.linalg.norm(point - Q)
        
        # Update the closest point if necessary
        if distance < min_distance:
            min_distance = distance
            closest_point = Q
    
    return closest_point, min_distance


def get_SetData_pos_vel(data: SetData) -> list[ list[list] ]:
    sample_time = data.sample_time

    pos = [(0.0, 0.0, 0.0)]
    vel = [(0.0, 0.0, 0.0)]

    current_x_vel = 0
    current_y_vel = 0
    current_z_vel = 0

    current_x_pos = 0
    current_y_pos = 0
    current_z_pos = 0

    for accel in data.accel:
        current_x_vel += accel[0] * sample_time
        current_y_vel += accel[1] * sample_time
        current_z_vel += accel[2] * sample_time

        vel.append((current_x_vel, current_y_vel, current_z_vel))

    for v in vel:
        current_x_pos += v[0] * sample_time
        current_y_pos += v[1] * sample_time
        current_z_pos += v[2] * sample_time

        pos.append((current_x_pos, current_y_pos, current_z_pos))

    # print(len(pos))
    # print(len(vel))

    return pos[1:], vel[1:]




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

    return dists_to_cal, dists_var


def main() -> None:
    ts = 0.01
    t = np.arange(0, 10, ts)

    perfect = np.array([(np.cos(i), 0, 0) for i in t])
    noise = np.array([( (np.random.random() - 0.5), 0, 0) for _ in t])

    zeros_3d = [(0,0,0) for _ in t]

    calibration = SetData(perfect, zeros_3d, 0.01)

    set = SetData(None,  zeros_3d, ts)
    # set.accel = (perfect[0] + noise[0] - 0.5, np.zeros(len(t)), np.zeros(len(t)))
    set.accel = [perfect[i] * 3 + noise[i] for i in range( len(t) )]

    # print(len(set.accel[0]))
    
    min_dists, _ = analyse_set(set, Exercise.TRICEP_PULLDOWN, calibration)


    print(min_dists)

    plt.figure()
    plt.plot(t, isolate_axis(perfect, 0), '--r')
    plt.plot(t, isolate_axis(set.accel, 0), '-b')
    plt.plot(t, min_dists[1:], '-k')
    plt.legend(["Calibration Rep", "Our Rep", "Min Dists"])
    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    main()

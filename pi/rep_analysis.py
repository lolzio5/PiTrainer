# import smbus2
# import gpiozero
import json
import time

from dataclasses import dataclass
from enum import Enum
import numpy as np
from scipy import signal
from scipy.signal import find_peaks
from scipy.stats import linregress, zscore, norm
# import pandas as pd
import ast
import re

# import matplotlib.pyplot as plt
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

    THIS ONLY AND ONLY PROVIDES FEEDBACK ON:
        1. DISTANCE TRAVELLED
        2. TIME CONSISTENCY
        3. SHAKINESS

    EACH FUNCTION WILL BE A MEASURE ABOUT THE ENTIRE SET OF REPS
    ERGO THE OUTPUT WILL HAVE THE SAME LENGTH AS THE NUMBER OF REPS
"""

## CLASSES
@dataclass
class SetData:
    accel: list[ list[ float, float, float] ]
    vel : list[ list[float,float,float]]
    pos : list[ list[float,float,float]]
    magn: list[ list[float, float, float] ]
    sample_times: list[ float]
    rep_indexes : list[float]
    ts : float

## UTILS FUNCTIONS
def isolate_axis(points: list[list[float]], axis: int) -> list[float]:
    return [point[axis] for point in points]

def zscore_to_percentile(score: float) -> float:
    return norm.sf(abs(score))*100

# VERIFY THIS
def separate_reps(data: SetData):
    indexes = data.rep_indexes

    accel_reps = []
    vel_reps = []
    pos_reps = []
    magn_reps = []
    for i in range(len(data.rep_indexes))-1:
        accel_reps.append( [data.accel[indexes[i] : indexes[i+1]]] )
        vel_reps.append( [data.vel[indexes[i] : indexes[i+1]]] )
        pos_reps.append( [data.pos[indexes[i] : indexes[i+1]]] )
        magn_reps.append( [data.magn[indexes[i] : indexes[i+1]]] )

    return accel_reps, vel_reps, pos_reps, magn_reps


#Returns percentage score of how consistent the distance travelled in reps is
def distance_analysis(pos_reps) -> float:
    num_reps = len(pos_reps)
    pos_reps = [[isolate_axis(pos_reps[i], 0), isolate_axis(pos_reps[i], 1), isolate_axis(pos_reps[i], 2)] for i in range(num_reps)]
    pos_ranges = []
    for i in range(num_reps): # num_reps x 3
        pos_ranges.append([
            np.max(pos_reps[0]) - np.min(pos_reps[0]),
            np.max(pos_reps[1]) - np.min(pos_reps[1]),
            np.max(pos_reps[2]) - np.min(pos_reps[2])
        ])

    # mean of all the x ranges, y ranges, z ranges
    # pos_ranges_means = [np.mean(isolate_axis(pos_ranges, i)) for i in range(3)]
    pos_zscores = []
    for i in range(num_reps):
        pos_zscores.append([
            zscore(pos_ranges[i][0]),
            zscore(pos_ranges[i][1]),
            zscore(pos_ranges[i][2])
        ])

    rep_scores = [np.mean(pos_zscores[i]) for i in range(num_reps)]

    return [zscore_to_percentile(score) for score in rep_scores]
    

def time_consistency_analysis(t, num_reps):
    _, _, r_value, _, _ = linregress(t, range(len(t)))
    return [100*r_value**2 for _ in range(num_reps)]


def shakiness_analysis(accel_reps, dt:float=1):
    # shakiness = [np.var(vel[rep[0]:rep[1]]) for rep in reps]
    # return [100*(1/(1+shak)) for shak in shakiness]
    rep_nb = len(accel_reps)
    accel_reps = [[isolate_axis(accel_reps[i], 0), isolate_axis(accel_reps[i], 1), isolate_axis(accel_reps[i], 2)] for i in range(rep_nb)]
    jerk_reps = [] # num_reps x 3 x num_points
    for i in range(rep_nb):
        jerk_reps.append([np.diff(accel_reps[i][0])/dt, 
                          np.diff(accel_reps[i][1])/dt, 
                          np.diff(accel_reps[i][2])/dt])

    jerk_ranges = [] # num_reps x 3
    for i in range(rep_nb):
        jerk_ranges.append([np.max(jerk_reps[i][0]) - np.min(jerk_reps[i][0]),
                            np.max(jerk_reps[i][1]) - np.min(jerk_reps[i][1]),
                            np.max(jerk_reps[i][2]) - np.min(jerk_reps[i][2])])

    scores_3d = [] # num_reps x 3
    for i in range(rep_nb):
        scores_3d.append([zscore(jerk_ranges[i][0]),
                       zscore(jerk_ranges[i][1]),
                       zscore(jerk_ranges[i][2])])
        
    rep_scores = [np.mean(scores_3d[i]) for i in rep_nb]

    return [zscore_to_percentile(score) for score in rep_scores]


def pos_score_to_feedback(score) -> str:
    if score > 90:
        return "Great job! You're keeping your range consistent throughout the reps."
    elif score > 70:
        return "Good job! Try to keep your range more consistent throughout the reps."
    elif score > 50:
        return "You're doing okay, but try to keep your range more consistent throughout the reps."
    else:
        return "You're having trouble maintaining range throughout the reps. Try to keep your range consistent. Make sure you fully extend on every movement."

def time_score_to_feedback(score) -> str:
    if score > 90:
        return "Great job! You're keeping a consistent pace throughout the reps."
    elif score > 70:
        return "Good job! Try to keep a more consistent pace throughout the reps."
    elif score > 50:
        return "You're doing okay, but try to keep a more consistent pace throughout the reps."
    else:
        return "You're having trouble maintaining a consistent pace throughout the reps. Try to keep a more consistent pace."

def shakiness_score_to_feedback(score) -> str:
    if score > 90:
        return "Great job! You're keeping your movements smooth throughout the reps."
    elif score > 70:
        return "Good job! Try to keep your movements smoother throughout the reps."
    elif score > 50:
        return "You're doing okay, but try to keep your movements smoother throughout the reps."
    else:
        return "You're having trouble maintaining smooth movements throughout the reps. Try to keep your movements smoother."


def give_feedback(accel_reps, vel_reps, pos_reps, magn_reps, timestamps):
    feedback = []
    num_reps = len(magn_reps)

    dist_scores = distance_analysis(pos_reps) # verify this, idk how to use this one
    time_consistency_scores = time_consistency_analysis(timestamps)
    shakiness_scores = shakiness_analysis(accel_reps)

    for i in range(num_reps):
        feedback.append({
            "distance": pos_score_to_feedback(dist_scores[i]),
            "time_consistency": time_score_to_feedback(time_consistency_scores[i]),
            "shakiness": shakiness_score_to_feedback(shakiness_scores[i])
        })

    return feedback


#################################################
    

def main() -> None:
    ...

if __name__ == '_main_':
    main()
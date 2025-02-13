# import smbus2
# import gpiozero

from dataclasses import dataclass
from enum import Enum
import numpy as np
from scipy import signal
from scipy.stats import linregress, zscore, norm


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
    rep_indices : list[int]
    ts : float

## UTILS FUNCTIONS
def isolate_axis(points: list[list[float]], axis: int) -> list[float]:
    return [point[axis] for point in points]

def join_axis(x : list[float] , y : list[float] , z : list[float]) -> list[list[float]]:
    return [ [x[i], y[i], z[i]] for i in range(len(x))]


def zscore_to_percentile(score: float) -> float:
    return norm.sf(abs(score))*100

def find_highest_peak(sig : list[float], offset : int):
    tmp_peaks, peak_props = signal.find_peaks(sig, -1 * np.inf)
    print(f'tmp_peaks: {tmp_peaks} \n peaks_props: {peak_props}')
    if peak_props['peak_heights'] == [] or peak_props['peak_heights'].size == 0:
        return int(offset)
    highest = np.argmax(peak_props["peak_heights"]) if tmp_peaks is not None else 0
    return int(tmp_peaks[highest] + offset)


## ANALYSIS FUNCTIONS
def sort_reps(data: SetData, reps_live : list[int] , sel):
    vel_smoothed = MovingAverage(50)
    vel_smoothed = [vel_smoothed.update(val[sel[0]]) for val in data.vel] #smoothed velocity
    # print(f'vel_smoothed shape: {np.shape(vel_smoothed)}')
    pos_peaks = []
    reps_live = data.rep_indices
    reps_live.insert(0, 0)

    for i in range(1, len(reps_live)):
        current = int(reps_live[i-1])
        next = int(reps_live[i])
        window = vel_smoothed[current:next]
        if not window:
            continue
        pos_peaks.append(find_highest_peak(window,current))

    # must also do on the last window
    # reps_live[-1] now becomes current
    window = vel_smoothed[reps_live[-1] :]
    if not window:
        return
    pos_peaks.append(find_highest_peak(window, reps_live[-1]))
    return pos_peaks


def separate_reps(data: SetData, sel):
    data.rep_indices = sort_reps(data, data.rep_indices, sel)
    indices = data.rep_indices

    # Split along the reps
    accel_reps = np.split(data.accel, indices[1:])
    vel_reps   = np.split(data.vel, indices[1:])
    pos_reps   = np.split(data.pos, indices[1:])
    magn_reps  = np.split(data.magn, indices[1:])

    return accel_reps, vel_reps, pos_reps, magn_reps, data


#Returns percentage score of how consistent the distance travelled in reps is
def distance_analysis(pos_reps) -> list[float]:
    num_reps = len(pos_reps)
    # pos_reps = num_reps x num_points x 3   --> pos_reps = num_reps x 3 x num_points
    pos_reps = [[isolate_axis(pos_reps[i], 0), isolate_axis(pos_reps[i], 1), isolate_axis(pos_reps[i], 2)] for i in range(num_reps)]
    pos_ranges = []
    for i in range(num_reps): # num_reps x 3
        pos_ranges.append([
            np.max(pos_reps[i][0]) - np.min(pos_reps[i][0]),
            np.max(pos_reps[i][1]) - np.min(pos_reps[i][1]),
            np.max(pos_reps[i][2]) - np.min(pos_reps[i][2])
        ])

    xranges = isolate_axis(pos_ranges, 0)
    yranges = isolate_axis(pos_ranges, 1)
    zranges = isolate_axis(pos_ranges, 2)

    pos_zscores = join_axis(
            zscore(xranges),
            zscore(yranges),
            zscore(zranges)
    )

    rep_scores = [np.mean(pos_zscores[i]) for i in range(num_reps)]
    # print(f'rep_scores: {rep_scores}')
    return [zscore_to_percentile(score) for score in rep_scores]
    

def time_consistency_analysis(t, reps):
    num_reps = len(reps)
    t_reps = [t[rep] for rep in reps]
    _, _, r_value, _, _ = linregress(t_reps, range(len(t_reps)))
    return [100*r_value**2 for _ in range(num_reps)]


def shakiness_analysis(accel_reps, dt:float=1):
    # shakiness = [np.var(vel[rep[0]:rep[1]]) for rep in reps]
    # return [100*(1/(1+shak)) for shak in shakiness]
    rep_nb = len(accel_reps)
    accel_reps = [[isolate_axis(accel_reps[i], 0), isolate_axis(accel_reps[i], 1), isolate_axis(accel_reps[i], 2)] for i in range(rep_nb)]
    # print(f'accel_reps shape: {np.shape(accel_reps)}')
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

    # print(f'jerk_ranges shape: {np.shape(jerk_ranges)}')

    xjerk_ranges = isolate_axis(jerk_ranges, 0)
    yjerk_ranges = isolate_axis(jerk_ranges, 1)
    zjerk_ranges = isolate_axis(jerk_ranges, 2)

    jerk_scores = join_axis(
        zscore(xjerk_ranges),
        zscore(yjerk_ranges),
        zscore(zjerk_ranges)
    )

    # print(f'jerk_scores shape: {np.shape(jerk_scores)}')
        
    rep_scores = [np.mean(jerk_scores[i]) for i in range(rep_nb)]

    return [100 - zscore_to_percentile(score) for score in rep_scores]


def pos_score_to_feedback(score) -> str:
    if score > 70:
        return "Great job! You're keeping your range consistent throughout the reps."
    elif score > 60:
        return "Good job! Try to keep your range more consistent throughout the reps."
    elif score > 40:
        return "You're doing okay, but try to keep your range more consistent throughout the reps."
    else:
        return "You're having trouble maintaining range throughout the reps. Try to keep your range consistent. Make sure you fully extend on every movement."

def time_score_to_feedback(score) -> str:
    if score > 70:
        return "Great job! You're keeping a consistent pace throughout the reps."
    elif score > 60:
        return "Good job! Try to keep a more consistent pace throughout the reps."
    elif score > 40:
        return "You're doing okay, but try to keep a more consistent pace throughout the reps."
    else:
        return "You're having trouble maintaining a consistent pace throughout the reps. Try to keep a more consistent pace."

def shakiness_score_to_feedback(score) -> str:
    if score > 70:
        return "Great job! You're keeping your movements smooth throughout the reps."
    elif score > 60:
        return "Good job! Try to keep your movements smoother throughout the reps."
    elif score > 40:
        return "You're doing okay, but try to keep your movements smoother throughout the reps."
    else:
        return "You're having trouble maintaining smooth movements throughout the reps. Try to keep your movements smoother."


def pos_time_shak_to_overall_score(pos_score, time_score, shakiness_score):
    # return np.mean([0.6*time_score, 0.2*pos_score, 0.2*shakiness_score])
    return 0.5*time_score + 0.25*pos_score + 0.25*shakiness_score


# def give_feedback(data : SetData, exercise : Workout) -> dict[str, float|str]:
def give_feedback(accel_reps, vel_reps, pos_reps, mag_reps, sample_times, rep_indices) -> dict[str, float|str]:
    # accel_reps, _, pos_reps, _, data = separate_reps(data, exercise.select)
    reps = rep_indices
    feedback = []
    rep_scores = []
    num_reps = len(reps)
    print(f'num_reps passed in: {num_reps}')

    dist_scores = distance_analysis(pos_reps)
    print(f'len dist_scores: {len(dist_scores)}, len pos: {len(pos_reps)}')
    time_consistency_scores = time_consistency_analysis(sample_times, reps)
    shakiness_scores = shakiness_analysis(accel_reps)


    # [rep_scores.append(pos_time_shak_to_overall_score(dist_scores[i],time_consistency_scores[i],shakiness_scores[i])) for i in range(0,num_reps-1)]
    rep_scores = [pos_time_shak_to_overall_score(dist_scores[i],time_consistency_scores[i],shakiness_scores[i]) for i in range(num_reps)]
    # print(f'rep_scores: {rep_scores}')
    feedback = {
        "score" : np.mean(rep_scores),
        "distance_score": np.mean(dist_scores),
        "distance_feedback" : pos_score_to_feedback(np.mean(dist_scores)),
        "time_consistency_score": np.mean(time_consistency_scores),
        "time_consistency_feedback" : time_score_to_feedback(np.mean(time_consistency_scores)),
        "shakiness_score": np.mean(shakiness_scores),
        "shakiness_feedback" : shakiness_score_to_feedback(np.mean(shakiness_scores))
    }

    return feedback

def workout_feedback(feedbacks: list[ dict[str, float | str] ]):
    # sorted_feedbacks = sorted(feedbacks, key=lambda x: x['score'])
    # worst_feedback = sorted_feedbacks[-1]
    # print(worst_feedback)
    # worst_feature, _ = min(worst_feedback.items(), key=lambda x: x[1] if not isinstance(x[1], str) else -np.inf)
    # print(f'worst_feature: {worst_feature}')
    # worst_feature = worst_feature.replace('score', '')
    # print(f'worst_feature: {worst_feature}')
    # worst_feature = worst_feature + 'feedback'
    # print(f'worst_feature: {worst_feature}')
    # displayed_feedback = worst_feedback[worst_feature]

    overall_score = np.mean( [feedback['score'] for feedback in feedbacks] )
    overall_dist_score = np.mean( [feedback['distance_score'] for feedback in feedbacks] )
    overall_time_score = np.mean( [feedback['time_consistency_score'] for feedback in feedbacks] )
    overall_shakiness_score = np.mean( [feedback['shakiness_score'] for feedback in feedbacks] )

    main_feedback = {
        'score': overall_score,
        'distance_score': overall_dist_score,
        'distance_feedback': pos_score_to_feedback(overall_dist_score),
        "time_consistency_score": overall_time_score,
        "time_consistency_feedback" : time_score_to_feedback(overall_time_score),
        "shakiness_score": overall_shakiness_score,
        "shakiness_feedback" : shakiness_score_to_feedback(overall_shakiness_score)
    }

    return main_feedback


#################################################
    

def main() -> None:
    print("Starting")
    file = open("data/50_points.csv","r")
    file_data = file.read().split("\n")
    file.close()
    file = open("reps.txt","r")
    reps = file.read().split(" ")
    file.close()
    file_data = [line.split(",") for line in file_data] #Time | accel xyz | vel xyz | pos xyz
    file_data.remove(file_data[-1])
    accel = [ [float(file_data[i][j]) for j in range(1, 4)] for i in range(len(file_data))]
    vel = [ [float(file_data[i][j]) for j in range(4, 7)] for i in range(len(file_data))]
    pos = [ [float(file_data[i][j]) for j in range(7, 10)] for i in range(len(file_data))]
    mag = []
    t = [float(file_data[i][0]) for i in range(len(file_data))]
    reps = [int(reps[i]) for i in range(len(reps))]
    data = SetData(accel, vel, pos, mag, t, reps, 0.01)
    exercise = Workout("Rows")
    # accel_reps, vel_reps, pos_reps, mag_reps, data.rep_indices = separate_reps(data, exercise.select)
    feedbacks = give_feedback(data,exercise)


    scores = feedbacks['score'] 
    print(f'average_score: {np.mean(scores)}')
    print(feedbacks)


if __name__ == '__main__':
    main()
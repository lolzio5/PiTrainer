import numpy as np


## ---- MOVING AVERAGE ---- ##

class MovingAverage:
    """
    NOTE:
    Insert new value at the beginning, leave last value out
    """
    buffer: list[ float ]
    output: float
    size: int

    def __init__(self, size: int = 15):
        self.buffer = [0.0 for _ in range(size)]
        self.output = 0
        self.size = size

    def update(self, newval: float) -> None:
        # assert not hasattr(newval, len)
        self.buffer = [newval, *self.buffer[:-1]]

        # print(self.buffer)

        self.output = sum(self.buffer) / len(self.buffer)
        return self.output



## ---- KALMAN FILTER ---- ##

class KalmanFilter3D:
    """
    n = 3 states : [displacement, velocity, acceleration]
    m = 1 measurement

    """
    dt: float
    current_state: list[ float, float, float ] # 3x1
    # state transition matrix
    A: list[ list[ float, float, float] ] # 3x3
    # control input matrix
    B: list[ list[ float, float, float] ] # 3x1 (will be 0: no ctrl input)

    # process noise covariance
    Q: list[ list[ float, float, float] ] # 3x3
    # measurement matrix (state vector -> measurement space)
    H:       list[ float, float, float]  # 1x3
    # measurement noise covariance
    R: float                            # 1x1
    # state covariance matrix
    P: list[ list[ float, float, float] ] #3x3 diag
    # Kalman Gain
    K: list[ list[ float, float, float] ] # 3x1

    # def __init__(self, dt, A, B, Q, H, R, P, K=[0,0,0]):
    def __init__(self, dt):
        self.dt = dt
        self.current_state = np.array([0, 0, 0])
        # self.A = A
        self.A = np.array([
            [1, dt, 0.5*dt**2],
            [0, 1,  dt],
            [0, 0, 1]
        ])
        self.A = np.array([
            [0, 1, 0],
            [0, 0, 1],
            [0, 0, 0]
        ])
        # self.B = B
        self.B = np.array([
            [0],
            [0],
            [0]
        ])
        # self.Q = Q
        variance_accel = 0.1 # ??
        variance_vel = 0.0
        variance_pos = 0.0

        self.Q = variance_accel * np.array([
            [0.25*dt**4, 0.5*dt**3, 0.5*dt**2],
            [0.5*dt**3 , dt**2    , dt       ],
            [0.5*dt**2 , dt       , 1],
        ])
        # self.H = H
        self.H = np.array([0, 0, 1])
        # self.R = R

        self.R = variance_accel
        self.P = np.diag([variance_pos, variance_vel, variance_accel])

        self.position = 0
        self.velocity = 0
        self.acceleration = 0
        # self.K = K

    def step(self, reading, ctrl_in=0) -> None:
        # predict next state
        self.current_state = np.matmul(self.A, self.current_state) + np.matmul(self.B, np.array([ctrl_in]))

        # predict next variance
        self.P = np.matmul( np.matmul(self.A, self.P), np.transpose(self.A) ) + self.Q

        # Kalman gain
        S =  np.matmul( np.matmul(self.H, self.P), np.transpose(self.H) ) + self.R
        # S is 1-dimensional! => use algebraic inverse instead of np.linagl.inv
        # S = np.array([S])

        K = np.matmul(self.P, np.transpose(self.H)) / S 

        # self.current_state = self.current_state + np.matmul(K, reading - np.matmul(self.H, self.current_state))
        self.current_state = self.current_state + K * ( reading - np.matmul(self.H, self.current_state) )

        self.position, self.velocity, self.acceleration = self.current_state

        # clamp state?
        self.P = np.matmul(np.eye(3) - np.matmul(K, self.H) , self.P)


    def print(self) -> None:
        print(f"Current State: {self.current_state}\tCovariance Coeff: {self.P}")



if __name__ == '__main__':
    # KALMAN TESTING
    import accelerometer
    import time

    accelerometer.lis3dh_init()
    ts = 0.01
    accelx_filter = KalmanFilter3D(ts)
    accely_filter = KalmanFilter3D(ts)
    accelz_filter = KalmanFilter3D(ts)

    filtered_accel = []
    filtered_vel = []
    filtered_pos = []

    try:
        # for i in range(1000):
        while True:
            accelx, accely, accelz = accelerometer.lis3dh_read_xyz()

            accelx_filter.step(accelx)
            accely_filter.step(accely)
            accelz_filter.step(accelz)

            filtered_accel.append((
                accelx_filter.acceleration,
                accely_filter.acceleration,
                accelz_filter.acceleration
            ))

            filtered_vel.append((
                accelx_filter.velocity,
                accely_filter.velocity,
                accelz_filter.velocity
            ))

            filtered_pos.append((
                accelx_filter.position,
                accely_filter.position,
                accelz_filter.position
            ))

            time.sleep(ts)

    except KeyboardInterrupt:
        print('Exiting...')
        
        for i, a in enumerate(filtered_accel):
            print(f"{filtered_accel[i]} | {filtered_vel[i]} | {filtered_pos[i]}")
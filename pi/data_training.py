import smbus2, time
from workout import Workout
from filtering import KalmanFilter3D,MovingAverage
import accelerometer
import magnet
import i2c_bus


if _name_ == "_main_":
    accelerometer.lis3dh_init()
    magnet.Mag_init()
    time.sleep(0.5)
    dt = 0.01 #max value of 0.01, due to sampling frequency of sensor set above
    accelx_filter = KalmanFilter3D(dt)
    accely_filter = KalmanFilter3D(dt)
    accelz_filter = KalmanFilter3D(dt)
    magx_filter = MovingAverage(50)
    magy_filter = MovingAverage(50)
    magz_filter = MovingAverage(50)
    current_workout = Workout("Lat Pulldowns")
    init_time = time.time()
    file = open("data.txt","w")
    file_2 = open("reps.txt","w")
    t = []
    velx = []
    print("Get ready")
    time.sleep(3)
    print("Go")
    try:
        while True:
            new_time = time.time() - init_time
            t.append(new_time)
            mag_x,mag_y,mag_z = magnet.Mag_Read()
            x, y, z = accelerometer.lis3dh_read_xyz()

            accelx_filter.step(x)
            accely_filter.step(y)
            accelz_filter.step(z)
            magx_filter.update(mag_x)
            magy_filter.update(mag_y)
            magz_filter.update(mag_z)

            velx.append(accelx_filter.velocity)

            file.write(f"{new_time},{accelx_filter.acceleration},{accely_filter.acceleration},{accelz_filter.acceleration},{accelx_filter.velocity},{accely_filter.velocity},{accelz_filter.velocity},{accelx_filter.position},{accely_filter.position},{accelz_filter.position},{magx_filter.output},{magy_filter.output},{magz_filter.output}\n")
            
            reps = current_workout.update([accelx_filter.velocity,accely_filter.velocity,accelz_filter.velocity],[magx_filter.output,magy_filter.output,magz_filter.output])
            if (reps[0] == True):
                file_2.write(f"{new_time} {reps[1]} \n")
                print(f"Rep at {new_time} | {reps[1]} \n")

            
            time.sleep(dt)

    except KeyboardInterrupt:
        file.close()
        file_2.close()
        print('Exiting...')
import smbus2, time

LIS3DH_ADDRESS = 0x18

## Control Registers
LIS3DH_REG_CTRL_REG1 = 0x20
LIS3DH_REG_CTRL_REG2 = 0x21
LIS3DH_REG_CTRL_REG3 = 0x22
LIS3DH_REG_CTRL_REG4 = 0x23 #Set scale with this (page 37 of MEMS data sheet) default is +/- 2g
LIS3DH_REG_CTRL_REG5 = 0x24
LIS3DH_REG_CTRL_REG6 = 0x25

## Axes Registers
LIS3DH_REG_OUT_X_L = 0x28  # X-axis LSB
LIS3DH_REG_OUT_X_H = 0x29  # X-axis MSB
LIS3DH_REG_OUT_Y_L = 0x2A  # Y-axis LSB
LIS3DH_REG_OUT_Y_H = 0x2B  # Y-axis MSB
LIS3DH_REG_OUT_Z_L = 0x2C  # Z-axis LSB
LIS3DH_REG_OUT_Z_H = 0x2D  # Z-axis MSB

# MLX90393 address, 0x0C(12)
MLX90393_ADDR = 0x0C
CMD_READ = 0x4E
CMD_SM = 0x1E# Start single meaurement mode (x30), X, Y, Z-Axis enabled (x0E)

## Default Bus
bus = smbus2.SMBus(1)
time.sleep(0.5)

def i2c_write_reg(address: int, register: int, value) -> None:
    bus.write_byte_data(address, register, value)


def i2c_read_reg(address:int, register: int) -> int:
    return bus.read_byte_data(address, register)

def Mag_Read() -> tuple[int,int,int]:	
    # #Set mode
    # bus.write_byte(MLX90393_ADDR, CMD_SM)

    # # Status byte
    # data = bus.read_byte(MLX90393_ADDR)
    # Status, xMag msb, xMag lsb, yMag msb, yMag lsb, zMag msb, zMag lsb
    data = bus.read_i2c_block_data(MLX90393_ADDR, CMD_READ, 7)
    # Convert the data
    xMag = (data[1] << 8) | data[2]
    #print("raw x : %d" %xMag)
    if xMag & 0x8000:
        xMag -= 0x10000

    yMag = (data[3] << 8) | data[4]
    if yMag & 0x8000:
        yMag -= 0x10000

    zMag = (data[5] << 8) | data[6]
    if zMag & 0x8000:
        zMag -= 0x10000

    return (xMag,yMag,zMag)

def Mag_init():
    #Extra code for adjusting gain and sensitvity
    #AH = 0x00, AL = 0x5C, GAIN_SEL = 5, Address register (0x00 << 2)
    config = [0x00, 0x0C, 0x00]
    try:
        bus.write_i2c_block_data(MLX90393_ADDR, 0x60, config)
    except:
        print("fucked up")

    # Read data back, 1 byte
    # Status byte
    data = bus.read_byte(MLX90393_ADDR)

    # AH = 0x02, AL = 0xB4, RES for magnetic measurement = 0, Address register (0x02 << 2)
    config = [0x02, 0xB4, 0x08]
    bus.write_i2c_block_data(MLX90393_ADDR, 0x60, config)

    # Read data back, 1 byte
    # Status byte
    data = bus.read_byte(MLX90393_ADDR)

	#Set mode
    bus.write_byte(MLX90393_ADDR, CMD_SM)

    # Status byte
    data = bus.read_byte(MLX90393_ADDR)

    time.sleep(0.5)

def lis3dh_init() -> None:
    print('Initialising LIS3DH...')
    # enable high resolution, xyz axes, and 100Hz sampling
    i2c_write_reg(LIS3DH_ADDRESS, LIS3DH_REG_CTRL_REG1, 0b0101_0111)
    #High resolution means each digit represets 1mg
    # set HPF
    i2c_write_reg(LIS3DH_ADDRESS, LIS3DH_REG_CTRL_REG2, 0b0000_0010)

    # the rest of the registers are ok with 0x00 by default

    # disable interrupts
    # i2c_write_reg(LIS3DH_ADDRESS, LIS3DH_REG_CTRL_REG3, 0b0000_0000)
    time.sleep(0.1)


def lis3dh_read_xyz_raw() -> tuple[int, int, int]:
    X_L = i2c_read_reg(LIS3DH_ADDRESS, LIS3DH_REG_OUT_X_L)
    X_H = i2c_read_reg(LIS3DH_ADDRESS, LIS3DH_REG_OUT_X_H)

    Y_L = i2c_read_reg(LIS3DH_ADDRESS, LIS3DH_REG_OUT_Y_L)
    Y_H = i2c_read_reg(LIS3DH_ADDRESS, LIS3DH_REG_OUT_Y_H)
    
    Z_L = i2c_read_reg(LIS3DH_ADDRESS, LIS3DH_REG_OUT_Z_L)
    Z_H = i2c_read_reg(LIS3DH_ADDRESS, LIS3DH_REG_OUT_Z_H)

    x = (X_H << 8) | X_L
    y = (Y_H << 8) | Y_L
    z = (Z_H << 8) | Z_L

    return (x, y, z)


def lis3dh_read_xyz() -> tuple[float, float, float]:#Changing from two's complement
    x, y, z = lis3dh_read_xyz_raw()

    if x & 0x8000:
        x -= 0x10000
    if y & 0x8000:
        y -= 0x10000
    if z & 0x8000:
        z -= 0x10000
    
    #Comment this section out if you want raw data
    max_value = 2 #Since scale is +/- 2g by default
    x = x/32768 * max_value
    y = y/32768 * max_value
    z = z/32768 * max_value

    return (x, y, z)

def velocity_filter(velocity_array, value):
    out = [0,0,0]
    for j in range(len(velocity_array)):
        for i in range(len(velocity_array[j])-1):
            velocity_array[j][i+1] = velocity_array[j][i]
        
        velocity_array[j][0] = value[j]
        out[j] = sum(velocity_array[j])/len(velocity_array[j])
    
    return velocity_array,out

# Output data to screen
if __name__ == "__main__":
    Mag_init()

    try:
        while True:
            x,y,z = Mag_Read()
            print ("X-Axis : %d | Y-Axis : %d | Z-Axis : %d" %(x, y, z))
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting")


# if __name__ == "__main__":
#     lis3dh_init()
#     dt = 0.01 #max value of 0.01, due to sampling frequency of sensor set above
#     g = 9.81
#     current_value = [0,0,0]
#     M = 50 #Size of window for Moving average filter
#     velocity_array = [ [0]*M , [0]*M , [0]*M] #X,Y,Z
#     velocity = [0,0,0]
#     filtered_velocity = [0,0,0]
#     rep_count = [0,0] #reps, timestamp to last rep
#     threshold = 0.022
#     timeout = 1.25
#     init_time = time.time()
#     file = open("data.txt","w")
#     try:
#         while True:
#             previous_value = current_value
#             previous_filtered_velocity = filtered_velocity

#             x, y, z = lis3dh_read_xyz()

#             current_value = [x,y,z]
#             for i in range(3): velocity[i] += (current_value[i] - previous_value[i]) * g * dt
#             velocity_array,filtered_velocity = velocity_filter(velocity_array,velocity)
#             #if (abs(velocity) <= 0.02) : velocity = 0
#             new_time = time.time() - init_time
#             file.write(f"{new_time} {filtered_velocity[0]} {filtered_velocity[1]} {filtered_velocity[2]} \n")
#             #print(filtered_velocity)
#             if (filtered_velocity[0] > threshold): 
#                 if (new_time - rep_count[1] > timeout):#Prevents double counts
#                     rep_count[0] += 1
#                     rep_count[1] = new_time
#                     print(f"New rep : {rep_count[0]} time : {rep_count[1]}")

#             time.sleep(dt)

#     except KeyboardInterrupt:
#         file.close()
#         print('Exiting...')
    

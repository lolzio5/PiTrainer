import smbus2
import time

# Get I2C bus
from i2c_bus import bus

# MLX90393 address, 0x0C(12)
MLX90393_ADDR = 0x0C
CMD_READ = 0x4E
CMD_SM = 0x3E# Start single meaurement mode (x30), X, Y, Z-Axis enabled (x0E)

def Mag_init():
    #Extra code for adjusting gain and sensitvity
    #AH = 0x00, AL = 0x5C, GAIN_SEL = 5, Address register (0x00 << 2)
    config = [0x00, 0x0C, 0x00]
    bus.write_i2c_block_data(MLX90393_ADDR, 0x60, config)

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

def Mag_Read() -> tuple[int,int,int]:	
    # Status, xMag msb, xMag lsb, yMag msb, yMag lsb, zMag msb, zMag lsb
    data = bus.read_i2c_block_data(MLX90393_ADDR, CMD_READ, 7)
    print(data)
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

# Output data to screen
if __name__ == "__main__":
    Mag_init()

    try:
        while True:
            x,y,z = Mag_Read()
            #print ("X-Axis : %d | Y-Axis : %d | Z-Axis : %d" %(x, y, z))
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Exiting")
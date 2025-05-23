# import smbus2
import time

## Default Bus
from i2c_bus import bus

## Registerss
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


def lis3dh_init() -> None:
    print('Initialising LIS3DH...')
    # enable high resolution, xyz axes, and 100Hz sampling
    global LIS3DH_ADDRESS
    try:
        bus.write_byte_data(LIS3DH_ADDRESS, LIS3DH_REG_CTRL_REG1, 0b0101_0111)

        #High resolution means each digit represets 1mg
        # set HPF
        bus.write_byte_data(LIS3DH_ADDRESS, LIS3DH_REG_CTRL_REG2, 0b0000_0010)

        # the rest of the registers are ok with 0x00 by default

        # disable interrupts
        # i2c_write_reg(LIS3DH_ADDRESS, LIS3DH_REG_CTRL_REG3, 0b0000_0000)
        time.sleep(0.1)
    except OSError:
        LIS3DH_ADDRESS = 0x19
        bus.write_byte_data(LIS3DH_ADDRESS, LIS3DH_REG_CTRL_REG1, 0b0101_0111)

        #High resolution means each digit represets 1mg
        # set HPF
        bus.write_byte_data(LIS3DH_ADDRESS, LIS3DH_REG_CTRL_REG2, 0b0000_0010)


def lis3dh_read_xyz_raw() -> tuple[int, int, int]:
    X_L = bus.read_byte_data(LIS3DH_ADDRESS, LIS3DH_REG_OUT_X_L)
    X_H = bus.read_byte_data(LIS3DH_ADDRESS, LIS3DH_REG_OUT_X_H)

    Y_L = bus.read_byte_data(LIS3DH_ADDRESS, LIS3DH_REG_OUT_Y_L)
    Y_H = bus.read_byte_data(LIS3DH_ADDRESS, LIS3DH_REG_OUT_Y_H)
    
    Z_L = bus.read_byte_data(LIS3DH_ADDRESS, LIS3DH_REG_OUT_Z_L)
    Z_H = bus.read_byte_data(LIS3DH_ADDRESS, LIS3DH_REG_OUT_Z_H)

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

if __name__ == "__main__":
    lis3dh_init()

    try:
        while True:
            x, y, z = lis3dh_read_xyz()

            print(f'X: {x:5} , Y: {y:5}, Z: {z:5} ')

            time.sleep(0.1)

    except KeyboardInterrupt:
        print('Exiting...')
    

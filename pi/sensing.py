import smbus2, time

LIS3DH_ADDRESS = 0x18

## Control Registers
LIS3DH_REG_CTRL_REG1 = 0x20
LIS3DH_REG_CTRL_REG2 = 0x21
LIS3DH_REG_CTRL_REG3 = 0x22
LIS3DH_REG_CTRL_REG4 = 0x23
LIS3DH_REG_CTRL_REG5 = 0x24
LIS3DH_REG_CTRL_REG6 = 0x25

## Axes Registers
LIS3DH_REG_OUT_X_L = 0x28  # X-axis LSB
LIS3DH_REG_OUT_X_H = 0x29  # X-axis MSB
LIS3DH_REG_OUT_Y_L = 0x2A  # Y-axis LSB
LIS3DH_REG_OUT_Y_H = 0x2B  # Y-axis MSB
LIS3DH_REG_OUT_Z_L = 0x2C  # Z-axis LSB
LIS3DH_REG_OUT_Z_H = 0x2D  # Z-axis MSB

## Default Bus
bus = smbus2.SMBus(1)


def i2c_write_reg(address: int, register: int, value) -> None:
    bus.write_byte_data(address, register, value)


def i2c_read_reg(address:int, register: int) -> int:
    return bus.read_byte_data(address, register)


def lis3dh_init() -> None:
    print('Initialising LIS3DH...')
    # enable high resolution, xyz axes, and 100Hz sampling
    i2c_write_reg(LIS3DH_ADDRESS, LIS3DH_REG_CTRL_REG1, 0b0101_0111)

    # set HPF
    i2c_write_reg(LIS3DH_ADDRESS, LIS3DH_REG_CTRL_REG2, 0b0000_0000)

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


def lis3dh_read_xyz() -> tuple[float, float, float]:
    x, y, z = lis3dh_read_xyz_raw()

    if x & 0x8000:
        x -= 0x10000
    if y & 0x8000:
        y -= 0x10000
    if z & 0x8000:
        z -= 0x10000
    
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
    

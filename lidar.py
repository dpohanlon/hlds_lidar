import serial

import numpy as np

import asyncio

class LIDAR(object):

    def __init__(self, port = '/dev/ttyAMA0', baud = 230400, returnXY = True):

        self.ser = serial.Serial(port, baud)
        self.returnXY = returnXY

    def start(self):
        self.ser.write(b'b')

    def stop(self):
        self.ser.write(b'e')

    def __del__(self):

        if self.ser.is_open:
            self.stop()
            self.ser.close()

    async def getLIDAR(self):

        dataToWrite = []

        # Read until we find the start of a frame
        while(1):

            data = self.ser.read()

            # Found the start of a frame, read it
            if data == b'\xFA':

                data = self.ser.read((360 // 6) * 42 - 1)
                data = b'\xFA' + data
                dataToWrite = [data[i:i+42] for i in range(0, len(data), 42)]
                break

        ranges = np.zeros(360) * np.nan
        angles = np.zeros(360) * np.nan
        intensities = np.zeros(360) * np.nan

        # Loop over length 42 blocks in frame
        for iData, data in enumerate(dataToWrite):

            if len(data) < 42:
                continue

            firstAngle = (data[1] - 160) * 6
            angles[iData * 6 : iData * 6 + 6] = list(range(firstAngle, firstAngle + 6))

            # Loop over entries in block (some are pairs upper and lower bits)
            for i, j in enumerate(range(4, 40, 6)):

                intensity0 = data[j + 0]
                intensity1 = data[j + 1]

                range0 = data[j + 2]
                range1 = data[j + 3]

                # Combine separated upper and lower bits
                intensityVal = (intensity1 << 8) + intensity0
                rangeVal = (range1 << 8) + range0

                intensities[iData * 6 + i] = intensityVal
                ranges[iData * 6 + i] = rangeVal

        # mm -> m
        ranges /= 1000.

        if self.returnXY:

            x = ranges * np.sin(np.radians(angles))
            y = ranges * np.cos(np.radians(angles))

            return x, y, intensities

        else:

            return ranges, angles, intensities

async def runLIDAR():

    import matplotlib.pyplot as plt

    try:
        lidar = LIDAR()
    except (RuntimeError, OSError) as e:
        raise e

    lidar.start()

    lidarXY = await lidar.getLIDAR()
    x, y, intensities = lidarXY

    plt.scatter(x, y, c = intensities, cmap='Greens')
    plt.xlim(-4.0, 4.0)
    plt.ylim(-4.0, 4.0)
    plt.savefig('lidar.pdf')

    lidar.stop()

if __name__ == '__main__':

    asyncio.run(runLIDAR())

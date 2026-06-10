import serial
import csv

ser = serial.Serial('COM5',115200)

with open('bcg_data.csv','w',newline='') as f:

    writer = csv.writer(f)
    writer.writerow(['az'])

    while True:
        line = ser.readline().decode().strip()

        try:
            writer.writerow([line])
            f.flush()
        except:
            pass
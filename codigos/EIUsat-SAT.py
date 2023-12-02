## CODIGO PARA CIRAR ACCESS POINT:
# import network
# ap = network.WLAN(network.AP_IF)
# ap.active(True)
# ap.config(essid='REDE', password='SENHA')


##libraries
import network
import time
import os
import machine
from machine import Pin
from machine import I2C, Pin
from bmp280 import *
from mpu9250 import MPU9250
from bmp180 import BMP180
import CCS811
from machine import RTC
from machine import ADC
import math
import urequests
from machine import UART
import gc
import ujson

## Enable the garbage collector
gc.enable()

##Inicia UART
uart1 = UART(1, 9600)
uart1 = UART(1, baudrate=9600, tx=17, rx=16)

##Define variaveis
log_number = None
atm_pressure = None
temperature_reading = None
co2 = None
gyro_data = None
aceleration_data = None
battery = None
uv = None
altitude = None
cam = None
cam_status = None
battery_percentage = None
http_data = None
HTTP_request = None
file_data = None
file_name = None
arquivo = None


##Inicia sensores
def sht20_temperature():
    i2c.writeto(0x40, b'\xf3')
    time.sleep_ms(70)
    t = i2c.readfrom(0x40, 2)
    return -46.86 + 175.72 * (t[0] * 256 + t[1]) / 65535


def sht20_humidity():
    i2c.writeto(0x40, b'\xf5')
    time.sleep_ms(70)
    t = i2c.readfrom(0x40, 2)
    return -6 + 125 * (t[0] * 256 + t[1]) / 65535


adc35 = ADC(Pin(35))
adc35.atten(ADC.ATTN_11DB)
adc35.width(ADC.WIDTH_12BIT)

##Inicia setup (wifi, SD e sensores)
print('hello world, starting setup!')
# mudar antes de rodar
sdcard = machine.SDCard(slot=2, width=1, cd=None, wp=None, sck=Pin(18), miso=Pin(19), mosi=Pin(23), cs=Pin(15),
                        freq=20000000)
os.mount(sdcard, '/sd')
time.sleep(1)
i2c = I2C(scl=Pin(22), sda=Pin(21))
bus = I2C(scl=Pin(22), sda=Pin(21))
bmp280 = BMP280(bus)
bmp280.use_case(BMP280_CASE_WEATHER)
bmp280.oversample(BMP280_OS_HIGH)
i2c = I2C(scl=Pin(22), sda=Pin(21))
mpu9250s = MPU9250(i2c)
bus = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
bmp180 = BMP180(bus)
bmp180.oversample_sett = 2
bmp180.baseline = 101325

bus = I2C(scl=Pin(22), sda=Pin(21))
sCCS811 = CCS811.CCS811(i2c=bus, addr=90)

print('end of setup')


def send_data_in_chunks(data):
    chunk_size = 1024  # Adjust the chunk size based on available memory
    data_str = ujson.dumps(data)
    try:
        i = 0
        while i < len(data_str):
            chunk = data_str[i:i + chunk_size]
            uart1.write(str(chunk))
            i += len(chunk)
    except MemoryError:
        print("Error: Not enough memory")
    except OSError as e:
        print("Unexpected OSError:", e)


def read_data_in_chunks(max_to_read, chunk_size):
    read_data = ''
    try:
        i = 0
        while i < max_to_read:
            chunk = uart1.read(chunk_size)
            read_data = str(read_data) + str(chunk)
            i += chunk_size
        return read_data
    except MemoryError:
        print("Error: Not enough memory")
    except OSError as e:
        print("Unexpected OSError:", e)


# Main loop
def main():
    log_number = 1
    while log_number != 0:
        print('log number' + str(log_number))

        ##medidas dos sensores
        bmp280.normal_measure()
        atm_pressure = (bmp280.pressure) * 2 / 101325
        temperature_reading = sht20_temperature()
        co2 = sCCS811.eCO2
        gyro_data = 'gyro rate:' + str(mpu9250s.gyro)
        aceleration_data = 'accerelation rate:' + str(mpu9250s.acceleration)
        battery = adc35.read()
        altitude = bmp180.altitude

        ##le os dados da camera
        try:
            cam = read_data_in_chunks(100000, 25000)

        ##if cam == None:
        # cam_status = 0
        # else:
        # cam_status = 1
        except MemoryError:
            print('ME, failed to read')
            cam_status = 2
        except OSError as e:
            print('Unkown error, failed to read')
            cacm_status = 3
        if cam != 'NoneNoneNoneNone':
            cam_status = 0
        else:
            cam_status = 1

        # converte bateria pra %
        battery_percentage = round((battery * 100) / 2600)
        # Construct JSON data
        http_data = {
            "equipe": 123,
            "bateria": battery_percentage,
            "temperatura": temperature_reading,
            "pressao": atm_pressure,
            "giroscopio": gyro_data,
            "acelerometro": aceleration_data,
            "payload": {
                "dados climatologicos": {
                    "altitude": altitude,
                    "co2": co2
                },
                "cam_status": cam_status
            }
        }

        # Try to send data via POST request, handle memory errors

        # Combine data for the SD card and write to a file
        file_data = '{{"http_data":{}, "cam_data":{}}}'.format(http_data, cam)
        file_name = '/sd/log_vac_test{}.csv'.format(log_number)
        with open(file_name, 'bw') as arquivo:
            arquivo.write(file_data)
        arquivo.close()
        print('Recorder on SD')
        print(file_data)

        # Send data via UART
        send_data_in_chunks(http_data)
        log_number += 1
        print('End of transmission\n')

        # Wait for the specified time
        time.sleep(9.5)


for i in range(0, 150):
    print(f'reading #{i}')
    initial_reading = uart1.read(200)
    if initial_reading != None:
        print('found cam')
        time.sleep(9.3)
        main()
    else:
        i += 1
    time.sleep(0.2)
    if i == 150:
        print('starting anyway, failed to read camera')
        main()


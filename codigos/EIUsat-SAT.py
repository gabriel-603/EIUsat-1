
##libraries
import network
import time
import os
import machine
from machine import Pin
from machine import I2C, Pin
import time
from bmp280 import *
from mpu9250 import MPU9250
from bmp180 import BMP180
import CCS811
from machine import RTC
from machine import ADC
import math
import urequests
from machine import UART

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
	i2c.writeto(0x40,b'\xf3')
	time.sleep_ms(70)
	t=i2c.readfrom(0x40, 2)
	return -46.86+175.72*(t[0]*256+t[1])/65535

def sht20_humidity():
	i2c.writeto(0x40,b'\xf5')
	time.sleep_ms(70)
	t=i2c.readfrom(0x40, 2)
	return -6+125*(t[0]*256+t[1])/65535

sta_if = network.WLAN(network.STA_IF)

sta_if.active(True)


adc35=ADC(Pin(35))
adc35.atten(ADC.ATTN_11DB)
adc35.width(ADC.WIDTH_12BIT)

adc34=ADC(Pin(34))
adc34.atten(ADC.ATTN_11DB)
adc34.width(ADC.WIDTH_12BIT)


##Inicia setup (wifi, SD e sensores)
print('hello world, starting setup')
sta_if = network.WLAN(network.STA_IF); sta_if.active(True)
sta_if.scan()
#mudar antes de rodar
sta_if.connect('rede de wifi','senha')
print("Waiting for Wifi connection")
while not sta_if.isconnected(): time.sleep(1)
print("Connected")
sdcard=machine.SDCard(slot=2, width=1, cd=None, wp=None, sck=Pin(18), miso=Pin(19), mosi=Pin(23), cs=Pin(15), freq=20000000)
os.mount(sdcard, '/sd')
time.sleep(1)
i2c=I2C(scl=Pin(22), sda=Pin(21))
bus=I2C(scl=Pin(22), sda=Pin(21))
bmp280 = BMP280(bus)
bmp280.use_case(BMP280_CASE_WEATHER)
bmp280.oversample(BMP280_OS_HIGH)
i2c=I2C(scl=Pin(22), sda=Pin(21))
mpu9250s = MPU9250(i2c)
bus=I2C(scl=Pin(5), sda=Pin(4), freq=100000)
bmp180 = BMP180(bus)
bmp180.oversample_sett = 2
bmp180.baseline = 101325

bus=I2C(scl=Pin(22), sda=Pin(21))
sCCS811 = CCS811.CCS811(i2c=bus, addr=90)

print('end of setup')
print(sta_if.ifconfig())
log_number = 1

##Loop principal
while True:
  print('log number' + str(log_number))

  ##medidas dos sensores
  bmp280.normal_measure()
  atm_pressure = (bmp280.pressure) / 101325
  temperature_reading = bmp280.temperature
  co2 = sCCS811.eCO2
  gyro_data = 'gyro rate:' + str(mpu9250s.gyro)
  aceleration_data = 'accerelation rate:' + str(mpu9250s.acceleration)
  battery = adc35.read()
  uv = adc34.read()
  altitude = bmp180.altitude

  ##le os dados da camera
  cam = uart1.read(3200)
  if cam == None:
    cam_status = 0
  else:
    cam_status = 1

  #converte bateria pra %
  battery_percentage = round((battery * 100) / 2600)
 
  ##junta os dados em JSON
  http_data = ''.join([str(x3) for x3 in ['{', '"equipe":' + str(123), ', "bateria":' + str(battery_percentage), ', "temperatura":' + str(temperature_reading), ', "pressao":' + str(atm_pressure), ', "giroscopio":', mpu9250s.gyro, ', "acelerometro":', mpu9250s.acceleration, ', "payload":', ''.join([str(x2) for x2 in ['{', '"dados climatologicos":', ''.join([str(x) for x in ['{', '"altitude":' + str(altitude),  ', "co2":' + str(co2), '}']]), ', "cam_status":' + str(cam_status), '}']]), '}']])
  time.sleep(1)
  
  ##tenta enviar por POST, se houver erro procede e avisa
  try:
    HTTP_request = urequests.post('https://putsreq.com/T8ueVaCJxjc9v2vVmHMY', json=http_data)
  except OSError as e:
    if e.errno == 12:
        print("Error: Not enough memory")
    else:
        print("Unexpected OSError:", e)
  time.sleep(1)
  
  ##Junta os dados enviados com a camera, nomeia um arquivo e escreve os dados
  file_data = ''.join([str(x) for x in ['{{"http_data":', http_data, '},"cam_data":', str(cam), '}']])
  file_name = ''.join([str(x4) for x4 in ['/sd/log_vac_test', str(log_number), '.csv']])
  arquivo = open(file_name, 'bw')

  arquivo.write(file_data)
  arquivo.close()
  print('recorder on sd ')
  print(http_data)

  ##Envia os dados por radio
  uart1.write(str(http_data))
  log_number = (log_number if isinstance(log_number, int) else 0) + 1
  print('end of transmission')
  print('   ')

  ##espera o tempo necessario
  time.sleep(180)

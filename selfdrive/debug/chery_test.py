# from openpilot.common.numpy_fast import clip,interp
import numpy as np
import time
from panda.python.isotp import isotp_send, isotp_recv
import struct
from openpilot.common.params import Params
from panda import Panda
from panda.python.uds import UdsClient, MessageTimeoutError, SESSION_TYPE, DTC_GROUP_TYPE
from hexdump import hexdump
from panda.python.uds import UdsClient, MessageTimeoutError, NegativeResponseError, InvalidSubAddressError, \
                             SESSION_TYPE, DATA_IDENTIFIER_TYPE
from openpilot.selfdrive.car.fw_versions import set_obd_multiplexing

from openpilot.selfdrive.car.isotp_parallel_query import IsoTpParallelQuery
import panda.python.uds as uds
import threading
import json
import requests
from common.op_params import opParams

def p16(val):
  return struct.pack("!H", val)

ACCEL_MAX = 2.0               # m/s^2 max acceleration
ACCEL_MAX_PLUS = 4.0          # m/s^2 max acceleration
ACCEL_MIN = -3.5              # m/s^2 max deceleration
MIN_GAS = -24
INACTIVE_GAS = -24

GAS_MAX = 512
GAS_MIN = -512

ACCEL_LOOKUP_BP = [ACCEL_MIN, 0, ACCEL_MAX]
ACCEL_LOOKUP_V = [GAS_MIN, -24, GAS_MAX]

accel = int(round(np.interp(-2, ACCEL_LOOKUP_BP, ACCEL_LOOKUP_V)))

# print(accel)


# import cereal.messaging as messaging

# sm = messaging.SubMaster(['longitudinalPlan'])

# while True:
#     sm.update()
#     if sm.updated['longitudinalPlan']:
#         print(sm['longitudinalPlan'])

# panda = Panda()
# serials = Panda.list()
# print(f"found {len(serials)} panda(s) - {serials}")
# for s in serials:
#     print("flashing", s)

# panda.set_safety_mode(Panda.SAFETY_ELM327)

# Connect to the Panda device
# panda = Panda()
# panda.set_safety_mode(Panda.SAFETY_ELM327)

# panda.can_clear(0)

# # 09 02 = Get VIN
# isotp_send(panda, b"\x09\x02", 0x7df)
# ret = isotp_recv(panda, 0x7e8)
# hexdump(ret)
# print("VIN: %s" % "".join(map(chr, ret[:2])))
# Define the UDS request for VIN (0x22 0xF1 0x90)
# uds_request = bytearray([0x22, 0xF1, 0x90])

# uds_request = bytearray([0x22, 0xF1, 0x90])

# # Send the request and receive the response
# def send_uds_request(panda, request):
#     # CAN message format: (address, data, extended)
#     panda.can_send(0x7E0, request, 1)
#     time.sleep(0.1)  # wait for response
#     response = panda.can_recv()

#     for msg in response:
#         print(msg)
#         # addr, data, _ = msg
#         # if addr == 0x7E8:  # Response address for UDS
#         #     return data
#     return None

# response_data = send_uds_request(panda, uds_request)

# if response_data:
#     vin = ''.join(chr(x) for x in response_data[3:20])
#     print(f"VIN: {vin}")
# else:
#     print("No response or VIN not found")


# uds_client = UdsClient(panda, 0x7e5, None, 1, sub_addr=None, timeout=0.2, debug=False)

# data = uds_client.read_data_by_identifier(0x441E)  # type: ignore
# if data:
#     print(hexdump(data))
#     soc = struct.unpack(">H", bytes(data)[6:8])[0]     *100 /10000       # revs

#     print(soc)
# params = Params()
# set_obd_multiplexing(params, False)

import time
import cereal.messaging as messaging

op_params = opParams()

def get_vin(logcan, sendcan, buses, timeout=0.1, retry=2, debug=False):

  addr = 0x7e0

  OBD_VIN_REQUEST = b'\x22\xF1\x90'
  OBD_VIN_RESPONSE = b'\x22\x40\xF190'
  uds_request = bytearray([0x22, 0xF1, 0x90])

  UDS_VIN_REQUEST = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER]) + p16(uds.DATA_IDENTIFIER_TYPE.VIN)
  UDS_VIN_RESPONSE = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER + 0x40]) + p16(uds.DATA_IDENTIFIER_TYPE.VIN)

  UDS_BMS_REQUEST = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER]) + p16(0x441E)
  UDS_BMS_RESPONSE = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER + 0x40]) + p16(0x441E)

  # addr = 0x7e5
  query = IsoTpParallelQuery(sendcan, logcan, 1, [addr],
                                    [UDS_VIN_REQUEST],
                                    [UDS_VIN_RESPONSE], debug=True)

  timeout=0.1
  results = query.get_data(timeout)
  vin = results.get((addr, None))
  print(vin)
  print(hexdump(vin))

def getSoc(logcan, sendcan, buses, timeout=0.1, retry=2, debug=False):
  # addr = 0x7e0

  OBD_VIN_REQUEST = b'\x22\xF1\x90'
  OBD_VIN_RESPONSE = b'\x22\x40\xF190'
  uds_request = bytearray([0x22, 0xF1, 0x90])

  UDS_VIN_REQUEST = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER]) + p16(uds.DATA_IDENTIFIER_TYPE.VIN)
  UDS_VIN_RESPONSE = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER + 0x40]) + p16(uds.DATA_IDENTIFIER_TYPE.VIN)

  UDS_BMS_REQUEST = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER]) + p16(0x441E)
  UDS_BMS_RESPONSE = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER + 0x40]) + p16(0x441E)

  addr = 0x7e5
  query = IsoTpParallelQuery(sendcan, logcan, 1, [addr],
                                    [UDS_BMS_REQUEST],
                                    [UDS_BMS_RESPONSE], debug=True)

  timeout=0.1
  results = query.get_data(timeout)
  data = results.get((addr, None))
  print(data)
  print(hexdump(data))

  # "SBI": 6,
  #   "DL": 2,
  #   "MUL": 100,
  #   "DIV": 10000,
  #   "OFS": 0,
  soc = struct.unpack(">H", bytes(data)[6:8])[0]     *100 /10000

  op_params.put("OBDDataSoc", soc)
  print(soc)
  print("Get SOC")

  return soc

def getSoh(logcan, sendcan, buses, timeout=0.1, retry=2, debug=False):
  subaddr = 0x1048 #221048

  UDS_BMS_REQUEST = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER]) + p16(subaddr)
  UDS_BMS_RESPONSE = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER + 0x40]) + p16(subaddr)

  addr = 0x7e5
  query = IsoTpParallelQuery(sendcan, logcan, 1, [addr],
                                    [UDS_BMS_REQUEST],
                                    [UDS_BMS_RESPONSE], debug=True)

  timeout=0.1
  results = query.get_data(timeout)
  data = results.get((addr, None))
  print(data)
  print(hexdump(data))

  #  "SBI": 0,
  #   "DL": 2,
  #   "MUL": 1,
  #   "DIV": 1,

  soc = struct.unpack(">H", bytes(data)[:2])[0]

  op_params.put("OBDDataSoh", soc)
  print(soc)
  print("Get SOH")

  return soc

def getChargeTimes(logcan, sendcan, buses, timeout=0.1, retry=2, debug=False):
  subaddr = 0x4410 #224410

  UDS_BMS_REQUEST = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER]) + p16(subaddr)
  UDS_BMS_RESPONSE = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER + 0x40]) + p16(subaddr)

  addr = 0x7e5
  query = IsoTpParallelQuery(sendcan, logcan, 1, [addr],
                                    [UDS_BMS_REQUEST],
                                    [UDS_BMS_RESPONSE], debug=True)

  timeout=0.1
  results = query.get_data(timeout)
  data = results.get((addr, None))
  print(data)
  print(hexdump(data))

  #  "SBI": 0,
  #   "DL": 2,
  #   "MUL": 1,
  #   "DIV": 1,

  soc = struct.unpack(">H", bytes(data)[:2])[0]

  op_params.put("OBDDataChargeTimes", soc)
  print(soc)
  print("Get Charge Times")

  return soc

url = "https://api1.openpilot.id/location"

def test(logcan, sendcan):
  try:
    print('get data from car')
    lat_long = get_last_lon_lat()
    print(lat_long)
    # print(sendcan)
    # get_vin(logcan,sendcan,1)
    # obdNum =  Params().get("OBDDataNum",1)
    obdNum = 1

    if obdNum ==1:
      soc = getSoc(logcan, sendcan, 1)
    elif obdNum == 2:
      soc = getSoh(logcan, sendcan, 1)
    elif obdNum == 3:
      soc = getChargeTimes(logcan, sendcan, 1)
    # pin_thread = threading.Thread(target=sendtoServer, args=(lat_long,soc))
    # pin_thread.start()

  except Exception as e:
     print(f"Failed get date chery {e}")

def log_data(logcan, sendcan, enable, speed):
  try:
    print('get data from car')
    lat_long = get_last_lon_lat()
    print(lat_long)
    obdNum =  op_params.get("OBDDataNum")
    # obdNum =  1

    # print(sendcan)
    # get_vin(logcan,sendcan,1)
    # soc = 0
    # soc = getSoc(logcan, sendcan, 1)
    if obdNum ==1:
      soc = getSoc(logcan, sendcan, 1)
      op_params.put("OBDDataNum", 2)
    elif obdNum == 2:
      soc = getSoh(logcan, sendcan, 1)
      op_params.put("OBDDataNum", 3)
    elif obdNum == 3:
      soc = getChargeTimes(logcan, sendcan, 1)
      op_params.put("OBDDataNum", 1)

    pin_thread = threading.Thread(target=sendtoServer, args=(lat_long, soc, enable, speed))
    pin_thread.start()


  except Exception as e:
     print(f"Failed get date chery {e}")

def log_soh(logcan, sendcan, enable, speed):
  try:
    print('get data from car soh')
    lat_long = get_last_lon_lat()
    print(lat_long)
    soc = getSoh(logcan, sendcan, 1)
  except Exception as e:
     print(f"Failed get date chery {e}")

def sendtoServer(lat_long,soc, enable, speed):

  soc =  op_params.get("OBDDataSoc")
  chargeTimes =  op_params.get("OBDDataChargeTimes")
  soh =  op_params.get("OBDDataSoh")

  params = {
      "longitude": lat_long[0],
      "latitude": lat_long[1],
      "soc":soc,
      "soh":soh,
      "chargeTimes":chargeTimes,
      "enable":enable,
      "speed": speed
  }
  print(json.dumps(params))

  # Make the POST request
  response = requests.post(url, data=params)
  # Check the response
  if response.status_code == 200:
      print("Success:", response.json())  # or response.text for non-JSON response
  else:
      print("Failed:", response.status_code, response.text)

def test_thread(logcan,sendcan):
  pin_thread = threading.Thread(target=test, args=(logcan,sendcan))
  pin_thread.start()

def get_last_lon_lat():
  last_pos = Params().get("LastGPSPosition")
  if last_pos is not None and last_pos != "":
    l = json.loads(last_pos)
    return l["longitude"], l["latitude"]
  return "", ""

if __name__ == "__main__":
  sendcan = messaging.pub_sock('sendcan')
  logcan = messaging.sub_sock('can')
  # pm = messaging.PubMaster(['sendcan'])
  # sendcan = pm.sock['sendcan']
  time.sleep(1)

  print('get data')
  # get_vin(logcan,sendcan,1)
  test(logcan,sendcan)
  # test()

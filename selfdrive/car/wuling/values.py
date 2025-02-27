from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, IntFlag, StrEnum
from typing import Dict, List, Union
from panda.python import uds

from cereal import car
from openpilot.selfdrive.car import AngleRateLimit, CarSpecs, DbcDict, PlatformConfig, Platforms, dbc_dict
from selfdrive.car.docs_definitions import CarFootnote, CarHarness, CarDocs, CarParts, Column
from selfdrive.car.fw_query_definitions import FwQueryConfig, Request, StdQueries, p16

Ecu = car.CarParams.Ecu



class CarControllerParams:

  STEER_STEP = 2          # control frames per command 50Hz
  LKAS_HUD_STEP = 5                     # LkasHUD frequency 20Hz

  STEER_MAX = 150  # Safety limit, not LKA max. Trucks use 600.
  STEER_DELTA_UP = 3      # 3 is stock. 100 is fine. 200 is too much it seems
  STEER_DELTA_DOWN = 4    # no faults on the way down it seems

  STEER_ERROR_MAX = 80
  MIN_STEER_SPEED = 3.  # m/s

  STEER_DRIVER_ALLOWANCE = 45
  STEER_DRIVER_MULTIPLIER = 2    # weight driver torque heavily
  STEER_DRIVER_FACTOR = 1        # from dbc
  NEAR_STOP_BRAKE_PHASE = 0.5  # m/s
  INACTIVE_STEER_STEP = 10  # Inactive control frames per command (10hz)

  # Heartbeat for dash "Service Adaptive Cruise" and "Service Front Camera"
  ADAS_KEEPALIVE_STEP = 100
  CAMERA_KEEPALIVE_STEP = 100
  STEER_THRESHOLD = 40
  HUD_MULTIPLIER = 0.685

  # Allow small margin below -3.5 m/s^2 from ISO 15622:2018 since we
  # perform the closed loop control, and might need some
  # to apply some more braking if we're on a downhill slope.
  # Our controller should still keep the 2 second average above
  # -3.5 m/s^2 as per planner limits
  ACCEL_MAX = 2.0  # m/s^2
  ACCEL_MIN = -3.5  # m/s^2

  GAS_MAX = 241
  GAS_MIN = -600

  ACCEL_LOOKUP_BP = [ACCEL_MIN, ACCEL_MAX]
  ACCEL_LOOKUP_V = [GAS_MIN, GAS_MAX]

  def __init__(self, CP):
    self.ZERO_GAS = 0  # Coasting


class CAR(StrEnum):
 ALMAS_RS_PRO = "WULING ALMAZ RS PRO 2022"


class Footnote(Enum):
  OBD_II = CarFootnote(
    'Wuling Almaz RS WITH Acc and LKAS',
    Column.MODEL)


@dataclass
class WulingCarDocs(CarDocs):
  package: str = "Adaptive Cruise Control (ACC)"
  car_parts: CarParts = field(default_factory=CarParts.common([CarHarness.vw]))

@dataclass
class WulingPlatformConfig(PlatformConfig):
  dbc_dict: DbcDict = field(default_factory=lambda: dbc_dict('wuling_almazrs_generated', None))


class CAR(Platforms):
  ALMAS_RS_PRO = WulingPlatformConfig(
    "WULING ALMAZ RS PRO 2022",
    [WulingCarDocs("Wuling Almaz RS Pro 2022")],
    CarSpecs(mass=1950, wheelbase=2.75, steerRatio=18)
  )

class CruiseButtons:
  INIT = 0
  NONE = 0
  UNPRESS = 0
  GAP_DOWN = 1
  GAP_UP = 2
  DECEL_SET = 4
  RES_ACCEL = 8
  MAIN = 16
  CANCEL = 32
  TJA = 32

class AccState:
  OFF = 0
  ACTIVE = 1
  FAULTED = 3
  STANDSTILL = 4

class CanBus:
  POWERTRAIN = 0
  OBSTACLE = 1
  CAMERA = 2
  CHASSIS = 2
  SW_GMLAN = 3
  LOOPBACK = 128
  DROPPED = 192

WULING_VERSION_REQUEST = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER]) + \
  p16(uds.DATA_IDENTIFIER_TYPE.ECU_MANUFACTURING_DATE) + \
  p16(uds.DATA_IDENTIFIER_TYPE.SYSTEM_SUPPLIER_ECU_SOFTWARE_VERSION_NUMBER) + \
  p16(uds.DATA_IDENTIFIER_TYPE.VEHICLE_MANUFACTURER_ECU_HARDWARE_NUMBER) + \
  p16(uds.DATA_IDENTIFIER_TYPE.SYSTEM_SUPPLIER_ECU_SOFTWARE_NUMBER)
WULING_VERSION_RESPONSE = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER + 0x40])

FW_QUERY_CONFIG = FwQueryConfig(
  requests=[
     Request(
      [WULING_VERSION_REQUEST],
      [WULING_VERSION_RESPONSE],
    ),
  ],
)


DBC = CAR.create_dbc_map()

PREGLOBAL_CARS = ()

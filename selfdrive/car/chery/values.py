from collections import defaultdict, namedtuple
from dataclasses import dataclass, field
from enum import Enum, IntFlag, StrEnum
from typing import Dict, List, Union
from panda.python import uds
from openpilot.selfdrive.car import CanBusBase
from openpilot.common.realtime import DT_CTRL

from cereal import car
from openpilot.selfdrive.car import AngleRateLimit, CarSpecs, DbcDict, PlatformConfig, Platforms, dbc_dict
from openpilot.selfdrive.car.docs_definitions import CarFootnote, CarHarness, CarDocs, CarParts, Column
from openpilot.selfdrive.car.fw_query_definitions import FwQueryConfig, Request, StdQueries, p16

Ecu = car.CarParams.Ecu
Button = namedtuple('Button', ['event_type', 'can_addr', 'can_msg', 'values'])

class CarControllerParams:
  STEER_STEP = 2
  LKAS_HUD_STEP = 5
  BUTTONS_STEP = 5
  ACC_CONTROL_STEP = 2
  HUD_MULTIPLIER = 1
  STEER_MAX = 2000
  STEER_DRIVER_MULTIPLIER = 3              # weight driver torque heavily
  STEER_DRIVER_FACTOR = 1                  # from dbc

  STEER_DELTA_UP = 2
  STEER_DELTA_DOWN = 3

  STEER_THRESHOLD = 70
  STEER_DRIVER_ALLOWANCE = 1.0  # Driver intervention threshold, Nm

  # Temporary steer fault timeout
  # Maximum time to continuously read 0 torque from EPS
  STEER_TIMEOUT = 30 / DT_CTRL
  # ANGLE_RATE_LIMIT_UP = AngleRateLimit(speed_bp=[0., 5., 15.], angle_v=[1., 1.2, .1])
  # ANGLE_RATE_LIMIT_DOWN = AngleRateLimit(speed_bp=[0., 5., 15.], angle_v=[1., 2.0, 0.2])

  # ANGLE_RATE_LIMIT_UP = AngleRateLimit(speed_bp=[5, 25], angle_v=[0.3, 0.15])
  # ANGLE_RATE_LIMIT_DOWN = AngleRateLimit(speed_bp=[5, 25], angle_v=[0.36, 0.26])

  # Best on SGO Model
  # ANGLE_RATE_LIMIT_UP = AngleRateLimit(speed_bp=[5, 25], angle_v=[0.4, 0.081])
  # ANGLE_RATE_LIMIT_DOWN = AngleRateLimit(speed_bp=[5, 25], angle_v=[0.525, 0.09])

  # tune for Notre Dame Model
  # ANGLE_RATE_LIMIT_UP = AngleRateLimit(speed_bp=[5, 25], angle_v=[0.1, 0.090])
  # ANGLE_RATE_LIMIT_DOWN = AngleRateLimit(speed_bp=[5, 25], angle_v=[0.125, 0.0925])



  # ANGLE_RATE_LIMIT_UP = AngleRateLimit(speed_bp=[5, 25], angle_v=[0.1, 0.081])
  # ANGLE_RATE_LIMIT_DOWN = AngleRateLimit(speed_bp=[5, 25], angle_v=[0.125, 0.09])

  # ANGLE_RATE_LIMIT_UP = AngleRateLimit(speed_bp=[5, 25], angle_v=[0.2, 0.071])
  # ANGLE_RATE_LIMIT_DOWN = AngleRateLimit(speed_bp=[5, 25], angle_v=[0.26, 0.08])

  # ANGLE_RATE_LIMIT_UP = AngleRateLimit(speed_bp=[5, 25], angle_v=[0.3, 0.085])
  # ANGLE_RATE_LIMIT_DOWN = AngleRateLimit(speed_bp=[5, 25], angle_v=[0.325, 0.09])

  # deg per command, and commands go out at 100Hz/STEER_STEP = 50Hz, so multiply by 50 for deg/s.
  # Sized against what the driver's own steering achieves, measured per 100ms window over 39min
  # of rlog (p95 by speed band): 142 deg/s below 5 m/s, 37 at 5-10, 13 at 10-25.
  # The old [0.4, 0.1] over [5, 25] allowed 20 deg/s below 5 m/s -- 7x under the driver -- which
  # left the command trailing the request by ~50deg for up to 4s through a tight turn. Above
  # 10 m/s it was already in line with the driver, so the top of the range is left alone and
  # only the low-speed end opens up.
  # The EPS is not the constraint: while openpilot steers, |commanded - measured| runs p50 0.10deg
  # and p95 0.70deg, so it tracks whatever it is given.
  # Four breakpoints, because three force a straight ramp from the low-speed anchor down to
  # 25 m/s that passes way over the driver's p95 through the middle of the range. The knee at
  # 10 m/s puts the curve back on the old values from there up.
  # panda's CHERY_STEERING_LIMITS must stay liberally above these or it drops the LKAS frame.
  ANGLE_RATE_LIMIT_UP = AngleRateLimit(speed_bp=[0, 5, 10, 25], angle_v=[1.2, 0.7, 0.32, 0.1])    # 60, 35, 16, 5 deg/s
  ANGLE_RATE_LIMIT_DOWN = AngleRateLimit(speed_bp=[0, 5, 10, 25], angle_v=[1.4, 0.85, 0.4, 0.2])  # 70, 42, 20, 10 deg/s

  ACCEL_MAX = 2.0               # m/s^2 max acceleration
  ACCEL_MAX_PLUS = 4.0          # m/s^2 max acceleration
  ACCEL_MIN = -3.5              # m/s^2 max deceleration
  MIN_GAS = -24
  INACTIVE_GAS = -24

  GAS_MAX = 511
  GAS_MIN = -511

  ACCEL_LOOKUP_BP = [ACCEL_MIN, 0, ACCEL_MAX]
  ACCEL_LOOKUP_V = [GAS_MIN, -24, GAS_MAX]

  def __init__(self, CP):
    self.BUTTONS = [
      Button(car.CarState.ButtonEvent.Type.setCruise, "STEER_BUTTON", "ACC", [1]),
      Button(car.CarState.ButtonEvent.Type.resumeCruise, "STEER_BUTTON", "RES_PLUS", [1]),
      Button(car.CarState.ButtonEvent.Type.accelCruise, "STEER_BUTTON", "RES_PLUS", [1]),
      Button(car.CarState.ButtonEvent.Type.decelCruise, "STEER_BUTTON", "RES_MINUS", [1]),
      Button(car.CarState.ButtonEvent.Type.cancel, "STEER_BUTTON", "ACC", [1]),
      Button(car.CarState.ButtonEvent.Type.gapAdjustCruise, "STEER_BUTTON", "GAP_ADJUST_UP", [1]),
    ]

class CheryFlags(IntFlag):
  # Static flags
  CANFD = 1


@dataclass
class CheryCarDocs(CarDocs):
  package: str = "Chery Pilot"
  car_parts: CarParts = field(default_factory=CarParts.common([CarHarness.custom]))

  def init(self):
    super().init()
    self.flags |= CheryFlags.CANFD

@dataclass(frozen=True)
class CheryCarSpecs(CarSpecs):
  centerToFrontRatio: float = 0.44
  steerRatio: float = 14.

@dataclass
class CheryPlatformConfig(PlatformConfig):
  dbc_dict: DbcDict = field(default_factory=lambda: dbc_dict('chery_canfd', None))


class CAR(Platforms):
  CHERY_OMODA_E5 = CheryPlatformConfig(
    [CheryCarDocs("Chery Omoda E5")],
    CheryCarSpecs(mass=1785, wheelbase=2.63, steerRatio=14)
  )


FW_QUERY_CONFIG = FwQueryConfig(
  requests=[
    # TODO: check data to ensure ABS does not skip ISO-TP frames on bus 0
    Request(
      [StdQueries.MANUFACTURER_SOFTWARE_VERSION_REQUEST],
      [StdQueries.MANUFACTURER_SOFTWARE_VERSION_RESPONSE],
      bus=0,
    ),
    Request(
      [StdQueries.TESTER_PRESENT_REQUEST, StdQueries.MANUFACTURER_SOFTWARE_VERSION_REQUEST],
      [StdQueries.TESTER_PRESENT_RESPONSE, StdQueries.MANUFACTURER_SOFTWARE_VERSION_RESPONSE],
      whitelist_ecus=[Ecu.abs, Ecu.debug, Ecu.engine, Ecu.eps, Ecu.fwdCamera, Ecu.fwdRadar, Ecu.shiftByWire],
      logging=True,
    ),
  ],
)

DBC = CAR.create_dbc_map()

# class CanBus:
#   POWERTRAIN = 0
#   OBSTACLE = 1
#   CAMERA = 2
#   CHASSIS = 2
#   SW_GMLAN = 3
#   CANFD_MAIN = 4
#   CANFD_AUX = 5
#   CANFD_CAM = 6
#   LOOPBACK = 128
#   DROPPED = 192
class CanBus(CanBusBase):
  def __init__(self, CP=None, fingerprint=None) -> None:
    super().__init__(CP, fingerprint)

  @property
  def main(self) -> int:
    return self.offset

  @property
  def radar(self) -> int:
    return self.offset + 1

  @property
  def camera(self) -> int:
    return self.offset + 2

#!/usr/bin/env python3
from cereal import car, custom
from openpilot.common.conversions import Conversions as CV
from panda import Panda

from openpilot.selfdrive.car import create_button_events, get_safety_config
from openpilot.selfdrive.car.interfaces import CarInterfaceBase
from openpilot.selfdrive.car.chery.values import CAR, CanBus, CarControllerParams
from openpilot.common.params import Params
from openpilot.common.op_params import opParams

ButtonType = car.CarState.ButtonEvent.Type
TransmissionType = car.CarParams.TransmissionType
FrogPilotButtonType = custom.FrogPilotCarState.ButtonEvent.Type
GearShifter = car.CarState.GearShifter
EventName = car.CarEvent.EventName
# BUTTONS_DICT = {CruiseButtons.RES_ACCEL: ButtonType.accelCruise, CruiseButtons.DECEL_SET: ButtonType.decelCruise,
#                 CruiseButtons.MAIN: ButtonType.altButton3, CruiseButtons.CANCEL: ButtonType.cancel}

CRUISE_OVERRIDE_SPEED_MIN = 5 * CV.KPH_TO_MS

class CarInterface(CarInterfaceBase):
  def __init__(self, CP, CarController, CarState):
    super().__init__(CP, CarController, CarState)

    self.dp_cruise_speed = 0. # km/h
    self.dp_override_speed_last = 0. # km/h
    self.dp_override_speed = 0. # m/s

  @staticmethod
  def _get_params(ret, candidate, fingerprint, car_fw, disable_openpilot_long, experimental_long, docs):
    ret.carName = "chery"

    CAN = CanBus(fingerprint=fingerprint)
    cfgs = [get_safety_config(car.CarParams.SafetyModel.cheryCanFd)]
    if CAN.main >= 4:
      cfgs.insert(0, get_safety_config(car.CarParams.SafetyModel.elm327))
    ret.safetyConfigs = cfgs

    ret.radarUnavailable = True

    ret.experimentalLongitudinalAvailable = True
    if experimental_long:
      ret.safetyConfigs[-1].safetyParam |= Panda.FLAG_CHERY_LONG_CONTROL
      ret.openpilotLongitudinalControl = True

    ret.pcmCruise = not ret.openpilotLongitudinalControl

    ret.wheelbase = 2.63
    ret.tireStiffnessFactor = 0.8
    ret.centerToFront = ret.wheelbase * 0.4

    ret.steerLimitTimer = 1.0
    ret.steerActuatorDelay = 0.2
    ret.steerControlType = car.CarParams.SteerControlType.angle

    ret.transmissionType = TransmissionType.automatic

    ret.stopAccel = CarControllerParams.ACCEL_MIN
    ret.stoppingDecelRate = 0.1
    ret.vEgoStarting = 0.1
    ret.vEgoStopping = 0.25
    # ret.longitudinalActuatorDelay = 0.5 # s
    # ret.startAccel = 1.0

    # ret.longitudinalTuning.kiBP = [0., 35.]
    # ret.longitudinalTuning.kiV = [0.15, 0.15]
    # ret.longitudinalTuning.kpBP = [5., 35.]
    # ret.longitudinalTuning.kpV = [0.05, 0.05]

    # ret.longitudinalTuning.deadzoneBP = [0.]
    # ret.longitudinalTuning.deadzoneV = [0.]
    # ret.longitudinalTuning.kpV = [0.0]
    # ret.longitudinalTuning.kiV = [0.0]

    ret.longitudinalTuning.kpBP = [0.]
    ret.longitudinalTuning.kpV = [0.1]
    ret.longitudinalTuning.kiV = [0.]
    ret.longitudinalTuning.deadzoneBP = [0.]
    ret.longitudinalTuning.deadzoneV = [0.]

    ret.enableBsm = 0x4B1 in fingerprint[CAN.main] and 0x4B3 in fingerprint[CAN.main]

    ret.minEnableSpeed = -1
    ret.minSteerSpeed = -1

    return ret

  # returns a car.CarState
  def _update(self, c, frogpilot_toggles):

    ret, fp_ret = self.CS.update(self.cp, self.cp_cam, c, self.cp_loopback, frogpilot_toggles)

    ret.buttonEvents = [
        *create_button_events(self.CS.cruise_decreased, self.CS.cruise_decreased_previously, {1: ButtonType.decelCruise}),
        *create_button_events(self.CS.cruise_increased, self.CS.cruise_increased_previously, {1: ButtonType.accelCruise}),
        *create_button_events(self.CS.distance_button, self.CS.prev_distance_button, {1: ButtonType.gapAdjustCruise}),
        *create_button_events(self.CS.lkas_enabled, self.CS.lkas_previously_enabled, {1: FrogPilotButtonType.lkas}),
      ]
    events = self.create_common_events(ret, extra_gears=[GearShifter.sport, GearShifter.eco], pcm_enable=self.CP.pcmCruise)

    if not self.CP.pcmCruise:
      if any(b.type == ButtonType.accelCruise and b.pressed for b in ret.buttonEvents):
        events.add(EventName.buttonEnable)

    ret.events = events.to_msg()
    return ret, fp_ret

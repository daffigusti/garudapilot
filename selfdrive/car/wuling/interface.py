#!/usr/bin/env python3
from cereal import car
from panda import Panda
from openpilot.common.conversions import Conversions as CV

from openpilot.selfdrive.car import STD_CARGO_KG,scale_tire_stiffness, create_button_events, get_safety_config
from openpilot.selfdrive.car.interfaces import CarInterfaceBase
from openpilot.selfdrive.car.wuling.values import CAR, CruiseButtons, PREGLOBAL_CARS, CarControllerParams, CanBus
from openpilot.common.op_params import opParams

ButtonType = car.CarState.ButtonEvent.Type
TransmissionType = car.CarParams.TransmissionType
GearShifter = car.CarState.GearShifter
EventName = car.CarEvent.EventName
BUTTONS_DICT = {CruiseButtons.RES_ACCEL: ButtonType.accelCruise, CruiseButtons.DECEL_SET: ButtonType.decelCruise,
                CruiseButtons.MAIN: ButtonType.altButton3, CruiseButtons.CANCEL: ButtonType.cancel}

CRUISE_OVERRIDE_SPEED_MIN = 5 * CV.KPH_TO_MS

class CarInterface(CarInterfaceBase):
  def __init__(self, CP, FPCP, CarController, CarState):
    super().__init__(CP, FPCP, CarController, CarState)

    self.dp_cruise_speed = 0. # km/h
    self.dp_override_speed_last = 0. # km/h
    self.dp_override_speed = 0. # m/s

  @staticmethod
  def get_pid_accel_limits(CP, current_speed, cruise_speed):
    return CarControllerParams.ACCEL_MIN, CarControllerParams.ACCEL_MAX

  @staticmethod
  def _get_params(ret, candidate, fingerprint, car_fw, experimental_long, docs, frogpilot_toggles):
    ret.carName = "wuling"
    ret.safetyConfigs = [get_safety_config(car.CarParams.SafetyModel.wuling)]
    ret.radarUnavailable = True
    ret.dashcamOnly = candidate in PREGLOBAL_CARS
    ret.pcmCruise = True

    op_params = opParams("wuling car_interface.py for lateral override")

    ret.experimentalLongitudinalAvailable = True
    ret.openpilotLongitudinalControl = experimental_long
    ret.pcmCruise = not ret.openpilotLongitudinalControl
    ret.steerRatio = op_params.get('steer_ratio', force_update=True)

    ret.steerLimitTimer = 0.4
    ret.steerActuatorDelay = 0.2

    ret.transmissionType = TransmissionType.automatic
    ret.enableBsm = 0xb1 in fingerprint[0]  # SWA_01

    CarInterfaceBase.configure_torque_tune(candidate, ret.lateralTuning)

    ret.longitudinalTuning.kpV = [0.1]
    ret.longitudinalTuning.kiV = [0.0]
    ret.stoppingControl = True
    ret.autoResumeSng = True
    ret.startingState = True
    ret.vEgoStarting = 0.1
    ret.startAccel = 0.8

    return ret

  # returns a car.CarState
  def _update(self, c, frogpilot_toggles):

    ret, fp_ret = self.CS.update(self.cp, self.cp_cam, self.cp_loopback, frogpilot_toggles)
    # self.CS = self.sp_update_params(self.CS)

    buttonEvents = []
    ret.engineRpm = self.CS.engineRPM

    # Don't add event if transitioning from INIT, unless it's to an actual button
    if self.CS.cruise_buttons != CruiseButtons.UNPRESS or self.CS.prev_cruise_buttons != CruiseButtons.INIT:
      ret.buttonEvents = create_button_events(self.CS.cruise_buttons, self.CS.prev_cruise_buttons, BUTTONS_DICT,
                                              unpressed_btn=CruiseButtons.UNPRESS)
    events = self.create_common_events(ret, extra_gears=[GearShifter.sport, GearShifter.low, GearShifter.eco, GearShifter.manumatic], pcm_enable=self.CP.pcmCruise)

    if not self.CP.pcmCruise:
      if any(b.type == ButtonType.accelCruise and b.pressed for b in ret.buttonEvents):
        events.add(EventName.buttonEnable)

    # Enabling at a standstill with brake is allowed
    # TODO: verify 17 Volt can enable for the first time at a stop and allow for all GMs
    below_min_enable_speed = ret.vEgo < self.CP.minEnableSpeed
    if below_min_enable_speed and not (ret.standstill and ret.brake >= 20):
      events.add(EventName.belowEngageSpeed)
    if self.CS.park_brake:
      events.add(EventName.parkBrake)
    if ret.cruiseState.standstill:
      events.add(EventName.resumeRequired)
    if ret.vEgo < self.CP.minSteerSpeed:
      events.add(EventName.belowSteerSpeed)

    ret.events = events.to_msg()
    return ret, fp_ret

  def apply(self, c, now_nanos, frogpilot_toggles):
    return self.CC.update(c, self.CS, now_nanos, frogpilot_toggles)

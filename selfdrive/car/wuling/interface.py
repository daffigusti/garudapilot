#!/usr/bin/env python3
from cereal import car
from panda import Panda
from common.conversions import Conversions as CV

from openpilot.selfdrive.car import STD_CARGO_KG,scale_tire_stiffness, create_button_events, get_safety_config
from openpilot.selfdrive.car.interfaces import CarInterfaceBase
from openpilot.selfdrive.car.wuling.values import CAR, CruiseButtons, PREGLOBAL_CARS, CarControllerParams, CanBus
from common.params import Params
from common.op_params import opParams

ButtonType = car.CarState.ButtonEvent.Type
TransmissionType = car.CarParams.TransmissionType
GearShifter = car.CarState.GearShifter
EventName = car.CarEvent.EventName
BUTTONS_DICT = {CruiseButtons.RES_ACCEL: ButtonType.accelCruise, CruiseButtons.DECEL_SET: ButtonType.decelCruise,
                CruiseButtons.MAIN: ButtonType.altButton3, CruiseButtons.CANCEL: ButtonType.cancel}

CRUISE_OVERRIDE_SPEED_MIN = 5 * CV.KPH_TO_MS

class CarInterface(CarInterfaceBase):
  def __init__(self, CP, CarController, CarState):
    super().__init__(CP, CarController, CarState)

    self.dp_cruise_speed = 0. # km/h
    self.dp_override_speed_last = 0. # km/h
    self.dp_override_speed = 0. # m/s

  @staticmethod
  def get_pid_accel_limits(CP, current_speed, cruise_speed, frogpilot_variables):
    return CarControllerParams.ACCEL_MIN, CarControllerParams.ACCEL_MAX

  @staticmethod
  def _get_params(ret, params, candidate, fingerprint, car_fw, experimental_long, docs):
    ret.carName = "wuling"
    ret.safetyConfigs = [get_safety_config(car.CarParams.SafetyModel.wuling)]
    ret.radarUnavailable = True
    ret.dashcamOnly = candidate in PREGLOBAL_CARS
    # ret.lateralTuning.init('pid')
    ret.pcmCruise = True

    op_params = opParams("wuling car_interface.py for lateral override")

    ret.experimentalLongitudinalAvailable = True
    ret.openpilotLongitudinalControl = experimental_long
    ret.pcmCruise = not ret.openpilotLongitudinalControl
    ret.mass = 1950.
    ret.wheelbase = 2.75
    ret.steerRatio = op_params.get('steer_ratio', force_update=True)
    ret.tireStiffnessFactor = 0.8
    ret.centerToFront = ret.wheelbase * 0.4

    ret.steerLimitTimer = 0.4
    ret.steerActuatorDelay = 0.2

    ret.transmissionType = TransmissionType.automatic
    ret.enableBsm = 0xb1 in fingerprint[0]  # SWA_01
    # CarInterfaceBase.dp_lat_tune_collection(candidate, ret.latTuneCollection)
    # CarInterfaceBase.configure_dp_tune(ret.lateralTuning, ret.latTuneCollection)
    
    # ret.lateralTuning.pid.kiBP, ret.lateralTuning.pid.kpBP = [[0., 41.0], [0., 41.0]]
    # ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.0002, 0.004], [0.1, 0.7]]
    # ret.lateralTuning.pid.kf = 0.00006   # full torque for 20 deg at 80mph means 0.00007818594

    # bp = [i * CV.MPH_TO_MS for i in op_params.get("TUNE_LAT_PID_bp_mph", force_update=True)]
    # kpV = [i for i in op_params.get("TUNE_LAT_PID_kp", force_update=True)]
    # kiV = [i for i in op_params.get("TUNE_LAT_PID_ki", force_update=True)]
    # ret.lateralTuning.pid.kpV = kpV
    # ret.lateralTuning.pid.kiV = kiV
    # ret.lateralTuning.pid.kpBP = bp
    # ret.lateralTuning.pid.kiBP = bp
    # ret.lateralTuning.pid.kf = op_params.get('TUNE_LAT_PID_kf', force_update=True)
        
    ret.minEnableSpeed = -1
    ret.minSteerSpeed = -1
    
    CarInterfaceBase.configure_torque_tune(candidate, ret.lateralTuning)
    
    params = Params()
    ret.longitudinalTuning.kpV = [0.1]
    ret.longitudinalTuning.kiV = [0.0]
    ret.stoppingControl = True
    ret.autoResumeSng = True
    ret.startingState = True
    ret.vEgoStarting = 0.1
    ret.startAccel = 0.8
    # ret.openpilotLongitudinalControl = False
    ret.longitudinalActuatorDelayLowerBound = 0.5
    ret.longitudinalActuatorDelayUpperBound = 0.5
    # ret.pcmCruise = not ret.openpilotLongitudinalControl
    
    return ret

  # returns a car.CarState
  def _update(self, c, conditional_experimental_mode, frogpilot_variables):

    ret = self.CS.update(self.cp, self.cp_cam, self.cp_loopback, conditional_experimental_mode, frogpilot_variables)
    # self.CS = self.sp_update_params(self.CS)

    buttonEvents = []
    ret.engineRpm = self.CS.engineRPM
    
    # Don't add event if transitioning from INIT, unless it's to an actual button
    if self.CS.cruise_buttons != CruiseButtons.UNPRESS or self.CS.prev_cruise_buttons != CruiseButtons.INIT:
      ret.buttonEvents = create_button_events(self.CS.cruise_buttons, self.CS.prev_cruise_buttons, BUTTONS_DICT,
                                              unpressed_btn=CruiseButtons.UNPRESS)
    events = self.create_common_events(ret,frogpilot_variables, extra_gears=[GearShifter.sport, GearShifter.low, GearShifter.eco, GearShifter.manumatic], pcm_enable=self.CP.pcmCruise)
    
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
    return ret

  def apply(self, c, now_nanos, frogpilot_variables):
    return self.CC.update(c, self.CS, now_nanos, frogpilot_variables)

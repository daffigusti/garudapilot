import copy

from cereal import car, custom

from openpilot.common.conversions import Conversions as CV
from opendbc.can.can_define import CANDefine
from opendbc.can.parser import CANParser
from openpilot.selfdrive.car.interfaces import CarStateBase
from openpilot.selfdrive.car.chery.values import DBC, CanBus, CarControllerParams

GearShifter = car.CarState.GearShifter

# Sits above the throttle openpilot's own hold request echoes back through ENGINE_DATA.GAS,
# which ramps in 25.6 steps to at most 205 while GAS_POS shows the pedal untouched. Real driver
# presses in the same logs measured 486..2442. Compared against the raw signal, not ret.gas.
# ponytail: a plain threshold, because this DBC has no trustworthy pedal signal -- GAS_POS sits
# at 2562 whether or not the pedal is down, and the camera's ACC_CMD.GAS_PRESSED bit is set in
# under 1% of frames even under full throttle. Tune here if a light press goes unnoticed.
GAS_PRESSED_THRESHOLD = 300

# Full scale for the 0..1 range cereal wants from ret.gas / ret.brake. Taken from the DBC's
# declared signal maxima; neither has been confirmed against a real pedal sweep, so treat the
# absolute values as indicative. Observed peaks were GAS 2442 and BRAKE_POS 134.
GAS_MAX = 3276.7    # ENGINE_DATA.GAS, 16 bits at 0.1
BRAKE_POS_MAX = 511  # BRAKE_DATA.BRAKE_POS

class CarState(CarStateBase):
  def __init__(self, CP, FPCP):
    super().__init__(CP, FPCP)
    self.frame = 0
    self.angleSensorLast = 0
    self.angleSensor = 0
    self.direction = 1
    can_define = CANDefine(DBC[CP.carFingerprint]["pt"])
    self.params = CarControllerParams(CP)
    self.shifter_values = can_define.dv["ENGINE_DATA"]["GEAR"]
    self.prev_distance_button = 0
    self.distance_button = 0
    self.prev_main_button = 0
    self.lkas_status = 0
    self.main_button = 0
    self.button_states = {button.event_type: False for button in self.params.BUTTONS}
    self.lkas_enabled = False
    self.prev_lkas_enabled = False

    # Detect if servo stop responding to steering command.
    self.eps_torque_timer = 0

  def create_button_events(self, pt_cp, buttons):
    button_events = []

    for button in buttons:
      state = pt_cp.vl[button.can_addr][button.can_msg] in button.values
      if self.button_states[button.event_type] != state:
        event = car.CarState.ButtonEvent.new_message()
        event.type = button.event_type
        event.pressed = state
        button_events.append(event)
      self.button_states[button.event_type] = state

    return button_events

  def update(self, pt_cp, cam_cp, CC, loopback_cp, frogpilot_toggles):
    ret = car.CarState.new_message()
    fp_ret = custom.FrogPilotCarState.new_message()

    ret.buttonEvents = self.create_button_events(pt_cp, self.params.BUTTONS)

    # car speed
    ret.wheelSpeeds = self.get_wheel_speeds(
      pt_cp.vl["WHEEL_SPEED_FRNT"]["WHEEL_SPEED_FR"],
      pt_cp.vl["WHEEL_SPEED_FRNT"]["WHEEL_SPEED_FL"],
      pt_cp.vl["WHEEL_SPEED_REAR"]["WHEEL_SPEED_RR"],
      pt_cp.vl["WHEEL_SPEED_REAR"]["WHEEL_SPEED_RL"],
    )

    ret.vEgoRaw = (ret.wheelSpeeds.fl + ret.wheelSpeeds.fr + ret.wheelSpeeds.rl + ret.wheelSpeeds.rr) / 4.
    ret.vEgo, ret.aEgo = self.update_speed_kf(ret.vEgoRaw)
    ret.vEgoCluster = ret.vEgo
    ret.standstill = ret.vEgoRaw < 1e-3

    self.acc_md = copy.copy(cam_cp.vl["ACC_CMD"])
    self.lkas = copy.copy(pt_cp.vl["LKAS"])
    self.lkas_state = copy.copy(cam_cp.vl["LKAS_STATE"])
    self.setting = copy.copy(cam_cp.vl["SETTING"])
    self.lkas_cmd = copy.copy(cam_cp.vl["LKAS_CAM_CMD_345"])
    self.acc_status = copy.copy(cam_cp.vl["ACC"])

    # gas pedal
    # NB: ENGINE_DATA.GAS is throttle the powertrain is executing, not pedal travel, so this is
    # not the "user pedal only" value cereal asks for. No signal in this DBC is.
    self.gasPos = pt_cp.vl["ENGINE_DATA"]["GAS"]
    ret.gas = self.gasPos / GAS_MAX
    # During an ACC standstill hold that throttle is openpilot's own request echoed back. The
    # old `> 1` fallback read the echo as a driver press: openpilot handed off to overriding,
    # the request stopped, GAS fell to 0, it re-engaged, and the request rose again -- a ~0.4s
    # lurch-and-hold loop.
    ret.gasPressed = (cam_cp.vl["ACC_CMD"]["GAS_PRESSED"]==1) if (cam_cp.vl["ACC"]["ACC_ACTIVE"] != 0) else (self.gasPos > GAS_PRESSED_THRESHOLD)

    # brake pedal
    ret.brake = pt_cp.vl["BRAKE_DATA"]["BRAKE_POS"] / BRAKE_POS_MAX
    ret.brakePressed = pt_cp.vl["ENGINE_DATA"]["BRAKE_PRESS"] != 0

    # gear
    # ret.gearShifter = GearShifter.drive
    gear = self.shifter_values.get(pt_cp.vl["ENGINE_DATA"]["GEAR"])
    ret.gearShifter = self.parse_gear_shifter(gear)
    # button presses
    ret.leftBlinker = pt_cp.vl["BCM_SIGNAL_1"]["SIGN_SIGNAL"] == 2
    ret.rightBlinker = pt_cp.vl["BCM_SIGNAL_1"]["SIGN_SIGNAL"] == 1

    # steering wheel
    self.angleSensor = pt_cp.vl["STEER_ANGLE_SENSOR"]["STEER_ANGLE"]

    # STEER_SENSOR_2.TORQUE_DRIVER is declared signed but only ever reads positive (18k samples,
    # 0.2..184.6), so it is a magnitude. Recover a sign from which way the angle is moving.
    # Only steeringPressed consumes it today, and that takes abs(), so the sign is advisory.
    if (self.frame % 10) == 0:
      self.direction = -1 if self.angleSensor < self.angleSensorLast else 1
      self.angleSensorLast = self.angleSensor

    ret.steeringAngleDeg = self.angleSensor
    ret.steeringTorque = pt_cp.vl["STEER_SENSOR_2"]["TORQUE_DRIVER"] * self.direction
    ret.steeringTorqueEps = pt_cp.vl["STEER_ANGLE_SENSOR"]['TORQUE']
    ret.steeringPressed = abs(ret.steeringTorque) > self.params.STEER_THRESHOLD

    self.prev_distance_button = self.distance_button
    self.distance_button = pt_cp.vl["STEER_BUTTON"]["GAP_ADJUST_UP"]
    self.prev_main_button = self.main_button
    self.main_button = pt_cp.vl["STEER_BUTTON"]["ACC"]
    self.buttons_stock_values = pt_cp.vl["STEER_BUTTON"]
    self.lkas_status = pt_cp.vl["LKAS"]['NEW_SIGNAL_1']

    # cruise state
    ret.cruiseState.available = cam_cp.vl["ACC_CMD"]["ACC_STATE"] != 1 or cam_cp.vl["ACC"]["ACC_ACTIVE"] != 0
    ret.cruiseState.enabled = cam_cp.vl["ACC"]["ACC_ACTIVE"] != 0 or cam_cp.vl["ACC_CMD"]["STOPPED"] == 1

    # The stock ACC drops ACC_ACTIVE ~3s into a standstill hold and then ignores ACC_CMD gas
    # requests until a RES+ press. Report that as cruise standstill so controlsd asks for a
    # resume. It must clear as soon as ACC_ACTIVE returns, otherwise long_control_state_trans
    # keeps starting_condition False and the car stays held after the button lands.
    ret.cruiseState.standstill = cam_cp.vl["ACC"]["ACC_ACTIVE"] == 0 and cam_cp.vl["ACC_CMD"]["STOPPED"] == 1

    # CC_SPEED is kph on the wire; cereal wants m/s
    ret.cruiseState.speed = cam_cp.vl["SETTING"]["CC_SPEED"] * CV.KPH_TO_MS

    # Check if the servo stops responding while the ACC is active. Must come after
    # cruiseState.enabled is assigned above -- reading it earlier always saw the message
    # default of False, which silently disabled this check entirely.
    if ret.cruiseState.enabled and ret.vEgo > self.CP.minSteerSpeed:
      if CC.latActive and pt_cp.vl["LKAS"]['LKAS_CMD'] == -1 and self.lkas_status == 1:
        self.eps_torque_timer += 1
      else:
        self.eps_torque_timer = 0
      ret.steerFaultTemporary = self.eps_torque_timer >= CarControllerParams.STEER_TIMEOUT
    else:
      self.eps_torque_timer = 0

    self.cruise_decreased_previously = self.cruise_decreased
    self.cruise_decreased = pt_cp.vl["STEER_BUTTON"]["RES_MINUS"]
    self.cruise_increased_previously = self.cruise_increased
    self.cruise_increased = pt_cp.vl["STEER_BUTTON"]["RES_PLUS"]

    # FrogPilot CarState functions
    self.lkas_previously_enabled = self.lkas_enabled
    self.lkas_enabled = cam_cp.vl["LKAS_STATE"]["LKA_ACTIVE"] != 0
    self.lkas_active = pt_cp.vl["LKAS"]['LKAS_CMD']

    # blindspot sensors
    if self.CP.enableBsm:
      ret.leftBlindspot = pt_cp.vl["BSM_LEFT"]["BSM_LEFT_DETECT"] != 0
      ret.rightBlindspot = pt_cp.vl["BSM_RIGHT"]["BSM_RIGHT_DETECT"] != 0

    # lock info
    # TODO: neither signal is mapped in this DBC yet, so openpilot cannot warn on an open door
    # or an unbuckled belt
    ret.doorOpen = False
    ret.seatbeltUnlatched = False

    fp_ret.brakeLights = bool(ret.brakePressed)

    self.frame += 1
    return ret, fp_ret

  @staticmethod
  def get_cam_can_parser(CP, FPCP):
    messages = [
      ("ACC_CMD", 50),
      ("ACC", 50),
      ("LKAS_CAM_CMD_345", 50),
      ("LKAS_STATE", 20),
      ("SETTING", 20),
    ]

    return CANParser(DBC[CP.carFingerprint]["pt"], messages, CanBus(CP).camera)

  @staticmethod
  def get_can_parser(CP, FPCP):

    messages = [
       ("STEER_ANGLE_SENSOR", 100),
       ("WHEEL_SPEED_FRNT", 50),
       ("WHEEL_SPEED_REAR", 50),
       ("BCM_SIGNAL_1", 50),
       ("BRAKE_DATA", 50),
       ("LKAS", 100),
       ("ENGINE_DATA", 100),
       ("STEER_SENSOR_2", 59),
       ("STEER_BUTTON", 20),
    ]

    if CP.enableBsm:
      messages += [
        ("BSM_LEFT", 10),
        ("BSM_RIGHT", 10),
      ]

    return CANParser(DBC[CP.carFingerprint]["pt"], messages, CanBus(CP).main)



import copy
from cereal import car
from openpilot.common.conversions import Conversions as CV
from openpilot.common.numpy_fast import clip
from openpilot.common.realtime import DT_CTRL
from openpilot.selfdrive.car import make_can_msg
from openpilot.selfdrive.car.wuling.values import CruiseButtons

VisualAlert = car.CarControl.HUDControl.VisualAlert

def wuling_checksum(dat):
  return sum(dat) & 0xFF

def create_steering_control(packer, apply_steer, frame, steer_req, stock_values=None):
  if stock_values is not None:
    values = {s: stock_values[s] for s in stock_values if s != "CHECKSUM"}
  else:
    values = {}

  values.update({
      "STEER_TORQUE_CMD": -apply_steer,
      "COUNTER": ((frame // 2) + 1) % 0x11,
      "STEER_REQUEST": steer_req,
  })

  dat = packer.make_can_msg("STEERING_LKA", 0, values)[2]
  crc = wuling_checksum(dat[:-1])
  values["CHECKSUM"] = crc

  return packer.make_can_msg("STEERING_LKA", 0, values)

def create_steering_status(packer, apply_steer, frame, steer_step):
  return packer.make_can_msg("ES_LKAS_State", 0, {})


def create_gas_command(packer,throttle, idx, acc_engaged, at_full_stop):
  values = {
    "ENABLE": acc_engaged,
    "COUNTER": idx,
    "COUNTER_2": idx,
    "GAS_CMD": throttle,
    "NEW_SIGNAL_2": 0x04,
    "NEW_SIGNAL_1": 0x0b,
  }

  return packer.make_can_msg("GasCmd", 0, values)

def create_brake_command(packer, apply_brake, idx, acc_engaged, at_full_stop):
  values = {
    "ENABLE": acc_engaged,
    "COUNTER": idx,
    "COUNTER_2": idx,
    "BRAKE_CMD": apply_brake,
    "BRAKE_CMD_2": 27,
    "NEW_SIGNAL_8": 0x50,
    "NEW_SIGNAL_5": 0x15,
    "NEW_SIGNAL_4": 0x01,
    "NEW_SIGNAL_2": 0x06,
    "NEW_SIGNAL_6": 0x01,
    "NEW_SIGNAL_3": 0x35,
  }

  return packer.make_can_msg("BRAKE_MODULE", 0, values)


def create_acc_dashboard_command(packer, acc_engaged, idx, target_speed_kph, resume_button, lead_car_in_sight, fcw):
  # Not a bit shift, dash can round up based on low 4 bits.
  target_speed = int(target_speed_kph) & 0xfff

  values = {
    "ACCAlwaysOne" : 1,
    "COUNTER_1" : idx,
    "COUNTER_2" : (idx+1) % 4,
    "ACCSTATE" : acc_engaged,
    "ACCResumeButton" : resume_button,
    "ACCSpeedSetpoint" : target_speed,
    "ACCGapLevel" : 6 * acc_engaged,  # 3 "far", 0 "inactive"
    "ACCCmdActive" : acc_engaged,
    "ACCAlwaysOne2" : 3,
    "ACCLeadCar" : lead_car_in_sight,
    "SET_ME_X16" : 0x16,
    "FCWAlert": 0x3 if fcw else 0
  }

  return packer.make_can_msg("ASCMActiveCruiseControlStatus", 0, values)

def create_buttons(packer, idx, button):
  resume = 0;
  acc_btn_2 = button;
  if (button == CruiseButtons.RES_ACCEL): 
    resume = 1;
    acc_btn_2 = CruiseButtons.MAIN
  
  values = {
    "RESUME_BTN_2" : resume,
    "ACC_BTN_1" : button,
    "ACC_BTN_2" : acc_btn_2,
    "LKA_BTN" : 0,
    "COUNTER_1" : (idx+1) % 0x4,
    "COUNTER_2" : (idx+1) % 0x4,
  }

  return packer.make_can_msg("STEER_BTN",  2, values)



def create_lkas_hud(packer, bus, lkas_hud_stock_values, lkas_active=0, steer_warning=0):
  commands = []

  values = {s: lkas_hud_stock_values[s] for s in [
    "ALERT",
    "LKA_ACTIVE",
    "LEAD_FOLLOW_1",
    "UNKNOWN_1",
    "UNKNOWN_2",
    "UNKNOWN_3",
    "LEAD_FOLLOW_2",
    "LKAS_STATE",
    "LKA_LINE",
    "LKA_LINE_2",
    "ALERT_DEPART1",
    "STEER_WARNING",
    "HUD_ALERT",
    "COUNTER_1",
    "COUNTER_2",
    "NEW_SIGNAL_1",
    "NEW_SIGNAL_2",
    "NEW_SIGNAL_3",
    "NEW_SIGNAL_4",
    "NEW_SIGNAL_6",
    "NEW_SIGNAL_7",
    "NEW_SIGNAL_8"
  ]}

  # --- Referensi kombinasi signal ---
  # Stock values (dari can_printer bus 2, 0x373):
  #   LKA_ACTIVE=1, LKAS_STATE=0, LKA_LINE=0, STEER_WARNING=1, NEW_SIGNAL_1=1
  #   Byte 4-6: ac 90 02 (counter/checksum)

  # Kombinasi 1: minimal - ERROR, trigger warning kuning
  # if lkas_active:
  #   values.update({
  #     "LKA_ACTIVE": 1,
  #     "STEER_WARNING": 1,
  #     "LKA_LINE_2": 0,
  #   })

  # Kombinasi 2: dengan state - ERROR, trigger warning kuning
  # if lkas_active:
  #   values.update({
  #     "LKA_ACTIVE": 1,
  #     "LKAS_STATE": 1,
  #     "LKA_LINE": 3,
  #   })

  # Kombinasi 3: full indicator (pernah jalan?)
  # if lkas_active:
  #   values.update({
  #     "LKA_ACTIVE": 1,
  #     "LKAS_STATE": 1,
  #     "LEAD_FOLLOW_1": 1,
  #     "LEAD_FOLLOW_2": 1,
  #     "HUD_ALERT": 1,
  #     "LKA_LINE": 3,
  #     "STEER_WARNING": 2,
  #     "LKA_LINE_2": 0,
  #     "NEW_SIGNAL_1": 1,
  #   })

  # Kombinasi 4: full + higher warning (pernah jalan?)
  # if lkas_active:
  #   values.update({
  #     "LKA_ACTIVE": 1,
  #     "LKAS_STATE": 1,
  #     "LEAD_FOLLOW_1": 1,
  #     "LEAD_FOLLOW_2": 1,
  #     "HUD_ALERT": 2,
  #     "STEER_WARNING": 3,
  #     "LKA_LINE_2": 1,
  #   })

  # Kombinasi 5: based on stock decode - ERROR
  # if lkas_active:
  #   values.update({
  #     "STEER_WARNING": 2,
  #     "LKA_LINE_2": 1,
  #   })

  # Kombinasi 3: full indicator - ERROR
  # if lkas_active:
  #   values.update({
  #     "LKA_ACTIVE": 1,
  #     "LKAS_STATE": 1,
  #     "LEAD_FOLLOW_1": 1,
  #     "LEAD_FOLLOW_2": 1,
  #     "HUD_ALERT": 1,
  #     "LKA_LINE": 3,
  #     "STEER_WARNING": 2,
  #     "LKA_LINE_2": 0,
  #     "NEW_SIGNAL_1": 1,
  #   })

  # Steer warning alert options:
  if steer_warning:
    values.update({
      "STEER_WARNING": 3,
    })

  # Alternative steer warning:
  # if steer_warning:
  #   values.update({
  #     "ALERT": 1,
  #     "STEER_WARNING": 3,
  #   })

  # if steer_warning:
  #   values.update({
  #     "ALERT": 1,
  #     "STEER_WARNING": 1,
  #   })

  commands.append(packer.make_can_msg("LkasHud", bus, values))

  return commands

def create_acc_hud_control(packer, bus, acc_hud_stock, enabled, target_speed_kph, lead_distance, gac_tr_cluster):
  target_speed = min(target_speed_kph, 255)
  # target_speed=30
  values = {s: acc_hud_stock[s] for s in [
      "ACCGapLevel",
      "ACCAlwaysOne2",
      "ACCAlwaysOne",
      "ACCSpeedSetpoint",
      "ACCCmdActive",
      "ACCResumeAlert",
      "ACCResumeButton",
      "ACCBUTTON",
      "NEW_SIGNAL_1",
      "NEW_SIGNAL_2",
      "NEW_SIGNAL_3",
      "NEW_SIGNAL_4",
      "FCWAlert",
      "GAPDisplay",
      "FCW",
      "ACCSTATE",
      "ACCSTATE2",
      "SET_ME_X16",
      "COUNTER_1",
      "COUNTER_2",
    ]}
  my_array = [30, 31, 35, 38, 40, 44, 45, 50, 55, 60, 65, 70, 75, 80]
  my_array2 = [4, 5, -7, 7, -2, -3, 3, -8, -3, 2, 7, -4, 1, 6]
 
  # try:
  #   index_of_value = my_array.index(target_speed)
  #   me_x_16 = my_array2[index_of_value]
  #   if enabled:
  #     values["ACCSpeedSetpoint"] = target_speed
  #     values["SET_ME_X16"] = me_x_16
  # except ValueError:
  #   pass

    # print(f"{value_to_find} not found in the list.")
  # if target_speed == 60 and enabled:
  #   values["ACCSpeedSetpoint"] = 80
  #   values["SET_ME_X16"]  = 6
  #   values["NEW_SIGNAL_4"]  = 1
    
  # values["ACCGapLevel"] = gac_tr_cluster * enabled
  # if enabled:
  #   values["ACCSTATE"]  = 1
  #   values["ACCBUTTON"]  = 0
  #   values["ACCLeadCar"]  = 1
  #   values["SET_ME_X16"]  = 11
  #   values["NEW_SIGNAL_1"]  = 3

  # print(values)

  return packer.make_can_msg("ASCMActiveCruiseControlStatus", bus, values)


def create_radar_command(packer, cmd_stock, apply_gas, frame, CC, CS, stopping=False, at_full_stop=False, near_stop=False):
  ret = []

  values = {s: cmd_stock[s] for s in [
      "GAS_CMD",
      "COUNTER",
      "STOP_REQUEST",
      "NEW_SIGNAL_4",
      "ACC_STATE",
      "NEW_SIGNAL_9",
      "NEW_SIGNAL_5",
      "NEW_SIGNAL_11",
      "NEW_SIGNAL_1",
      "STOPPING_T1",
      "FULL_STOP",
      "NEW_SIGNAL_2",
      "FULL_STOP_INV",
      "NEW_SIGNAL_3",
      "COUNTER_2",
    ]}

  if CC.longActive:
    values["GAS_CMD"] = apply_gas
    if at_full_stop:
      values["FULL_STOP"] = 1
      values["FULL_STOP_INV"] = 0
      values["STOP_REQUEST"] = 1
      values["GAS_CMD"] = 0
    elif near_stop:
      values["STOPPING_T1"] = 1
      values["STOP_REQUEST"] = 1
      values["GAS_CMD"] = 0
    else:
      values["FULL_STOP"] = 0
      values["FULL_STOP_INV"] = 1
      values["STOP_REQUEST"] = 0
      values["STOPPING_T1"] = 0

  ret.append(packer.make_can_msg("GasCmd", 0, values))

  return ret

def create_adas_time_status(bus, tt, idx):
  dat = [(tt >> 20) & 0xff, (tt >> 12) & 0xff, (tt >> 4) & 0xff,
    ((tt & 0xf) << 4) + (idx << 2)]
  chksum = 0x1000 - dat[0] - dat[1] - dat[2] - dat[3]
  chksum = chksum & 0xfff
  dat += [0x40 + (chksum >> 8), chksum & 0xff, 0x12]
  return make_can_msg(0xa1, bytes(dat), bus)

def create_adas_steering_status(bus, idx):
  dat = [idx << 6, 0xf0, 0x20, 0, 0, 0]
  chksum = 0x60 + sum(dat)
  dat += [chksum >> 8, chksum & 0xff]
  return make_can_msg(0x306, bytes(dat), bus)

def create_adas_accelerometer_speed_status(bus, speed_ms, idx):
  spd = int(speed_ms * 16) & 0xfff
  accel = 0 & 0xfff
  # 0 if in park/neutral, 0x10 if in reverse, 0x08 for D/L
  #stick = 0x08
  near_range_cutoff = 0x27
  near_range_mode = 1 if spd <= near_range_cutoff else 0
  far_range_mode = 1 - near_range_mode
  dat = [0x08, spd >> 4, ((spd & 0xf) << 4) | (accel >> 8), accel & 0xff, 0]
  chksum = 0x62 + far_range_mode + (idx << 2) + dat[0] + dat[1] + dat[2] + dat[3] + dat[4]
  dat += [(idx << 5) + (far_range_mode << 4) + (near_range_mode << 3) + (chksum >> 8), chksum & 0xff]
  return make_can_msg(0x308, bytes(dat), bus)

def create_adas_headlights_status(packer, bus):
  values = {
    "Always42": 0x42,
    "Always4": 0x4,
  }
  return packer.make_can_msg("ASCMHeadlight", bus, values)

def create_lka_icon_command(bus, active, critical, steer):
  dat = b"\xc6\x3d\x01\x00\xac\x90\x02\x42"
  return make_can_msg(0x104c006c, dat, bus)

def create_resume_button(bus, active, critical, steer):
  # dat = b"\x48\x08\x00\x00\x00\x00\x00\x50"
  dat = b"\x80\x20\x00\x00\x00\x00\x00\xa0"
  return make_can_msg(0x1e1, dat, bus)


def create_wuling_cc_spam_command(packer, controller, CS, actuators):
  _CV = CV.MS_TO_KPH
  # Interval pengiriman pesan tombol (detik). Semakin kecil = semakin responsif.
  SEND_INTERVAL = 0.04  # ~25Hz
  # Interval auto-resume saat standstill (lebih lambat agar tidak terlalu agresif)
  RESUME_INTERVAL = 0.2  # ~5Hz

  target_speed_kph = int(round(CS.out.vEgo * _CV + actuators.accel * _CV))
  current_set_speed = int(round(CS.out.cruiseState.speed * _CV))

  cruiseBtn = CruiseButtons.INIT
  interval = SEND_INTERVAL

  # Auto-resume: saat mobil berhenti (standstill) dan planner mau jalan
  if CS.out.standstill and actuators.accel > 0:
    cruiseBtn = CruiseButtons.RES_ACCEL
    controller.apply_speed = current_set_speed
    interval = RESUME_INTERVAL
  elif current_set_speed <= 0 and actuators.accel < -1:
    cruiseBtn = CruiseButtons.CANCEL
    controller.apply_speed = 0
  elif target_speed_kph < current_set_speed:
    # Target lebih rendah dari set point -> tahan tombol DECEL
    cruiseBtn = CruiseButtons.DECEL_SET
    controller.apply_speed = target_speed_kph
  elif target_speed_kph > current_set_speed:
    # Target lebih tinggi dari set point -> tahan tombol RES/ACCEL
    cruiseBtn = CruiseButtons.RES_ACCEL
    controller.apply_speed = target_speed_kph
  else:
    # Sudah sesuai, tidak perlu tekan tombol
    controller.apply_speed = current_set_speed

  # Kirim pesan tombol secara kontinu (long press) selama perlu mengubah kecepatan
  if (cruiseBtn != CruiseButtons.INIT) and ((controller.frame - controller.last_button_frame) * DT_CTRL >= interval):
    controller.last_button_frame = controller.frame
    idx = int(CS.buttons_counter + 1) % 4
    return [create_buttons(packer, idx, cruiseBtn)]
  else:
    return []


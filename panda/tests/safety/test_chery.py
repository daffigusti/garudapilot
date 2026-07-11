#!/usr/bin/env python3
import unittest
from panda import Panda
from panda.tests.libpanda import libpanda_py
import panda.tests.safety.common as common
from panda.tests.safety.common import CANPackerPanda

# Chery steers by ANGLE. Safety works in decidegrees (deg * 10) to match the
# LKAS CMD encoding used by the car port (cherycan.py): CMD = deg*10 - 392.
MSG_LKAS_CMD = 0x345           # LKAS_CAM_CMD_345 (TX, angle command)
MSG_LKAS_HUD = 0x307           # LkasHud (TX)
MSG_HUD_ALERT = 0x3FC          # Hud alert (TX)
MSG_ACC_SETTING = 0x387        # Acc setting (TX)
MSG_STEER_BUTTON = 0x360       # STEER_BUTTON (TX)
MSG_ACC_CMD = 0x3A2            # ACC_CMD (long TX + RX gas)
MSG_ACC = 0x3A5               # ACC (RX cruise engaged)
MSG_ENGINE = 0x3E             # ENGINE_DATA (RX brake)
MSG_WHEEL = 0x316             # WHEEL_SPEED_FRNT (RX speed)
MSG_STEER_ANGLE = 0x1D3        # STEER_ANGLE_SENSOR (RX angle)


class TestCherySafety(common.PandaCarSafetyTest, common.AngleSteeringSafetyTest):

  TX_MSGS = [[MSG_LKAS_CMD, 0], [MSG_LKAS_HUD, 0], [MSG_HUD_ALERT, 0],
             [MSG_ACC_SETTING, 0], [MSG_STEER_BUTTON, 0], [MSG_STEER_BUTTON, 2]]
  STANDSTILL_THRESHOLD = 0
  GAS_PRESSED_THRESHOLD = 0
  RELAY_MALFUNCTION_ADDRS = {0: (MSG_LKAS_CMD,)}
  FWD_BLACKLISTED_ADDRS = {2: [MSG_LKAS_CMD, MSG_LKAS_HUD]}
  FWD_BUS_LOOKUP = {0: 2, 2: 0}

  # Angle control limits (decidegrees on CAN => DEG_TO_CAN = 10)
  DEG_TO_CAN = 10
  ANGLE_RATE_BP = [0., 5., 25.]
  ANGLE_RATE_UP = [.8, .8, .2]   # windup limit
  ANGLE_RATE_DOWN = [.9, .9, .4]  # unwind limit

  def setUp(self):
    self.packer = CANPackerPanda("chery_canfd")
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_CHERY, 0)
    self.safety.init_tests()

  def _angle_cmd_msg(self, angle: float, enabled: bool):
    # decode in safety is: desired = to_signed(CMD, 13) + 392  (decidegrees)
    # so encode CMD = angle*DEG_TO_CAN - 392
    values = {"CMD": round(angle * self.DEG_TO_CAN) - 392, "LKA_ACTIVE": 1 if enabled else 0}
    return self.packer.make_can_msg_panda("LKAS_CAM_CMD_345", 0, values)

  def _angle_meas_msg(self, angle: float):
    # STEER_ANGLE scale 0.1, offset -780 -> DBC packer inverts to raw; safety
    # recovers decidegrees = raw - 7800 = angle*10
    values = {"STEER_ANGLE": angle}
    return self.packer.make_can_msg_panda("STEER_ANGLE_SENSOR", 0, values)

  def _pcm_status_msg(self, enable):
    values = {"ACC_ACTIVE": 1 if enable else 0}
    return self.packer.make_can_msg_panda("ACC", 2, values)

  def _speed_msg(self, speed):
    # m/s -> kph for the DBC signals (scale handled by packer)
    values = {"WHEEL_SPEED_FR": speed * 3.6, "WHEEL_SPEED_FL": speed * 3.6}
    return self.packer.make_can_msg_panda("WHEEL_SPEED_FRNT", 0, values)

  def _user_brake_msg(self, brake):
    values = {"BRAKE_PRESS": 1 if brake else 0}
    return self.packer.make_can_msg_panda("ENGINE_DATA", 0, values)

  def _user_gas_msg(self, gas):
    values = {"GAS_PRESSED": 1 if gas else 0}
    return self.packer.make_can_msg_panda("ACC_CMD", 2, values)


class TestCheryLongSafety(TestCherySafety):
  """Longitudinal: ACC_CMD gas command is additionally allowed and checked."""

  TX_MSGS = TestCherySafety.TX_MSGS + [[MSG_ACC_CMD, 0]]
  FWD_BLACKLISTED_ADDRS = {2: [MSG_LKAS_CMD, MSG_LKAS_HUD, MSG_ACC_CMD]}

  MAX_GAS = 511
  MIN_GAS = -511
  INACTIVE_GAS = -24

  def setUp(self):
    self.packer = CANPackerPanda("chery_canfd")
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_CHERY, Panda.FLAG_CHERY_LONG_CONTROL)
    self.safety.init_tests()

  def _long_gas_cmd_msg(self, gas: int):
    return self.packer.make_can_msg_panda("ACC_CMD", 0, {"CMD": gas})

  def test_gas_safety_check(self):
    for controls_allowed in (True, False):
      for gas in range(self.MIN_GAS - 20, self.MAX_GAS + 20):
        self.safety.set_controls_allowed(controls_allowed)
        should_tx = (controls_allowed and self.MIN_GAS <= gas <= self.MAX_GAS) or (gas == self.INACTIVE_GAS)
        self.assertEqual(should_tx, self._tx(self._long_gas_cmd_msg(gas)), (controls_allowed, gas))


if __name__ == "__main__":
  unittest.main()

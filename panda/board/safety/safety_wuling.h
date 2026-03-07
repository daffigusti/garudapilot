// CAN msgs we care about
#define WULING_WHEEL_SPEED     0x348  // 840 EBCMWheelSpdFront
#define WULING_STEERING_ANGLE  0x1E5  // 485 PSCMSteeringAngle
#define WULING_ENGINE_DATA     0x0C9  // 201 ECMEngineStatus
#define WULING_GAS_PEDAL       0x191  // 401 GAS_PEDAL
#define WULING_ACC_STATUS      0x263  // 611 AccStatus
#define WULING_STEERING_LKA    0x225  // 549 STEERING_LKA (TX)
#define WULING_LKAS_HUD        0x373  // 883 LkasHud (TX)
#define WULING_CRZ_BTN         0x1E1  // 481 STEER_BTN (TX)
#define WULING_CRZ_CTRL        0x370  // 880 ASCMActiveCruiseControlStatus (TX)
#define WULING_ACC_CMD         0x260  // 608 GasCmd (TX)
#define WULING_ACC_STS         0x263  // 611 AccStatus (TX)

// CAN bus numbers
#define WULING_BUS_MAIN   0
#define WULING_BUS_RADAR  1
#define WULING_BUS_CAM    2

// Cruise button values from ACC_BTN_1 field in STEER_BTN message
#define WULING_BTN_UNPRESS    0
#define WULING_BTN_RES_ACCEL  8
#define WULING_BTN_CANCEL     32

const SteeringLimits WULING_STEERING_LIMITS = {
  .max_steer = 200,
  .max_rate_up = 3,
  .max_rate_down = 2,
  .driver_torque_allowance = 35,
  .driver_torque_factor = 2,
  .max_rt_delta = 128,
  .max_rt_interval = 250000,
  .type = TorqueDriverLimited,
};

const CanMsg WULING_TX_MSGS[] = {
  {WULING_STEERING_LKA, 0, 8},
  {WULING_CRZ_BTN, 0, 8},
  {WULING_CRZ_BTN, 2, 8},
  {WULING_LKAS_HUD, 0, 8},
  {WULING_CRZ_CTRL, 0, 8},
  {WULING_CRZ_CTRL, 2, 8},
  {WULING_ACC_STS, 0, 8},
  {WULING_ACC_CMD, 0, 8},
};

RxCheck wuling_rx_checks[] = {
  {.msg = {{WULING_CRZ_BTN, 0, 8, .frequency = 50U}, {0}, {0}}},
  {.msg = {{WULING_ENGINE_DATA, 0, 8, .frequency = 10U}, {0}, {0}}},
  {.msg = {{WULING_GAS_PEDAL, 0, 8, .frequency = 10U}, {0}, {0}}},
  {.msg = {{WULING_WHEEL_SPEED, 0, 6, .frequency = 20U}, {0}, {0}}},
  {.msg = {{WULING_STEERING_ANGLE, 0, 8, .frequency = 100U}, {0}, {0}}},
  {.msg = {{WULING_ACC_STATUS, 0, 8, .frequency = 20U}, {0}, {0}}},
};

static void wuling_rx_hook(const CANPacket_t *to_push) {
  if (((int)GET_BUS(to_push) == WULING_BUS_MAIN)) {
    int addr = GET_ADDR(to_push);

    // Speed from EBCMWheelSpdFront
    // FLWheelSpd: start_bit 6, 15 bits, big-endian, unsigned, scale 0.0311 kph
    if (addr == WULING_WHEEL_SPEED) {
      int speed = ((GET_BYTE(to_push, 0) & 0x7FU) << 8) | GET_BYTE(to_push, 1);
      vehicle_moving = speed > 10;  // > 0.311 kph
    }

    // Driver torque from PSCMSteeringAngle
    // SteeringTorque: start_bit 55, 8 bits, big-endian, signed, factor -1
    if (addr == WULING_STEERING_ANGLE) {
      int torque_driver_new = to_signed(GET_BYTE(to_push, 6), 8);
      torque_driver_new = -torque_driver_new;  // DBC factor is -1
      update_sample(&torque_driver, torque_driver_new);
    }

    // Brake pressed from ECMEngineStatus
    // Brake_Pressed: bit 40
    if (addr == WULING_ENGINE_DATA) {
      brake_pressed = GET_BIT(to_push, 40U) != 0U;
    }

    // Gas pressed from GAS_PEDAL
    // GAS_POS: start_bit 55, 8 bits, big-endian, unsigned
    if (addr == WULING_GAS_PEDAL) {
      gas_pressed = GET_BYTE(to_push, 6) != 0U;
    }

    // Cruise engagement from AccStatus
    // CruiseState: bit 21 (byte 2 bit 5)
    if (addr == WULING_ACC_STATUS) {
      bool cruise_engaged = GET_BIT(to_push, 21U) != 0U;
      pcm_cruise_check(cruise_engaged);
    }

    generic_rx_checks((addr == WULING_STEERING_LKA));
  }
}

static bool wuling_tx_hook(const CANPacket_t *to_send) {
  bool tx = true;
  int addr = GET_ADDR(to_send);

  // Steer torque command checks
  // STEER_TORQUE_CMD: start_bit 2, 11 bits, big-endian, signed
  // STEER_REQUEST: bit 5
  if (addr == WULING_STEERING_LKA) {
    int desired_torque = ((GET_BYTE(to_send, 0) & 0x7U) << 8) + GET_BYTE(to_send, 1);
    desired_torque = to_signed(desired_torque, 11);

    bool steer_req = GET_BIT(to_send, 5U) != 0U;

    if (steer_torque_cmd_checks(desired_torque, steer_req, WULING_STEERING_LIMITS)) {
      tx = false;
    }
  }

  // Cruise button checks
  // ACC_BTN_1: start_bit 0, 6 bits, little-endian
  if (addr == WULING_CRZ_BTN) {
    int button = GET_BYTE(to_send, 0) & 0x3FU;

    // Unpress is always allowed
    bool allowed = (button == WULING_BTN_UNPRESS);
    // Resume allowed when cruise was previously engaged (for standstill resume)
    allowed |= (button == WULING_BTN_RES_ACCEL) && cruise_engaged_prev;
    // Cancel allowed when cruise was previously engaged
    allowed |= (button == WULING_BTN_CANCEL) && cruise_engaged_prev;

    if (!allowed) {
      tx = false;
    }
  }

  return tx;
}

static int wuling_fwd_hook(int bus, int addr) {
  int bus_fwd = -1;

  if (bus == WULING_BUS_MAIN) {
    bus_fwd = WULING_BUS_CAM;
  } else if (bus == WULING_BUS_CAM) {
    // Block messages that openpilot replaces
    bool is_steer_msg = (addr == WULING_STEERING_LKA);
    bool is_lkas_hud_msg = (addr == WULING_LKAS_HUD);
    bool is_cruise_ctrl_msg = (addr == WULING_CRZ_CTRL);
    bool is_acc_cmd_msg = (addr == WULING_ACC_CMD);
    bool block = is_steer_msg || is_lkas_hud_msg || is_cruise_ctrl_msg || is_acc_cmd_msg;
    if (!block) {
      bus_fwd = WULING_BUS_MAIN;
    }
  }

  return bus_fwd;
}

static safety_config wuling_init(uint16_t param) {
  UNUSED(param);
  return BUILD_SAFETY_CFG(wuling_rx_checks, WULING_TX_MSGS);
}

const safety_hooks wuling_hooks = {
  .init = wuling_init,
  .rx = wuling_rx_hook,
  .tx = wuling_tx_hook,
  .fwd = wuling_fwd_hook,
};

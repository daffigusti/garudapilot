// CAN msgs we care about
#define CHERY_ACC_CMD 0x3A2
#define CHERY_ACC_STATUS 0x3A5
#define CHERY_LKAS_HUD 0x307
#define CHERY_LKAS_CMD 0x345
#define CHERY_ACC_SETTING 0x387
#define CHERY_HUD_ALERT 0x3FC

#define CHERY_ENGINE 0x3E
#define CHERY_BRAKE 0x29A
#define CHERY_BRAKE_SENSOR 0x4ED
#define CHERY_WHEEL_SENSOR 0x316 // RX for vehicle speed
#define CHERY_ACC_DATA 0x3A5
#define CHERY_STEER_BUTTON 0x360

// CAN bus numbers
#define CHERY_MAIN 0U
#define CHERY_AUX 1U
#define CHERY_CAM 2U

static bool lkas_msg_check(int addr)
{
  return (addr == CHERY_LKAS_CMD) || (addr == CHERY_LKAS_HUD);
}

const uint16_t CHERY_PARAM_LONGITUDINAL = 1;

bool chery_longitudinal = false;

const SteeringLimits CHERY_STEERING_LIMITS = {
    .max_steer = 800,
    .max_rate_up = 10,
    .max_rate_down = 25,
    .max_rt_delta = 300,
    .max_rt_interval = 250000,
    .driver_torque_factor = 1,
    .driver_torque_allowance = 15,
    .type = TorqueDriverLimited,
};

const CanMsg CHERY_TX_MSGS[] = {
    {CHERY_LKAS_CMD, 0, 8},
    {CHERY_LKAS_HUD, 0, 8},
    {CHERY_HUD_ALERT, 0, 8},
    {CHERY_ACC_SETTING, 0, 8},
    {CHERY_STEER_BUTTON, 0, 6},
    {CHERY_STEER_BUTTON, 2, 6},
};

const CanMsg CHERY_LONG_TX_MSGS[] = {
    {CHERY_ACC_CMD, 0, 8},
    {CHERY_LKAS_CMD, 0, 8},
    {CHERY_LKAS_HUD, 0, 8},
    {CHERY_HUD_ALERT, 0, 8},
    {CHERY_ACC_SETTING, 0, 8},
    {CHERY_STEER_BUTTON, 0, 6},
    {CHERY_STEER_BUTTON, 2, 6},
};

RxCheck chery_rx_checks[] = {
    {.msg = {{CHERY_WHEEL_SENSOR, CHERY_MAIN, 8, .frequency = 50U}, {0}, {0}}},
    {.msg = {{CHERY_ENGINE, CHERY_MAIN, 48, .frequency = 100U}, {0}, {0}}},
    {.msg = {{CHERY_BRAKE, CHERY_MAIN, 8, .frequency = 50U}, {0}, {0}}},
    {.msg = {{CHERY_BRAKE_SENSOR, CHERY_MAIN, 8, .frequency = 10U}, {0}, {0}}},
};

// track msgs coming from OP so that we know what CAM msgs to drop and what to forward
static void chery_rx_hook(const CANPacket_t *to_push)
{
  const int bus = GET_BUS(to_push);
  const int addr = GET_ADDR(to_push);

  if (bus == CHERY_MAIN)
  {

    if (addr == CHERY_WHEEL_SENSOR)
    {
      // Get current speed and standstill
      uint16_t right_rear = (GET_BYTE(to_push, 0) << 8) | (GET_BYTE(to_push, 1));
      uint16_t left_rear = (GET_BYTE(to_push, 2) << 8) | (GET_BYTE(to_push, 3));
      vehicle_moving = (right_rear | left_rear) != 0U;
      UPDATE_VEHICLE_SPEED((right_rear + left_rear) / 2.0 * 0.00828 / 3.6);
    }

    // if (addr == CHERY_STEER_TORQUE) {
    //   int torque_driver_new = GET_BYTE(to_push, 0) - 127U;
    //   // update array of samples
    //   update_sample(&torque_driver, torque_driver_new);
    // }

    // // enter controls on rising edge of ACC, exit controls on ACC off
    // if (addr == CHERY_CRZ_CTRL) {
    //   acc_main_on = GET_BIT(to_push, 17U);
    //   bool cruise_engaged = GET_BYTE(to_push, 0) & 0x8U;
    //   pcm_cruise_check(cruise_engaged);
    // }

    // if (addr == CHERY_ENGINE_DATA) {
    //   gas_pressed = (GET_BYTE(to_push, 4) || (GET_BYTE(to_push, 5) & 0xF0U));
    // }

    if (addr == CHERY_ENGINE)
    {
      brake_pressed = ((GET_BYTES(to_push, 0, 27) >> 4) & 0x01) != 0U;
    }
  }
  else if (bus == CHERY_CAM)
  {
    if (addr == CHERY_ACC_CMD)
    {
      acc_main_on = ((GET_BYTE(to_push, 1) & 0x03) != 1U);
      // bool stand_still = (GET_BYTE(to_push, 1) >> 2) & 0x01;

      gas_pressed = (GET_BYTE(to_push, 5) & 0x80U) != 0U;
    }
    if (addr == CHERY_ACC_DATA)
    {
      // Signal: ACCStatus
      bool cruise_engaged = GET_BIT(to_push, 20U);
      pcm_cruise_check(cruise_engaged);
    }
  }
  generic_rx_checks((addr == CHERY_LKAS_CMD) && (bus == CHERY_MAIN));
  controls_allowed = true;
}

static bool chery_tx_hook(const CANPacket_t *to_send)
{
  bool tx = true;
  int addr = GET_ADDR(to_send);
  // int bus = GET_BUS(to_send);

  // Check if msg is sent on the main BUS

  if (addr == CHERY_LKAS_CMD)
  {
    // tx = false;
  }

  return tx;
}

static int chery_fwd_hook(int bus, int addr)
{
  int bus_fwd = -1;

  if (bus == CHERY_MAIN)
  {
    bool block = (addr == 0x1110);
    if (!block)
    {
      bus_fwd = CHERY_CAM;
    }
  }
  else if (bus == CHERY_CAM)
  {

    // bool block = (addr == CHERY_LKAS) || (addr == CHERY_ACC) || (addr == CHERY_LKAS_HUD) || (addr == CHERY_LKAS_CMD) || (addr == 0x387) || (addr == 0x3fc) || (addr == CHERY_ACC_DATA);
    // bool block = (addr == CHERY_LKAS) || (addr == CHERY_ACC) || (addr == CHERY_LKAS_HUD) || (addr == CHERY_LKAS_HUD) || (addr == 0x345);
    // bool block = (addr == CHERY_LKAS) || (addr == CHERY_ACC) || (addr == CHERY_LKAS_HUD) || (addr == CHERY_LKAS_HUD) || (addr == 0x345) || (addr == 0x3dc) || (addr == 0x3de) || (addr == 0x3ed) || (addr == 0x3fa) || (addr == 0x4dd);
    // bool block = (addr == CHERY_LKAS);
    // --|| (addr != CHERY_ACC) || (addr != CHERY_LKAS_HUD) || (addr != 0x387) || (addr != CHERY_ACC_DATA);
    if (lkas_msg_check(addr) || (chery_longitudinal && (addr == CHERY_ACC_CMD)))
    {
      bus_fwd = -1;
      // print("  Address: 0x");
      // puth(addr);
      // print("\n");
    }
    else
    {
      bus_fwd = CHERY_MAIN;
    }
  }
  else
  {
    // don't fwd
  }

  return bus_fwd;
}

static safety_config chery_init(uint16_t param)
{
#ifdef ALLOW_DEBUG
  chery_longitudinal = GET_FLAG(param, CHERY_PARAM_LONGITUDINAL);
#endif
  safety_config ret;
  ret = chery_longitudinal ? BUILD_SAFETY_CFG(chery_rx_checks, CHERY_LONG_TX_MSGS) : BUILD_SAFETY_CFG(chery_rx_checks, CHERY_TX_MSGS);
  return ret;
}

const safety_hooks chery_hooks = {
    .init = chery_init,
    .rx = chery_rx_hook,
    .tx = chery_tx_hook,
    .fwd = chery_fwd_hook,
};

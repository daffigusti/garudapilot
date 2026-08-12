// CAN msgs we care about
#define CHERY_ACC_CMD 0x3A2
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
#define CHERY_STEER_ANGLE_SENSOR 0x1D3 // RX steering wheel angle (STEER_ANGLE_SENSOR)

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

// ACC_CMD.STOPPED: set by the stock ACC while holding the car at standstill.
// ACC.ACC_ACTIVE drops to 0 in that state, so it is tracked to keep controls
// allowed through a stop (see chery_rx_hook).
bool chery_acc_stopped = false;

// Chery steers by ANGLE (carcontroller uses apply_std_steer_angle_limits).
// Units are decidegrees (deg * 10) to match the LKAS CMD encoding: cmd = deg*10 - 392.
// angle_deg_to_can = 10 (decidegrees per degree).
// NOTE: rate lookups are set liberally above openpilot's and MUST be validated on-vehicle.
const SteeringLimits CHERY_STEERING_LIMITS = {
    .angle_deg_to_can = 10,
    .angle_rate_up_lookup = {
        {0., 5., 25.},
        {.8, .8, .2},
    },
    .angle_rate_down_lookup = {
        {0., 5., 25.},
        {.9, .9, .4},
    },
};

const LongitudinalLimits CHERY_LONG_LIMITS = {
    .max_gas = 511,
    .min_gas = -511,
    .inactive_gas = -24,
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
    {.msg = {{CHERY_STEER_ANGLE_SENSOR, CHERY_MAIN, 8, .frequency = 100U}, {0}, {0}}},
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

    if (addr == CHERY_ENGINE)
    {
      // ENGINE_DATA.BRAKE_PRESS = bit 220 (chery_canfd.dbc)
      brake_pressed = GET_BIT(to_push, 220U) != 0U;
    }

    if (addr == CHERY_STEER_ANGLE_SENSOR)
    {
      // STEER_ANGLE: 7|14@0+ (0.1, -780), big-endian 14-bit unsigned
      // raw = byte0 << 6 | byte1 >> 2 ; degrees = raw*0.1 - 780
      // store in decidegrees to match LKAS CMD units: deg*10 = raw - 7800
      int angle_meas_new = ((GET_BYTE(to_push, 0) << 6) | (GET_BYTE(to_push, 1) >> 2)) - 7800;
      update_sample(&angle_meas, angle_meas_new);
    }
  }
  else if (bus == CHERY_CAM)
  {
    if (addr == CHERY_ACC_CMD)
    {
      acc_main_on = ((GET_BYTE(to_push, 1) & 0x03) != 1U);

      // STOPPED: 10|1@0+
      chery_acc_stopped = GET_BIT(to_push, 10U) != 0U;

      gas_pressed = (GET_BYTE(to_push, 5) & 0x80U) != 0U;
    }
    if (addr == CHERY_ACC_DATA)
    {
      // Signal: ACC_ACTIVE. It drops to 0 while the stock ACC holds the car at
      // standstill, so STOPPED keeps an existing engagement alive. Requiring
      // cruise_engaged_prev means STOPPED can never engage controls on its own.
      bool cruise_engaged = (GET_BIT(to_push, 20U) != 0U) || (chery_acc_stopped && cruise_engaged_prev);
      pcm_cruise_check(cruise_engaged);
    }
  }
  generic_rx_checks((addr == CHERY_LKAS_CMD) && (bus == CHERY_MAIN));
}

static bool chery_tx_hook(const CANPacket_t *to_send)
{
  bool tx = true;
  int addr = GET_ADDR(to_send);

  // Steering angle command check
  if (addr == CHERY_LKAS_CMD)
  {
    // CMD: 6|13@0- (signed, big-endian). Packer encodes cmd = deg*10 - 392,
    // so desired angle in decidegrees = to_signed(cmd, 13) + 392.
    int cmd = ((GET_BYTE(to_send, 0) & 0x7F) << 6) | (GET_BYTE(to_send, 1) >> 2);
    int desired_angle = to_signed(cmd, 13) + 392;

    // LKA_ACTIVE: bit 9
    bool steer_control_enabled = GET_BIT(to_send, 9U) != 0U;

    if (steer_angle_cmd_checks(desired_angle, steer_control_enabled, CHERY_STEERING_LIMITS))
    {
      tx = false;
    }
  }

  // Longitudinal gas command check (only reachable when chery_longitudinal)
  if (addr == CHERY_ACC_CMD)
  {
    // CMD: 6|10@0- (signed, big-endian)
    int desired_gas = ((GET_BYTE(to_send, 0) & 0x7F) << 3) | (GET_BYTE(to_send, 1) >> 5);
    desired_gas = to_signed(desired_gas, 10);

    if (longitudinal_gas_checks(desired_gas, CHERY_LONG_LIMITS))
    {
      tx = false;
    }
  }

  return tx;
}

static int chery_fwd_hook(int bus, int addr)
{
  int bus_fwd = -1;

  if (bus == CHERY_MAIN)
  {
    // forward everything from the car to the camera
    bus_fwd = CHERY_CAM;
  }
  else if (bus == CHERY_CAM)
  {
    // block OP-controlled msgs from the stock camera; forward the rest to the car
    if (lkas_msg_check(addr) || (chery_longitudinal && (addr == CHERY_ACC_CMD)))
    {
      bus_fwd = -1;
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
  chery_acc_stopped = false;
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

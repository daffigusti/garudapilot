// CAN msgs we care about
#define ENGINE_DATA 0xc9
#define LKAS_HUD 0x373
#define STEERING_LKAS 0x225
#define BRAKE_DATA 0x269
#define GAS_DATA 0x191
#define CRZ_BTN 0x1e1
#define CRZ_CTRL 0x370
#define ACC_CMD 0x260
#define ACC_STS 0x263

// CAN bus numbers
#define BUS_MAIN 0
#define BUS_RADAR 1
#define BUS_CAM 2

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

const CanMsg WULING_TX_MSGS[] = {{STEERING_LKAS, 0, 8}, {CRZ_BTN, 0, 8}, {CRZ_BTN, 2, 8},  {LKAS_HUD, 0, 8}, {CRZ_CTRL, 0, 8}, {CRZ_CTRL, 2, 8}, {ACC_STS, 0, 8}, {ACC_CMD, 0, 8}};

RxCheck wuling_rx_checks[] = {
    {.msg = {{CRZ_BTN, 0, 8, .frequency = 50U}, {0}, {0}}},
    {.msg = {{ENGINE_DATA, 0, 8, .frequency = 100U}, {0}, {0}}},
    {.msg = {{BRAKE_DATA, 0, 8, .frequency = 50U}, {0}, {0}}},
    {.msg = {{GAS_DATA, 0, 8, .frequency = 50U}, {0}, {0}}},
};

// track msgs coming from OP so that we know what CAM msgs to drop and what to forward
static void wuling_rx_hook(const CANPacket_t *to_push)
{
  if (((int)GET_BUS(to_push) == BUS_MAIN))
  {
    int addr = GET_ADDR(to_push);

    //speed data
    if (addr == 840)
    {
      // sample speed: scale by 0.01 to get kph
      int speed = (GET_BYTE(to_push, 0) << 8) | GET_BYTE(to_push, 1);
      vehicle_moving = speed > 10; // moving when speed > 0.1 kph
    }

    //torque driver data
    if (addr == 485)
    {
      int torque_driver_new = GET_BYTE(to_push, 6);
      // update array of samples
      update_sample(&torque_driver, torque_driver_new);
    }

    //brake data
    if (addr == 201)
    {
      brake_pressed = GET_BIT(to_push, 40U) != 0U;
    }

    //gas data
    if (addr == 401)
    {
      gas_pressed = GET_BYTE(to_push, 6) != 0U;
    }

    //cruize data
    if ((addr == 611))
    {
      bool cruise_available = (GET_BYTE(to_push, 4) >> 6) != 0U;
      if (!cruise_available) {
        // lateral_controls_allowed = false;
      }

      bool cruise_status = (GET_BYTE(to_push, 2) >> 5) != 0U;
      bool cruise_engaged = cruise_status || cruise_available;

      pcm_cruise_check(cruise_engaged);
    }

    generic_rx_checks((addr == STEERING_LKAS));
  }
  controls_allowed = true;
}

static bool wuling_tx_hook(const CANPacket_t *to_send)
{

  bool tx = true;
  int addr = GET_ADDR(to_send);
  int bus = GET_BUS(to_send);

  // Check if msg is sent on the main BUS
  if (bus == BUS_MAIN)
  {

    // steer cmd checks
    if (addr == STEERING_LKAS)
    {
      //  int desired_torque = ((GET_BYTE(to_send, 0) & 0x7U) << 8) + GET_BYTE(to_send, 1);
      //  desired_torque = to_signed(desired_torque, 11);

      //  bool steer_req = (GET_BIT(to_send, 5U) != 0U);
      //   if (steer_torque_cmd_checks(desired_torque, steer_req, WULING_STEERING_LIMITS)) {
      //     // tx = 0;
      //   }
    }

    // // cruise buttons check
    if (addr == CRZ_BTN)
    {
      // allow resume spamming while controls allowed, but
      // only allow cancel while contrls not allowed
      // int button = (GET_BYTE(to_send, 0) >> 2) & 0x15U;

      // bool cancel_cmd = (button == 8) && cruise_engaged_prev;
      // if (!controls_allowed && !cancel_cmd)
      // {
      //   // tx = 0;
      // }
    }
  }

  // 1 allows the message through
  return tx;
}

static int wuling_fwd_hook(int bus, int addr)
{
  int bus_fwd = -1;

  if (bus == BUS_MAIN)
  {
    bool block_msg = (addr == 00);
    if (!block_msg) {
      bus_fwd = BUS_CAM;
    }
  }
  else if (bus == BUS_CAM)
  {
    // bool block = (addr == STEERING_LKAS) || (addr == ACC_CMD);
    bool is_lkas_msg = (addr == LKAS_HUD);
    bool is_acc_md = (addr == ACC_CMD);
    bool block = (addr == STEERING_LKAS) || is_lkas_msg || (addr == CRZ_CTRL) || is_acc_md; 
    if (!block)
    {
      bus_fwd = BUS_MAIN;
    }
  }
  else
  {
    // don't fwd
  }

  return bus_fwd;
}

static safety_config wuling_init(uint16_t param)
{
  UNUSED(param);
  return BUILD_SAFETY_CFG(wuling_rx_checks, WULING_TX_MSGS);
}

const safety_hooks wuling_hooks = {
    .init = wuling_init,
    .rx = wuling_rx_hook,
    .tx = wuling_tx_hook,
    .fwd = wuling_fwd_hook,
};

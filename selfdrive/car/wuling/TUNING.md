# Wuling Almaz RS Pro - Tuning Reference

## Architecture Overview

Wuling menggunakan **hybrid control**:
- **Lateral (steering)**: Dikontrol langsung oleh openpilot via STEERING_LKA message
- **Longitudinal (gas/brake)**: Dikontrol oleh stock ACC, openpilot mengatur cruise speed via **button spamming** (CC_LONG mode)

### CAN Bus Layout
| Bus | Nama | Fungsi |
|-----|------|--------|
| 0 | POWERTRAIN | ECM, EPS, ACC module, wheel speed |
| 1 | OBSTACLE | Radar (tidak dipakai) |
| 2 | CAMERA | Stock ADAS camera, LKAS, BSM |

### Messages on Bus 2 (dari can_printer)
| Address | Message | Freq |
|---------|---------|------|
| 0x225 (549) | STEERING_LKA | 50Hz |
| 0x373 (883) | LkasHud | 20Hz |
| 0x415 (1045) | Unknown | 4Hz |
| 0x610 (1552) | Unknown | ~0Hz |

**Note**: ACC messages (GasCmd, AccStatus, ASCMActiveCruiseControlStatus) **TIDAK ada** di bus 2, hanya di bus 0.

### Message Forwarding (fwd_hook)
- Bus 0 → Bus 2: Semua message di-forward
- Bus 2 → Bus 0: Semua message di-forward **kecuali STEERING_LKA** (di-replace openpilot)
- LkasHud, ASCMActiveCruiseControlStatus, GasCmd: **Passthrough** (stock camera handle)

### Key Settings
| Parameter | Value | Catatan |
|-----------|-------|---------|
| `pcmCruise` | `True` | Selalu True, stock ACC kontrol gas/brake & engagement |
| `openpilotLongitudinalControl` | `experimental_long` | Enable via setting |
| `radarUnavailable` | `True` | Tidak pakai radar |
| `experimentalLongitudinalAvailable` | `True` | Bisa di-enable user |

### Safety (CC_LONG Mode)
Saat `openpilotLongitudinalControl = True`:
- Safety flag `WULING_PARAM_CC_LONG` di-set
- TX messages dibatasi: **hanya steering + button** (WULING_CC_LONG_TX_MSGS)
- Tidak boleh kirim gas/brake commands (GasCmd, ASCMActiveCruiseControlStatus)
- FrogPilot `has_cc_long` flag di-set untuk Wuling

---

## Lateral Tuning Parameters

### Live Tuning via FrogPilot UI
Parameter lateral bisa di-adjust **live** via UI tanpa restart:
1. Settings → **Advanced Lateral Tune**
2. Aktifkan **"Force Auto-Tune Off"** supaya slider muncul
3. Tuning Level harus **≥ 3**

| UI Toggle | Parameter | Current |
|-----------|-----------|---------|
| Steer Friction | FRICTION | 0.12 |
| Lateral Acceleration | LAT_ACCEL_FACTOR | 1.70 |
| Steer Ratio | steerRatio | 18.00 |
| Actuator Delay | steerActuatorDelay | 0.30 |
| Kp Factor | steerKp | default |

**Note**: `STEER_MAX` dan `STEER_DELTA_UP/DOWN` tidak bisa via UI — harus edit code + flash panda.

### 1. Torque Params (`selfdrive/car/torque_data/params.toml`)

```toml
"ALMAS_RS_PRO" = [LAT_ACCEL_FACTOR, MAX_LAT_ACCEL_MEASURED, FRICTION]
```

**Current: `[1.7, 1.94, 0.12]`**

| Parameter | Fungsi | Range | Efek naikkan | Efek turunkan |
|-----------|--------|-------|-------------|---------------|
| LAT_ACCEL_FACTOR | Agresivitas respons lateral | 1.0 - 2.5 | Koreksi lebih cepat/kuat | Lebih smooth/lambat |
| MAX_LAT_ACCEL_MEASURED | Batas max lateral accel | - | Lebih banyak torque tersedia | Kurangi kemampuan belok |
| FRICTION | Kompensasi friction | 0.05 - 0.20 | Lebih aktif koreksi di jalan lurus | Lebih tenang di jalan lurus |

### 2. Steer Params (`selfdrive/car/wuling/values.py`)

| Parameter | Current | Fungsi | Catatan |
|-----------|---------|--------|---------|
| `STEER_MAX` | 200 | Batas torque max | Range aman: 150-300 |
| `STEER_DELTA_UP` | 3 | Rate naik torque per frame | Semakin tinggi = semakin cepat respond |
| `STEER_DELTA_DOWN` | 3 | Rate turun torque per frame | Semakin tinggi = semakin cepat lepas |
| `STEER_DRIVER_ALLOWANCE` | 45 | Toleransi torque driver sebelum override | Turunkan = lebih mudah takeover |
| `STEER_DRIVER_MULTIPLIER` | 2 | Weight driver torque | Naikkan = driver lebih dominan |
| `STEER_THRESHOLD` | 40 | Threshold steeringPressed trigger | Turunkan = lebih sensitif takeover |
| `MIN_STEER_SPEED` | 3.0 m/s | Speed minimum steering aktif | ~11 km/h |

### 3. Interface Params (`selfdrive/car/wuling/interface.py`)

| Parameter | Current | Fungsi |
|-----------|---------|--------|
| `steerRatio` | 18 (CarSpecs) | Rasio steering. Turunkan = responsif, naikkan = smooth |
| `steerLimitTimer` | 0.4 | Waktu sebelum steer fault di-flag |
| `steerActuatorDelay` | 0.3 | Delay aktuator. Turunkan = cepat respond tapi bisa oscillate |

### 4. Safety Limits (`panda/board/safety/safety_wuling.h`)

**HARUS match dengan values.py!**

| Parameter | Current | Catatan |
|-----------|---------|---------|
| `max_steer` | 200 | = STEER_MAX |
| `max_rate_up` | 3 | = STEER_DELTA_UP |
| `max_rate_down` | 3 | = STEER_DELTA_DOWN |
| `driver_torque_allowance` | 35 | Safety layer untuk driver override |
| `driver_torque_factor` | 2 | Safety layer weight |
| `max_rt_delta` | 128 | Realtime torque rate limit |

---

## Tuning Troubleshooting

### Mobil oscillate/ping-pong di jalan lurus
1. Turunkan `LAT_ACCEL_FACTOR` (coba -0.2)
2. Turunkan `FRICTION` (coba -0.03)
3. Naikkan `steerActuatorDelay` (coba +0.05)

### Steering kurang kuat di tikungan
1. Naikkan `STEER_MAX` (+ safety max_steer)
2. Naikkan `MAX_LAT_ACCEL_MEASURED`
3. Naikkan `STEER_DELTA_UP` (+ safety max_rate_up)

### Steering terlalu lambat respond
1. Naikkan `STEER_DELTA_UP` (+ safety max_rate_up)
2. Turunkan `steerActuatorDelay`
3. Turunkan `steerRatio`

### Koreksi terlalu agresif
1. Turunkan `LAT_ACCEL_FACTOR`
2. Turunkan `STEER_DELTA_UP/DOWN`
3. Naikkan `steerActuatorDelay`

### Susah takeover steering
1. Turunkan `STEER_DRIVER_ALLOWANCE`
2. Turunkan `STEER_THRESHOLD`

---

## Tuning History

| Date | LAT_ACCEL | MAX_LAT | FRICTION | STEER_MAX | DELTA_UP/DOWN | ActuatorDelay | Result |
|------|-----------|---------|----------|-----------|---------------|---------------|--------|
| Initial | 2.0 | 1.94 | 0.166 | 150 | 3/4 | 0.2 | Terlalu agresif, banyak koreksi |
| v2 | 2.0 | 1.94 | 0.166 | 300 | 5/5 | 0.2 | Ping-pong, terlalu kuat |
| v3 | 2.0 | 1.94 | 0.166 | 200 | 4/4 | 0.3 | Lumayan, masih kejut |
| v4 | 2.0 | 1.94 | 0.166 | 200 | 3/3 | 0.3 | Smoother, masih agresif |
| v5 | 1.8 | 1.94 | 0.13 | 200 | 3/3 | 0.3 | Smoother |
| v6 | 1.5 | 1.94 | 0.10 | 200 | 2/2 | 0.3 | Terlalu lambat |
| **Current** | **1.7** | **1.94** | **0.12** | **200** | **3/3** | **0.3** | **Balanced** |

---

## Longitudinal Control (Button Spamming / CC_LONG)

### Setup
- `openpilotLongitudinalControl = True` → planner generate `actuators.accel`
- `pcmCruise = True` → stock ACC handle engagement & gas/brake
- Safety `WULING_PARAM_CC_LONG` → hanya boleh kirim steering + button
- FrogPilot `has_cc_long = True` untuk Wuling

### Button Spam Logic
Openpilot mengontrol cruise speed stock ACC dengan mengirim button CAN message ke bus 2:

| Button | Value | Fungsi |
|--------|-------|--------|
| `DECEL_SET` | 4 | Turunkan set speed |
| `RES_ACCEL` | 8 | Naikkan set speed / resume |
| `CANCEL` | 32 | Cancel cruise |
| `UNPRESS` | 0 | Lepas tombol |

### Target Speed Calculation
```python
target_speed_kph = vEgo_kph + actuators.accel_kph
```
Planner generate `actuators.accel`, dikonversi ke target speed, lalu dibandingkan dengan `cruiseState.speed` untuk tentukan tombol mana yang dikirim.

### Intervals
| Kondisi | Interval | Rate |
|---------|----------|------|
| Normal (accel/decel) | 0.04s | ~25Hz |
| Auto-resume standstill | 0.2s | ~5Hz |
| Auto-resume (cruise disengaged at stop) | 0.3s | ~3Hz |

### Stop & Go (Auto-Resume)
Saat stock ACC disengage karena mobil stop:
1. `cruise_was_active` flag track bahwa cruise aktif sebelum stop
2. Selama standstill + tidak brake → kirim `RES_ACCEL` tiap 0.3s
3. Begitu cruise re-engage → button spam normal
4. Reset flag saat brake ditekan atau cancel

---

## Auto High Beam

Auto high beam dikontrol oleh stock camera via **STEERING_LKA** message byte 2-6.

### Fix
- DBC menambahkan `LKA_BYTE2` - `LKA_BYTE6` untuk capture byte yang sebelumnya undefined
- `create_steering_control` copy stock STEERING_LKA values dari camera sebagai base
- Override hanya steer torque/request/counter/checksum
- `SET_ME_X0` ikut stock, tidak di-hardcode

---

## LkasHud (Dashboard Indicator)

Currently **disabled** — stock camera passthrough. Semua kombinasi yang dicoba trigger warning kuning di dashboard.

### Stock Values (dari can_printer bus 2)
```
Active (grey/standby): c2010000ac900201
LKA mati:              00010000ac90023f
```

| Signal | Grey (mati) | Active (standby) |
|--------|-------------|------------------|
| LKA_ACTIVE | 0 | 1 |
| STEER_WARNING | 15 | 1 |
| LKA_LINE_2 | 3 | 1 |
| NEW_SIGNAL_1 | 1 | 1 |

### Kombinasi yang Dicoba (Semua ERROR)
| # | Signal yang diubah | Result |
|---|-------------------|--------|
| 1 | LKA_ACTIVE=1, STEER_WARNING=1, LKA_LINE_2=0 | Warning kuning |
| 2 | LKA_ACTIVE=1, LKAS_STATE=1, LKA_LINE=3 | Warning kuning |
| 3 | Full: LKA_ACTIVE=1, LKAS_STATE=1, LEAD_FOLLOW=1, HUD_ALERT=1, LKA_LINE=3, STEER_WARNING=2 | Warning kuning |
| 5 | STEER_WARNING=2, LKA_LINE_2=1 (stock base) | Warning kuning |

### Root Cause (Likely)
Kemungkinan bukan signal values yang salah, tapi **counter/checksum di byte 4-6** (`UNKNOWN_2`, `NEW_SIGNAL_6`, `NEW_SIGNAL_7`, `NEW_SIGNAL_8`). Stock camera kirim counter yang increment, tapi openpilot kirim via packer tanpa handle counter → ECU reject message.

### Next Steps
- [ ] Decode byte 4-6 dari LkasHud (capture beberapa frame, lihat pattern counter)
- [ ] Atau kirim raw CAN bytes (bypass packer) dengan counter yang benar
- [ ] Atau passthrough stock + hanya modify signal tanpa re-pack (raw byte manipulation)

---

## Bug Fixes Log

### 1. KeyError: ALMAS_RS_PRO (torque params)
- **Masalah**: Key di `params.toml` pakai display name `"WULING ALMAZ RS PRO 2022"`, tapi lookup pakai enum name `ALMAS_RS_PRO`
- **Fix**: Rename key di `params.toml` ke `"ALMAS_RS_PRO"`

### 2. opParams crash (capnp type mismatch)
- **Masalah**: `op_params.get('steer_ratio')` return `None`, tidak bisa di-assign ke capnp float field
- **Fix**: Hapus opParams, pakai steerRatio dari CarSpecs (18)

### 3. actuators.copy() crash
- **Masalah**: capnp struct tidak punya method `copy()`
- **Fix**: Ganti ke `actuators.as_builder()` seperti car interface lain

### 4. ACC message timeout saat openpilot long enabled
- **Masalah**: `GasCmd`, `AccStatus`, `ASCMActiveCruiseControlStatus` di-parse dari bus 2 (CAMERA) saat long enabled, tapi message ini berasal dari bus 0
- **Fix**: Selalu parse ACC messages dari bus 0 (POWERTRAIN), `cp_cruise` selalu pakai `pt_cp`

### 5. Dashboard warning kuning saat cruise stop & go
- **Masalah**: `fwd_hook` block `ASCMActiveCruiseControlStatus` dan `GasCmd` dari camera, lalu openpilot kirim ulang tapi timing/values tidak konsisten
- **Fix**: Unblock message ini di `fwd_hook`, biarkan stock camera passthrough

### 6. Auto high beam tidak berfungsi
- **Masalah**: `create_steering_control` hanya set signal yang di-decode di DBC (5 signal). Byte 2-6 yang berisi auto high beam signal di-zero-kan oleh packer
- **Fix**:
  - Tambah `LKA_BYTE2` - `LKA_BYTE6` di DBC untuk cover byte 2-6
  - Copy stock STEERING_LKA values dari camera sebagai base
  - Override hanya steer torque/request/counter/checksum
  - Hapus hardcode `SET_ME_X0`, biarkan ikut stock

### 7. pcmCruise dan safety conflict
- **Masalah**: `pcmCruise = False` + `openpilotLongitudinalControl = True` → safety expect gas/brake commands, tapi kita cuma kirim button spam
- **Fix**: Tambah `WULING_PARAM_CC_LONG` safety flag (seperti GM `FLAG_GM_CC_LONG`)
  - CC_LONG TX msgs: hanya steering + button
  - `pcmCruise = True` (stock ACC handle engagement)
  - `has_cc_long` flag di FrogPilot

### 8. Stop & Go cruise disengage
- **Masalah**: Stock ACC disengage saat stop → `CC.longActive = False` → button spam berhenti → tidak bisa resume
- **Fix**: Track `cruise_was_active` state, kirim `RES_ACCEL` tiap 0.3s saat standstill untuk auto-resume

---

## TODO / Known Issues

- [ ] LkasHud indikator steering: kemungkinan masalah counter/checksum byte 4-6
- [ ] Button spam rate: bisa di-improve ke dynamic rate seperti GM
- [ ] `longitudinalTuning.kiV = [0.0]`: integral gain disabled
- [ ] Radar command (`create_radar_command`): disabled, perlu di-enable kalau mau direct longitudinal control
- [ ] Decode unknown messages di bus 2: 0x415 (1045), 0x610 (1552)

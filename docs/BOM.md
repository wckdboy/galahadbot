# Bill of materials

**These are planning anchors, not quotes.** Prices were captured by the project
brief on 29 October 2026 from US manufacturer storefronts. They exclude VAT,
shipping, import fees and tools. For Denmark, the purchasing gate is the
delivered total — a $2,900 ex-tax basket is not a $3,000 delivered build.

Stock and lead time change constantly. Re-check every line before ordering.

## Actuation

| Part | Variant | Qty | Unit | Ext. | Source |
|---|---|---|---|---|---|
| DYNAMIXEL XC330-M288-T | low-voltage, TTL, metal gears | 8 | $103.39 | $827.12 | robotis.us |
| DYNAMIXEL XL330-M288-T | low-voltage, TTL | 6 | $27.49 | $164.94 | robotis.us |
| ROBOTIS U2D2 | USB ↔ TTL | 1 | $36.92 | $36.92 | robotis.us |
| X330 horns / idlers | FPX330-H101 family | 1 set | — | in allowance | robotis.us |

Do **not** substitute the XC330-T288: it is the higher-voltage part.

## Drive

| Part | Item | Qty | Note |
|---|---|---|---|
| Pololu 30T Track Set, black | 3033 | 1 | two tracks, sprockets, idlers |
| 100:1 Micro Metal Gearmotor HPCB 6 V, 12 CPR encoder, back connector | 5190 | 2 | match encoder cables |
| DRV8838 single brushed motor driver carrier | 2990 | 2 | 1.7 A cont / 1.8 A peak nominal |

## Compute and control

| Part | Qty | Note |
|---|---|---|
| Raspberry Pi 5, 4 GB | 1 | 5 V / 5 A USB-C PD; do not assume a buck advertises 5 A |
| High-endurance microSD, 64 GB | 1 | |
| Raspberry Pi Active Cooler | 1 | |
| PJRC Teensy 4.1 | 1 | 3.3 V GPIO only |
| Official 27 W USB-C PSU | 1 | bench bring-up only |

## Sensing

| Part | Product | Qty | Note |
|---|---|---|---|
| Raspberry Pi Camera Module 3, standard AF | — | 1 | correct Pi 5 flex cable |
| VL53L5CX Qwiic ToF imager | SEN-18642 | 1 | head, coarse multi-zone |
| VL53L4CD breakout | 5396 | 4 | downward, chassis corners |
| VL53L1X breakout | 3967 | 2 | fore and aft |
| BNO085 breakout | 4754 | 1 | chassis-mounted, SPI preferred |
| TCA9548A I2C mux breakout | — | 1 | resolve duplicate addresses |
| Bumper microswitches | — | 2 | normally closed |

## Interaction

| Part | Qty | Note |
|---|---|---|
| reSpeaker XVF3800 USB 4-mic array | 1 | USB mode; confirm exact revision |
| Visaton BF 32, 4 Ω, article 2243 | 1 | 2 W rated, 5 W max — not 5 W continuous |
| Adafruit 1.3″ 240×240 ST7789 | 4313 | 1 | SPI, full PCB in CAD |
| Physical mute switch + camera LED | 1 | circuit must actually enforce it |

## Power

| Part | Qty | Note |
|---|---|---|
| Tattu 850 mAh 3S 45C, XT30 (TA-45C-850-3S1P-XT30) | 3 | 2 installed + 1 spare |
| Pololu D24V150F5, 5 V 15 A class | 1 | servo branch — see stall budget |
| Pololu D24V50F5, 5 V | 1 | logic branch |
| Pololu D24V50F6, 6 V | 1 | tread branch |
| External balance charger + LiPo bag | 1 | non-negotiable |
| Fuses, connectors, bulk caps | — | sized from measurements |

## Planning totals

| Category | Allowance |
|---|---|
| 14 installed actuators | $992 |
| Compute, cooler, storage | $110 |
| U2D2 + MCU | $75 |
| Track set, motors, drivers, cables | $120 |
| Camera, range sensors, IMU, I2C routing | $190 |
| Audio and chest display | $110 |
| Regulators, protection, monitors, interconnect | $210 |
| Batteries and charger | $110 |
| Printed structure, fittings, bearings, hardware | $160 |
| **Indicative subtotal** | **$2,077** |
| 25 % VAT planning allowance | ≈$519 |

Budget cap is $3,000 delivered. Keep the headroom for shipping, import, spares
and the inevitable second print revision.

## Ordering strategy

Do not buy all 14 servos up front. Buy **one XC330, one XL330, one drive
pair with a track set**, and the minimum control and power hardware to validate
interfaces, waist loading and drive feasibility. Reuse them in the final build.
Add spares only once the ledger confirms headroom.

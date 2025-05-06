# gopher

Ground station for Nerve controller system.

---

<details markdown="1">
  <summary>Table of Contents</summary>

<!-- TOC -->
- [gopher](#gopher)
  - [1 Overview](#1-overview)
  - [2 Development](#2-development)
    - [2.3 CAN Bus](#23-can-bus)
  - [3 Release Notes](#3-release-notes)
    - [3.1 v0.1.0-alpha](#31-v010-alpha)
<!-- TOC -->

</details>

---

## 1 Overview

![gopher.drawio.png](docs/gopher.drawio.png)

> Drawio file here: [gopher.drawio](docs/gopher.drawio).

---

## 2 Development

Developed using [PlatformIO](https://platformio.org/).

### 2.3 CAN Bus

Python cantools is used to turn the CAN DBC into `.h`/`.c` files:

```shell
pip install cantools
cantools generate_c_source --use-float gopher.dbc
```

Executing the above will produce `gopher.h` and `gopher.c`.

Each message in the DBC will be generated utilizing:

```c
// Example for a message named “ExMessage”.
void pack_ExMessage(const float physical_values[], uint8_t data_out[8]);
void decode_ExMessage(const uint8_t data_in[8], float physical_values[]);
```

---

## 3 Release Notes

### 3.1 v0.1.0-alpha

Pre-release concept prototype.

- **Python desktop application** (exe package-able).
- SQLite XBee message database logging.
- Live telemetry display.
    - Quaternion 3 vector display.
    - Quaternion 3D model display.
    - 2 axis graph display (temperature demo).

![v0_1_0-alpha_quaternion_demo.gif](docs/pictures/v0_1_0-alpha_quaternion_demo.gif)

|                          Main Screen                          |                            Quaternion Display                             |                               Quaternion Model Display                                |
|:-------------------------------------------------------------:|:-------------------------------------------------------------------------:|:-------------------------------------------------------------------------------------:|
| ![v0_1_0-alpha_home.png](docs/pictures/v0_1_0-alpha_home.png) | ![v0_1_0-alpha_quaternion.png](docs/pictures/v0_1_0-alpha_quaternion.png) | ![v0_1_0-alpha_quaternion_model.png](docs/pictures/v0_1_0-alpha_quaternion_model.png) |

- Pictures and GIF animation show v0.1.0-alpha concept prototype with
  [nerve_ada_board](https://github.com/danielljeon/nerve_ada_board).

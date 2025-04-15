# gopher

![black_formatter](https://github.com/danielljeon/gopher/actions/workflows/black_formatter.yaml/badge.svg)
![pytest](https://github.com/danielljeon/gopher/actions/workflows/pytest.yaml/badge.svg)

Ground station for Nerve controller system.

---

<details markdown="1">
  <summary>Table of Contents</summary>

<!-- TOC -->
* [gopher](#gopher)
  * [1 Overview](#1-overview)
  * [2 Development](#2-development)
    * [2.1 GitHub Actions Workflows](#21-github-actions-workflows)
      * [2.1.1 black](#211-black)
      * [2.1.2 pytest](#212-pytest)
      * [2.1.3 pyinstaller](#213-pyinstaller)
  * [3 Release Notes](#3-release-notes)
    * [3.1 v0.1.0-alpha](#31-v010-alpha)
<!-- TOC -->

</details>

---

## 1 Overview

![gopher.drawio.png](docs/gopher.drawio.png)

> Drawio file here: [gopher.drawio](docs/gopher.drawio)

![v0_1_0-alpha_quaternion_demo.gif](docs/pictures/v0_1_0-alpha_quaternion_demo.gif)

|                          Main Screen                          |                            Quaternion Display                             |                               Quaternion Model Display                                |
|:-------------------------------------------------------------:|:-------------------------------------------------------------------------:|:-------------------------------------------------------------------------------------:|
| ![v0_1_0-alpha_home.png](docs/pictures/v0_1_0-alpha_home.png) | ![v0_1_0-alpha_quaternion.png](docs/pictures/v0_1_0-alpha_quaternion.png) | ![v0_1_0-alpha_quaternion_model.png](docs/pictures/v0_1_0-alpha_quaternion_model.png) |

---

## 2 Development

### 2.1 GitHub Actions Workflows

#### 2.1.1 black

[black_formatter.yaml](.github/workflows/black_formatter.yaml)

#### 2.1.2 pytest

[pytest.yaml](.github/workflows/pytest.yaml)

#### 2.1.3 pyinstaller

PyInstaller macOS, Windows, Linux `main.spec` builds workflow is saved
in [docs/pyinstaller.yaml](docs/pyinstaller.yaml) for reference.

- Discontinued use due to high GitHub Actions storage consumption (could be
  optimized much better).

The badge markdown would be as follows:

```
![pyinstaller](https://github.com/danielljeon/gopher/actions/workflows/pyinstaller.yaml/badge.svg)
```

---

## 3 Release Notes

### 3.1 v0.1.0-alpha

Concept prototype release.

- **Python desktop application** (exe package-able).
- SQLite XBee message database logging.
- Live telemetry display.
    - Quaternion 3 vector display.
    - Quaternion 3D model display.
    - 2 axis graph display (temperature demo).

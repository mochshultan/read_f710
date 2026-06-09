# 🎮 read_f710

<div align="center">

<!-- TODO: Add project logo (e.g., a joystick icon or HUD graphic) -->

[![GitHub stars](https://img.shields.io/github/stars/mochshultan/read_f710?style=for-the-badge)](https://github.com/mochshultan/read_f710/stargazers)

[![GitHub forks](https://img.shields.io/github/forks/mochshultan/read_f710?style=for-the-badge)](https://github.com/mochshultan/read_f710/network)

[![GitHub issues](https://img.shields.io/github/issues/mochshultan/read_f710?style=for-the-badge)](https://github.com/mochshultan/read_f710/issues)

[![GitHub license](https://img.shields.io/github/license/mochshultan/read_f710?style=for-the-badge)](LICENSE)

**A Head-Up Display (HUD) and utility for real-time monitoring and debugging of Logitech F710 joystick input, with ROS 2 integration.**

</div>

## 📖 Overview

`read_f710` is a specialized Python application designed to interface with the Logitech F710 wireless gamepad. Its primary purpose is to provide a real-time Head-Up Display (HUD) that visualizes the current state of joystick axes, buttons, and D-pad inputs. This tool is invaluable for debugging joystick input, verifying controller functionality, or integrating joystick controls into robotics projects via ROS 2. It also includes a dedicated utility for detailed trigger debugging, making it a comprehensive solution for F710 users and developers.

## ✨ Features

-   🎯 **Real-time HUD**: Displays all Logitech F710 joystick axis and button states graphically.
-   🕹️ **Joystick Input Reading**: Accurately captures input from the Logitech F710 gamepad.
-   🛠️ **Trigger Debugging Utility**: A separate script to specifically aid in debugging joystick trigger inputs.
-   🤖 **ROS 2 Integration**: Designed with a `ros2` directory, indicating readiness for integration into a ROS 2 ecosystem, potentially for publishing joystick commands to robots or other nodes.
-   ⚙️ **Configurable**: Utilizes a `config` directory for easy customization of settings.

## 🖥️ Screenshots

<!-- TODO: Add actual screenshots of the HUD in action and the trigger debugging utility. -->
<!-- Example: -->
<!-- ![HUD Screenshot](screenshots/hud_display.png) -->
<!-- *Real-time visualization of joystick inputs.* -->
<!-- ![Trigger Debugger Screenshot](screenshots/trigger_debugger.png) -->
<!-- *Dedicated utility for fine-tuning trigger responses.* -->

## 🛠️ Tech Stack

**Runtime:**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

**Libraries & Frameworks:**
-   **GUI & Joystick Input**: Pygame (inferred, common for Python HUDs and joystick handling)
-   **Robotics Integration**: ROS 2 ([rclpy](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Creating-Your-First-ROS2-Package.html#python-interface) for Python)

## 🚀 Quick Start

Follow these steps to get `read_f710` up and running on your local machine.

### Prerequisites

-   **Python 3.x**: Ensure Python 3 is installed.
-   **Logitech F710 Gamepad**: Connected and recognized by your operating system.
-   **Operating System Joystick Device Access**:
    -   **Linux**: May require `joystick` package and proper permissions (e.g., `sudo apt-get install joystick`, or ensuring user is in `input` group).
    -   **Windows/macOS**: Drivers usually handled automatically.
-   **ROS 2 (Optional)**: If you plan to use the ROS 2 integration features, a working ROS 2 environment (e.g., Humble, Iron) must be installed and sourced.

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/mochshultan/read_f710.git
    cd read_f710
    ```

2.  **Install Python dependencies**
    It is recommended to use a virtual environment.
    ```bash
    python3 -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    pip install pygame # Main GUI and input library
    # pip install python-evdev # Alternative/additional input library if pygame's input isn't sufficient for triggers on Linux
    ```

3.  **ROS 2 Setup (Optional)**
    If the `ros2` directory contains a ROS 2 package, you will need to build it within a ROS 2 workspace.
    ```bash
    # Assuming 'read_f710' is cloned into your ROS 2 workspace's 'src' directory (e.g., ~/ros2_ws/src)
    cd ~/ros2_ws
    rosdep install -i --from-path src --rosdistro <YOUR_ROS_DISTRO> -y
    colcon build --packages-select read_f710_ros_package # Replace with actual package name if different
    source install/setup.bash
    ```

### Running the Application

1.  **Start the F710 HUD**
    ```bash
    python3 hud_f710.py
    ```
    This will launch the graphical Head-Up Display showing the joystick input.

2.  **Run the Trigger Debugging Utility**
    ```bash
    python3 debug_triggers.py
    ```
    This script provides specific output for debugging trigger mechanisms.

## 📁 Project Structure

```
read_f710/
├── config/             # Configuration files for the application
├── debug_triggers.py   # Script for debugging joystick trigger inputs
├── hud_f710.py         # Main application script for the F710 HUD
├── ros2/               # Directory for ROS 2 related packages or scripts
└── README.md           # This README file
```

## ⚙️ Configuration

The `config/` directory is intended to hold configuration files for the application. You might find settings related to HUD display options, joystick mapping, or ROS 2 node parameters within this directory.

<!-- TODO: Detail specific configuration files and their parameters if they exist within the `config` directory. -->

## 🔧 Development

### Running Scripts
-   **Main HUD**: `python3 hud_f710.py`
-   **Trigger Debugger**: `python3 debug_triggers.py`

### Development Workflow
Ensure your virtual environment is activated (`source venv/bin/activate`) before running any Python scripts or installing dependencies. Modify `.py` files to implement new features or fix bugs.

## 🧪 Testing

No automated test suite was detected for this project. Testing is primarily performed by running `hud_f710.py` and `debug_triggers.py` and observing their behavior with a connected Logitech F710 joystick.

## 🤝 Contributing

We welcome contributions to `read_f710`! If you have suggestions, bug reports, or want to contribute code, please feel free to open an issue or pull request.

### Development Setup for Contributors
1.  Fork the repository.
2.  Clone your forked repository.
3.  Set up the development environment as described in the [Installation](#installation) section.
4.  Create a new branch for your feature or bug fix.
5.  Commit your changes following a clear commit message convention.
6.  Push your branch and open a pull request.

## 📄 License

This project is currently **Unlicensed**. For open-source projects, it is recommended to add a license. See the [Choose a License](https://choosealicense.com/) website for more information.

<!-- TODO: Add a LICENSE file to the repository (e.g., MIT, Apache 2.0). -->

## 🙏 Acknowledgments

-   The developers of [Pygame](https://www.pygame.org) for providing a robust library for game development and GUI creation in Python (if confirmed as used).
-   The [ROS 2](https://www.ros.org/) community for the flexible robotics operating system.
-   Logitech for creating the reliable F710 gamepad.

## 📞 Support & Contact

-   🐛 Issues: Feel free to report any issues or suggest features on the [GitHub Issues](https://github.com/mochshultan/read_f710/issues) page.
-   👤 Author: [mochshultan](https://github.com/mochshultan)

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ by mochshultan

</div>
```


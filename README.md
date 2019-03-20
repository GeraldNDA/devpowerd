# Devpowerd
Depowerd is an application that allows multiple users to easily send commands to an Arduino relay controller (at the same time).
It is powered by `python3`, `pexpect` and `conserver` and works by creating a server daemon to watch for requests (devpowerd) and a CLI 
application to send the reqeuests (devpowerctl).

## Sample usage
`devpowerctl turn_on pinea64`
- turn on the `pinea64` device

`devpowerctl turn_off beaglebone`
- turn off the `beaglebone` device

`devpowerctl restart all`
- turn off and then turn on available devices.

## Installation
0. Program arduino (leonardo) with `ci_relay_controller.ino` and wire Arduino, relay module,  power supply and devices.

1. Copy `devpowerd` into the `/usr/local/rc.d` folder.

2. Create a symbolic link `/usr/local/bin/devpowerctl` to `devpowerctl.py`.

3. Set up conserver to contain consoles for `devpowerctl` (and any devices to be supported).
   See ["setting up arduino controller"](https://hackmd.io/WaraH18ZQK2LgxyFFQxJOA) for more info.

4. Enable and start the server
   ```sh
   sudo sysrc devpowerd_enable=YES
   sudo service devpowerd start
   ```

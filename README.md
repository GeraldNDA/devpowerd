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

1. Clone this repository into `/usr/local/devpowerd`

2. Copy `devpowerd` into the `/usr/local/rc.d` folder.

3. Create a symbolic link `/usr/local/bin/devpowerctl` to `devpowerctl.py`.

4. Set up conserver to contain consoles for `devpowerctl` (and any devices to be supported).
   See ["setting up arduino controller"](https://hackmd.io/WaraH18ZQK2LgxyFFQxJOA) for more info.

5. Enable and start the server
   ```sh
   sudo sysrc devpowerd_enable=YES
   sudo service devpowerd start
   ```
 ## Additional Notes
 Depends on `conserver>=8.2.4`. Otherwise `devpowerserial.py` should be modified to use the `-M <SERIAL_HOST>` option.
 
 `localconserver.cf.sample` and `remoteconserver.cf.sample` are included to show what the conserver configurations are for the remote user (where devpowerd is being used) and the local user (where the serial connections are). If these are the same computer, than `localconserver.cf` is sufficient although the `access` block is unnecessary.
 
 You can either change the hostname in the files to match your local environment or you can modify `/etc/hosts` or add a DNS alias instead.

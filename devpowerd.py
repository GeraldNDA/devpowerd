#!/usr/bin/env python3

"""Device Power Controller Daemon

Currently supports only one Relay Power Controller.
"""
import sys
import json

from os import environ
from time import sleep
from contextlib import suppress
from collections import OrderedDict
from json.decoder import JSONDecodeError
from pathlib import Path

#from serial import Serial, serial_for_url
#from serial.serialutil import SerialException
#import serial.tools.list_ports as SerialPortList

from subprocess import call, check_output
from re import finditer

from socket import socket, AF_INET, SOCK_STREAM
from socket import SOL_SOCKET, SO_REUSEADDR
from socket import gethostname
if "devpowerd_dir" in environ:
    sys.path.append(str(Path(environ["devpowerd_dir"]).resolve()))

class PowerController():
    @staticmethod
    def get_devices():
        console_info = check_output(("/usr/local/bin/console", "-x"))
        matches = finditer(r"\s+(slot\d+)\s+on\s+/dev/cuaU\d+", str(console_info))
        return sorted(match.group(1) for match in matches)

    def __init__(self):
        pass

    #
    # Helper methods
    #

    def _send_command(self, command, device):
        """Sends a command via the serial port and verifies it was done"""
        if device == "all":
            res = True
            for device in PowerController.get_devices():
               res = res and self._send_command(command, device)
            return res
        try:
            from devpowerserial import ConsoleHandler, ConsoleError
            try:
                ch = ConsoleHandler(device)
                ch.do_command(command)
            except ConsoleError as e:
                # System error i.e. no alias, console is down, console failed or command failed on controller
                print(e, file=sys.stderr)
                return False
            except Exception as e:
                # timeout or early exit from running any commands
                print(e, file=sys.stderr)
                return False
        except ModuleNotFoundError:
            print(f"ERROR: Could not find file devpowerserial.py in {environ['devpowerd_dir']}", file=sys.stderr)
            return False
        return True
        
    #
    # Commands
    #

    def restart(self, device):
        """Sends the command to turn the device off then on"""
        return self._send_command("restart", device)

    def turn_on(self, device):
        """Sends the command to turn the device on"""
        return self._send_command("turn_on", device)

    def turn_off(self, device):
        """Sends the command to turn the device off"""
        return self._send_command("turn_off", device)

class SocketServer():
    HOST = gethostname()
    PORT = 9009

    def __init__(self, port=PORT):
        self.host = SocketServer.HOST
        self.port = port
        self.socket = socket(AF_INET, SOCK_STREAM)

    def __enter__(self):
        self.socket.__enter__()
        try:
            self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen()
        except Exception as e:
            self.__exit__(type(e), e, e.__traceback__)
            raise e
        return self.socket

    def __exit__(self, *args):
        return self.socket.__exit__(*args)

def do_command(controller, command):
    command = command.strip().split(" ")
    if len(command) != 2:
        print(f"Error: Expected <operation> <device> but got {tuple(command)}")
        return False
    op, dev = command
    if op  == "restart":
        return controller.restart(dev)
    elif op == "turn_off":
        return controller.turn_off(dev)
    elif op == "turn_on":
        return controller.turn_on(dev)
    else:
        print(f"Error: Operation {op} is unsupported. Supported commands are {{'restart', 'turn_off', 'turn_on'}}")
        return False

def main(*args):
    port = SocketServer.PORT
    if len(args):
        port=int(args[0])

    controller = PowerController()
    done = False
    with SocketServer(port) as sckt:
        while not done:
            recieved_command = ""
            conn, addr = sckt.accept()
            with conn:
                data = conn.recv(1024)
                while data and data[-1] != ord("\n"):
                    recieved_command += data.decode('utf-8')
                    data = conn.recv(1024)
                else:
                    recieved_command += data.decode('utf-8')
                recieved_command = recieved_command.strip()
                good = True
                # TODO: Should allow multiple error codes for errors in commands vs. errors from controller etc.
                print(f"Doing {recieved_command} from {addr}")
                good = do_command(controller, recieved_command)
                print(f"Done with status good={good}")
                response = int(not good)
                conn.sendall(f"RECV {response}".encode())

if __name__ == "__main__":
    main(*sys.argv[1:])

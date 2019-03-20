#!/usr/bin/env python3
"""'Device Power Controller' Controller

This tool communicates with the daemon to send requests
to the device power control device. Allows users to
turn the power on/off remotely.

Available commands:
    devpowerctl.py turn_on <device_name>
    devpowerctl.py turn_off <device_name>
    devpowerctl.py restart <device_name>

Devices are determined based on conserver.cf. They should be aliases
of a console of the form `slot###`.

Requires that the Power Controler Daemon service (devpowerd)
is already running.

"""
import sys

from argparse import ArgumentParser, RawDescriptionHelpFormatter

from socket import socket, AF_INET, SOCK_STREAM
from socket import gethostname

class SocketClient():
    HOST = gethostname()
    PORT = 9009

    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.socket = socket(AF_INET, SOCK_STREAM)

    def __enter__(self, *args):
        self.socket.__enter__(*args)
        self.socket.connect((self.host, self.port))
        return self.socket

    def __exit__(self, *args):
        self.socket.__exit__(*args)

def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("command", choices={"restart", "turn_on", "turn_off"},
            help="Operation to perform on device.")
    parser.add_argument("device", help="Device to turn be controlled.")
    parser.add_argument("--master", "-m", help="The hostname of the device "
            "where the devpowerd service is running. (Default: localhost[%(default)s])")
    parser.add_argument("--port", "-p", type=int, help="The port that the devpowerd service "
            "is listening to. (Default: %(default)s)")
    parser.set_defaults(
        master=SocketClient.HOST,
        port=SocketClient.PORT
    )
    return parser.parse_args()
    

def main(args):
    try:
        with SocketClient(host=args.master, port=args.port) as sckt:
            to_send = f"{args.command} {args.device}\n"
            sckt.sendall(to_send.encode())
            response = sckt.recv(1024).decode("utf-8")
        response = response.split()
        print(f"GOT: {response}")
        if response and len(response) >= 2:
            sys.exit(int(response[1]))
    except ConnectionRefusedError as e:
        print("ERROR: Could not connect to devpowerd. "
                "Ensure that the service is started.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    args = parse_args()
    main(args)

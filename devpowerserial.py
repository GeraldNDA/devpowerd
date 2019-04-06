#!/usr/local/bin/python3
"""Power Controller Serial Interface

"""
import sys
import re

from argparse import ArgumentParser
from pexpect import spawn, run, EOF

class ConsoleError(Exception):
    pass

class ConsoleHandler(object):
    # only needs to be included if conserver version is older than:
    # https://github.com/conserver/conserver/commit/8cfbe1a
    # NOTE: If SERIAL_HOST is to be used, it should be put in /etc/hosts or as a DNS alias
    SERIAL_HOST = "consolehost"
    CMD_TIMEOUT = 60
    def __init__(self, device):
        self.console = spawn("/usr/local/bin/console -f devpowerctl",
            timeout=ConsoleHandler.CMD_TIMEOUT,
            echo=False
        )
        self.slot_num = self.load_slot_num(device)

    def load_slot_num(self, device):
        # port_info, status = run(f"/usr/local/bin/console -M {ConsoleHandler.SERIAL_HOST} -x {device}", withexitstatus=True)
        port_info, status = run(f"/usr/local/bin/console -x {device}", withexitstatus=True)
        if status != 0:
            raise ConsoleError(f"Couldn't get info for '{device}'. Full Response: {port_info}'")
        slot_name = r"slot(\d+)"
        device_path = r"/dev/\w+"
        hostname = r"[\w.]+"
        baud_rate = r"\d+n"
        match = re.search(f"{slot_name}\\s+on\\s+{device_path}@{hostname}\\s+at\\s+{baud_rate}", port_info.decode(sys.stdout.encoding))
        if match:
            return int(match.group(1))
        else:
            raise ConsoleError(f"Couldn't determine slot to power cycle. '{device} on {ConsoleHandler.SERIAL_HOST} should be an alias for a 'slot###' console")

    def verify(self):
        idx = self.console.expect_exact([
            "[connected]",
            "console is down"
        ])
        if idx == 1:
            raise ConsoleError("Couldn't connect to devpowerctl serial console. Ensure it is plugged in and 'up' in the conserver")
        
        self.console.sendline("?")
        self.console.expect("=== CI Relay Controller ===")

    def close(self):
        self.console.sendcontrol('e')
        self.console.send("c.")
        self.console.expect(EOF)
    
    def send_command(self, command):
        if command == "restart":
            self.send_command("turn_off")
            self.send_command("turn_on")
            return
        self.console.sendline(f"{command} {self.slot_num}")
        idx = self.console.expect_exact([
            f"Did: {command} for device",
            "Error:"
        ])

        if idx == 1:
            self.close()
            raise ConsoleError(f"'{command}' for device num '{self.slot_num}' failed on relay controller.")

    def do_command(self, command):
        assert self.slot_num is not None
        self.verify()
        self.send_command(command)
        self.close()

def parse_args():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("command", choices={"restart", "turn_on", "turn_off"},help="Operation to perform on device.")
    parser.add_argument("device", help="Device to turn be controlled.")
    return parser.parse_args()
 
def main():
    args = parse_args()
    ch = ConsoleHandler(args.device)
    ch.do_command(args.command)


if __name__ == "__main__":
    main()

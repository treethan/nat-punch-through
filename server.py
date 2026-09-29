import argparse
import datetime
import socket
import sys

DEFAULT_HOST = ''
DEFAULT_PORT = 50007
DEFAULT_TIMEOUT = 6.0

waiting_clients: list[Client] = []


class Client:
    def __init__(self, address: tuple[str, int], isHost:bool=False):
        self.address = address
        self.isHost = isHost


def server_loop(HOST: str, PORT: int, socket_timeout: float):
    print(f"[START] Beginning server start-up...")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(socket_timeout)
        try:
            s.bind((HOST, PORT))
        except OverflowError as msg:
            sys.exit(str(msg))
        except socket.error as msg:
            sys.exit(str(msg))

        print(f"[INFO] NAT punchthrough server running on UDP port {socket.gethostbyname(HOST)}:{PORT}")

        while True:
            try:
                data, address = s.recvfrom(1024)
                handle_client_message(s, data, address)

                if len(waiting_clients) >= 2:
                    c1 = waiting_clients.pop(0)
                    c2 = waiting_clients.pop(0)

                    print(f"[MATCH] Pairing {c1.address} <-> {c2.address}")

                    s.sendto(f"PEER:{c2.address[0]}:{c2.address[1]}".encode(), c1.address)
                    s.sendto(f"PEER:{c1.address[0]}:{c1.address[1]}".encode(), c2.address)
            except (socket.timeout, TimeoutError):
                try:
                    print(f"[INFO] No data received within timeout: {datetime.datetime.now()}")
                except KeyboardInterrupt:
                    # Without this except, program fails to exit gracefully
                    print("[EXIT] KeyboardInterrupt")
                    sys.exit()
            except ConnectionResetError:
                print("[ERROR] Connection was reset")
            except KeyboardInterrupt:  # TODO: Is this ever reached if interrupts are detected on timeouts?
                print("[EXIT] KeyboardInterrupt")
                sys.exit()


def handle_client_message(s: socket.socket, data: bytes, client_address: tuple[str, int]):
    try:
        msg = data.decode().strip()

        print(f"[RECV] {client_address}: {msg}")

        if msg == "CONNECT":
            # Client already exists
            if any(c.address == client_address for c in waiting_clients):
                print("[INFO] Client already exists, resending ACK")
                s.sendto(b"ACK:Connected", client_address)
                return

            # Add new client
            client = Client(client_address)
            waiting_clients.append(client)
            print(f"[INFO] Client added: {client_address}")
            print(f"[INFO] Sending ACK to {client_address}")
            s.sendto(b"ACK:Connected", client_address)
    except UnicodeDecodeError:
        print("[ERROR] Could not decode client message")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple NAT punchthrough server')
    parser.add_argument('-H','--host', default=DEFAULT_HOST,
                        help='Host/IPv4 address to bind to (default: all interfaces)')
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT,
                        help='UDP port to bind to (default: 50007)')
    parser.add_argument('-t', '--timeout', type=float, default=DEFAULT_TIMEOUT,
                        help='Socket timeout in seconds (default: 1.0)')
    args = parser.parse_args()

    server_loop(args.host, args.port, args.timeout)

import argparse
import datetime
import socket
import sys

DEFAULT_HOST = ''
DEFAULT_PORT = 50007
DEFAULT_TIMEOUT = 6.0

waiting_clients = []


class Client:
    def __init__(self, addr, host=False):
        self.address = addr
        self.isHost = host


def handle_client_message(sock, data, addr):
    try:
        msg = data.decode().strip()

        print(f"[RECV] {addr}: {msg}")
        if msg == "CONNECT":
            # Client already exists
            if any(c.address == addr for c in waiting_clients):
                print("[INFO] Client already exists, resending ACK")
                sock.sendto(b"ACK:Connected", addr)
                return

            # Add new client
            client = Client(addr)
            waiting_clients.append(client)
            print(f"[INFO] Client added: {addr}")
            sock.sendto(b"ACK:Connected", addr)
    except UnicodeDecodeError:
        print("[ERROR] Could not decode client message")




def server_loop(HOST, PORT, socket_timeout):
    print(f"[START] Beginning server start-up...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.bind((HOST, PORT))
        except OverflowError as msg:
            sys.exit(msg)
        except socket.error as msg:
            sys.exit(msg)

        s.settimeout(socket_timeout)

        h = '0.0.0.0' if HOST == '' else HOST

        print(f"[INFO] NAT punchthrough server running on UDP port {h}:{PORT}")

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
            except TimeoutError:
                print(f"[INFO] No data received within timeout: {datetime.datetime.now()}")
            except ConnectionResetError:
                print("[ERROR] Connection was reset")
            except KeyboardInterrupt:
                print("[EXIT] KeyboardInterrupt")
                sys.exit()
            


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

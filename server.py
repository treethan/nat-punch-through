import argparse
import datetime
import socket

DEFAULT_HOST = ''
DEFAULT_PORT = 50007
DEFAULT_TIMEOUT = 6.0

waiting_clients = []


class Client:
    def __init__(self, addr, host=False):
        self.address = addr
        self.isHost = host


def handle_client_message(sock, data, addr):
    msg = data.decode().strip()

    print(f"[RECV] {addr}: {msg}")
    if msg == "CONNECT":
        client = Client(addr)
        waiting_clients.append(client)
        print(f"[INFO] Client added: {addr}")
        sock.sendto(f"ACK:Connected".encode(), addr)
        
        if len(waiting_clients) >= 2:
            c1 = waiting_clients.pop(0)
            c2 = waiting_clients.pop(0)

            print(f"[MATCH] Pairing {c1.address} <-> {c2.address}")

            sock.sendto(f"PEER:{c2.address[0]}:{c2.address[1]}".encode(), c1.address)
            sock.sendto(f"PEER:{c1.address[0]}:{c1.address[1]}".encode(), c2.address) 



def server_loop(HOST, PORT, socket_timeout):
    print(f"[START] Beginning server start-up...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.bind((HOST, PORT))
        except OverflowError as msg:
            print(msg)
            exit()
        except socket.error as msg:
            print(msg)
            exit()

        s.settimeout(socket_timeout)

        h = '0.0.0.0' if HOST == '' else HOST

        print(f"[INFO] NAT punchthrough server running on UDP port {h}:{PORT}")

        while True:
            try:
                data, address = s.recvfrom(1024)
                handle_client_message(s, data, address)
            except socket.timeout or TimeoutError:
                # Allow interrupts from console
                try:
                    print(f"[INFO] No data received within timeout: {datetime.datetime.now()}")
                except KeyboardInterrupt:
                    print("[EXIT] KeyboardInterrupt")
                    exit()


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

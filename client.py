import socket
import sys
import time

HOST = '127.0.0.1'
PORT = 50007
PROBE_DELAY = 0.5
PROBE_TIMEOUT = 10
SERVER_CONNECTION_TIMEOUT = 10


def chat(sock, addr):
    print("Pairing successful. Begin chat...")
    input()


def client_loop():
    print("[START] Starting client set-up")

    peer_address = ()
    registered: bool = False

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(1.0)
        print("[INFO] Socket established")

        s.sendto(b"CONNECT", (HOST, PORT))
        print(f"[SEND] Connection request to {HOST}:{PORT}")

        connection_attempt_start_time = time.monotonic()

        while True:
            if not registered and time.monotonic() - connection_attempt_start_time >= SERVER_CONNECTION_TIMEOUT:
                sys.exit("[EXIT] Connection to server timed out")
            try:
                data, address = s.recvfrom(1024)
                if address != (HOST, PORT):  # Filter non-server
                    continue
                msg = data.decode().strip().split(":")  # For example, "PEER:127.0.0.1:51234"
                if msg[0] == "ACK":
                    print(f"[RECV] Server ACK at {address}")
                    registered = True
                elif msg[0] == "PEER":
                    print(f"[RECV] Peer at {msg[1]}:{msg[2]}")
                    peer_address = (msg[1], int(msg[2]))
                    break
            except TimeoutError:
                # Allow interrupts from console, and resend server connection if necessary
                if not registered:
                    s.sendto(b"CONNECT", (HOST, PORT))
            except ConnectionResetError:
                pass
            except IndexError:
                pass
            except ValueError:
                print("[ERROR] Bad bytes or bad port")
            except KeyboardInterrupt:
                print("[EXIT] KeyboardInterrupt")
                sys.exit()

        print("[INFO] Beginning punchthrough")
        s.settimeout(0.25)
        print("[SEND] PUNCH")
        s.sendto(b"PUNCH", peer_address)
        last_send_time = time.monotonic()
        punch_start_time = time.monotonic()

        while True:
            if time.monotonic() - punch_start_time >= PROBE_TIMEOUT:
                sys.exit("[EXIT] Unable to establish connection with peer")
            if time.monotonic() - last_send_time >= PROBE_DELAY:
                print("[SEND] PUNCH")
                s.sendto(b"PUNCH", peer_address)
                last_send_time = time.monotonic()
            
            try:
                data, address = s.recvfrom(1024)
                if address != peer_address:  # Filter non-peers
                    continue
                msg = data.decode().strip().split(":")
                if msg[0] == "PUNCH":
                    print("[SEND] PUNCH_ACK")
                    s.sendto(b"PUNCH_ACK", peer_address)
                elif msg[0] == "PUNCH_ACK":
                    print("[RECV] PUNCH_ACK received")
                    break
            except TimeoutError:
                pass
            except ConnectionResetError:
                pass
            except IndexError:
                pass
            except ValueError:
                print("[ERROR] Bad bytes or bad port")
            except KeyboardInterrupt:
                print("[EXIT] KeyboardInterrupt")
                sys.exit()

        chat(s, peer_address)


if __name__ == "__main__":
    client_loop()

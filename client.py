import socket
import sys
import threading
import time

HOST = '127.0.0.1'
PORT = 50007
PROBE_DELAY = 0.5
PROBE_TIMEOUT = 10
SERVER_CONNECTION_TIMEOUT = 10


def chat_receiver(s: socket.socket, addr: tuple[str, int], stop: threading.Event):
    while True:
        if stop.is_set():
            return

        try:
            data, address = s.recvfrom(1024)
            if address != addr:  # Filter non-peer
                continue
            msg = data.decode().split(":", 1)  # "CHAT:Hello world!"
            if msg[0] == "CHAT":
                print(f"[MESSAGE] {msg[1]}")
            elif msg[0] == "PUNCH":
                s.sendto(b"PUNCH_ACK", addr)
            elif msg[0] == "BYE":
                print("[EXIT] Peer has left the chat")
                stop.set()
        except TimeoutError:
            pass
        except ConnectionResetError:
            pass
        except ValueError:
            pass
        except IndexError:
            pass
        except Exception as e:
            print(f"[ERROR] {e}")
            stop.set()


def chat(sock: socket.socket, addr):
    print("[INFO] Pairing successful. Begin chatting:")
    stop_event = threading.Event()
    t = threading.Thread(target=chat_receiver, args=(sock, addr, stop_event), daemon=True)
    t.start()

    while True:
        if stop_event.is_set():
            break
        try:
            i: str = input()
            if stop_event.is_set():
                break
            if i == "/quit":
                sock.sendto(b"BYE", addr)
                stop_event.set()
                break
            if i == "":
                continue
            i = "CHAT:" + i
            sock.sendto(i.encode(), addr)
        except (KeyboardInterrupt, EOFError):
            print("[INFO] Input closed")
            sock.sendto(b"BYE", addr)
            stop_event.set()
            break
        except ConnectionResetError:
            pass
    
    t.join()
    sys.exit()


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

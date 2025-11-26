import socket

HOST = 'localhost'
PORT = 50007


def chat(addr):
    pass


def client_loop():
    print("[START] Starting client set-up")

    peer_address = ()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(1.0)
        print("[INFO] Socket established")

        s.connect((HOST, PORT))
        print(f"[INFO] Connected to {HOST} on port {PORT}")

        s.sendall(b"CONNECT")

        print("[INFO] Awaiting peer from server")

        while True:
            try:
                data, server_address = s.recvfrom(1024)
                msg = data.decode().strip().split(":")
                if msg[0] == "PEER":
                    print(f"[RECV] Peer at {msg[1]}:{msg[2]}")
                    peer_address = (msg[1], msg[2])
                    break
            except TimeoutError:
                pass  # Allow interrupts from console
            except KeyboardInterrupt:
                print("[EXIT]")
                break
    
    if peer_address != ():
        chat(peer_address)


if __name__ == "__main__":
    client_loop()

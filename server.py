import socket

waiting_clients = []

class Client:
    def __init__(self, addr):
        self.address = addr


def handle_client_message(sock, data, addr):
    msg = data.decode().strip()

    print(f"[RECV] {addr}: {msg}")
    if msg == "CONNECT":
        client = Client(addr)
        waiting_clients.append(client)
        print(f"[INFO] Client added: {addr}")
        
        if len(waiting_clients) >= 2:
            c1 = waiting_clients.pop(0)
            c2 = waiting_clients.pop(0)

            print(f"[MATCH] Pairing {c1.address} <-> {c2.address}")

            sock.sendto(f"PEER:{c2.address[0]}:{c2.address[1]}".encode(), c1.address)
            sock.sendto(f"PEER:{c1.address[0]}:{c1.address[1]}".encode(), c2.address) 



def server_loop():
    print(f"[START] Beginning server start-up")

    HOST = ''
    PORT = 50007

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))
        s.settimeout(1.0)

        print(f"[INFO] NAT punchthrough server running on UDP port {PORT}")

        while True:
            try:
                data, address = s.recvfrom(1024)
                handle_client_message(s, data, address)
            except TimeoutError:
                pass  # Allow interrupts from console
            except KeyboardInterrupt:
                print("[EXIT]")
                break


if __name__ == '__main__':
    server_loop()

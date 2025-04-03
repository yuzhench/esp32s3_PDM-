import socket

def main():
    HOST = ''         # Listen on all available network interfaces
    PORT = 1234       # Port to listen on (must match the ESP32 configuration)

    # Create a TCP/IP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Bind the socket to the host and port
        s.bind((HOST, PORT))
        # Listen for incoming connections (allowing 1 connection in the backlog)
        s.listen(1)
        print(f"Server listening on port {PORT}...")

        while True:
            # Wait for a connection
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    # Receive data from the client (max 1024 bytes)
                    data = conn.recv(1024)
                    if not data:
                        print(f"Connection with {addr} closed.")
                        break
                    # Decode and print the received data
                    print("Received:", data.decode())
                    # Optionally, send a response back to the client (e.g., "ACK")
                    conn.sendall(b"ACK")

if __name__ == '__main__':
    main()

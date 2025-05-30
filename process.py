import socket
import sys
import time
from datetime import datetime

def get_simulated_time(offset):
    return time.time() + offset

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def main():
    if len(sys.argv) < 3:
        print("Uso: python process.py <coordinator_ip> <offset_segundos>")
        return

    host = sys.argv[1]
    offset = float(sys.argv[2])
    port = 5000

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))

        msg = client.recv(1024)
        if msg.decode() == 'REQUEST_TIME':
            local_time = get_simulated_time(offset)
            log(f"Relógio local (com offset): {datetime.fromtimestamp(local_time).strftime('%H:%M:%S')}")
            client.sendall(str(local_time).encode())

            ajuste = float(client.recv(1024).decode())
            novo_tempo = local_time + ajuste
            log(f"Ajuste recebido: {ajuste:.2f} segundos")
            log(f"Novo tempo ajustado: {datetime.fromtimestamp(novo_tempo).strftime('%H:%M:%S')}")

        client.close()
    except Exception as e:
        log(f"Erro: {e}")

if __name__ == "__main__":
    main()
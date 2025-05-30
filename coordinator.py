import socket
import threading
from datetime import datetime

HOST = '0.0.0.0'
PORT = 5000
NUM_CLIENTS = 3  # Altere para 5 no laboratório

received_times = []
connections = []

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def handle_client(conn, addr):
    log(f"Conectado a {addr}")
    try:
        conn.sendall(b'REQUEST_TIME')
        data = conn.recv(1024)
        local_time = float(data.decode())
        log(f"Tempo recebido de {addr}: {datetime.fromtimestamp(local_time).strftime('%H:%M:%S')}")
        received_times.append((conn, local_time))
    except:
        log(f"Erro ao comunicar com {addr}")
        conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(NUM_CLIENTS)
    log(f"Aguardando {NUM_CLIENTS} conexões...")

    threads = []
    for _ in range(NUM_CLIENTS):
        conn, addr = server.accept()
        connections.append(conn)
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    if not received_times:
        log("Nenhum tempo recebido.")
        return

    # Calcular média
    tempos = [t[1] for t in received_times]
    media = sum(tempos) / len(tempos)
    log(f"Média calculada: {datetime.fromtimestamp(media).strftime('%H:%M:%S')}")

    # Enviar ajuste
    for conn, tempo in received_times:
        ajuste = media - tempo
        conn.sendall(str(ajuste).encode())
        conn.close()

    server.close()
    log("Sincronização finalizada.")

if __name__ == "__main__":
    main()
import socket
import threading
import time
from datetime import datetime
import argparse
import statistics

received_offsets = []
connections = []
received_lock = threading.Lock()


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def handle_client(conn, addr):
    log(f"Conectado a: {addr}")
    try:
        conn.settimeout(10.0)
        t0 = time.time()
        conn.sendall(b"REQUEST_TIME")

        data = conn.recv(1024)
        t2 = time.time()

        client_time = float(data.decode())
        rtt = t2 - t0
        coord_midpoint = t0 + rtt / 2
        offset = client_time - coord_midpoint

        log(f"t0: {t0:.3f}, t2: {t2:.3f}, RTT: {rtt:.3f}s")
        log(
            f"Horário cliente: {datetime.fromtimestamp(client_time).strftime('%H:%M:%S')}"
        )
        log(f"Offset estimado (com RTT/2): {offset:+.3f}s")

        with received_lock:
            received_offsets.append((conn, offset))
    except socket.timeout:
        log(f"[TIMEOUT] Cliente {addr} não respondeu a tempo.")
        conn.close()
    except Exception as e:
        log(f"Erro ao se comunicar com {addr}: {e}")
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Coordenador do algoritmo de Berkeley")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--clients", type=int, default=5)
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((args.host, args.port))
    server.listen(args.clients)
    log(f"Escutando {args.host}:{args.port}, aguardando {args.clients} clientes")

    threads = []
    timeout_accept = 15
    start_time = time.time()

    while len(connections) < args.clients and time.time() - start_time < timeout_accept:
        server.settimeout(1.0)
        try:
            conn, addr = server.accept()
            connections.append(conn)
            t = threading.Thread(target=handle_client, args=(conn, addr))
            t.start()
            threads.append(t)
        except socket.timeout:
            continue

    for t in threads:
        t.join()

    if not received_offsets:
        log("Nenhum cliente respondeu a tempo.")
        return

    # Extrai os offsets e adiciona o do coordenador (0)
    offsets = [offset for _, offset in received_offsets]
    offsets.append(0.0)  # coordenador
    log(f"Offset do coordenador (0.000s) incluído no cálculo")

    if len(offsets) > 1:
        mean = statistics.mean(offsets)
        stdev = statistics.stdev(offsets)
        filtered = [
            (conn, o) for conn, o in received_offsets if abs(o - mean) <= 2 * stdev
        ]
        log(f"Outliers removidos: {len(received_offsets) - len(filtered)}")
    else:
        filtered = received_offsets

    if not filtered:
        log("Todos os offsets foram descartados como outliers.")
        return

    # Recalcular média com offsets filtrados + coordenador
    final_offsets = [o for _, o in filtered] + [0.0]
    offset_medio = statistics.mean(final_offsets)
    log(f"Offset médio final: {offset_medio:+.3f} segundos")

    for conn, o in filtered:
        try:
            adjustment = offset_medio - o
            conn.sendall(str(adjustment).encode())
            time.sleep(0.1)
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
        except:
            log("Erro ao enviar ajuste ao cliente.")

    server.close()
    log("Sincronização concluída com sucesso.")


if __name__ == "__main__":
    main()

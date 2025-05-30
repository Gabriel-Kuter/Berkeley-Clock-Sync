import socket
import threading
import time
from datetime import datetime
import argparse
import statistics

received_times = []
connections = []

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def handle_client(conn, addr):
    log(f"Conectado a: {addr}")
    try:
        conn.settimeout(10.0)  # sets a 10 second timeout after connection has been estabilished
        conn.sendall(b'REQUEST_TIME')
        data = conn.recv(1024)
        local_time = float(data.decode())
        log(f"Recebeu o horário de {addr}: {datetime.fromtimestamp(local_time).strftime('%H:%M:%S')}")
        received_times.append((conn, local_time))
    except socket.timeout:
        log(f"[TIMEOUT] Cliente {addr} não respondeu a tempo.")
        conn.close()
    except:
        log(f"Erro ao se comunicar com {addr}")
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Berkeley Clock Coordinator")
    parser.add_argument('--host', type=str, default='0.0.0.0', help='IP do host para se conectar (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port para realizar o listen (default: 5000)')
    parser.add_argument('--clients', type=int, default=5, help='Número de clientes esperados (default: 5)')
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((args.host, args.port))
    server.listen(args.clients)
    log(f"Esperando por {args.clients} conexões em {args.host}:{args.port}...")

    threads = []
    start_time = time.time()
    timeout_accept = 15  # waits 15 seconds for the expected number of clients to connect
    log(f"Aguardando até {args.clients} clientes por até {timeout_accept} segundos...")
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

    # counts successful responses vs expected responses
    num_responded = len(received_times)
    num_expected = args.clients
    num_connected = len(connections)
    num_failed = num_expected - num_responded
    log(f"Clientes conectados: {num_connected}/{num_expected}")    
    if num_connected < num_expected:
        log(f"{num_failed} cliente(s) não se conectaram.")

    if not received_times:
        log("Nenhum horário recebido.")
        return

    times = [t[1] for t in received_times]
    mean = statistics.mean(times)
    if len(times) > 1:
        stdev = statistics.stdev(times)
        filtered = [(conn, t) for conn, t in received_times if abs(t - mean) <= 2 * stdev]
        log(f"Filtrando outliers: {len(received_times) - len(filtered)} removidos")
    else:
        filtered = received_times

    if not filtered:
        log("Todos os tempos foram descartados como outliers.")
        return
    
    filtered_times = [t for _, t in filtered]
    final_mean = statistics.mean(filtered_times)
    log(f"Média final (ajustada): {datetime.fromtimestamp(final_mean).strftime('%H:%M:%S')}")

    for conn, t in filtered:
        adjustment = final_mean - t
        try:
            conn.sendall(str(adjustment).encode())
            time.sleep(0.1) 
            conn.close()
        except:
            log("Erro ao enviar o ajuste.")
    
    server.close()
    log("Sincronização de relógios concluída!")

if __name__ == "__main__":
    main()

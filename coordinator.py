import socket
import threading
import time
from datetime import datetime
import argparse
import statistics
import os
import csv

"""
Coordenador do Algoritmo de Berkeley para sincronização de relógios em sistemas distribuídos.
Aceita conexões de múltiplos clientes, calcula offsets relativos e envia ajustes baseados na média dos tempos.
Do ponto de vista da literatura, representa o 'Master'
"""

# Armazena offsets recebidos dos clientes
received_offsets = []

# Lista de conexões ativas
connections = []

# Lock para  acesso seguro às listas em threads paralelas
received_lock = threading.Lock()


def log(msg):
    """Imprime mensagem com timestamp formatado."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def persist_offset(offset: float):
    """
    Salva o offset atual do coordenador em arquivo local (coordinator.txt)
    e atualiza o histórico de ciclos no CSV (coordinator.csv)
    """
    try:
        with open("offset_coordinator.txt", "w") as f:
            f.write(f"{offset:+.3f}")
    except Exception as e:
        log(f"[Coordenador] Erro ao salvar offset: {e}")

    try:
        csv_path = "offset_coordinator.csv"
        file_exists = os.path.isfile(csv_path)
        next_cycle = 1
        if file_exists:
            with open(csv_path, "r") as f:
                last_line = list(csv.reader(f))[-1]
                next_cycle = int(last_line[0]) + 1
        with open(csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["cycle", "offset"])
            writer.writerow([next_cycle, round(offset, 6)])
    except Exception as e:
        log(f"[Coordenador] Erro ao gravar CSV: {e}")


def handle_client(conn, addr):
    """
    Lida com um cliente conectado:
    - Solicita o horário atual do cliente
    - Calcula o offset com base no RTT
    - Armazena o offset para posterior ajuste
    """

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
    """
    Função principal do coordenador:
    - Cria socket servidor e aguarda conexões
    - Inicia threads para cada cliente conectado
    - Coleta offsets e calcula média
    - Remove outliers e envia ajustes aos clientes
    - Aplica ajuste no próprio relógio e persiste valor
    """
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
    timeout_accept = 15  # Tempo total para aceitar as conexões
    start_time = time.time()

    # Aceita conexões até o número de clientes esperado ou até o tempo limite
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

    # Espera todas as threads terminarem
    for t in threads:
        t.join()

    if not received_offsets:
        log("Nenhum cliente respondeu a tempo.")
        return

    # Extrai os offsets dos clientes e adiciona o do coordenador (para esta demonstração, considerado como 0.0)
    offsets = [offset for _, offset in received_offsets]
    offsets.append(0.0)  # coordenador
    log(f"Offset do coordenador (0.000s) incluído no cálculo")

    # Remove outliers: offsets fora de 1 desvio padrão
    if len(offsets) > 1:
        mean = statistics.mean(offsets)
        stdev = statistics.stdev(offsets)
        filtered = [(conn, o) for conn, o in received_offsets if abs(o - mean) <= stdev]
        log(f"Outliers removidos: {len(received_offsets) - len(filtered)}")
    else:
        filtered = received_offsets

    if not filtered:
        log("Todos os offsets foram descartados como outliers.")
        return

    # Recalcula offset médio com clientes filtrados + coordenador
    final_offsets = [o for _, o in filtered] + [0.0]
    offset_medio = statistics.mean(final_offsets)
    log(f"Offset médio final: {offset_medio:+.3f} segundos")

    # Aplica o ajuste ao próprio coordenador e salva
    adjusted_time = time.time() + offset_medio
    log(f"Relógio do coordenador ajustado em {offset_medio:+.3f}s")
    log(
        f"Novo horário do coordenador: {datetime.fromtimestamp(adjusted_time).strftime('%H:%M:%S')}"
    )
    persist_offset(offset_medio)

    # Envia o ajuste calculado para cada cliente
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

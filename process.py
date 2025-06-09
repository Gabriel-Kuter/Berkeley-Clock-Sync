import socket
import argparse
import time
import os
import csv
from datetime import datetime


def get_simulated_time(offset):
    return time.time() + offset


def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def load_offset(process_id: str, base_offset: float) -> float:
    filename = f"offset_{process_id}.txt"
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return float(f.read().strip())
        except:
            log(
                f"[Processo {process_id}] Erro ao carregar offset salvo, usando offset base."
            )
    return base_offset


def persist_offset(process_id: str, offset: float):
    try:
        with open(f"offset_{process_id}.txt", "w") as f:
            f.write(f"{offset:+.3f}")
    except Exception as e:
        log(f"[Processo {process_id}] Erro ao salvar offset: {e}")


def get_next_cycle_number(process_id: str) -> int:
    csv_path = f"offset_{process_id}.csv"
    if not os.path.exists(csv_path):
        return 1
    try:
        with open(csv_path, "r") as f:
            last_line = list(csv.reader(f))[-1]
            return int(last_line[0]) + 1
    except:
        return 1


def append_cycle_csv(process_id: str, cycle: int, offset: float):
    csv_path = f"offset_{process_id}.csv"
    try:
        file_exists = os.path.isfile(csv_path)
        with open(csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["cycle", "offset"])
            writer.writerow([cycle, round(offset, 6)])
    except Exception as e:
        log(f"[Processo {process_id}] Erro ao gravar CSV: {e}")


def main():
    parser = argparse.ArgumentParser(description="Cliente do algoritmo de Berkeley")
    parser.add_argument("--host", type=str, required=True, help="IP do coordenador")
    parser.add_argument("--port", type=int, default=5000, help="Porta do coordenador")
    parser.add_argument(
        "--offset", type=float, default=0, help="Offset inicial do relógio local"
    )
    parser.add_argument(
        "--id", type=str, default="N/A", help="Identificador do processo"
    )
    args = parser.parse_args()

    current_offset = load_offset(args.id, args.offset)
    cycle = get_next_cycle_number(args.id)

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((args.host, args.port))

        message = client_socket.recv(1024)
        if message.decode() == "REQUEST_TIME":
            local_time = get_simulated_time(current_offset)
            log(
                f"[Processo {args.id}] Horário local (offset {current_offset:+.3f}s): {datetime.fromtimestamp(local_time).strftime('%H:%M:%S')}"
            )
            client_socket.sendall(str(local_time).encode())

            response = client_socket.recv(1024).decode().strip()
            if response:
                adjustment = float(response)
                current_offset += adjustment
                adjusted_time = get_simulated_time(current_offset)

                log(f"[Processo {args.id}] Ajuste recebido: {adjustment:+.3f} segundos")
                log(
                    f"[Processo {args.id}] Novo horário ajustado: {datetime.fromtimestamp(adjusted_time).strftime('%H:%M:%S')}"
                )

                persist_offset(args.id, current_offset)
                append_cycle_csv(args.id, cycle, current_offset)
            else:
                log(f"[Processo {args.id}] Nenhum ajuste recebido do coordenador.")

        client_socket.shutdown(socket.SHUT_RDWR)
        client_socket.close()

    except Exception as error:
        log(f"[Processo {args.id}] Erro na conexão ou execução: {error}")


if __name__ == "__main__":
    main()

import socket
import argparse
import time
from datetime import datetime

def get_simulated_time(offset):
    return time.time() + offset

def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def main():
    parser = argparse.ArgumentParser(description="Processo cliente do algoritmo de Berkeley")
    parser.add_argument('--host', type=str, required=True, help='IP do coordenador')
    parser.add_argument('--port', type=int, default=5000, help='Porta do coordenador (padrão: 5000)')
    parser.add_argument('--offset', type=float, default=0, help='Desvio do relógio local em segundos')
    parser.add_argument('--id', type=str, default='N/A', help='Identificador do processo')
    args = parser.parse_args()

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((args.host, args.port))

        message = client_socket.recv(1024)
        if message.decode() == 'REQUEST_TIME':
            local_time = get_simulated_time(args.offset)
            log(f"[Processo {args.id}] Relógio local (offset {args.offset:+.1f}s): {datetime.fromtimestamp(local_time).strftime('%H:%M:%S')}")
            client_socket.sendall(str(local_time).encode())

            response = client_socket.recv(1024).decode().strip()
            if response:
                adjustment = float(response)
                adjusted_time = local_time + adjustment
                log(f"[Processo {args.id}] Ajuste recebido: {adjustment:+.2f} segundos")
                log(f"[Processo {args.id}] Novo horário ajustado: {datetime.fromtimestamp(adjusted_time).strftime('%H:%M:%S')}")
            else:
                log(f"[Processo {args.id}] Nenhum ajuste recebido do coordenador.")

        client_socket.close()

    except Exception as error:
        log(f"[Processo {args.id}] Erro na conexão ou execução: {error}")

if __name__ == "__main__":
    main()
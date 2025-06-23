import socket
import argparse
import time
import os
import csv
from datetime import datetime

"""
Cliente (processo) do Algoritmo de Berkeley para sincronização de relógios em sistemas distribuídos.
Realiza a conexão ao coordenador, envia o seu offset, recebe o ajuste e realiza a correção.
Do ponto de vista da literatura, representa o 'Slave'
"""


def get_simulated_time(offset):
    """
    Retorna o horário atual simulado com o offset aplicado.

    :param offset: Deslocamento do relógio local em relação ao tempo real.
    :return: timestamp ajustado com o offset.
    """
    return time.time() + offset


def log(message):
    """Exibe mensagens no console com timestamp atual."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def load_offset(process_id: str, base_offset: float) -> float:
    """
    Carrega o offset salvo em arquivo, caso exista. Função especificamente para demonstração didática (local)
    do algoritmo. Ou seja, não é estritamente necessária para o funcionamento distribuído

    :param process_id: ID do processo (cliente).
    :param base_offset: Offset padrão caso o arquivo não exista ou falhe.
    :return: Offset carregado ou o valor padrão.
    """
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
    """
    Salva o offset atual em arquivo local para uso em futuros ciclos.
    Função especificamente para demonstração didática (local)

    :param process_id: ID do processo.
    :param offset: Valor do offset a ser salvo.
    """
    try:
        with open(f"offset_{process_id}.txt", "w") as f:
            f.write(f"{offset:+.3f}")
    except Exception as e:
        log(f"[Processo {process_id}] Erro ao salvar offset: {e}")


def get_next_cycle_number(process_id: str) -> int:
    """
    Determina o número do próximo ciclo com base no último salvo no CSV.
    Função especificamente para demonstração didática (local)

    :param process_id: ID do processo.
    :return: Número do próximo ciclo.
    """
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
    """
    Registra no CSV o offset atualizado de cada ciclo de sincronização.

    :param process_id: ID do processo.
    :param cycle: Número do ciclo atual.
    :param offset: Offset ajustado após sincronização.
    """

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
    """
    Método principal do cliente:
    - Conecta ao coordenador via socket TCP
    - Envia o horário local (simulado com offset)
    - Recebe o ajuste calculado e aplica ao seu offset
    - Salva o novo offset para uso futuro
    """
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

        # Se for a mensagem esperada, envia o horário local simulado
        if message.decode() == "REQUEST_TIME":
            # Calcula o horário local atual com offset
            local_time = get_simulated_time(current_offset)

            # Exibe o horário local no log
            log(
                f"[Processo {args.id}] Horário local (offset {current_offset:+.3f}s): {datetime.fromtimestamp(local_time).strftime('%H:%M:%S')}"
            )

            # Envia o horário local simulado ao coordenador
            client_socket.sendall(str(local_time).encode())

            # Aguarda o valor de ajuste do coordenador
            response = client_socket.recv(1024).decode().strip()
            if response:

                # Converte o valor recebido e atualiza o offset local
                adjustment = float(response)
                current_offset += adjustment

                # Calcula o novo horário ajustado
                adjusted_time = get_simulated_time(current_offset)

                # Exibe os logs do ajuste e novo horário
                log(f"[Processo {args.id}] Ajuste recebido: {adjustment:+.3f} segundos")
                log(
                    f"[Processo {args.id}] Novo horário ajustado: {datetime.fromtimestamp(adjusted_time).strftime('%H:%M:%S')}"
                )
                # Persiste o novo offset em um arquivo .txt
                persist_offset(args.id, current_offset)
                # Registra o ciclo e o novo offset em um arquivo .csv
                append_cycle_csv(args.id, cycle, current_offset)
            else:
                # No caso de não haver recebido ajuste do coordenador
                log(f"[Processo {args.id}] Nenhum ajuste recebido do coordenador.")

        # Após o processo ser realizado, fecha a conexão
        client_socket.shutdown(socket.SHUT_RDWR)
        client_socket.close()

    except Exception as error:
        log(f"[Processo {args.id}] Erro na conexão ou execução: {error}")


if __name__ == "__main__":
    main()

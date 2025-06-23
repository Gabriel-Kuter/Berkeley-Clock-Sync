import subprocess
import time
import csv
import os

"""
Script auxiliar para demonstrar didaticamente o Algoritmo de Berkeley para sincronização de relógios.
Essencialmente, automatiza o processo de envio e ajuste de offsets, de forma que, no dashboard,
haja uma experiência bem orgânica/prática de visualização. Ainda utiliza exatamente o mesmo algoritmo da
versão distribuída.
"""
NUM_CICLOS = 30
NUM_CLIENTES = 5
PROCESS_IDS = [f"P{i+1}" for i in range(NUM_CLIENTES)]
HOST = "127.0.0.1"
PORT = "5000"

offsets_iniciais = {
    "P1": 16.0,
    "P2": -6.0,
    "P3": 12.5,
    "P4": -10.5,
    "P5": 2.0,
}


def registrar_offset_inicial(pid, offset):
    """
    Cria o arquivo CSV de offset para o processo com o valor inicial (ciclo 0)

    :param pid: ID do processo (ex: "P1")
    :param offset: Offset inicial a ser registrado
    """
    csv_path = f"offset_{pid}.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["cycle", "offset"])
        writer.writerow([0, round(offset, 6)])


def run_coordinator():
    """
    Inicia o processo do coordenador como subprocesso, escutando o número esperado de clientes.

    :return: Popen do coordenador
    """
    return subprocess.Popen(
        [
            "python",
            "coordinator.py",
            "--host",
            HOST,
            "--port",
            PORT,
            "--clients",
            str(NUM_CLIENTES),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_client(pid, offset=None):
    """
    Inicia um cliente (processo) como subprocesso.
    Se for o primeiro ciclo, envia o offset inicial.

    :param pid: ID do processo (ex: "P1")
    :param offset: Offset inicial opcional
    :return: Popen do cliente
    """
    cmd = ["python", "process.py", "--host", HOST, "--port", PORT, "--id", pid]
    if offset is not None:
        cmd += ["--offset", str(offset)]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main():
    """
    Executa a simulação de vários ciclos do algoritmo de Berkeley:
    - Para cada ciclo, roda o coordenador e todos os clientes
    - Aguarda todos finalizarem
    - Registra progresso no terminal
    """
    print(
        f"⏳ Iniciando {NUM_CICLOS} ciclos de sincronização com {NUM_CLIENTES} clientes...\n"
    )
    # Grava ciclo 0 com offset inicial

    for pid in PROCESS_IDS:
        offset = offsets_iniciais.get(pid, 0.0)
        registrar_offset_inicial(pid, offset)

    for ciclo in range(1, NUM_CICLOS + 1):
        print(f"--- Ciclo {ciclo} ---")

        coord_proc = run_coordinator()

        clientes = []
        for pid in PROCESS_IDS:
            offset = offsets_iniciais.get(pid) if ciclo == 1 else None
            clientes.append(run_client(pid, offset))

        for proc in clientes:
            proc.wait()
        coord_proc.wait()

        print(f"✓ Ciclo {ciclo} concluído\n")
        time.sleep(2)

    print("✅ Todos os ciclos finalizados.")


if __name__ == "__main__":
    main()

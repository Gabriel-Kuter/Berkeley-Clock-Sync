import subprocess
import time
import csv
import os

NUM_CICLOS = 30
NUM_CLIENTES = 5
PROCESS_IDS = [f"P{i+1}" for i in range(NUM_CLIENTES)]
HOST = "127.0.0.1"
PORT = "5000"

# Valores mais extremos para tornar a convergência visual mais perceptível
offsets_iniciais = {
    "P1": 8.0,
    "P2": -6.0,
    "P3": 3.5,
    "P4": -5.5,
    "P5": 2.0,
}


def registrar_offset_inicial(pid, offset):
    csv_path = f"offset_{pid}.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["cycle", "offset"])
        writer.writerow([0, round(offset, 6)])


def run_coordinator():
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
    cmd = ["python", "process.py", "--host", HOST, "--port", PORT, "--id", pid]
    if offset is not None:
        cmd += ["--offset", str(offset)]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main():
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
        time.sleep(1.5)

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

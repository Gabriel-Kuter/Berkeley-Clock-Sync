import subprocess
import time

NUM_CICLOS = 30
NUM_CLIENTES = 3
PROCESS_IDS = ["P1", "P2", "P3"]
HOST = "127.0.0.1"
PORT = "5000"


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
    print(f"⏳ Iniciando {NUM_CICLOS} ciclos de sincronização...\n")

    # Apenas no primeiro ciclo, passamos offset inicial
    offsets_iniciais = {"P1": 5.0, "P2": -3.0, "P3": 1.5}

    for ciclo in range(1, NUM_CICLOS + 1):
        print(f"--- Ciclo {ciclo} ---")

        coord_proc = run_coordinator()
        time.sleep(1.5)  # tempo para coordenador inicializar

        clientes = []
        for pid in PROCESS_IDS:
            offset = offsets_iniciais[pid] if ciclo == 1 else None
            clientes.append(run_client(pid, offset))

        for proc in clientes:
            proc.wait()
        coord_proc.wait()

        print(f"✓ Ciclo {ciclo} concluído\n")
        time.sleep(2)

    print("✅ Todos os ciclos finalizados.")


if __name__ == "__main__":
    main()

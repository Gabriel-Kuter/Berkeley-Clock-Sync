import glob
import csv
import matplotlib.pyplot as plt


def ler_dados():
    dados = {}
    for arquivo in glob.glob("offset_*.csv"):
        processo = arquivo.replace("offset_", "").replace(".csv", "")
        ciclos, offsets = [], []
        try:
            with open(arquivo, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ciclos.append(int(row["cycle"]))
                    offsets.append(float(row["offset"]))
            dados[processo] = (ciclos, offsets)
        except Exception as e:
            print(f"Erro ao ler {arquivo}: {e}")
    return dados


def plotar(dados):
    plt.figure()
    for processo, (ciclos, offsets) in dados.items():
        plt.plot(ciclos, offsets, marker="o", label=f"Processo {processo}")
    plt.xlabel("Ciclo de Sincronização")
    plt.ylabel("Offset acumulado (s)")
    plt.title("Convergência dos Relógios - Algoritmo de Berkeley")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("grafico_offsets.png")
    plt.show()


if __name__ == "__main__":
    dados = ler_dados()
    if not dados:
        print("Nenhum arquivo offset_*.csv encontrado.")
    else:
        plotar(dados)

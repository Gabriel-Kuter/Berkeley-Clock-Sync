# offsets.py
import glob


def main():
    arquivos = glob.glob("offset_*.txt")
    if not arquivos:
        print("Nenhum offset salvo encontrado.")
        return

    print("Histórico de offsets aplicados:")
    for arquivo in sorted(arquivos):
        try:
            with open(arquivo, "r") as f:
                valor = f.read().strip()
                print(f"{arquivo}: {valor} segundos")
        except Exception as e:
            print(f"Erro ao ler {arquivo}: {e}")


if __name__ == "__main__":
    main()

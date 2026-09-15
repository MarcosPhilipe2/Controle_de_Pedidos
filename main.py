"""Controle de Pedidos — versão empresa: ponto de entrada da aplicação.

Basta executar este arquivo (duplo clique ou `python main.py`) para abrir a
interface gráfica. Na primeira vez que ninguém tiver feito isso ainda, a tela
inicial pede para criar o usuário administrador.
"""

from pathlib import Path


def main():
    try:
        import tkinter
    except ImportError:
        print(
            "Não foi possível abrir a interface gráfica porque o módulo 'tkinter' "
            "não está instalado neste Python."
        )
        print("- Windows/Mac (instalador oficial python.org): o tkinter já vem incluído;")
        print("  reinstale marcando a opção 'tcl/tk and IDLE' se tiver removido.")
        print("- Linux (Debian/Ubuntu): rode 'sudo apt install python3-tk' e tente de novo.")
        raise SystemExit(1)

    import gui

    print(f"Controle de Pedidos — versão {gui.VERSAO}")
    print(f"Arquivo executado: {Path(__file__).resolve()}")
    gui.iniciar()


if __name__ == "__main__":
    main()

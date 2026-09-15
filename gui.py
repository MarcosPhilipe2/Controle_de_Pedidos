"""Interface gráfica (Tkinter) do Controle de Pedidos — versão empresa.

Fluxo: se ainda não existe nenhum usuário no banco, a primeira tela pede para
criar o administrador inicial. Depois disso, todo acesso passa por login, e o
que cada pessoa pode fazer depende do papel (admin ou operador).

Este arquivo também define a "identidade visual" do app: uma paleta de cores,
um estilo ttk único e botões com efeito de destaque ao passar o mouse (hover),
para dar uma sensação mais moderna e interativa do que os widgets padrão do
Tkinter.
"""

import tkinter as tk
from datetime import date
from tkinter import font as tkfont
from tkinter import messagebox, ttk

import auth
import db
import pedidos_repositorio as repo
from regras_pedidos import STATUS_DISPONIVEIS, converter_data_consulta, interpretar_data_cadastro


VERSAO = "1.2.0"
TITULO_JANELA = f"📦 Controle de Pedidos — Empresa (v{VERSAO})"


# ========================================================================== #
# Paleta de cores e estilo visual
# ========================================================================== #

COR_FUNDO = "#eef1f8"
COR_CARTAO = "#ffffff"
COR_BORDA = "#dbe2ef"

COR_PRIMARIA = "#4f46e5"
COR_PRIMARIA_ESCURA = "#3f37c9"
COR_SECUNDARIA = "#0ea5e9"
COR_SECUNDARIA_ESCURA = "#0284c7"

COR_TEXTO = "#1e293b"
COR_TEXTO_SUAVE = "#64748b"
COR_TEXTO_CLARO = "#ffffff"

COR_SUCESSO = "#16a34a"
COR_SUCESSO_ESCURA = "#0f7a34"
COR_SUCESSO_CLARA = "#dcfce7"

COR_ALERTA = "#d97706"
COR_ALERTA_ESCURA = "#b45f04"
COR_ALERTA_CLARA = "#fef3c7"

COR_INFO = "#2563eb"
COR_INFO_ESCURA = "#1d4ed8"
COR_INFO_CLARA = "#dbeafe"

COR_PERIGO = "#dc2626"
COR_PERIGO_ESCURA = "#b91c1c"
COR_PERIGO_CLARA = "#fee2e2"

COR_NEUTRO = "#e2e8f0"
COR_NEUTRO_ESCURO = "#cbd5e1"

FONTE_FAMILIA = "Segoe UI"


def _fonte(tamanho=10, negrito=False, italico=False):
    estilo = []
    if negrito:
        estilo.append("bold")
    if italico:
        estilo.append("italic")
    return (FONTE_FAMILIA, tamanho, *estilo)


def configurar_estilo(root):
    """Define a paleta e o estilo ttk usados em toda a aplicação."""
    root.configure(background=COR_FUNDO)

    fonte_padrao = tkfont.nametofont("TkDefaultFont")
    try:
        fonte_padrao.configure(family=FONTE_FAMILIA, size=10)
    except tk.TclError:
        pass

    estilo = ttk.Style(root)
    try:
        estilo.theme_use("clam")
    except tk.TclError:
        pass

    estilo.configure(".", background=COR_FUNDO, foreground=COR_TEXTO, font=_fonte())
    estilo.configure("TFrame", background=COR_FUNDO)
    estilo.configure("Cartao.TFrame", background=COR_CARTAO)
    estilo.configure("Cabecalho.TFrame", background=COR_PRIMARIA)
    estilo.configure("TLabel", background=COR_FUNDO, foreground=COR_TEXTO, font=_fonte())
    estilo.configure("Cartao.TLabel", background=COR_CARTAO, foreground=COR_TEXTO, font=_fonte())
    estilo.configure("Titulo.TLabel", background=COR_FUNDO, foreground=COR_TEXTO, font=_fonte(18, negrito=True))
    estilo.configure("TituloCartao.TLabel", background=COR_CARTAO, foreground=COR_TEXTO, font=_fonte(17, negrito=True))
    estilo.configure("Subtitulo.TLabel", background=COR_FUNDO, foreground=COR_TEXTO_SUAVE, font=_fonte(10))
    estilo.configure("SubtituloCartao.TLabel", background=COR_CARTAO, foreground=COR_TEXTO_SUAVE, font=_fonte(10))
    estilo.configure("Erro.TLabel", background=COR_FUNDO, foreground=COR_PERIGO, font=_fonte(9, negrito=True))
    estilo.configure("ErroCartao.TLabel", background=COR_CARTAO, foreground=COR_PERIGO, font=_fonte(9, negrito=True))
    estilo.configure("Cabecalho.TLabel", background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO, font=_fonte(10))
    estilo.configure("CabecalhoTitulo.TLabel", background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO, font=_fonte(13, negrito=True))
    estilo.configure("Legenda.TLabel", background=COR_FUNDO, foreground=COR_TEXTO_SUAVE, font=_fonte(9, italico=True))
    estilo.configure("TEntry", padding=6, foreground=COR_TEXTO)
    estilo.configure("TCombobox", padding=4)
    estilo.configure("Treeview", background=COR_CARTAO, fieldbackground=COR_CARTAO, foreground=COR_TEXTO, rowheight=28, font=_fonte(10), borderwidth=0)
    estilo.configure("Treeview.Heading", background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO, font=_fonte(10, negrito=True), relief="flat", padding=6)
    estilo.map("Treeview.Heading", background=[("active", COR_PRIMARIA_ESCURA)])
    estilo.map("Treeview", background=[("selected", COR_PRIMARIA)], foreground=[("selected", COR_TEXTO_CLARO)])
    estilo.configure("TSeparator", background=COR_BORDA)
    estilo.configure("TScrollbar", background=COR_NEUTRO, troughcolor=COR_FUNDO, borderwidth=0)


def _escurecer(cor_hex, fator=0.85):
    cor_hex = cor_hex.lstrip("#")
    r, g, b = (int(cor_hex[i : i + 2], 16) for i in (0, 2, 4))
    r, g, b = (max(0, min(255, int(c * fator))) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def criar_botao(pai, texto, comando, bg=COR_PRIMARIA, fg=COR_TEXTO_CLARO, bg_hover=None,
                 tamanho_fonte=10, negrito=True, padx=16, pady=8, largura=None, estado="normal"):
    bg_hover = bg_hover or _escurecer(bg)
    botao = tk.Button(pai, text=texto, command=comando, bg=bg, fg=fg, activebackground=bg_hover,
        activeforeground=fg, disabledforeground=COR_TEXTO_SUAVE, relief="flat", bd=0,
        cursor="hand2" if estado == "normal" else "arrow", font=_fonte(tamanho_fonte, negrito=negrito),
        padx=padx, pady=pady, highlightthickness=0, state=estado)
    if largura:
        botao.config(width=largura)
    botao.bind("<Enter>", lambda _e: botao.config(bg=bg_hover) if str(botao["state"]) != "disabled" else None)
    botao.bind("<Leave>", lambda _e: botao.config(bg=bg) if str(botao["state"]) != "disabled" else None)
    return botao


def botao_secundario(pai, texto, comando, **kwargs):
    return criar_botao(pai, texto, comando, bg=COR_NEUTRO, fg=COR_TEXTO, bg_hover=COR_NEUTRO_ESCURO, **kwargs)


def botao_perigo(pai, texto, comando, **kwargs):
    return criar_botao(pai, texto, comando, bg=COR_PERIGO, bg_hover=COR_PERIGO_ESCURA, **kwargs)


def botao_sucesso(pai, texto, comando, **kwargs):
    return criar_botao(pai, texto, comando, bg=COR_SUCESSO, bg_hover=COR_SUCESSO_ESCURA, **kwargs)


def normalizar_texto_peso(entrada):
    tem_ponto = "." in entrada
    tem_virgula = "," in entrada
    if tem_ponto and tem_virgula:
        entrada = entrada.replace(".", "")
    if tem_virgula:
        entrada = entrada.replace(",", ".")
    return entrada


def formatar_peso(peso):
    return f"{peso:.2f}".replace(".", ",")


def formatar_data_cadastro(pedido):
    momento = interpretar_data_cadastro(pedido.get("criado_em"))
    if momento is None:
        return "Não informada"
    return momento.strftime("%d/%m/%Y %H:%M:%S")


class AplicativoPedidos:
    def __init__(self, root):
        self.root = root
        self.root.title(TITULO_JANELA)
        self.root.geometry("1060x640")
        self.root.minsize(820, 480)
        self.usuario_atual = None
        configurar_estilo(self.root)
        self.container = ttk.Frame(root)
        self.container.pack(fill="both", expand=True)
        db.inicializar_banco()
        self.ir_para_tela_inicial()

    def _limpar_container(self):
        for filho in self.container.winfo_children():
            filho.destroy()

    def ir_para_tela_inicial(self):
        self.usuario_atual = None
        self._limpar_container()
        TelaLogin(self.container, self) if db.banco_tem_usuarios() else TelaCriarAdministrador(self.container, self)

    def login_bem_sucedido(self, usuario):
        self.usuario_atual = usuario
        self._limpar_container()
        TelaPrincipal(self.container, self)

    def sair_da_conta(self):
        if messagebox.askyesno("Sair", "Deseja encerrar a sessão atual?"):
            self.ir_para_tela_inicial()

    def eh_admin(self):
        return self.usuario_atual is not None and self.usuario_atual["papel"] == "admin"

    def exigir_admin(self):
        if not self.eh_admin():
            messagebox.showerror("Acesso restrito", "Esta ação é permitida apenas a administradores.")
            return False
        return True


class _CartaoCentral(ttk.Frame):
    def __init__(self, container, app, emoji, titulo, subtitulo):
        super().__init__(container, style="TFrame")
        self.app = app
        self.pack(fill="both", expand=True)
        faixa_superior = tk.Frame(self, bg=COR_PRIMARIA, height=140)
        faixa_superior.pack(fill="x", side="top")
        self.cartao = tk.Frame(self, bg=COR_CARTAO, highlightbackground=COR_BORDA, highlightthickness=1)
        self.cartao.place(relx=0.5, rely=0.5, anchor="center")
        interno = tk.Frame(self.cartao, bg=COR_CARTAO, padx=36, pady=32)
        interno.pack()
        tk.Label(interno, text=emoji, bg=COR_CARTAO, font=_fonte(38)).pack(pady=(0, 6))
        tk.Label(interno, text=titulo, bg=COR_CARTAO, fg=COR_TEXTO, font=_fonte(18, negrito=True)).pack()
        tk.Label(interno, text=subtitulo, bg=COR_CARTAO, fg=COR_TEXTO_SUAVE, font=_fonte(10), wraplength=320, justify="center").pack(pady=(4, 18))
        self.corpo = interno

    def campo(self, linha_pai, rotulo, variavel, oculto=False, foco=False):
        bloco = tk.Frame(linha_pai, bg=COR_CARTAO)
        bloco.pack(fill="x", pady=6)
        tk.Label(bloco, text=rotulo, bg=COR_CARTAO, fg=COR_TEXTO_SUAVE, font=_fonte(9, negrito=True)).pack(anchor="w")
        entrada = ttk.Entry(bloco, textvariable=variavel, width=30, show="*" if oculto else "", font=_fonte(11))
        entrada.pack(fill="x", pady=(2, 0))
        if foco:
            entrada.focus_set()
        return entrada


class TelaCriarAdministrador(_CartaoCentral):
    def __init__(self, container, app):
        super().__init__(container, app, "🛠️", "Bem-vindo!", "Este é o primeiro acesso. Crie a conta de administrador do sistema.")
        self.var_nome_completo = tk.StringVar(); self.var_nome_usuario = tk.StringVar(); self.var_senha = tk.StringVar(); self.var_confirmar_senha = tk.StringVar()
        self.campo(self.corpo, "Nome completo", self.var_nome_completo, foco=True)
        self.campo(self.corpo, "Usuário (sem espaços)", self.var_nome_usuario)
        self.campo(self.corpo, "Senha (mín. 8 caracteres)", self.var_senha, oculto=True)
        self.campo(self.corpo, "Confirmar senha", self.var_confirmar_senha, oculto=True)
        self.rotulo_erro = tk.Label(self.corpo, text="", bg=COR_CARTAO, fg=COR_PERIGO, font=_fonte(9, negrito=True), wraplength=300, justify="center")
        self.rotulo_erro.pack(pady=(6, 0))
        criar_botao(self.corpo, "Criar administrador", self._criar, largura=28).pack(pady=(14, 0))
        self.bind_all("<Return>", lambda evento: self._criar())

    def _criar(self):
        senha = self.var_senha.get()
        if senha != self.var_confirmar_senha.get():
            self.rotulo_erro.config(text="As senhas digitadas não são iguais."); return
        try:
            auth.criar_usuario(self.var_nome_usuario.get(), self.var_nome_completo.get(), senha, papel="admin")
        except auth.ErroAutenticacao as erro:
            self.rotulo_erro.config(text=str(erro)); return
        messagebox.showinfo("Conta criada", "Administrador criado com sucesso. Faça login para continuar.")
        self.app.ir_para_tela_inicial()


class TelaLogin(_CartaoCentral):
    def __init__(self, container, app):
        super().__init__(container, app, "📦", "Controle de Pedidos", "Faça login para acessar o sistema.")
        self.var_nome_usuario = tk.StringVar(); self.var_senha = tk.StringVar()
        self.campo(self.corpo, "Usuário", self.var_nome_usuario, foco=True)
        self.campo(self.corpo, "Senha", self.var_senha, oculto=True)
        self.rotulo_erro = tk.Label(self.corpo, text="", bg=COR_CARTAO, fg=COR_PERIGO, font=_fonte(9, negrito=True), wraplength=300, justify="center")
        self.rotulo_erro.pack(pady=(6, 0))
        criar_botao(self.corpo, "Entrar", self._entrar, largura=28).pack(pady=(14, 0))
        self.bind_all("<Return>", lambda evento: self._entrar())

    def _entrar(self):
        try:
            usuario = auth.autenticar(self.var_nome_usuario.get(), self.var_senha.get())
        except auth.ErroAutenticacao as erro:
            self.rotulo_erro.config(text=str(erro)); return
        self.app.login_bem_sucedido(usuario)


class TelaPrincipal(ttk.Frame):
    COLUNAS = ("id", "cliente", "cidade", "peso", "status", "criado_em")
    TITULOS_COLUNAS = {"id": "ID", "cliente": "Cliente", "cidade": "Cidade de destino", "peso": "Peso (kg)", "status": "Status", "criado_em": "Cadastrado em"}

    def __init__(self, container, app):
        super().__init__(container); self.app = app; self.pack(fill="both", expand=True); self._rotulos_kpi = {}
        self._montar_menu(); self._montar_cabecalho(); self._montar_kpis(); self._montar_barra_ferramentas(); self._montar_tabela(); self.recarregar(mostrar_todos=True)

    def _montar_menu(self):
        barra_menu = tk.Menu(self.app.root)
        menu_pedidos = tk.Menu(barra_menu, tearoff=False)
        menu_pedidos.add_command(label="Novo pedido...", command=self.abrir_novo_pedido)
        menu_pedidos.add_command(label="Editar selecionado...", command=self.abrir_editar_pedido)
        menu_pedidos.add_command(label="Atualizar status do selecionado...", command=self.abrir_atualizar_status)
        menu_pedidos.add_separator(); item_excluir = "Excluir selecionado..."; menu_pedidos.add_command(label=item_excluir, command=self.excluir_selecionado)
        if not self.app.eh_admin(): menu_pedidos.entryconfig(item_excluir, state="disabled")
        barra_menu.add_cascade(label="Pedidos", menu=menu_pedidos)
        menu_consultas = tk.Menu(barra_menu, tearoff=False)
        menu_consultas.add_command(label="Mostrar todos", command=lambda: self.recarregar(mostrar_todos=True))
        menu_consultas.add_command(label="Buscar por cliente/cidade...", command=self.abrir_busca_texto)
        menu_consultas.add_command(label="Filtrar por status...", command=self.abrir_filtro_status)
        menu_consultas.add_command(label="Consultar por período...", command=self.abrir_consulta_periodo)
        menu_consultas.add_separator(); menu_consultas.add_command(label="Resumo da operação...", command=self.mostrar_resumo)
        barra_menu.add_cascade(label="Consultas", menu=menu_consultas)
        menu_arquivo = tk.Menu(barra_menu, tearoff=False); menu_arquivo.add_command(label="Exportar para CSV...", command=self.exportar_csv)
        menu_arquivo.add_command(label="Fazer backup agora", command=self.fazer_backup); menu_arquivo.add_command(label="Restaurar backup...", command=self.abrir_restaurar_backup)
        if not self.app.eh_admin(): menu_arquivo.entryconfig("Fazer backup agora", state="disabled"); menu_arquivo.entryconfig("Restaurar backup...", state="disabled")
        barra_menu.add_cascade(label="Arquivo", menu=menu_arquivo)
        if self.app.eh_admin():
            menu_usuarios = tk.Menu(barra_menu, tearoff=False); menu_usuarios.add_command(label="Gerenciar usuários...", command=self.abrir_gerenciar_usuarios); barra_menu.add_cascade(label="Usuários", menu=menu_usuarios)
        menu_sessao = tk.Menu(barra_menu, tearoff=False); menu_sessao.add_command(label="Sair da conta", command=self._sair); barra_menu.add_cascade(label="Sessão", menu=menu_sessao)
        self.app.root.config(menu=barra_menu)

    def _sair(self):
        self.app.root.config(menu=tk.Menu(self.app.root)); self.app.sair_da_conta()

    def _montar_cabecalho(self):
        cabecalho = tk.Frame(self, bg=COR_PRIMARIA); cabecalho.pack(fill="x")
        esquerda = tk.Frame(cabecalho, bg=COR_PRIMARIA); esquerda.pack(side="left", padx=18, pady=14)
        tk.Label(esquerda, text="📦 Controle de Pedidos", bg=COR_PRIMARIA, fg=COR_TEXTO_CLARO, font=_fonte(15, negrito=True)).pack(anchor="w")
        usuario = self.app.usuario_atual; emblema = "👑 admin" if usuario["papel"] == "admin" else "🧑‍💼 operador"
        tk.Label(esquerda, text=f"Olá, {usuario['nome_completo']}  ·  {emblema}", bg=COR_PRIMARIA, fg="#e0e7ff", font=_fonte(9)).pack(anchor="w")
        direita = tk.Frame(cabecalho, bg=COR_PRIMARIA); direita.pack(side="right", padx=18, pady=14)
        criar_botao(direita, "🚪 Sair", self._sair, bg=COR_PRIMARIA_ESCURA, bg_hover="#2f2a99", tamanho_fonte=9, padx=12, pady=6).pack()

    def _montar_kpis(self):
        faixa = tk.Frame(self, bg=COR_FUNDO); faixa.pack(fill="x", padx=18, pady=(14, 6))
        for chave, titulo, cor in (("total","📊 Total de pedidos",COR_PRIMARIA),("Pendente","🟡 Pendentes",COR_ALERTA),("Em transporte","🚚 Em transporte",COR_INFO),("Entregue","✅ Entregues",COR_SUCESSO)):
            cartao = tk.Frame(faixa, bg=cor); cartao.pack(side="left", fill="x", expand=True, padx=(0 if chave == "total" else 8, 0)); miolo = tk.Frame(cartao, bg=cor, padx=16, pady=10); miolo.pack(fill="both", expand=True)
            tk.Label(miolo, text=titulo, bg=cor, fg=COR_TEXTO_CLARO, font=_fonte(9, negrito=True)).pack(anchor="w"); rotulo = tk.Label(miolo, text="0", bg=cor, fg=COR_TEXTO_CLARO, font=_fonte(24, negrito=True)); rotulo.pack(anchor="w"); self._rotulos_kpi[chave] = rotulo

    def _atualizar_kpis(self):
        resumo = repo.gerar_resumo(); self._rotulos_kpi["total"].config(text=str(resumo["total_pedidos"]))
        for status, quantidade in resumo["quantidade_por_status"].items():
            if status in self._rotulos_kpi: self._rotulos_kpi[status].config(text=str(quantidade))

    def _montar_barra_ferramentas(self):
        barra = tk.Frame(self, bg=COR_FUNDO); barra.pack(fill="x", padx=18, pady=(6, 6))
        criar_botao(barra,"➕ Novo pedido",self.abrir_novo_pedido,bg=COR_SUCESSO,bg_hover=COR_SUCESSO_ESCURA).pack(side="left",padx=(0,8)); criar_botao(barra,"✏️ Editar",self.abrir_editar_pedido,bg=COR_INFO,bg_hover=COR_INFO_ESCURA).pack(side="left",padx=(0,8)); criar_botao(barra,"🔄 Status",self.abrir_atualizar_status,bg=COR_SECUNDARIA,bg_hover=COR_SECUNDARIA_ESCURA).pack(side="left",padx=(0,8))
        self.botao_excluir = botao_perigo(barra,"🗑️ Excluir",self.excluir_selecionado); self.botao_excluir.pack(side="left",padx=(0,8));
        if not self.app.eh_admin(): self.botao_excluir.config(state="disabled",cursor="arrow")
        botao_secundario(barra,"⟲ Atualizar lista",lambda:self.recarregar(mostrar_todos=True)).pack(side="right")
        self.rotulo_titulo_lista = tk.Label(self,text="",bg=COR_FUNDO,fg=COR_TEXTO_SUAVE,font=_fonte(10,italico=True),anchor="w"); self.rotulo_titulo_lista.pack(fill="x",padx=20)

    def _montar_tabela(self):
        moldura = tk.Frame(self,bg=COR_FUNDO,padx=18,pady=10); moldura.pack(fill="both",expand=True); self.tabela = ttk.Treeview(moldura,columns=self.COLUNAS,show="headings",selectmode="browse")
        for coluna in self.COLUNAS: self.tabela.heading(coluna,text=self.TITULOS_COLUNAS[coluna]); self.tabela.column(coluna,width=70 if coluna=="id" else 150,anchor="w")
        self.tabela.tag_configure("status_pendente",background=COR_ALERTA_CLARA); self.tabela.tag_configure("status_transporte",background=COR_INFO_CLARA); self.tabela.tag_configure("status_entregue",background=COR_SUCESSO_CLARA)
        rolagem = ttk.Scrollbar(moldura,orient="vertical",command=self.tabela.yview); self.tabela.configure(yscrollcommand=rolagem.set); self.tabela.pack(side="left",fill="both",expand=True); rolagem.pack(side="right",fill="y"); self.tabela.bind("<Double-1>",lambda evento:self.abrir_editar_pedido())

    _TAG_POR_STATUS={"Pendente":"status_pendente","Em transporte":"status_transporte","Entregue":"status_entregue"}
    def _preencher_tabela(self,pedidos,titulo):
        self.rotulo_titulo_lista.config(text=f"🔎  {titulo}   ·   {len(pedidos)} pedido(s)"); self.tabela.delete(*self.tabela.get_children())
        for pedido in pedidos: self.tabela.insert("","end",iid=str(pedido["id"]),values=(pedido["id"],pedido["cliente"],pedido["cidade_destino"],formatar_peso(pedido["peso_kg"]),pedido["status"],formatar_data_cadastro(pedido)),tags=(self._TAG_POR_STATUS.get(pedido["status"],""),))
        self._atualizar_kpis()
    def recarregar(self,mostrar_todos=False): self._preencher_tabela(repo.listar_pedidos(),"Todos os pedidos")
    def _pedido_selecionado(self):
        selecao=self.tabela.selection()
        if not selecao: messagebox.showwarning("Nenhum pedido selecionado","Selecione um pedido na lista primeiro."); return None
        pedido=repo.obter_pedido_por_id(int(selecao[0]))
        if pedido is None: messagebox.showerror("Pedido não encontrado","Este pedido não existe mais. Atualize a lista.")
        return pedido
    def abrir_novo_pedido(self): DialogoPedido(self.app.root,"➕ Novo pedido",self._salvar_novo_pedido)
    def _salvar_novo_pedido(self,cliente,cidade,peso):
        try: repo.criar_pedido(cliente,cidade,peso,usuario=self.app.usuario_atual["nome_usuario"])
        except ValueError as erro: messagebox.showerror("Não foi possível cadastrar",str(erro)); return False
        self.recarregar(True); return True
    def abrir_editar_pedido(self):
        p=self._pedido_selecionado()
        if p: DialogoPedido(self.app.root,f"✏️ Editar pedido {p['id']}",lambda c,d,w:self._salvar_edicao(p["id"],c,d,w),p["cliente"],p["cidade_destino"],p["peso_kg"])
    def _salvar_edicao(self,i,c,d,w):
        try: repo.editar_pedido(i,c,d,w,usuario=self.app.usuario_atual["nome_usuario"])
        except ValueError as erro: messagebox.showerror("Não foi possível salvar",str(erro)); return False
        self.recarregar(True); return True
    def abrir_atualizar_status(self):
        p=self._pedido_selecionado()
        if p: DialogoStatus(self.app.root,p["status"],lambda s:self._salvar_status(p["id"],s))
    def _salvar_status(self,i,s):
        try: repo.alterar_status(i,s,usuario=self.app.usuario_atual["nome_usuario"])
        except ValueError as erro: messagebox.showerror("Não foi possível atualizar",str(erro)); return False
        self.recarregar(True); return True
    def excluir_selecionado(self):
        if not self.app.exigir_admin(): return
        p=self._pedido_selecionado()
        if p and messagebox.askyesno("Confirmar exclusão",f"Excluir o pedido {p['id']} de {p['cliente']}? Esta ação não pode ser desfeita."):
            repo.excluir_pedido(p["id"]); self.recarregar(True)
    def abrir_busca_texto(self):
        texto=_pedir_texto_simples(self.app.root,"🔍 Buscar pedidos","Parte do nome do cliente ou da cidade:")
        if texto:
            try: self._preencher_tabela(repo.buscar_por_texto(texto),f'Resultados para "{texto}"')
            except ValueError as erro: messagebox.showerror("Busca inválida",str(erro))
    def abrir_filtro_status(self): DialogoEscolherStatus(self.app.root,lambda s:self._preencher_tabela(repo.filtrar_por_status(s),f"Pedidos com status: {s}"))
    def abrir_consulta_periodo(self): DialogoPeriodo(self.app.root,self._aplicar_consulta_periodo)
    def _aplicar_consulta_periodo(self,a,b):
        try: resultado=repo.consultar_por_periodo(a,b)
        except ValueError as erro: messagebox.showerror("Período inválido",str(erro)); return False
        self._preencher_tabela(resultado,f"Cadastrados de {a:%d/%m/%Y} a {b:%d/%m/%Y}"); return True
    def mostrar_resumo(self):
        r=repo.gerar_resumo(); linhas=[f"Total de pedidos: {r['total_pedidos']}"]+[f"{s}: {q}" for s,q in r["quantidade_por_status"].items()]; linhas.append("Peso total cadastrado: soma acima do limite numérico suportado." if r["peso_total_kg"] is None else f"Peso total cadastrado: {formatar_peso(r['peso_total_kg'])} kg"); messagebox.showinfo("📊 Resumo da operação","\n".join(linhas))
    def exportar_csv(self):
        try: caminho=repo.exportar_csv()
        except ValueError as erro: messagebox.showerror("Não foi possível exportar",str(erro)); return
        messagebox.showinfo("Exportação concluída",f"Arquivo criado em:\n{caminho}")
    def fazer_backup(self):
        if self.app.exigir_admin(): messagebox.showinfo("Backup criado",f"Backup salvo em:\n{repo.fazer_backup(usuario=self.app.usuario_atual['nome_usuario'])}")
    def abrir_restaurar_backup(self):
        if not self.app.exigir_admin(): return
        backups=repo.listar_backups()
        if backups: DialogoRestaurarBackup(self.app.root,backups,self._restaurar_backup)
        else: messagebox.showinfo("Nenhum backup","Ainda não existe nenhum backup salvo.")
    def _restaurar_backup(self,caminho):
        if not messagebox.askyesno("Confirmar restauração","Isso vai substituir TODOS os pedidos atuais pelos do backup escolhido. Continuar?"): return False
        q=repo.restaurar_backup(caminho); messagebox.showinfo("Backup restaurado",f"{q} pedido(s) restaurado(s) com sucesso."); self.recarregar(True); return True
    def abrir_gerenciar_usuarios(self):
        if self.app.exigir_admin(): JanelaGerenciarUsuarios(self.app.root)


def centralizar_sobre_pai(janela,pai):
    janela.update_idletasks(); largura=janela.winfo_width(); altura=janela.winfo_height(); x=pai.winfo_rootx()+(pai.winfo_width()-largura)//2; y=pai.winfo_rooty()+(pai.winfo_height()-altura)//2; x=min(max(x,0),max(janela.winfo_screenwidth()-largura,0)); y=min(max(y,0),max(janela.winfo_screenheight()-altura,0)); janela.geometry(f"+{x}+{y}")


class _DialogoBase(tk.Toplevel):
    def __init__(self,pai,titulo):
        super().__init__(pai); self.title(titulo); self.configure(background=COR_CARTAO); self.resizable(False,False); self.transient(pai); self.grab_set(); self._pai=pai
        faixa=tk.Frame(self,bg=COR_PRIMARIA); faixa.pack(fill="x"); tk.Label(faixa,text=titulo,bg=COR_PRIMARIA,fg=COR_TEXTO_CLARO,font=_fonte(12,negrito=True)).pack(padx=16,pady=10,anchor="w"); self.corpo=tk.Frame(self,bg=COR_CARTAO); self.corpo.pack(fill="both",expand=True)
    def _centralizar(self): centralizar_sobre_pai(self,self._pai)


def _campo_dialogo(pai,rotulo,variavel,largura=32,oculto=False,foco=False):
    bloco=tk.Frame(pai,bg=COR_CARTAO); bloco.pack(fill="x",pady=6); tk.Label(bloco,text=rotulo,bg=COR_CARTAO,fg=COR_TEXTO_SUAVE,font=_fonte(9,negrito=True)).pack(anchor="w"); entrada=ttk.Entry(bloco,textvariable=variavel,width=largura,show="*" if oculto else ""); entrada.pack(fill="x",pady=(2,0));
    if foco: entrada.focus_set()
    return entrada


class DialogoPedido(_DialogoBase):
    def __init__(self,pai,titulo,ao_confirmar,cliente_inicial="",cidade_inicial="",peso_inicial=None):
        super().__init__(pai,titulo); self.ao_confirmar=ao_confirmar; moldura=tk.Frame(self.corpo,bg=COR_CARTAO,padx=20,pady=16); moldura.pack(); self.var_cliente=tk.StringVar(value=cliente_inicial); self.var_cidade=tk.StringVar(value=cidade_inicial); self.var_peso=tk.StringVar(value="" if peso_inicial is None else str(peso_inicial).replace(".",",")); entrada=_campo_dialogo(moldura,"Cliente",self.var_cliente,foco=True); _campo_dialogo(moldura,"Cidade de destino",self.var_cidade); _campo_dialogo(moldura,"Peso em kg (ex.: 350,5)",self.var_peso); self.rotulo_erro=tk.Label(moldura,text="",bg=COR_CARTAO,fg=COR_PERIGO,font=_fonte(9,negrito=True),wraplength=280); self.rotulo_erro.pack(pady=(6,0)); botoes=tk.Frame(moldura,bg=COR_CARTAO); botoes.pack(pady=(14,0)); criar_botao(botoes,"💾 Salvar",self._confirmar).pack(side="left",padx=4); botao_secundario(botoes,"Cancelar",self.destroy).pack(side="left",padx=4); entrada.focus_set(); self.bind("<Return>",lambda e:self._confirmar()); self.bind("<Escape>",lambda e:self.destroy()); self._centralizar()
    def _confirmar(self):
        cliente=self.var_cliente.get().strip(); cidade=self.var_cidade.get().strip(); texto=normalizar_texto_peso(self.var_peso.get().strip())
        if not cliente: self.rotulo_erro.config(text="Informe o nome do cliente."); return
        if not cidade: self.rotulo_erro.config(text="Informe a cidade de destino."); return
        try: peso=float(texto)
        except ValueError: self.rotulo_erro.config(text="Peso inválido. Exemplo válido: 350,5 ou 1.234,5."); return
        if self.ao_confirmar(cliente,cidade,peso): self.destroy()


class DialogoStatus(_DialogoBase):
    def __init__(self,pai,status_atual,ao_confirmar):
        super().__init__(pai,"🔄 Atualizar status"); self.ao_confirmar=ao_confirmar; moldura=tk.Frame(self.corpo,bg=COR_CARTAO,padx=20,pady=16); moldura.pack(); tk.Label(moldura,text=f"Status atual:  {status_atual}",bg=COR_CARTAO,fg=COR_TEXTO,font=_fonte(10)).pack(anchor="w",pady=(0,10)); self.var_status=tk.StringVar(value=status_atual); ttk.Combobox(moldura,textvariable=self.var_status,values=STATUS_DISPONIVEIS,state="readonly",width=24).pack(fill="x"); botoes=tk.Frame(moldura,bg=COR_CARTAO); botoes.pack(pady=(16,0)); criar_botao(botoes,"💾 Salvar",self._confirmar).pack(side="left",padx=4); botao_secundario(botoes,"Cancelar",self.destroy).pack(side="left",padx=4); self._centralizar()
    def _confirmar(self):
        if self.ao_confirmar(self.var_status.get()): self.destroy()


class DialogoEscolherStatus(_DialogoBase):
    def __init__(self,pai,ao_confirmar):
        super().__init__(pai,"🏷️ Filtrar por status"); self.ao_confirmar=ao_confirmar; moldura=tk.Frame(self.corpo,bg=COR_CARTAO,padx=20,pady=16); moldura.pack(); tk.Label(moldura,text="Qual status deseja consultar?",bg=COR_CARTAO,fg=COR_TEXTO,font=_fonte(10)).pack(anchor="w",pady=(0,8)); self.var_status=tk.StringVar(value=STATUS_DISPONIVEIS[0]); ttk.Combobox(moldura,textvariable=self.var_status,values=STATUS_DISPONIVEIS,state="readonly",width=24).pack(fill="x"); botoes=tk.Frame(moldura,bg=COR_CARTAO); botoes.pack(pady=(16,0)); criar_botao(botoes,"🔍 Consultar",self._confirmar).pack(side="left",padx=4); botao_secundario(botoes,"Cancelar",self.destroy).pack(side="left",padx=4); self._centralizar()
    def _confirmar(self): self.ao_confirmar(self.var_status.get()); self.destroy()


class DialogoPeriodo(_DialogoBase):
    def __init__(self,pai,ao_confirmar):
        super().__init__(pai,"📅 Consultar por período de cadastro"); self.ao_confirmar=ao_confirmar; moldura=tk.Frame(self.corpo,bg=COR_CARTAO,padx=20,pady=16); moldura.pack(); tk.Label(moldura,text="Datas no formato DD/MM/AAAA",bg=COR_CARTAO,fg=COR_TEXTO_SUAVE,font=_fonte(9)).pack(anchor="w",pady=(0,8)); self.var_data_inicial=tk.StringVar(); self.var_data_final=tk.StringVar(); entrada=_campo_dialogo(moldura,"Data inicial",self.var_data_inicial,largura=16,foco=True); _campo_dialogo(moldura,"Data final",self.var_data_final,largura=16); self.rotulo_erro=tk.Label(moldura,text="",bg=COR_CARTAO,fg=COR_PERIGO,font=_fonte(9,negrito=True),wraplength=260); self.rotulo_erro.pack(pady=(6,0)); botoes=tk.Frame(moldura,bg=COR_CARTAO); botoes.pack(pady=(14,0)); criar_botao(botoes,"🔍 Consultar",self._confirmar).pack(side="left",padx=4); botao_secundario(botoes,"Cancelar",self.destroy).pack(side="left",padx=4); entrada.focus_set(); self._centralizar()
    def _confirmar(self):
        try: a=converter_data_consulta(self.var_data_inicial.get()); b=converter_data_consulta(self.var_data_final.get())
        except ValueError as erro: self.rotulo_erro.config(text=str(erro)); return
        if self.ao_confirmar(a,b): self.destroy()


class DialogoRestaurarBackup(_DialogoBase):
    def __init__(self,pai,backups,ao_confirmar):
        super().__init__(pai,"♻️ Restaurar backup"); self.ao_confirmar=ao_confirmar; self.backups=backups; moldura=tk.Frame(self.corpo,bg=COR_CARTAO,padx=20,pady=16); moldura.pack(); tk.Label(moldura,text="Escolha o backup que deseja restaurar:",bg=COR_CARTAO,fg=COR_TEXTO,font=_fonte(10)).pack(anchor="w",pady=(0,8)); self.lista=tk.Listbox(moldura,width=42,height=8,bg=COR_CARTAO,fg=COR_TEXTO,highlightthickness=1,highlightbackground=COR_BORDA,selectbackground=COR_PRIMARIA,selectforeground=COR_TEXTO_CLARO,relief="flat",font=_fonte(10)); [self.lista.insert("end",c.name) for c in backups]; self.lista.selection_set(0); self.lista.pack(); botoes=tk.Frame(moldura,bg=COR_CARTAO); botoes.pack(pady=(14,0)); criar_botao(botoes,"♻️ Restaurar",self._confirmar).pack(side="left",padx=4); botao_secundario(botoes,"Cancelar",self.destroy).pack(side="left",padx=4); self._centralizar()
    def _confirmar(self):
        s=self.lista.curselection()
        if s and self.ao_confirmar(self.backups[s[0]]): self.destroy()


def _pedir_texto_simples(pai,titulo,rotulo):
    resultado={}; janela=_DialogoBase(pai,titulo); moldura=tk.Frame(janela.corpo,bg=COR_CARTAO,padx=20,pady=16); moldura.pack(); tk.Label(moldura,text=rotulo,bg=COR_CARTAO,fg=COR_TEXTO,font=_fonte(10),wraplength=280).pack(anchor="w",pady=(0,8)); variavel=tk.StringVar(); entrada=ttk.Entry(moldura,textvariable=variavel,width=34); entrada.pack(); entrada.focus_set()
    def confirmar():
        texto=variavel.get().strip()
        if texto: resultado["texto"]=texto
        janela.destroy()
    botoes=tk.Frame(moldura,bg=COR_CARTAO); botoes.pack(pady=(14,0)); criar_botao(botoes,"🔍 Buscar",confirmar).pack(side="left",padx=4); botao_secundario(botoes,"Cancelar",janela.destroy).pack(side="left",padx=4); janela.bind("<Return>",lambda e:confirmar()); janela._centralizar(); janela.wait_window(); return resultado.get("texto")


class JanelaGerenciarUsuarios(tk.Toplevel):
    def __init__(self,pai):
        super().__init__(pai); self.title("👤 Gerenciar usuários"); self.configure(background=COR_CARTAO); self.geometry("760x520"); self.resizable(False,False); self.transient(pai); self.grab_set(); faixa=tk.Frame(self,bg=COR_PRIMARIA); faixa.pack(fill="x"); tk.Label(faixa,text="👤 Gerenciar usuários",bg=COR_PRIMARIA,fg=COR_TEXTO_CLARO,font=_fonte(12,negrito=True)).pack(padx=16,pady=10,anchor="w"); moldura=tk.Frame(self,bg=COR_CARTAO,padx=18,pady=16); moldura.pack(fill="both",expand=True)
        colunas=("nome_completo","nome_usuario","papel","ativo"); self.tabela=ttk.Treeview(moldura,columns=colunas,show="headings",height=8); titulos={"nome_completo":"Nome","nome_usuario":"Usuário","papel":"Papel","ativo":"Ativo"}; larguras={"nome_completo":220,"nome_usuario":140,"papel":90,"ativo":60}
        for c in colunas: self.tabela.heading(c,text=titulos[c]); self.tabela.column(c,width=larguras[c])
        self.tabela.tag_configure("inativo",foreground=COR_TEXTO_SUAVE); self.tabela.pack(fill="both",expand=True); botoes=tk.Frame(moldura,bg=COR_CARTAO); botoes.pack(fill="x",pady=(10,16)); criar_botao(botoes,"🔁 Ativar/Desativar selecionado",self._alternar_ativo,bg=COR_SECUNDARIA,bg_hover=COR_SECUNDARIA_ESCURA).pack(side="left",padx=(0,8)); botao_secundario(botoes,"🔑 Redefinir senha do selecionado...",self._redefinir_senha).pack(side="left"); ttk.Separator(moldura).pack(fill="x",pady=(0,12)); tk.Label(moldura,text="Criar novo usuário",bg=COR_CARTAO,fg=COR_TEXTO,font=_fonte(11,negrito=True)).pack(anchor="w"); formulario=tk.Frame(moldura,bg=COR_CARTAO); formulario.pack(fill="x",pady=(8,0)); self.var_nome_completo=tk.StringVar(); self.var_nome_usuario=tk.StringVar(); self.var_senha=tk.StringVar(); self.var_papel=tk.StringVar(value="operador")
        for i,t in enumerate(("Nome completo","Usuário","Senha (mín. 8)","Papel")): tk.Label(formulario,text=t,bg=COR_CARTAO,fg=COR_TEXTO_SUAVE,font=_fonte(9,negrito=True)).grid(row=0,column=i,sticky="w",padx=(0 if i==0 else 6,0))
        ttk.Entry(formulario,textvariable=self.var_nome_completo,width=18).grid(row=1,column=0); ttk.Entry(formulario,textvariable=self.var_nome_usuario,width=13).grid(row=1,column=1,padx=(6,0)); ttk.Entry(formulario,textvariable=self.var_senha,width=13,show="*").grid(row=1,column=2,padx=(6,0)); ttk.Combobox(formulario,textvariable=self.var_papel,values=auth.PAPEIS_DISPONIVEIS,state="readonly",width=9).grid(row=1,column=3,padx=(6,0)); criar_botao(formulario,"➕ Criar",self._criar_usuario,bg=COR_SUCESSO,bg_hover=COR_SUCESSO_ESCURA).grid(row=1,column=4,padx=(10,0)); self._recarregar(); centralizar_sobre_pai(self,pai)
    def _recarregar(self):
        self.tabela.delete(*self.tabela.get_children())
        for u in auth.listar_usuarios(): self.tabela.insert("","end",iid=str(u["id"]),values=(u["nome_completo"],u["nome_usuario"],u["papel"],"Sim" if u["ativo"] else "Não"),tags=() if u["ativo"] else ("inativo",))
    def _usuario_selecionado_id(self):
        s=self.tabela.selection()
        if not s: messagebox.showwarning("Nenhum usuário selecionado","Selecione um usuário na lista primeiro."); return None
        return int(s[0])
    def _alternar_ativo(self):
        i=self._usuario_selecionado_id()
        if i is None: return
        u=next((x for x in auth.listar_usuarios() if x["id"]==i),None)
        if not u: return
        novo=not u["ativo"]
        if not novo and u["papel"]=="admin" and auth.contar_admins_ativos()<=1: messagebox.showerror("Não é possível desativar","Este é o único administrador ativo. Crie outro administrador antes de desativar este."); return
        auth.definir_ativo(i,novo); self._recarregar()
    def _redefinir_senha(self):
        i=self._usuario_selecionado_id()
        if i is None: return
        nova=_pedir_texto_simples(self,"🔑 Redefinir senha","Nova senha (mín. 8 caracteres):")
        if nova is None: return
        try: auth.redefinir_senha(i,nova)
        except auth.ErroAutenticacao as erro: messagebox.showerror("Não foi possível redefinir",str(erro)); return
        messagebox.showinfo("Senha redefinida","A senha foi redefinida com sucesso.")
    def _criar_usuario(self):
        try: auth.criar_usuario(self.var_nome_usuario.get(),self.var_nome_completo.get(),self.var_senha.get(),self.var_papel.get())
        except auth.ErroAutenticacao as erro: messagebox.showerror("Não foi possível criar",str(erro)); return
        self.var_nome_completo.set(""); self.var_nome_usuario.set(""); self.var_senha.set(""); self._recarregar()


def iniciar():
    root=tk.Tk(); AplicativoPedidos(root); root.mainloop()


if __name__ == "__main__":
    iniciar()

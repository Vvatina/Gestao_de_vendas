# ARQUIVO: popups.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import re
from datetime import datetime

BG_COLOR = "#E6D9E0"
CARD_COLOR = "#FFFFFF"
PRIMARY_COLOR = "#5D1B8B"
BUTTON_BG = "#97589C"
BUTTON_HOVER = "#7A3E80"
TEXT_COLOR = "#FFFFFF"

class ProdutoPopup(tk.Toplevel):
    def __init__(self, master, db, produto_atual=None):
        super().__init__(master)
        self.db = db
        self.produto_atual = produto_atual

        self.title("Gerir Produto")
        self.geometry("500x600")
        self.configure(bg=BG_COLOR)  # Fundo Lilás Suave
        self.resizable(False, False)

        # Categorias
        self.categorias_padrao = [
            "Base", "Corretor", "Pó Compacto/Solto", "Blush", "Iluminador",
            "Bronzeador", "Sombra", "Máscara de pestanas", "Delineador",
            "Lápis de Olhos", "Batom", "Gloss", "Lápis de Lábios",
            "Sobrancelhas", "Primer/Fixador", "Paletas/Kits"
        ]

        self.setup_ui()
        if produto_atual:
            self.preencher_campos()

    #layout
    def setup_ui(self):
        main_frame = tk.Frame(self, bg=BG_COLOR)
        main_frame.pack(fill="both", expand=True)

        self.card = tk.Frame(main_frame, bg=CARD_COLOR, bd=1, relief="solid")
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=420, height=520)

        titulo_txt = "Novo Produto" if not self.produto_atual else "Editar Produto"
        tk.Label(self.card, text=titulo_txt.upper(), bg=CARD_COLOR, fg=PRIMARY_COLOR,
                 font=("Segoe UI", 16, "bold")).pack(pady=(30, 20))

        def criar_input(rotulo):
            frame = tk.Frame(self.card, bg=CARD_COLOR)
            frame.pack(fill="x", padx=40, pady=5)

            lbl = tk.Label(frame, text=rotulo, bg=CARD_COLOR, fg="#555555",
                           font=("Segoe UI", 9, "bold"))
            lbl.pack(anchor="w")
            return frame

        f_nome = criar_input("NOME DO PRODUTO")
        self.entry_nome = self.estilizar_entry(tk.Entry(f_nome))
        self.entry_nome.pack(fill="x", ipady=4, pady=(2, 0))

        f_cat = criar_input("CATEGORIA")
        self.entry_cat = ttk.Combobox(f_cat, values=self.categorias_padrao, state="readonly", font=("Segoe UI", 11))
        self.entry_cat.pack(fill="x", ipady=4, pady=(2, 0))

        f_marca = criar_input("MARCA")
        self.entry_marca = self.estilizar_entry(tk.Entry(f_marca))
        self.entry_marca.pack(fill="x", ipady=4, pady=(2, 0))

        f_duplo = tk.Frame(self.card, bg=CARD_COLOR)
        f_duplo.pack(fill="x", padx=40, pady=10)

        f_preco = tk.Frame(f_duplo, bg=CARD_COLOR)
        f_preco.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(f_preco, text="PREÇO (€)", bg=CARD_COLOR, fg="#555", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.entry_preco = self.estilizar_entry(tk.Entry(f_preco))
        self.entry_preco.pack(fill="x", ipady=4)

        f_qtd = tk.Frame(f_duplo, bg=CARD_COLOR)
        f_qtd.pack(side="right", fill="x", expand=True, padx=(10, 0))
        tk.Label(f_qtd, text="STOCK (UN)", bg=CARD_COLOR, fg="#555", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.entry_qtd = self.estilizar_entry(tk.Entry(f_qtd))
        self.entry_qtd.pack(fill="x", ipady=4)

        self.btn_salvar = tk.Button(self.card, text="SALVAR DADOS", command=self.salvar,
                                    bg=BUTTON_BG, fg="white",
                                    font=("Segoe UI", 11, "bold"),
                                    relief="flat", cursor="hand2")
        self.btn_salvar.pack(fill="x", padx=40, pady=(30, 20), ipady=5)

        self.btn_salvar.bind("<Enter>", lambda e: self.btn_salvar.config(bg=BUTTON_HOVER))
        self.btn_salvar.bind("<Leave>", lambda e: self.btn_salvar.config(bg=BUTTON_BG))

    def estilizar_entry(self, widget):
        widget.config(bg="#F5F5F5", fg="#333", font=("Segoe UI", 11),
                      relief="flat", highlightthickness=1, highlightbackground="#DDD", highlightcolor=PRIMARY_COLOR)
        return widget

    def preencher_campos(self):
        self.entry_nome.insert(0, self.produto_atual[1])
        self.entry_cat.set(self.produto_atual[2])
        self.entry_marca.insert(0, self.produto_atual[3])
        self.entry_preco.insert(0, str(self.produto_atual[4]))
        self.entry_qtd.insert(0, str(self.produto_atual[5]))

    def salvar(self):
        try:
            nome = self.entry_nome.get().strip()
            cat = self.entry_cat.get()
            marca = self.entry_marca.get().strip()

            preco_raw = self.entry_preco.get().replace(",", ".").replace("€", "")
            qtd_raw = self.entry_qtd.get()

            if not nome or not cat:
                return messagebox.showwarning("Atenção", "Os campos Nome e Categoria são obrigatórios.")

            if not preco_raw: preco_raw = "0"
            if not qtd_raw: qtd_raw = "0"

            preco = float(preco_raw)
            qtd = int(float(qtd_raw))

            # Atualizar
            if self.produto_atual:
                self.db.atualizar_produto(self.produto_atual[0], nome, cat, marca, preco, qtd)
            else:
                self.db.adicionar_produto(nome, cat, marca, preco, qtd)

            messagebox.showinfo("Sucesso", "Produto salvo com sucesso!")
            self.destroy()
            if hasattr(self.master, "open_produtos"):
                self.master.open_produtos()

        except ValueError:
            messagebox.showerror("Erro de Formato", "O Preço e a Quantidade devem ser números válidos.\nExemplo: 12.50")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}")
    pass


class FuncionarioPopup(tk.Toplevel):
    def __init__(self, master, db, func_atual=None):
        super().__init__(master)
        self.db = db
        self.func_atual = func_atual

        titulo = "Editar Funcionário" if func_atual else "Novo Funcionário"
        self.title(titulo)
        self.geometry("400x580")
        self.configure(bg=BG_COLOR)
        self.resizable(False, False)
        self.setup_ui(titulo)
        if func_atual: self.preencher_campos()

    #layout
    def setup_ui(self, titulo_texto):
        main_frame = tk.Frame(self, bg=BG_COLOR)
        main_frame.pack(fill="both", expand=True)
        self.card = tk.Frame(main_frame, bg=CARD_COLOR, bd=1, relief="solid")
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=340, height=500)

        tk.Label(self.card, text=titulo_texto.upper(), bg=CARD_COLOR, fg=PRIMARY_COLOR,
                 font=("Segoe UI", 14, "bold")).pack(pady=(25, 20))

        self.criar_label("NOME COMPLETO")
        self.entry_nome = self.criar_entry()
        self.criar_label("UTILIZADOR (LOGIN)")
        self.entry_user = self.criar_entry()
        self.criar_label("PALAVRA-PASSE")
        self.entry_pass = self.criar_entry(is_password=True)
        self.criar_label("CARGO")
        self.entry_cargo = ttk.Combobox(self.card, values=["Admin", "Funcionario"], state="readonly",
                                        font=("Segoe UI", 11))
        self.entry_cargo.pack(fill="x", padx=30, ipady=4)
        self.entry_cargo.current(1)

        btn = tk.Button(self.card, text="GRAVAR DADOS", command=self.salvar, bg=BUTTON_BG, fg="white",
                        font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2")
        btn.pack(fill="x", padx=30, pady=(30, 20), ipady=5)
        btn.bind("<Enter>", lambda e: btn.config(bg=BUTTON_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=BUTTON_BG))

    def criar_label(self, texto):
        tk.Label(self.card, text=texto, bg=CARD_COLOR, fg="#555", font=("Segoe UI", 9, "bold")).pack(anchor="w",
                                                                                                     padx=30,
                                                                                                     pady=(10, 0))

    def criar_entry(self, is_password=False):
        show_char = "*" if is_password else ""
        e = tk.Entry(self.card, font=("Segoe UI", 11), bg="#F5F5F5", relief="flat", highlightthickness=1,
                     highlightbackground="#DDD", highlightcolor=PRIMARY_COLOR, show=show_char)
        e.pack(fill="x", padx=30, ipady=4)
        return e

    def preencher_campos(self):
        try:
            self.entry_nome.insert(0, self.func_atual[1])
            self.entry_user.insert(0, self.func_atual[2])
            self.entry_pass.insert(0, self.func_atual[3])
            self.entry_cargo.set(self.func_atual[4])
        except IndexError:
            pass

    def salvar(self):
        nome = self.entry_nome.get().strip()
        user = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        cargo = self.entry_cargo.get()

        if not nome or not user or not password or not cargo: return messagebox.showwarning("Aviso", "Preencha tudo!")
        if len(password) < 3: return messagebox.showwarning("Segurança", "Password curta.")

        try:
            if self.func_atual:
                self.db.atualizar_funcionario(self.func_atual[0], nome, user, password, cargo)
                messagebox.showinfo("Sucesso", "Atualizado!")
            else:
                self.db.adicionar_funcionario(nome, user, password, cargo)
                messagebox.showinfo("Sucesso", "Criado!")
            self.destroy()
            if hasattr(self.master, "open_funcionarios"): self.master.open_funcionarios()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Utilizador já existe.")
        except Exception as e:
            messagebox.showerror("Erro", f"{e}")


class ClientePopup(tk.Toplevel):
    def __init__(self, master, db, cliente_atual=None):
        super().__init__(master)
        self.db = db
        self.cli_atual = cliente_atual

        titulo = "Editar Cliente" if cliente_atual else "Novo Cliente"
        self.title(titulo)
        self.geometry("400x520")
        self.configure(bg=BG_COLOR)
        self.resizable(False, False)
        self.setup_ui(titulo)
        if cliente_atual: self.preencher_campos()

    #layout
    def setup_ui(self, titulo_texto):
        main_frame = tk.Frame(self, bg=BG_COLOR)
        main_frame.pack(fill="both", expand=True)
        self.card = tk.Frame(main_frame, bg=CARD_COLOR, bd=1, relief="solid")
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=340, height=440)

        tk.Label(self.card, text=titulo_texto.upper(), bg=CARD_COLOR, fg=PRIMARY_COLOR,
                 font=("Segoe UI", 14, "bold")).pack(pady=(25, 20))

        self.criar_label("NOME COMPLETO")
        self.entry_nome = self.criar_entry()
        self.criar_label("TELEFONE")
        self.entry_tel = self.criar_entry()
        self.criar_label("EMAIL")
        self.entry_email = self.criar_entry()

        btn = tk.Button(self.card, text="GRAVAR DADOS", command=self.salvar, bg=BUTTON_BG, fg="white",
                        font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2")
        btn.pack(fill="x", padx=30, pady=(30, 20), ipady=5)
        btn.bind("<Enter>", lambda e: btn.config(bg=BUTTON_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=BUTTON_BG))

    def criar_label(self, texto):
        tk.Label(self.card, text=texto, bg=CARD_COLOR, fg="#555", font=("Segoe UI", 9, "bold")).pack(anchor="w",
                                                                                                     padx=30,
                                                                                                     pady=(10, 0))

    def criar_entry(self):
        e = tk.Entry(self.card, font=("Segoe UI", 11), bg="#F5F5F5", relief="flat", highlightthickness=1,
                     highlightbackground="#DDD", highlightcolor=PRIMARY_COLOR)
        e.pack(fill="x", padx=30, ipady=4)
        return e

    def preencher_campos(self):
        self.entry_nome.insert(0, self.cli_atual[1])
        self.entry_tel.insert(0, self.cli_atual[2])
        self.entry_email.insert(0, self.cli_atual[3])

    def salvar(self):
        nome = self.entry_nome.get().strip()
        tel = self.entry_tel.get().strip()
        email = self.entry_email.get().strip()

        if not nome: return messagebox.showwarning("Aviso", "Nome obrigatório.")

        # Regex Telefone
        if not re.match(r"^(\+\d{1,3})?\s?\d{9}$", tel):
            return messagebox.showwarning("Erro", "Telefone inválido (Ex: 912345678 ou +351 912345678)")

        # Regex Email
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            return messagebox.showwarning("Erro", "Email inválido.")

        try:
            if self.cli_atual:
                self.db.atualizar_cliente(self.cli_atual[0], nome, tel, email)
                messagebox.showinfo("Sucesso", "Atualizado!")
            else:
                self.db.adicionar_cliente(nome, tel, email)
                messagebox.showinfo("Sucesso", "Criado!")
            self.destroy()
            if hasattr(self.master, "open_clientes"): self.master.open_clientes()
        except Exception as e:
            messagebox.showerror("Erro", f"{e}")


class EncomendaPopup(tk.Toplevel):
    def __init__(self, master, db, user):
        super().__init__(master)
        self.db = db
        self.user = user
        self.itens_compra = []  # Carrinho: Lista de (id, qtd, preco)

        self.title("POS - Nova Venda")
        self.state("zoomed")
        self.configure(bg=BG_COLOR)

        #estrutura principal
        self.setup_ui_structure()

        self.setup_left_panel()  # carrinho
        self.setup_right_panel()  # produtos

        # carregar dados
        self.carregar_dados_seguro()

    def setup_ui_structure(self):
        main_container = tk.Frame(self, bg=BG_COLOR)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # painel esquerdo (carrinho)
        self.left_panel = tk.Frame(main_container, bg=CARD_COLOR, bd=0,
                                   highlightthickness=1, highlightbackground="#D1C4D9")
        self.left_panel.pack(side="left", fill="y", padx=(0, 20))
        self.left_panel.pack_propagate(False)
        self.left_panel.config(width=420)

        # painel direito (produtos)
        self.right_panel = tk.Frame(main_container, bg=BG_COLOR)
        self.right_panel.pack(side="right", fill="both", expand=True)

    def setup_left_panel(self):
        header = tk.Frame(self.left_panel, bg=PRIMARY_COLOR, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="RESUMO DO PEDIDO", bg=PRIMARY_COLOR, fg="white",
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=20)

        # combox clientes
        tk.Label(self.left_panel, text="CLIENTE", font=("Segoe UI", 10, "bold"),
                 bg=CARD_COLOR, fg=PRIMARY_COLOR).pack(anchor="w", padx=20, pady=(20, 5))

        self.clientes = self.db.consultar_clientes()
        self.cli_map = {f"{c[1]}": c[0] for c in self.clientes}  # nome e id de cada cliente

        self.cb_cli = ttk.Combobox(self.left_panel, values=list(self.cli_map.keys()),
                                   state="readonly", font=("Segoe UI", 11))
        self.cb_cli.pack(fill="x", padx=20, ipady=4)

        # itens selecionados
        tk.Label(self.left_panel, text="ITENS SELECIONADOS", font=("Segoe UI", 10, "bold"),
                 bg=CARD_COLOR, fg=PRIMARY_COLOR).pack(anchor="w", padx=20, pady=(20, 5))

        tree_frame = tk.Frame(self.left_panel, bg=CARD_COLOR)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # treeview
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("Treeview", rowheight=25)

        self.tree = ttk.Treeview(tree_frame, columns=("Prod", "Qtd", "Total"), show="headings")
        self.tree.heading("Prod", text="Produto");
        self.tree.column("Prod", width=160)
        self.tree.heading("Qtd", text="Qtd");
        self.tree.column("Qtd", width=50, anchor="center")
        self.tree.heading("Total", text="Total");
        self.tree.column("Total", width=70, anchor="e")

        # scroll
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.reduzir_item)

        # finalizar venda
        bottom_frame = tk.Frame(self.left_panel, bg="#F9F9F9", bd=1, relief="solid")
        bottom_frame.pack(side="bottom", fill="x")

        self.lbl_total_valor = tk.Label(bottom_frame, text="0.00 €",
                                        font=("Segoe UI", 26, "bold"),
                                        bg="#F9F9F9", fg=PRIMARY_COLOR)
        self.lbl_total_valor.pack(pady=(15, 5))

        btn_finish = tk.Button(bottom_frame, text="FINALIZAR VENDA", command=self.finalizar_venda,
                               bg=BUTTON_BG, fg="white", font=("Segoe UI", 12, "bold"),
                               relief="flat", cursor="hand2")
        btn_finish.pack(fill="x", padx=20, pady=20, ipady=8)

        btn_finish.bind("<Enter>", lambda e: btn_finish.config(bg=BUTTON_HOVER))
        btn_finish.bind("<Leave>", lambda e: btn_finish.config(bg=BUTTON_BG))

    def setup_right_panel(self):
        #barra de pesquisa de produtos
        search_container = tk.Frame(self.right_panel, bg=BG_COLOR)
        search_container.pack(fill="x", pady=(0, 15))

        f_entry = tk.Frame(search_container, bg="white", bd=0, highlightthickness=1, highlightbackground=BUTTON_BG)
        f_entry.pack(fill="x", ipady=8, padx=5)

        lbl_icon = tk.Label(f_entry, text="🔍", bg="white", fg=PRIMARY_COLOR, font=("Segoe UI", 12))
        lbl_icon.pack(side="left", padx=10)

        self.search_entry = tk.Entry(f_entry, font=("Segoe UI", 12), bg="white", bd=0, fg="#333")
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.filtrar_pesquisa)  # Filtra ao digitar

        #filtro dos produtos
        self.cat_frame = tk.Frame(self.right_panel, bg=BG_COLOR)
        self.cat_frame.pack(fill="x", pady=(0, 10))

        # area dos botões com produtos
        container = tk.Frame(self.right_panel, bg=BG_COLOR)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=BG_COLOR, highlightthickness=0)
        sb_v = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = tk.Frame(self.canvas, bg=BG_COLOR)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=sb_v.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        sb_v.pack(side="right", fill="y")

        # scroll
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def carregar_dados_seguro(self):
        conn = self.db.connect()
        c = conn.cursor()

        try:
            c.execute("SELECT * FROM Produtos")
            raw_data = c.fetchall()

            self.todos_produtos = []
            for row in raw_data:
                p_id = row[0]
                p_nome = row[1]
                p_cat = row[2] if len(row) > 2 else "Geral"

                p_preco = 0.0
                p_stock = 0

                # Tenta encontrar o preço na linha
                for item in row:
                    if isinstance(item, float): p_preco = item
                    if isinstance(item, int) and item > 1000:
                        pass  # Ignora IDs grandes
                    elif isinstance(item, int) and item != p_id:
                        p_stock = item

                if p_stock == 0: p_stock = 50

                self.todos_produtos.append((p_id, p_nome, p_cat, "Marca", p_preco, p_stock))

        except Exception as e:
            messagebox.showerror("Erro BD", f"Erro ao ler produtos: {e}")
            self.todos_produtos = []

        conn.close()

        categorias = sorted(list(set(p[2] for p in self.todos_produtos)))
        self.criar_botoes_categoria(categorias)

        self.carregar_botoes_produtos(self.todos_produtos)

    def criar_botoes_categoria(self, categorias):
        for w in self.cat_frame.winfo_children(): w.destroy()

        self.btn_filtros = {}

        def cmd(c):
            return lambda: self.filtrar_categoria(c)

        #botão tudo (fixo)
        b = tk.Button(self.cat_frame, text="TUDO", command=cmd("TUDO"),
                      bg=PRIMARY_COLOR, fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=15)
        b.pack(side="left", padx=5)
        self.btn_filtros["TUDO"] = b

        # Botoões das outras categorias que variam de acordo com os produtos inseridos
        for cat in categorias:
            b = tk.Button(self.cat_frame, text=cat.upper(), command=cmd(cat),
                          bg="white", fg=PRIMARY_COLOR, font=("Segoe UI", 9, "bold"), relief="flat", padx=15)
            b.pack(side="left", padx=5)
            self.btn_filtros[cat] = b

    def carregar_botoes_produtos(self, lista):
        for w in self.scrollable_frame.winfo_children(): w.destroy()

        cols = 4  # Número de colunas na grelha

        for i, prod in enumerate(lista):
            p_id, p_nome, p_cat, p_marca, p_preco, p_stock = prod

            row = i // cols
            col = i % cols

            texto = f"{p_nome}\n\n{p_preco:.2f} €"

            if p_stock <= 0:
                bg_btn = "#E0E0E0"
                fg_btn = "#999"
                texto = f"{p_nome}\n\nESGOTADO"
                state = "disabled"
                cursor = "arrow"
            else:
                bg_btn = "white"
                fg_btn = PRIMARY_COLOR
                state = "normal"
                cursor = "hand2"

            btn = tk.Button(self.scrollable_frame, text=texto,
                            font=("Segoe UI", 11, "bold"),
                            bg=bg_btn, fg=fg_btn,
                            relief="flat", bd=0,
                            highlightthickness=1, highlightbackground=BUTTON_BG,
                            width=22, height=8,
                            wraplength=160, justify="center",
                            cursor=cursor, state=state,
                            command=lambda p=prod: self.adicionar_item(p))

            btn.grid(row=row, column=col, padx=8, pady=8)

            if state == "normal":
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#F3EBFF"))  # Roxo muito claro
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg="white"))

    def filtrar_pesquisa(self, event):
        termo = self.search_entry.get().lower()
        if termo == "":
            self.filtrar_categoria("TUDO")  # Reseta se vazio
            return

        filtrados = [p for p in self.todos_produtos if termo in p[1].lower()]

        for b in self.btn_filtros.values(): b.config(bg="white", fg=PRIMARY_COLOR)

        self.carregar_botoes_produtos(filtrados)

    def filtrar_categoria(self, categoria):
        self.search_entry.delete(0, tk.END)

        for cat, btn in self.btn_filtros.items():
            if cat == categoria:
                btn.config(bg=PRIMARY_COLOR, fg="white")
            else:
                btn.config(bg="white", fg=PRIMARY_COLOR)

        if categoria == "TUDO":
            self.carregar_botoes_produtos(self.todos_produtos)
        else:
            filtrados = [p for p in self.todos_produtos if p[2] == categoria]
            self.carregar_botoes_produtos(filtrados)

    # logica do carrinho de compras
    def adicionar_item(self, prod):
        p_id, p_nome, _, _, p_preco, p_stock = prod

        # Verifica se já existe
        for i, item in enumerate(self.itens_compra):
            if item[0] == p_id:
                if item[1] + 1 > p_stock:
                    return messagebox.showwarning("Stock", f"Apenas {p_stock} unidades disponíveis.")
                # Atualiza quantidade
                self.itens_compra[i] = (p_id, item[1] + 1, p_preco)
                self.atualizar_tabela()
                return

        self.itens_compra.append((p_id, 1, p_preco))
        self.atualizar_tabela()

    def reduzir_item(self, event):
        sel = self.tree.selection()
        if not sel: return
        idx = self.tree.index(sel[0])

        item = self.itens_compra[idx]
        if item[1] > 1:
            self.itens_compra[idx] = (item[0], item[1] - 1, item[2])
        else:
            self.itens_compra.pop(idx)
        self.atualizar_tabela()

    def atualizar_tabela(self):
        for i in self.tree.get_children(): self.tree.delete(i)

        total = 0
        for p_id, qtd, preco in self.itens_compra:
            nome = next((p[1] for p in self.todos_produtos if p[0] == p_id), "Produto")
            sub = qtd * preco
            total += sub
            self.tree.insert("", "end", values=(nome, qtd, f"{sub:.2f} €"))

        self.lbl_total_valor.config(text=f"{total:.2f} €")

    def finalizar_venda(self):
        if not self.itens_compra:
            return messagebox.showwarning("Vazio", "Adicione produtos ao carrinho.")
        if not self.cb_cli.get():
            return messagebox.showwarning("Cliente", "Selecione um cliente.")

        try:
            cli_id = self.cli_map[self.cb_cli.get()]
            hoje = datetime.today().strftime('%Y-%m-%d')

            # Salvar na BD
            self.db.adicionar_encomenda(hoje, cli_id, self.itens_compra, self.user['id'])

            messagebox.showinfo("Sucesso", f"Venda de {self.lbl_total_valor.cget('text')} registada!")
            self.destroy()

            # Atualiza janela principal
            if hasattr(self.master, "open_encomendas"):
                self.master.open_encomendas()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gravar: {e}")
    pass
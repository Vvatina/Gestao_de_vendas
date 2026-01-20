import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
import functools  # Importante para os botões funcionarem
import re
import hashlib
from popups import FuncionarioPopup, ClientePopup, EncomendaPopup, ProdutoPopup

# ------------------- CONFIGURAÇÕES -------------------
PRIMARY_COLOR = "#5D1B8B"
SECONDARY_COLOR = "#2C1F8C"
BUTTON_BG = "#97589C"
TEXT_COLOR = "#FFFFFF"
BG_COLOR = "#E6D9E0"
CARD_COLOR = "#FFFFFF"
BUTTON_HOVER = "#7A3E80"
ACCENT_COLOR = "#2C1F8C"
#base
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

class MaquilhagemDB:
    def __init__(self, db_name="maquilhagem.db"):
        self.db_name = db_name
        self.init_db()

    def connect(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        conn = self.connect()
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS Clientes (
                        CodCli INTEGER PRIMARY KEY AUTOINCREMENT, 
                        NomeCli TEXT NOT NULL, 
                        Telefone TEXT, 
                        Email TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS Produtos (
                        CodProd INTEGER PRIMARY KEY AUTOINCREMENT, 
                        Produto TEXT NOT NULL, 
                        Categoria TEXT, Marca TEXT, 
                        Preco REAL NOT NULL, 
                        Quantidade INTEGER NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS Funcionarios (
                        CodFunc INTEGER PRIMARY KEY AUTOINCREMENT, 
                        Nome TEXT NOT NULL, 
                        Username TEXT UNIQUE NOT NULL, 
                        Password TEXT NOT NULL, 
                        Cargo TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS Encomendas (
                        NEnc INTEGER PRIMARY KEY AUTOINCREMENT,
                        DataEnc DATE NOT NULL,
                        CodCli INTEGER,
                        CodFunc INTEGER,
                        FOREIGN KEY (CodCli) REFERENCES Clientes(CodCli) ON DELETE RESTRICT,
                        FOREIGN KEY (CodFunc) REFERENCES Funcionarios(CodFunc) ON DELETE RESTRICT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS ItensEncomenda (
                        NItem INTEGER PRIMARY KEY AUTOINCREMENT,
                        NEnc INTEGER,
                        CodProd INTEGER,
                        Quant INTEGER,
                        PrecoUnitario REAL,
                        FOREIGN KEY (NEnc) REFERENCES Encomendas(NEnc) ON DELETE CASCADE,
                        FOREIGN KEY (CodProd) REFERENCES Produtos(CodProd) ON DELETE RESTRICT)""")
        conn.commit()

        # Utilizador inicial (admin)
        c.execute("SELECT COUNT(*) FROM Funcionarios")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO Funcionarios (Nome, Username, Password, Cargo) VALUES (?, ?, ?, ?)",
                      ("Administrador", "admin", hash_password("admin123"), "Admin"))
            conn.commit()
        conn.close()

    # Métodos
    def efetuar_login(self, username, password):
        conn = self.connect()
        c = conn.cursor()
        c.execute("SELECT CodFunc, Nome, Cargo, Password FROM Funcionarios WHERE Username=?", (username,))
        row = c.fetchone()
        conn.close()
        if row and row[3] == hash_password(password):
            return {"id": row[0], "nome": row[1], "cargo": row[2], "username": username}
        return None

    # Clientes
    def consultar_clientes(self):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM Clientes").fetchall()
    def adicionar_cliente(self, nome, telefone, email):
        with self.connect() as conn:
            conn.execute("INSERT INTO Clientes (NomeCli, Telefone, Email) VALUES (?, ?, ?)",
                         (nome, telefone, email))
    def atualizar_cliente(self, cod, nome, telefone, email):
        with self.connect() as conn:
            conn.execute("UPDATE Clientes SET NomeCli=?, Telefone=?, Email=? WHERE CodCli=?",
                         (nome, telefone, email, cod))
    def excluir_cliente(self, cod):
        with self.connect() as conn:
            conn.execute("DELETE FROM Clientes WHERE CodCli=?", (cod,))

    # Produtos
    def consultar_produtos(self):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM Produtos").fetchall()
    def obter_produto_por_id(self, cod_prod):
        with self.connect() as conn:
            return conn.execute("SELECT CodProd, Produto, Preco, Quantidade FROM Produtos WHERE CodProd=?",
                                (cod_prod,)).fetchone()
    def adicionar_produto(self, produto, categoria, marca, preco, quantidade):
        with self.connect() as conn:
            conn.execute("INSERT INTO Produtos (Produto, Categoria, Marca, Preco, Quantidade) VALUES (?, ?, ?, ?, ?)",
                         (produto, categoria, marca, float(preco), int(quantidade)))
    def atualizar_produto(self, cod, produto, categoria, marca, preco, quantidade):
        with self.connect() as conn:
            conn.execute("UPDATE Produtos SET Produto=?, Categoria=?, Marca=?, Preco=?, Quantidade=? WHERE CodProd=?",
                         (produto, categoria, marca, float(preco), int(quantidade), cod))

        # Na classe Database

    def excluir_produto(self, cod):
        conn = sqlite3.connect("maquilhagem.db")
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON")

            # Tenta apagar
            cursor.execute("DELETE FROM Produtos WHERE CodProd=?", (cod,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Se der erro (produto já vendido), fecha e retorna False
            conn.close()
            return False

    # Funcionários
    def consultar_funcionarios(self):
        with self.connect() as conn:
            return conn.execute("SELECT CodFunc, Nome, Username, Cargo FROM Funcionarios").fetchall()
    def adicionar_funcionario(self, nome, username, password, cargo):
        with self.connect() as conn:
            conn.execute("INSERT INTO Funcionarios (Nome, Username, Password, Cargo) VALUES (?, ?, ?, ?)",
                         (nome, username, hash_password(password), cargo))
    def atualizar_funcionario(self, cod, nome, username, password, cargo):
        with self.connect() as conn:
            if password:
                conn.execute("UPDATE Funcionarios SET Nome=?, Username=?, Password=?, Cargo=? WHERE CodFunc=?",
                             (nome, username, hash_password(password), cargo, cod))
            else:
                conn.execute("UPDATE Funcionarios SET Nome=?, Username=?, Cargo=? WHERE CodFunc=?",
                             (nome, username, cargo, cod))
    def excluir_funcionario(self, cod):
        with self.connect() as conn:
            conn.execute("DELETE FROM Funcionarios WHERE CodFunc=?", (cod,))

    # Encomendas
    def adicionar_encomenda(self, data, cod_cli, itens: list, cod_func):
        conn = self.connect()
        c = conn.cursor()
        c.execute("INSERT INTO Encomendas (DataEnc, CodCli, CodFunc) VALUES (?, ?, ?)",
                  (data, cod_cli, cod_func))
        nenc = c.lastrowid
        for item in itens:
            cod_prod, quant, preco_unitario = item
            c.execute("SELECT Quantidade FROM Produtos WHERE CodProd=?", (cod_prod,))
            stock = c.fetchone()[0]
            if stock < quant:
                conn.rollback()
                conn.close()
                raise ValueError(f"Stock insuficiente para o produto ID {cod_prod}. Disponível: {stock}")
            c.execute("INSERT INTO ItensEncomenda (NEnc, CodProd, Quant, PrecoUnitario) VALUES (?, ?, ?, ?)",
                      (nenc, cod_prod, quant, preco_unitario))
            c.execute("UPDATE Produtos SET Quantidade = Quantidade - ? WHERE CodProd=?", (quant, cod_prod))
        conn.commit()
        conn.close()
        return True

    def consultar_encomendas(self, cod_func_filter=None):
        conn = self.connect()
        c = conn.cursor()
        sql = """SELECT 
                    E.NEnc, 
                    E.DataEnc, 
                    C.NomeCli, 
                    F.Nome,
                    SUM(I.Quant * I.PrecoUnitario) AS Total
                 FROM Encomendas E
                 JOIN Clientes C ON E.CodCli=C.CodCli
                 JOIN Funcionarios F ON E.CodFunc=F.CodFunc
                 JOIN ItensEncomenda I ON E.NEnc=I.NEnc"""
        params = []
        if cod_func_filter:
            sql += " WHERE E.CodFunc = ?"
            params.append(cod_func_filter)
        sql += " GROUP BY E.NEnc, E.DataEnc, C.NomeCli, F.Nome ORDER BY E.NEnc DESC"
        rows = c.execute(sql, params).fetchall()
        conn.close()
        return rows

    def excluir_encomenda(self, nenc):
        conn = self.connect()
        c = conn.cursor()
        c.execute("SELECT CodProd, Quant FROM ItensEncomenda WHERE NEnc=?", (nenc,))
        itens = c.fetchall()
        for cod_prod, quant in itens:
            c.execute("UPDATE Produtos SET Quantidade = Quantidade + ? WHERE CodProd=?", (quant, cod_prod))

        c.execute("DELETE FROM ItensEncomenda WHERE NEnc=?", (nenc,))

        c.execute("DELETE FROM Encomendas WHERE NEnc=?", (nenc,))
        conn.commit()
        conn.close()


    def resumo_vendas_funcionarios(self, cod_func=None):
        with self.connect() as conn:
            sql = """
                SELECT 
                    F.Nome,
                    COUNT(DISTINCT E.NEnc) AS NumEncomendas,
                    IFNULL(SUM(I.Quant * I.PrecoUnitario), 0) AS TotalVendas
                FROM Funcionarios F
                LEFT JOIN Encomendas E ON F.CodFunc = E.CodFunc
                LEFT JOIN ItensEncomenda I ON E.NEnc = I.NEnc
            """
            params = []

            if cod_func:
                sql += " WHERE F.CodFunc = ?"
                params.append(cod_func)

            sql += " GROUP BY F.CodFunc, F.Nome"

            return conn.execute(sql, params).fetchall()

    def vendas_por_funcionario_mes(self, cod_func):
        with self.connect() as conn:
            # Seleciona o Mês (YYYY-MM) e a Soma Total das vendas desse mês
            sql = """
            SELECT 
                strftime('%Y-%m', E.DataEnc) AS Mes,
                SUM(I.Quant * I.PrecoUnitario) AS Total
            FROM Encomendas E
            JOIN ItensEncomenda I ON E.NEnc = I.NEnc
            WHERE E.CodFunc = ?
            GROUP BY Mes
            ORDER BY Mes
            """
            return conn.execute(sql, (cod_func,)).fetchall()


# ------------------- INTERFACE GRÁFICA -------------------
class LoginWindow(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("Login")
        self.geometry("500x600")
        self.configure(bg=BG_COLOR)
        self.resizable(True, True)

        frame = tk.Frame(self, bg=BG_COLOR)
        frame.pack(expand=True, fill="both")

        # Logo
        img = Image.open("icons/logo.png").resize((200,200))
        self.logo_img = ImageTk.PhotoImage(img)
        tk.Label(frame, image=self.logo_img, bg=BG_COLOR).pack(pady=20)

        tk.Label(frame, text="Bem-vindo ao Sistema de Gestão de Maquilhagem!",
                 bg=BG_COLOR, fg=PRIMARY_COLOR, font=("Arial",16,"bold"), wraplength=400, justify="center").pack(pady=30)

        tk.Label(frame, text="Utilizador", bg=BG_COLOR, font=("Arial", 12, "bold")).pack(anchor="w", padx=40)
        self.user = tk.Entry(frame, font=("Arial",12), bd=2, relief="groove")
        self.user.pack(fill="x", padx=40, pady=(0,15))

        tk.Label(frame, text="Palavra-passe", bg=BG_COLOR, font=("Arial", 12, "bold")).pack(anchor="w", padx=40)
        self.pwd = tk.Entry(frame, show="*", font=("Arial",12), bd=2, relief="groove")
        self.pwd.pack(fill="x", padx=40, pady=(0,25))

        tk.Button(frame, text="Entrar", command=self.login,
                  bg=BUTTON_BG, fg=TEXT_COLOR, font=("Arial",14,"bold"),
                  relief="flat", padx=10, pady=10, activebackground=SECONDARY_COLOR,
                  cursor="hand2").pack(fill="x", padx=40)

        tk.Label(frame, text="© 2025 Sistema Maquilhagem", bg=BG_COLOR, fg=PRIMARY_COLOR, font=("Arial",10)).pack(pady=20)

    def login(self):
        res = self.db.efetuar_login(self.user.get(), self.pwd.get())
        if res:
            self.destroy()
            MainApp(self.db, res).mainloop()
        else:
            messagebox.showerror("Erro", "Login inválido")

# ------------------- MAIN APP -------------------
class MainApp(tk.Tk):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.title(f"Sistema - {user['nome']} ({user['cargo']})")
        self.geometry("1100x650")
        self.configure(bg=BG_COLOR)
        self.relatorio_frame = None

        # Sidebar
        self.sidebar = tk.Frame(self, bg=PRIMARY_COLOR, width=160)
        self.sidebar.pack(side="left", fill="y")


        # carregar ícones
        self.icons = {}
        icon_files = {
            "clientes": "icons/clientes.png",
            "produtos": "icons/produtos.png",
            "encomendas": "icons/encomendas.png",
            "funcionarios": "icons/funcionarios.png",
            "logout": "icons/logout.png",
            "relatorios": "icons/relatorio.png"

        }
        for key, file in icon_files.items():
            img = Image.open(file).resize((50,50))
            self.icons[key] = ImageTk.PhotoImage(img)

        self.btn_frame_top = tk.Frame(self.sidebar, bg=PRIMARY_COLOR)
        self.btn_frame_top.pack(side="top", fill="y", pady=20)
        self.add_menu_btn(self.btn_frame_top, self.icons["clientes"], self.open_clientes)
        self.add_menu_btn(self.btn_frame_top, self.icons["produtos"], self.open_produtos)
        self.add_menu_btn(self.btn_frame_top, self.icons["encomendas"], self.open_encomendas)

        if self.user['cargo'] == "Admin":
            self.add_menu_btn(self.btn_frame_top, self.icons["funcionarios"], self.open_funcionarios)
            self.add_menu_btn(self.btn_frame_top, self.icons["relatorios"], self.open_relatorios)

        self.btn_frame_bottom = tk.Frame(self.sidebar, bg=PRIMARY_COLOR)
        self.btn_frame_bottom.pack(side="bottom", fill="x", pady=20)
        tk.Button(self.btn_frame_bottom, image=self.icons["logout"], command=self.logout,
                  bg="red", relief="flat").pack(pady=10)

        self.main = tk.Frame(self, bg=BG_COLOR)
        self.main.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.lbl_title = tk.Label(self.main, text="", font=("Arial",18,"bold"), bg=BG_COLOR)
        self.lbl_title.pack(anchor="w")

        # Busca
        self.search_frame = tk.Frame(self.main, bg=BG_COLOR)
        self.search_frame.pack(fill="x", pady=10)
        tk.Label(self.search_frame, text="🔍", bg=BG_COLOR).pack(side="left")
        self.search = tk.Entry(self.search_frame)
        self.search.pack(side="left", fill="x", expand=True)
        self.search.bind("<KeyRelease>", self.filtrar)

        # Treeview
        self.tree = ttk.Treeview(self.main, show="headings")
        self.tree.pack(fill="both", expand=True)

        # Botões funcionalidades
        self.btn_frame = tk.Frame(self.main, bg=BG_COLOR)
        self.btn_frame.pack(fill="x", pady=10)

        self.open_clientes()

    def limpar_tela_extra(self):
        if self.relatorio_frame:
            self.relatorio_frame.destroy()
            self.relatorio_frame = None

    def add_menu_btn(self, parent_frame, image, cmd):
        tk.Button(parent_frame, image=image, command=cmd,
                  bg=PRIMARY_COLOR, relief="flat").pack(pady=20)

    def set_buttons(self, cad, alt, exc):
        for w in self.btn_frame.winfo_children(): w.destroy()
        b_style = {"bg": BUTTON_BG, "fg": TEXT_COLOR, "width":12, "font":("Arial",12,"bold"), "relief":"flat"}
        tk.Button(self.btn_frame, text="Novo", command=cad, **b_style).pack(side="left", padx=10)
        tk.Button(self.btn_frame, text="Editar" if self.lbl_title["text"]!="Encomendas" else "Detalhes",
                  command=alt, **b_style).pack(side="left", padx=10)
        tk.Button(self.btn_frame, text="Apagar", command=exc, **b_style).pack(side="left", padx=10)

    # Popups


    # Filtrar (busca)
    def filtrar(self, event):
        termo = self.search.get().lower()
        tela = self.lbl_title["text"]
        data = []
        if tela=="Clientes": data = self.db.consultar_clientes()
        elif tela=="Produtos": data = self.db.consultar_produtos()
        elif tela=="Funcionários": data = self.db.consultar_funcionarios()
        elif tela=="Encomendas":
            filtro = None if self.user['cargo']=="Admin" else self.user['id']
            data = self.db.consultar_encomendas(filtro)
        clean_data = []
        for row in data:
            full_str = " ".join([str(x).lower() for x in row if x is not None])
            if termo in full_str: clean_data.append(row)
        self.tree.delete(*self.tree.get_children())
        for row in clean_data:
            if tela=="Encomendas":
                row_list = list(row); row_list[4] = f"{row_list[4]:.2f} €"
                self.tree.insert("", "end", values=tuple(row_list))
            else: self.tree.insert("", "end", values=row)

    def get_sel(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("Aviso","Selecione um item"); return None
        return self.tree.item(sel[0])["values"]

    # Logout
    def logout(self):
        if messagebox.askyesno("Logout","Deseja realmente sair do sistema?"):
            self.destroy()
            LoginWindow(self.db).mainloop()

    # Telas
    def open_clientes(self):
        self.limpar_tela_extra()
        self.search_frame.pack(fill="x", pady=10)

        self.lbl_title.config(text="Clientes")
        self.search.delete(0,tk.END)
        self.populate_tree(("ID","Nome","Telefone","Email"), self.db.consultar_clientes())
        self.set_buttons(self.cad_cli, self.alt_cli, self.exc_cli)

    def open_produtos(self):
        self.limpar_tela_extra()
        self.search_frame.pack(fill="x", pady=10)

        self.lbl_title.config(text="Produtos")
        self.search.delete(0,tk.END)
        self.populate_tree(("ID","Produto","Categoria","Marca","Preço","Qtd"), self.db.consultar_produtos())
        self.set_buttons(self.cad_prod, self.alt_prod, self.exc_prod)

    def open_funcionarios(self):
        self.limpar_tela_extra()
        self.search_frame.pack(fill="x", pady=10)

        self.lbl_title.config(text="Funcionários")
        self.search.delete(0,tk.END)
        self.populate_tree(("ID","Nome","User","Cargo"), self.db.consultar_funcionarios())
        self.set_buttons(self.cad_func, self.alt_func, self.exc_func)

    def open_encomendas(self):
        self.limpar_tela_extra()
        self.search_frame.pack(fill="x", pady=10)

        self.lbl_title.config(text="Encomendas")
        self.search.delete(0,tk.END)
        filtro = None if self.user['cargo']=="Admin" else self.user['id']
        data = self.db.consultar_encomendas(filtro)
        self.populate_tree(("ID","Data","Cliente","Vendedor","Total"), data)
        self.set_buttons(self.cad_enc, self.alt_enc, self.exc_enc)

    def open_relatorios(self):
        self.limpar_tela_extra()
        self.search_frame.pack_forget()  # Esconde a barra de pesquisa

        # --- CORREÇÃO: Limpa os botões (Novo, Editar, Apagar) ---
        for widget in self.btn_frame.winfo_children():
            widget.destroy()

        self.lbl_title.config(text="Relatórios de Vendas")

        # Configura o frame exclusivo do relatório
        self.relatorio_frame = tk.Frame(self.main, bg=BG_COLOR)
        self.relatorio_frame.pack(fill="x", pady=10)

        # Seletor de Funcionário
        tk.Label(
            self.relatorio_frame,
            text="Selecione o Funcionário:",
            bg=BG_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=5)

        funcionarios = self.db.consultar_funcionarios()
        # Mapeia Nome -> ID
        self.func_map = {f[1]: f[0] for f in funcionarios}

        self.cb_func = ttk.Combobox(
            self.relatorio_frame,
            values=["Todos"] + list(self.func_map.keys()),
            state="readonly",
            width=30
        )
        self.cb_func.set("Todos")
        self.cb_func.pack(side="left", padx=5)

        # Evento: Quando mudar o funcionário na combobox, atualiza a tabela automaticamente
        self.cb_func.bind("<<ComboboxSelected>>", lambda e: self.atualizar_relatorio_funcionario())

        # Botão para Gerar Gráfico
        tk.Button(
            self.relatorio_frame,
            text="📊 Ver Gráfico Mensal",
            command=self.open_grafico_vendas,
            bg=SECONDARY_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 11, "bold"),
            relief="flat"
        ).pack(side="left", padx=10)

        # Configurar a Tabela (Treeview) para mostrar Resumo
        self.tree.delete(*self.tree.get_children())
        columns = ("Funcionário", "Qtd Encomendas", "Total Vendido (€)")
        self.tree["columns"] = columns
        self.tree["displaycolumns"] = "#all"
        self.tree["show"] = "headings"

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200, anchor=tk.CENTER)

        # Carrega os dados iniciais
        self.atualizar_relatorio_funcionario()

    def atualizar_relatorio_funcionario(self):
        # Limpa a tabela atual
        self.tree.delete(*self.tree.get_children())

        escolha = self.cb_func.get()
        cod_func = None

        if escolha != "Todos" and escolha in self.func_map:
            cod_func = self.func_map[escolha]

        # Busca dados no banco (Resumo total por funcionário)
        dados = self.db.resumo_vendas_funcionarios(cod_func)

        total_geral = 0
        for nome, qtd, total in dados:
            total_geral += total
            self.tree.insert("", "end", values=(nome, qtd, f"{total:.2f} €"))

        # Opcional: Adicionar uma linha de Total Geral no final se for "Todos"
        if escolha == "Todos" and dados:
            self.tree.insert("", "end", values=("TOTAL GERAL", "", f"{total_geral:.2f} €"))

    def open_grafico_vendas(self):
        escolha = self.cb_func.get()

        if escolha == "Todos":
            messagebox.showwarning("Aviso",
                                   "Por favor, selecione um funcionário específico para ver a evolução mensal.")
            return

        cod_func = self.func_map[escolha]

        # Busca dados cronológicos (Mês a Mês)
        dados = self.db.vendas_por_funcionario_mes(cod_func)

        if not dados:
            messagebox.showinfo("Informação", f"O funcionário {escolha} não possui vendas registadas.")
            return

        # Prepara dados para o Matplotlib
        meses = [row[0] for row in dados]  # Eixo X (2025-01, 2025-02...)
        totais = [row[1] for row in dados]  # Eixo Y (Valores)

        # Criação do Gráfico
        plt.figure(figsize=(10, 6))

        # Linha com marcadores
        plt.plot(meses, totais, marker='o', linestyle='-', color='#5D1B8B', linewidth=2, label='Vendas (€)')

        # Preencher área abaixo da linha (opcional, fica bonito)
        plt.fill_between(meses, totais, color='#CCB4BE', alpha=0.4)

        plt.title(f"Evolução de Vendas - {escolha}", fontsize=14, fontweight='bold')
        plt.xlabel("Mês", fontsize=12)
        plt.ylabel("Total Vendido (€)", fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)  # Roda as datas para não sobrepor
        plt.tight_layout()

        # Adiciona os valores em cima dos pontos
        for i, txt in enumerate(totais):
            plt.annotate(f"{txt:.0f}€", (meses[i], totais[i]), textcoords="offset points", xytext=(0, 10), ha='center')

        plt.show()

    def populate_tree(self, columns, data, display_cols=None):
        self.tree.delete(*self.tree.get_children())
        self.tree["displaycolumns"] = "#all"
        self.tree["columns"] = columns
        if display_cols: self.tree["displaycolumns"] = display_cols
        for c in columns:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, anchor=tk.CENTER)
        for row in data:
            if self.lbl_title["text"]=="Encomendas":
                row_list = list(row); row_list[4]=f"{row_list[4]:.2f} €"
                self.tree.insert("", "end", values=tuple(row_list))
            else:
                self.tree.insert("", "end", values=row)

    # Ações
        # Dentro da classe App:

    def cad_cli(self):
            # Abre a janela bonita de Novo Cliente
        ClientePopup(self, self.db, None)

    def alt_cli(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Selecione um cliente para editar.")

            # Pega os dados atuais (ID, Nome, Tel, Email)
        dados = self.tree.item(sel[0], 'values')

            # Abre a janela bonita de Editar Cliente
        ClientePopup(self, self.db, dados)

    def exc_cli(self):
        if self.user['cargo'] != "Admin":
            return messagebox.showerror("Erro", "Permissão negada")

        selecionados = self.tree.selection()
        if not selecionados:
            return messagebox.showwarning("Aviso", "Selecione pelo menos um cliente.")

        if not messagebox.askyesno("Apagar", f"Tem a certeza que deseja apagar {len(selecionados)} cliente(s)?"):
            return

        try:
            for item_id in selecionados:
                valores = self.tree.item(item_id, 'values')
                id_cli = valores[0]
                # Nota: Se o cliente tiver encomendas, o DB pode dar erro.
                # O ideal é envolver num try/except ou garantir que apaga as encomendas antes.
                self.db.excluir_cliente(id_cli)

            self.open_clientes()
            messagebox.showinfo("Sucesso", "Clientes apagados com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao apagar (possivelmente o cliente tem encomendas):\n{e}")

        # Procure onde está "def cad_prod(self):" dentro da classe App e substitua por:

    def cad_prod(self):
        ProdutoPopup(self, self.db, None)

    def alt_prod(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Selecione um produto para editar.")

        # Pega os dados da linha selecionada
        dados = self.tree.item(sel[0], 'values')
        ProdutoPopup(self, self.db, dados)

    def exc_prod(self):
        # 1. Pega TODOS os itens selecionados
        sel = self.tree.selection()

        if not sel:
            return messagebox.showwarning("Aviso", "Selecione pelo menos um produto para apagar.")

        # 2. Confirmação Única (para não perguntar produto por produto)
        qtd = len(sel)
        resp = messagebox.askyesno("Confirmar", f"Tem certeza que deseja apagar {qtd} produto(s)?")

        if not resp:
            return

        # Variáveis para relatório final
        apagados = 0
        nao_apagados = []

        # 3. Loop para tentar apagar cada um
        for item_id in sel:
            # Pega os dados da linha
            valores = self.tree.item(item_id, 'values')
            cod_prod = valores[0]
            nome_prod = valores[1]

            # Tenta apagar no banco
            sucesso = self.db.excluir_produto(cod_prod)

            if sucesso:
                apagados += 1
            else:
                # Se falhar (por ter vendas associadas), guarda o nome na lista
                nao_apagados.append(nome_prod)

        # 4. Atualiza a tabela visualmente
        self.open_produtos()

        # 5. Exibe o resultado final
        if len(nao_apagados) == 0:
            messagebox.showinfo("Sucesso", f"{apagados} produto(s) apagado(s) com sucesso!")
        else:
            # Mensagem mais detalhada se houver erros
            msg = f"{apagados} apagado(s).\n\n"
            msg += f"{len(nao_apagados)} não puderam ser apagados (já possuem vendas):\n"
            msg += ", ".join(nao_apagados)  # Mostra os nomes separados por vírgula
            msg += "\n\nDica: Para estes, altere o stock para 0 ou mude o nome."

            messagebox.showwarning("Relatório de Exclusão", msg)
        # ---------------------------------------------------------
        # GESTÃO DE FUNCIONÁRIOS (NOVO CÓDIGO)
        # ---------------------------------------------------------

    def cad_func(self):
        FuncionarioPopup(self, self.db, None)

    def alt_func(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecione um funcionário.")
        dados = self.tree.item(sel[0], 'values')
        FuncionarioPopup(self, self.db, dados)

    def exc_func(self):
        selecionados = self.tree.selection()
        if not selecionados:
            return messagebox.showwarning("Aviso", "Selecione pelo menos um funcionário.")

            # Confirmação antes de apagar
        resp = messagebox.askyesno("Confirmar Exclusão",
                                       f"Tem a certeza que deseja apagar {len(selecionados)} registo(s)?\nEssa ação não pode ser desfeita.")
        if not resp:
            return

        apagados_count = 0
        erro_proprio = False

        for item_id in selecionados:
            valores = self.tree.item(item_id, 'values')
            cod_func = valores[0]

                # Proteção: Não apagar o próprio usuário logado
            if int(cod_func) == self.user['id']:
                erro_proprio = True
                continue

            self.db.excluir_funcionario(cod_func)
            apagados_count += 1

            # Atualiza tabela
        self.open_funcionarios()

            # Mensagens finais
        if erro_proprio:
            messagebox.showwarning("Aviso",
                                   "Alguns utilizadores foram apagados, mas você não pode apagar o seu próprio login!")
        elif apagados_count > 0:
            messagebox.showinfo("Sucesso", f"{apagados_count} funcionário(s) apagado(s).")

    def cad_enc(self):
        # Abre o POS (Ponto de )
        EncomendaPopup(self, self.db, self.user)

    def alt_enc(self):
        d = self.get_sel()
        if not d: return
        nenc = d[0]

        # Buscar detalhes da encomenda
        conn = self.db.connect()
        c = conn.cursor()
        c.execute("SELECT CodCli, DataEnc FROM Encomendas WHERE NEnc=?", (nenc,))
        encomenda_info = c.fetchone()
        cod_cli, data_enc = encomenda_info

        c.execute("""SELECT I.CodProd, P.Produto, I.Quant, I.PrecoUnitario
                     FROM ItensEncomenda I
                     JOIN Produtos P ON I.CodProd = P.CodProd
                     WHERE I.NEnc=?""", (nenc,))
        itens = c.fetchall()
        conn.close()

        # popup
        win = tk.Toplevel(self)
        win.title(f"Detalhes Encomenda {nenc}")
        win.geometry("700x500")
        win.configure(bg=BG_COLOR)

        # Cliente e data
        tk.Label(win, text="Cliente:", bg=BG_COLOR, fg=PRIMARY_COLOR, font=("Arial", 12, "bold")).pack(anchor="w",
                                                                                                       padx=10, pady=5)
        clientes = self.db.consultar_clientes()
        cli_name = next(c[1] for c in clientes if c[0] == cod_cli)
        tk.Label(win, text=cli_name, bg=BG_COLOR, font=("Arial", 12)).pack(anchor="w", padx=20)

        tk.Label(win, text="Data:", bg=BG_COLOR, fg=PRIMARY_COLOR, font=("Arial", 12, "bold")).pack(anchor="w", padx=10,
                                                                                                    pady=5)
        tk.Label(win, text=data_enc, bg=BG_COLOR, font=("Arial", 12)).pack(anchor="w", padx=20)

        # itens da encomenda
        tree_itens = ttk.Treeview(win, columns=("Produto", "Qtd", "Preço Unit.", "Subtotal"), show="headings")
        for col, w in zip(("Produto", "Qtd", "Preço Unit.", "Subtotal"), (250, 50, 100, 100)):
            tree_itens.heading(col, text=col)
            tree_itens.column(col, width=w, anchor=tk.CENTER if col != "Produto" else tk.W)
        tree_itens.pack(fill="both", expand=True, padx=10, pady=10)

        total = 0
        for cod_prod, nome, qtd, preco_unit in itens:
            subtotal = qtd * preco_unit
            total += subtotal
            tree_itens.insert("", "end", values=(nome, qtd, f"{preco_unit:.2f} €", f"{subtotal:.2f} €"))

        tk.Label(win, text=f"Total: {total:.2f} €", bg=BG_COLOR, fg=PRIMARY_COLOR, font=("Arial", 14, "bold")).pack(
            pady=10)

    def exc_enc(self):
        # 1. Verificação de segurança
        if self.user['cargo'] != "Admin":
            return messagebox.showerror("Erro", "Permissão negada")

        # 2. Obter TODOS os itens selecionados na tabela
        selecionados = self.tree.selection()

        if not selecionados:
            return messagebox.showwarning("Aviso", "Selecione pelo menos uma encomenda.")

        # 3. Confirmação única para tudo
        qtd = len(selecionados)
        if not messagebox.askyesno("Apagar", f"Tem a certeza que deseja apagar {qtd} encomenda(s)?"):
            return

        # 4. Loop para apagar um por um
        try:
            for item_id in selecionados:
                # Pega os valores da linha (o ID geralmente é o primeiro item, índice 0)
                valores = self.tree.item(item_id, 'values')
                id_encomenda = valores[0]

                # Chama a função de apagar do banco
                self.db.excluir_encomenda(id_encomenda)

            # 5. Atualiza a tela
            messagebox.showinfo("Sucesso", "Encomendas apagadas com sucesso!")
            self.open_encomendas()

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao apagar: {e}")


# execução
if __name__=="__main__":
    db=MaquilhagemDB()
    LoginWindow(db).mainloop()

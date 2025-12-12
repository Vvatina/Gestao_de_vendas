import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from datetime import datetime
import hashlib

# ------------------- CONFIGURAÇÕES -------------------
BG_COLOR = "#CCB4BE"
PRIMARY_COLOR = "#5D1B8B"
SECONDARY_COLOR = "#2C1F8C"
BUTTON_BG = "#97589C"
TEXT_COLOR = "#FFFFFF"

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
    def excluir_produto(self, cod):
        with self.connect() as conn:
            conn.execute("DELETE FROM Produtos WHERE CodProd=?", (cod,))

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

        # Sidebar
        self.sidebar = tk.Frame(self, bg=PRIMARY_COLOR, width=160)
        self.sidebar.pack(side="left", fill="y")


        # Carregar ícones
        self.icons = {}
        icon_files = {
            "clientes": "icons/clientes.png",
            "produtos": "icons/produtos.png",
            "encomendas": "icons/encomendas.png",
            "funcionarios": "icons/funcionarios.png",
            "logout": "icons/logout.png"
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
    def popup(self, title, save_func, fields, values=None):
        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=BG_COLOR)
        win.geometry("400x400")
        entries = []
        for i, f in enumerate(fields):
            tk.Label(win, text=f, bg=BG_COLOR, fg=PRIMARY_COLOR, font=("Arial",12,"bold")).pack(anchor="w", padx=10, pady=5)
            if f=="Cargo":
                e = ttk.Combobox(win, values=["Admin","Funcionario"], state="readonly")
            else:
                e = tk.Entry(win, font=("Arial",12))
            e.pack(fill="x", padx=10, pady=5)
            if values and values[i] is not None: e.insert(0, values[i])
            entries.append(e)
        tk.Button(win, text="Salvar", command=lambda: self._save_popup(win, entries, save_func, title),
                  bg=BUTTON_BG, fg=TEXT_COLOR, font=("Arial",12,"bold"), relief="flat").pack(pady=20)

    def _save_popup(self, win, entries, save_func, title):
        vals = [e.get() for e in entries]
        save_func(*vals)
        win.destroy()
        if "Cliente" in title: self.open_clientes()
        elif "Produto" in title: self.open_produtos()
        elif "Func" in title: self.open_funcionarios()

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
        self.lbl_title.config(text="Clientes")
        self.search.delete(0,tk.END)
        self.populate_tree(("ID","Nome","Telefone","Email"), self.db.consultar_clientes())
        self.set_buttons(self.cad_cli, self.alt_cli, self.exc_cli)

    def open_produtos(self):
        self.lbl_title.config(text="Produtos")
        self.search.delete(0,tk.END)
        self.populate_tree(("ID","Produto","Categoria","Marca","Preço","Qtd"), self.db.consultar_produtos())
        self.set_buttons(self.cad_prod, self.alt_prod, self.exc_prod)

    def open_funcionarios(self):
        self.lbl_title.config(text="Funcionários")
        self.search.delete(0,tk.END)
        self.populate_tree(("ID","Nome","User","Cargo"), self.db.consultar_funcionarios())
        self.set_buttons(self.cad_func, self.alt_func, self.exc_func)

    def open_encomendas(self):
        self.lbl_title.config(text="Encomendas")
        self.search.delete(0,tk.END)
        filtro = None if self.user['cargo']=="Admin" else self.user['id']
        data = self.db.consultar_encomendas(filtro)
        self.populate_tree(("ID","Data","Cliente","Vendedor","Total"), data)
        self.set_buttons(self.cad_enc, self.alt_enc, self.exc_enc)

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
    def cad_cli(self): self.popup("Novo Cliente", self.db.adicionar_cliente, ["Nome","Telefone","Email"])
    def alt_cli(self):
        d = self.get_sel()
        if d: self.popup("Editar Cliente", lambda n,t,e:self.db.atualizar_cliente(d[0],n,t,e),
                         ["Nome","Telefone","Email"], d[1:])
    def exc_cli(self):
        if self.user['cargo']!="Admin": return messagebox.showerror("Erro","Permissão negada")
        d = self.get_sel()
        if d and messagebox.askyesno("Apagar","Confirma?"):
            self.db.excluir_cliente(d[0]); self.open_clientes()

    def cad_prod(self): self.popup("Novo Produto", self.db.adicionar_produto,
                                   ["Produto","Categoria","Marca","Preço","Qtd"])
    def alt_prod(self):
        d = self.get_sel()
        if d: self.popup("Editar Produto", lambda p,c,m,pr,q:self.db.atualizar_produto(d[0],p,c,m,pr,q),
                         ["Produto","Categoria","Marca","Preço","Qtd"], d[1:])
    def exc_prod(self):
        if self.user['cargo']!="Admin": return messagebox.showerror("Erro","Permissão negada")
        d = self.get_sel()
        if d and messagebox.askyesno("Apagar","Confirma?"):
            self.db.excluir_produto(d[0]); self.open_produtos()

    def cad_func(self): self.popup("Novo Func", self.db.adicionar_funcionario,
                                   ["Nome","User","Pass","Cargo"])
    def alt_func(self):
        d = self.get_sel()
        if d: self.popup("Editar Func", lambda n,u,p,c:self.db.atualizar_funcionario(d[0],n,u,p,c),
                         ["Nome","User","Pass","Cargo"], d[1:])
    def exc_func(self):
        d = self.get_sel()
        if d and messagebox.askyesno("Apagar","Confirma?"):
            self.db.excluir_funcionario(d[0]); self.open_funcionarios()

    def cad_enc(self): EncomendaPopup(self, self.db, self.user).grab_set()

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
            if self.user['cargo']!="Admin": return messagebox.showerror("Erro","Permissão negada")
            d = self.get_sel()
            if d and messagebox.askyesno("Apagar",f"Confirma apagar Encomenda {d[0]}?"):
                self.db.excluir_encomenda(d[0]); self.open_encomendas()

# tela para efetuar a encomenda
class EncomendaPopup(tk.Toplevel):
    def __init__(self, master, db, user):
        super().__init__(master)
        self.db, self.user = db, user
        self.title("Nova Encomenda")
        self.geometry("800x600")
        self.configure(bg=BG_COLOR)
        self.itens_compra = []

        main_frame = tk.Frame(self, bg=BG_COLOR, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        # Cabeçalho
        header_frame = tk.Frame(main_frame, bg=BG_COLOR)
        header_frame.pack(fill="x", pady=10)
        tk.Label(header_frame,text="Cliente:", bg=BG_COLOR, fg=PRIMARY_COLOR,font=("Arial",12,"bold")).pack(side="left", padx=(0,5))
        self.clientes = db.consultar_clientes()
        self.cli_map = {f"{c[1]} (ID:{c[0]})": c[0] for c in self.clientes}
        self.cb_cli = ttk.Combobox(header_frame, values=list(self.cli_map.keys()), state="readonly", width=40)
        self.cb_cli.pack(side="left", padx=(0,20))
        tk.Label(header_frame,text="Data (YYYY-MM-DD):", bg=BG_COLOR, fg=PRIMARY_COLOR,font=("Arial",12,"bold")).pack(side="left", padx=(0,5))
        self.dt = tk.Entry(header_frame, width=15, font=("Arial",12))
        self.dt.insert(0, datetime.today().strftime('%Y-%m-%d'))
        self.dt.pack(side="left")

        # Adicionar item
        add_frame = tk.LabelFrame(main_frame, text="Adicionar Produto", bg=BG_COLOR, fg=PRIMARY_COLOR, padx=5, pady=5, font=("Arial",12,"bold"))
        add_frame.pack(fill="x", pady=10)
        tk.Label(add_frame,text="Produto:", bg=BG_COLOR, fg=PRIMARY_COLOR,font=("Arial",12,"bold")).pack(side="left", padx=5)
        self.produtos = db.consultar_produtos()
        self.prod_map = {f"{p[1]} (Stock:{p[5]})": p for p in self.produtos}
        self.cb_prod = ttk.Combobox(add_frame, values=list(self.prod_map.keys()), state="readonly", width=40)
        self.cb_prod.pack(side="left", padx=5)
        tk.Label(add_frame,text="Qtd:", bg=BG_COLOR, fg=PRIMARY_COLOR,font=("Arial",12,"bold")).pack(side="left", padx=5)
        self.qtd = tk.Entry(add_frame, width=5); self.qtd.insert(0,"1"); self.qtd.pack(side="left", padx=5)
        tk.Button(add_frame,text="Adicionar", command=self.add_item, bg=BUTTON_BG, fg=TEXT_COLOR, font=("Arial",12,"bold"), relief="flat").pack(side="left", padx=5)
        tk.Button(add_frame,text="Remover Selecionado", command=self.remove_item, bg="red", fg=TEXT_COLOR, font=("Arial",12,"bold"), relief="flat").pack(side="right", padx=5)

        # Treeview
        self.tree_itens = ttk.Treeview(main_frame, columns=("ID","Produto","Qtd","Preço Unit.","Subtotal"), show="headings", height=15)
        self.tree_itens.heading("ID", text="ID Prod"); self.tree_itens.column("ID", width=50, anchor=tk.CENTER)
        self.tree_itens.heading("Produto", text="Produto"); self.tree_itens.column("Produto", width=250)
        self.tree_itens.heading("Qtd", text="Qtd"); self.tree_itens.column("Qtd", width=50, anchor=tk.CENTER)
        self.tree_itens.heading("Preço Unit.", text="Preço Unit."); self.tree_itens.column("Preço Unit.", width=100, anchor=tk.E)
        self.tree_itens.heading("Subtotal", text="Subtotal"); self.tree_itens.column("Subtotal", width=100, anchor=tk.E)
        self.tree_itens.pack(fill="both", expand=True, pady=10)

        # Total e finalizar encomenda
        footer_frame = tk.Frame(main_frame, bg=BG_COLOR)
        footer_frame.pack(fill="x", pady=10)
        self.lbl_total = tk.Label(footer_frame, text="Total da Encomenda: 0.00 €", font=("Arial",14,"bold"), bg=BG_COLOR, fg=PRIMARY_COLOR)
        self.lbl_total.pack(side="left", padx=10)
        tk.Button(footer_frame, text="FINALIZAR ENCOMENDA", command=self.save_encomenda, bg=BUTTON_BG, fg=TEXT_COLOR,
                  font=("Arial",12,"bold"), relief="flat").pack(side="right")

    def add_item(self):
        produto_nome = self.cb_prod.get()
        if not produto_nome: return messagebox.showwarning("Aviso","Selecione um produto.")
        produto_data = self.prod_map[produto_nome]; cod_prod=produto_data[0]; preco_unit=produto_data[4]; stock_disp=produto_data[5]
        quantidade=int(self.qtd.get())
        if quantidade<=0: return messagebox.showwarning("Aviso","Quantidade deve ser maior que 0.")
        for i,(p_id,q,p_unit) in enumerate(self.itens_compra):
            if p_id==cod_prod:
                nova_qtd=q+quantidade
                if nova_qtd>stock_disp: return messagebox.showwarning("Stock Insuficiente",f"O total ({nova_qtd}) excede stock.")
                self.itens_compra[i]=(cod_prod,nova_qtd,preco_unit); self.update_item_tree(); return
        self.itens_compra.append((cod_prod,quantidade,preco_unit)); self.update_item_tree()

    def remove_item(self):
        sel=self.tree_itens.selection()
        if not sel: return messagebox.showwarning("Aviso","Selecione um item para remover.")
        item_data=self.tree_itens.item(sel[0],'values'); cod_prod_to_remove=int(item_data[0])
        self.itens_compra=[item for item in self.itens_compra if item[0]!=cod_prod_to_remove]; self.update_item_tree()

    def update_item_tree(self):
        self.tree_itens.delete(*self.tree_itens.get_children()); total=0
        for cod_prod, quant, preco_unit in self.itens_compra:
            nome_produto=next(p[1] for p in self.produtos if p[0]==cod_prod)
            subtotal=quant*preco_unit; total+=subtotal
            self.tree_itens.insert("", "end", values=(cod_prod,nome_produto,quant,f"{preco_unit:.2f} €",f"{subtotal:.2f} €"))
        self.lbl_total.config(text=f"Total da Encomenda: {total:.2f} €")

    def save_encomenda(self):
        if not self.cb_cli.get(): return messagebox.showwarning("Aviso","Selecione um cliente.")
        if not self.itens_compra: return messagebox.showwarning("Aviso","Adicione pelo menos um produto.")
        cod_cli=self.cli_map[self.cb_cli.get()]; data=self.dt.get()
        self.db.adicionar_encomenda(data, cod_cli, self.itens_compra, self.user['id'])
        messagebox.showinfo("Sucesso","Encomenda salva com sucesso!"); self.destroy(); self.master.open_encomendas()

# execução
if __name__=="__main__":
    db=MaquilhagemDB()
    LoginWindow(db).mainloop()

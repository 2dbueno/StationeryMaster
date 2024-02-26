import re
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3

class BancoDeDados:
    def __init__(self, nome_banco="papelaria.db"):
        self.nome_banco = nome_banco

    def conectar(self):
        return sqlite3.connect(self.nome_banco)

    def criar_tabelas(self):
        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpf TEXT NOT NULL,
                    nome TEXT NOT NULL,
                    email TEXT,
                    telefone TEXT,
                    quantidade_comprada INTEGER DEFAULT 0
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    preco REAL NOT NULL,
                    quantidade INTEGER NOT NULL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpf_cliente TEXT,
                    id_produto INTEGER,
                    quantidade INTEGER,
                    FOREIGN KEY (cpf_cliente) REFERENCES clientes (cpf),
                    FOREIGN KEY (id_produto) REFERENCES produtos (id)
                )
            ''')

            conexao.commit()

class OperacoesBancoDeDados:
    def __init__(self, banco_de_dados):
        self.banco_de_dados = banco_de_dados

    def cadastrar_cliente(self, cpf, nome, email, telefone):
        with self.banco_de_dados.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute("INSERT INTO clientes (cpf, nome, email, telefone) VALUES (?, ?, ?, ?)", (cpf, nome, email, telefone))
            conexao.commit()

    def cadastrar_produto(self, nome, preco, quantidade):
        with self.banco_de_dados.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute("INSERT INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)", (nome, preco, quantidade))
            conexao.commit()

    def realizar_venda(self, produto_id, cpf_cliente, quantidade_vendida):
        with self.banco_de_dados.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id=?", (quantidade_vendida, produto_id))
            cursor.execute("INSERT INTO vendas (cpf_cliente, id_produto, quantidade) VALUES (?, ?, ?)", (cpf_cliente, produto_id, quantidade_vendida))
            cursor.execute("UPDATE clientes SET quantidade_comprada = quantidade_comprada + ? WHERE cpf=?", (quantidade_vendida, cpf_cliente))

            conexao.commit()

class PapelariaApp:
    def __init__(self):
        self.janela_login = tk.Tk()
        self.janela_login.title("Login")

        tk.Label(self.janela_login, text="Usuário:").pack()
        self.entry_usuario = tk.Entry(self.janela_login)
        self.entry_usuario.pack()

        tk.Label(self.janela_login, text="Senha:").pack()
        self.entry_senha = tk.Entry(self.janela_login, show="*")
        self.entry_senha.pack()

        btn_login = tk.Button(self.janela_login, text="Login", command=self.fazer_login)
        btn_login.pack()

        self.banco_de_dados = BancoDeDados()
        self.operacoes_bd = OperacoesBancoDeDados(self.banco_de_dados)

    def run(self):
        self.janela_login.mainloop()

    def fazer_login(self):
        usuario = self.entry_usuario.get()
        senha = self.entry_senha.get()

        if usuario == "admin" and senha == "admin":
            self.abrir_interface_principal()
        else:
            messagebox.showerror("Erro de Login", "Login incorreto")

    def abrir_interface_principal(self):
        self.janela_login.withdraw()  # Oculta a janela de login

        janela_principal = tk.Toplevel(self.janela_login)  # Cria uma janela secundária
        janela_principal.title("Papelaria")

        btn_cadastrar_cliente = tk.Button(janela_principal, text="Cadastrar Cliente", command=self.cadastrar_cliente)
        btn_cadastrar_cliente.pack()

        btn_cadastrar_produto = tk.Button(janela_principal, text="Cadastrar Produto", command=self.cadastrar_produto)
        btn_cadastrar_produto.pack()

        btn_gerar_venda = tk.Button(janela_principal, text="Gerar Venda", command=self.gerar_venda)
        btn_gerar_venda.pack()

        janela_principal.protocol("WM_DELETE_WINDOW", self.encerrar_aplicacao)  # Adiciona tratamento de fechamento

        janela_principal.mainloop()

    def cadastrar_cliente(self):
        nome = simpledialog.askstring("Cadastro de Cliente", "Nome:")
        if not nome:
            messagebox.showerror("Erro no Cadastro", "Nome não preenchido.")
            return

        cpf = simpledialog.askstring("Cadastro de Cliente", "CPF:")
        if not cpf or not self.validar_cpf(cpf):
            messagebox.showerror("Erro no Cadastro", "CPF inválido ou não preenchido.")
            return

        email = simpledialog.askstring("Cadastro de Cliente", "E-mail:")
        telefone = simpledialog.askstring("Cadastro de Cliente", "Telefone:")
        if not self.validar_telefone(telefone):
            messagebox.showerror("Erro no Cadastro", "Telefone inválido.")
            return

        self.operacoes_bd.cadastrar_cliente(cpf, nome, email, telefone)
        messagebox.showinfo("Cadastro de Cliente", "Cliente cadastrado com sucesso.")

    def cadastrar_produto(self):
        nome_produto = simpledialog.askstring("Cadastro de Produto", "Nome do Produto:")
        preco_produto = simpledialog.askfloat("Cadastro de Produto", "Preço do Produto:")
        quantidade_produto = simpledialog.askinteger("Cadastro de Produto", "Quantidade em Estoque:")

        if nome_produto and preco_produto and quantidade_produto is not None:
            self.operacoes_bd.cadastrar_produto(nome_produto, preco_produto, quantidade_produto)
            messagebox.showinfo("Cadastro de Produto", "Produto cadastrado com sucesso.")

    def gerar_venda(self):
        cpf_cliente = simpledialog.askstring("Gerar Venda", "CPF do Cliente:")
        nome_produto = simpledialog.askstring("Gerar Venda", "Nome do Produto (comece a digitar):")

        if cpf_cliente and nome_produto:
            try:
                with self.banco_de_dados.conectar() as conexao:
                    conexao.execute("PRAGMA foreign_keys = ON")  # Habilita suporte a chaves estrangeiras
                    conexao.execute("BEGIN TRANSACTION")

                    cursor = conexao.cursor()
                    cursor.execute("SELECT id, nome, preco, quantidade FROM produtos WHERE nome LIKE ?", (f'%{nome_produto}%',))

                    resultados_produto = cursor.fetchall()

                    if resultados_produto:
                        janela_produtos = tk.Toplevel()
                        janela_produtos.title("Escolha um Produto")

                        tk.Label(janela_produtos, text="Selecione o produto:").pack()

                        lista_produtos = ttk.Combobox(janela_produtos, values=[produto[1] for produto in resultados_produto])
                        lista_produtos.pack()

                        btn_selecionar = tk.Button(janela_produtos, text="Selecionar", command=lambda: self.selecionar_produto(janela_produtos, lista_produtos.get(), resultados_produto, cpf_cliente))
                        btn_selecionar.pack()
                    else:
                        messagebox.showerror("Erro na Venda", "Nenhum produto encontrado com o nome fornecido.")

            except sqlite3.Error as e:
                messagebox.showerror("Erro na Venda", f"Erro ao realizar venda: {str(e)}")

            finally:
                conexao.commit()

    def selecionar_produto(self, janela_produtos, produto_selecionado, resultados_produto, cpf_cliente):
        janela_produtos.destroy()

        if produto_selecionado:
            produto_escolhido = next((produto for produto in resultados_produto if produto[1] == produto_selecionado), None)

            if produto_escolhido:
                produto_id = produto_escolhido[0]
                quantidade_em_estoque = produto_escolhido[3]

                quantidade_vendida = simpledialog.askinteger("Gerar Venda", f"Quantidade Vendida para '{produto_selecionado}' (Disponível: {quantidade_em_estoque}):")

                if quantidade_vendida is not None:
                    if quantidade_vendida <= quantidade_em_estoque:
                        self.operacoes_bd.realizar_venda(produto_id, cpf_cliente, quantidade_vendida)
                        messagebox.showinfo("Venda Realizada", "Venda registrada com sucesso.")
                    else:
                        messagebox.showerror("Erro na Venda", "Quantidade insuficiente em estoque.")
            else:
                messagebox.showerror("Erro na Venda", "Produto não encontrado.")

    def encerrar_aplicacao(self):
        if messagebox.askokcancel("Encerrar Aplicação", "Deseja realmente encerrar a aplicação?"):
            self.janela_login.destroy()

    def validar_telefone(self, telefone):
        telefone = re.sub(r'\D', '', telefone)
        return len(telefone) == 11

    def validar_cpf(self, cpf):
        if not cpf.isdigit() or len(cpf) != 11:
            return False

        soma = 0
        multiplicador = 10

        for i in range(9):
            soma += int(cpf[i]) * multiplicador
            multiplicador -= 1

        resto = soma % 11

        if resto < 2:
            digito_verificador1 = 0
        else:
            digito_verificador1 = 11 - resto

        if int(cpf[9]) != digito_verificador1:
            return False

        # Verificação do segundo dígito
        soma = 0
        multiplicador = 11

        for i in range(10):
            soma += int(cpf[i]) * multiplicador
            multiplicador -= 1

        resto = soma % 11

        if resto < 2:
            digito_verificador2 = 0
        else:
            digito_verificador2 = 11 - resto

        if int(cpf[10]) != digito_verificador2:
            return False

        return True

    def cadastrar_cliente(self):
        nome = simpledialog.askstring("Cadastro de Cliente", "Nome:")

        if not nome:
            messagebox.showerror("Erro no Cadastro", "Nome não preenchido.")
            return

        cpf = simpledialog.askstring("Cadastro de Cliente", "CPF:")

        if not cpf or not self.validar_cpf(cpf):
            messagebox.showerror("Erro no Cadastro", "CPF inválido ou não preenchido.")
            return

        with sqlite3.connect("papelaria.db") as conexao:
            cursor = conexao.cursor()

            cursor.execute("SELECT cpf FROM clientes WHERE cpf=?", (cpf,))
            resultado = cursor.fetchone()

            if resultado:
                messagebox.showerror("Erro no Cadastro", "CPF já cadastrado.")
            else:
                email = simpledialog.askstring("Cadastro de Cliente", "E-mail:")
                telefone = simpledialog.askstring("Cadastro de Cliente", "Telefone:")

                if not self.validar_telefone(telefone):
                    messagebox.showerror("Erro no Cadastro", "Telefone inválido.")
                    return

                cursor.execute("INSERT INTO clientes (cpf, nome, email, telefone) VALUES (?, ?, ?, ?)", (cpf, nome, email, telefone))
                conexao.commit()
                messagebox.showinfo("Cadastro de Cliente", "Cliente cadastrado com sucesso.")

    def cadastrar_produto(self):
        nome_produto = simpledialog.askstring("Cadastro de Produto", "Nome do Produto:")
        preco_produto = simpledialog.askfloat("Cadastro de Produto", "Preço do Produto:")
        quantidade_produto = simpledialog.askinteger("Cadastro de Produto", "Quantidade em Estoque:")

        if nome_produto and preco_produto and quantidade_produto is not None:
            with sqlite3.connect("papelaria.db") as conexao:
                cursor = conexao.cursor()

                cursor.execute("INSERT INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)", (nome_produto, preco_produto, quantidade_produto))
                conexao.commit()
                messagebox.showinfo("Cadastro de Produto", "Produto cadastrado com sucesso.")

    def gerar_venda(self):
        cpf_cliente = simpledialog.askstring("Gerar Venda", "CPF do Cliente:")
        nome_produto = simpledialog.askstring("Gerar Venda", "Nome do Produto (comece a digitar):")

        if cpf_cliente and nome_produto:
            with sqlite3.connect("papelaria.db") as conexao:
                conexao.execute("PRAGMA foreign_keys = ON")  # Habilita suporte a chaves estrangeiras

                try:
                    conexao.execute("BEGIN TRANSACTION")

                    cursor = conexao.cursor()
                    cursor.execute("SELECT id, nome, preco, quantidade FROM produtos WHERE nome LIKE ?",
                                   (f'%{nome_produto}%',))

                    resultados_produto = cursor.fetchall()

                    if resultados_produto:
                        janela_produtos = tk.Toplevel()
                        janela_produtos.title("Escolha um Produto")

                        tk.Label(janela_produtos, text="Selecione o produto:").pack()

                        lista_produtos = ttk.Combobox(janela_produtos, values=[produto[1] for produto in resultados_produto])
                        lista_produtos.pack()

                        btn_selecionar = tk.Button(janela_produtos, text="Selecionar", command=lambda: self.selecionar_produto(janela_produtos, lista_produtos.get(), resultados_produto, cpf_cliente))
                        btn_selecionar.pack()
                    else:
                        messagebox.showerror("Erro na Venda", "Nenhum produto encontrado com o nome fornecido.")

                except Exception as e:
                    conexao.rollback()
                    messagebox.showerror("Erro na Venda", f"Erro ao realizar venda: {str(e)}")

    def selecionar_produto(self, janela_produtos, produto_selecionado, resultados_produto, cpf_cliente):
        janela_produtos.destroy()

        if produto_selecionado:
            produto_escolhido = next((produto for produto in resultados_produto if produto[1] == produto_selecionado), None)

            if produto_escolhido:
                produto_id = produto_escolhido[0]
                quantidade_em_estoque = produto_escolhido[3]

                quantidade_vendida = simpledialog.askinteger("Gerar Venda", f"Quantidade Vendida para '{produto_selecionado}' (Disponível: {quantidade_em_estoque}):")

                if quantidade_vendida is not None:
                    if quantidade_vendida <= quantidade_em_estoque:
                        self.realizar_venda(produto_id, cpf_cliente, quantidade_vendida)
                    else:
                        messagebox.showerror("Erro na Venda", "Quantidade insuficiente em estoque.")
            else:
                messagebox.showerror("Erro na Venda", "Produto não encontrado.")

    def realizar_venda(self, produto_id, cpf_cliente, quantidade_vendida):
        with sqlite3.connect("papelaria.db") as conexao:
            cursor = conexao.cursor()

            cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id=?", (quantidade_vendida, produto_id))
            cursor.execute("INSERT INTO vendas (cpf_cliente, id_produto, quantidade) VALUES (?, ?, ?)", (cpf_cliente, produto_id, quantidade_vendida))
            cursor.execute("UPDATE clientes SET quantidade_comprada = quantidade_comprada + ? WHERE cpf=?", (quantidade_vendida, cpf_cliente))

            conexao.commit()
            messagebox.showinfo("Venda Realizada", "Venda registrada com sucesso.")


    def encerrar_aplicacao(self):
        if messagebox.askokcancel("Encerrar Aplicação", "Deseja realmente encerrar a aplicação?"):
            self.janela_login.destroy()


if __name__ == "__main__":
    banco_de_dados = BancoDeDados()
    banco_de_dados.criar_tabelas()
    app = PapelariaApp()
    app.run()

import re
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from validate_docbr import CPF
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
                    cpf TEXT NOT NULL UNIQUE,
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
        # Proceder com o cadastro do cliente
        with self.banco_de_dados.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute("INSERT INTO clientes (cpf, nome, email, telefone) VALUES (?, ?, ?, ?)", (cpf, nome, email, telefone))

            conexao.commit()

    def cadastrar_produto(self, nome, preco, quantidade):
        # Proceder com o cadastro do produto
        with self.banco_de_dados.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute("INSERT INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)", (nome, preco, quantidade))

            conexao.commit()

    def realizar_venda(self, produto_id, cpf_cliente, quantidade_vendida):
        # Proceder com o cadastro de venda
        with self.banco_de_dados.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id=?", (quantidade_vendida, produto_id))
            cursor.execute("INSERT INTO vendas (cpf_cliente, id_produto, quantidade) VALUES (?, ?, ?)", (cpf_cliente, produto_id, quantidade_vendida))
            cursor.execute("UPDATE clientes SET quantidade_comprada = quantidade_comprada + ? WHERE cpf=?", (quantidade_vendida, cpf_cliente))

            conexao.commit()

class ValidarCPF:
    @staticmethod
    def validar_cpf(cpf):
        cpf_validator = CPF()

        if not cpf_validator.validate(cpf):
            return False

        return True

class PapelariaApp:
    def __init__(self):
        self.cpf_validator = ValidarCPF()
        self.janela_login = tk.Tk()
        self.janela_login.title("Login")

        tk.Label(self.janela_login, text="Usuário:").pack()
        self.entry_usuario = tk.Entry(self.janela_login)
        self.entry_usuario.pack()

        tk.Label(self.janela_login, text="Senha:").pack()
        self.entry_senha = tk.Entry(self.janela_login, show="*")
        self.entry_senha.pack()
        self.entry_senha.bind('<Return>', lambda event=None: self.fazer_login())
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
        self.janela_login.withdraw()

        janela_principal = tk.Toplevel(self.janela_login)
        janela_principal.title("Papelaria")

        btn_cadastrar_cliente = tk.Button(janela_principal, text="Cadastrar Cliente", command=self.cadastrar_cliente)
        btn_cadastrar_cliente.pack()

        btn_cadastrar_produto = tk.Button(janela_principal, text="Cadastrar Produto", command=self.cadastrar_produto)
        btn_cadastrar_produto.pack()

        btn_gerar_venda = tk.Button(janela_principal, text="Gerar Venda", command=self.gerar_venda)
        btn_gerar_venda.pack()

        janela_principal.protocol("WM_DELETE_WINDOW", self.encerrar_aplicacao)

        janela_principal.mainloop()

    def cadastrar_cliente(self):
        dialog = tk.Toplevel(self.janela_login)
        dialog.title("Cadastro de Cliente")

        tk.Label(dialog, text="Nome:").grid(row=0, column=0)
        tk.Label(dialog, text="CPF:").grid(row=1, column=0)
        tk.Label(dialog, text="E-mail:").grid(row=2, column=0)
        tk.Label(dialog, text="Telefone:").grid(row=3, column=0)

        nome_var = tk.StringVar()
        cpf_var = tk.StringVar()
        email_var = tk.StringVar()
        telefone_var = tk.StringVar()

        tk.Entry(dialog, textvariable=nome_var).grid(row=0, column=1)
        tk.Entry(dialog, textvariable=cpf_var).grid(row=1, column=1)
        tk.Entry(dialog, textvariable=email_var).grid(row=2, column=1)
        tk.Entry(dialog, textvariable=telefone_var).grid(row=3, column=1)

        enviar_button = tk.Button(dialog, text="Enviar", command=lambda: self.enviar_cliente(dialog, cpf_var.get(), nome_var.get(), email_var.get(), telefone_var.get()))
        enviar_button.grid(row=4, columnspan=2)

    def enviar_cliente(self, dialog, cpf, nome, email, telefone):
        if not cpf or not self.cpf_validator.validar_cpf(cpf):
            messagebox.showerror("Erro no Cadastro", "CPF inválido.")
            return

        if not nome or nome.isdigit():
            messagebox.showerror("Erro no Cadastro", "O nome do cliente não pode ser composto apenas por números.")
            return
        
        # Verificar se o Telefone é válido
        if not self.validar_telefone(telefone):
            messagebox.showerror("Erro no Cadastro", "Telefone inválido.")
            return

        # Verificar se o CPF já está cadastrado
        with self.banco_de_dados.conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT cpf FROM clientes WHERE cpf = ?", (cpf,))
            existing_cpf = cursor.fetchone()

        if existing_cpf:
            messagebox.showerror("Erro no Cadastro", f"CPF '{cpf}' já cadastrado.")
            return

        # Se todas as verificações passarem, cadastra o cliente
        self.operacoes_bd.cadastrar_cliente(cpf, nome, email, telefone)
        messagebox.showinfo("Cadastro de Cliente", "Cliente cadastrado com sucesso.")
        dialog.destroy()

    def cadastrar_produto(self):
        dialog = tk.Toplevel(self.janela_login)
        dialog.title("Cadastro de Produto")

        tk.Label(dialog, text="Nome do Produto:").grid(row=0, column=0)
        tk.Label(dialog, text="Preço do Produto:").grid(row=1, column=0)
        tk.Label(dialog, text="Quantidade em Estoque:").grid(row=2, column=0)

        nome_produto_var = tk.StringVar()
        preco_produto_var = tk.DoubleVar()
        quantidade_produto_var = tk.IntVar()

        tk.Entry(dialog, textvariable=nome_produto_var).grid(row=0, column=1)
        tk.Entry(dialog, textvariable=preco_produto_var).grid(row=1, column=1)
        tk.Entry(dialog, textvariable=quantidade_produto_var).grid(row=2, column=1)

        enviar_button = tk.Button(dialog, text="Enviar", command=lambda: self.enviar_produto(dialog, nome_produto_var.get(), preco_produto_var.get(), quantidade_produto_var.get()))
        enviar_button.grid(row=3, columnspan=2)

    def enviar_produto(self, dialog, nome_produto, preco_produto, quantidade_produto):
        if not nome_produto or preco_produto is None or quantidade_produto is None:
            messagebox.showerror("Erro no Cadastro", "Por favor, verifique os dados inseridos.")
            return

        # Se todas as verificações passarem, cadastra o produto
        self.operacoes_bd.cadastrar_produto(nome_produto, preco_produto, quantidade_produto)
        messagebox.showinfo("Cadastro de Produto", "Produto cadastrado com sucesso.")
        dialog.destroy()

    def gerar_venda(self):
        dialog = tk.Toplevel(self.janela_login)
        dialog.title("Gerar Venda")

        tk.Label(dialog, text="CPF do Cliente:").grid(row=0, column=0)
        tk.Label(dialog, text="Nome do Produto (comece a digitar):").grid(row=1, column=0)

        cpf_cliente_var = tk.StringVar()
        nome_produto_var = tk.StringVar()

        tk.Entry(dialog, textvariable=cpf_cliente_var).grid(row=0, column=1)
        tk.Entry(dialog, textvariable=nome_produto_var).grid(row=1, column=1)

        enviar_button = tk.Button(dialog, text="Enviar", command=lambda: self.enviar_venda(dialog, cpf_cliente_var.get(), nome_produto_var.get()))
        enviar_button.grid(row=2, columnspan=2)

    def enviar_venda(self, dialog, cpf_cliente, nome_produto):
        if not cpf_cliente or not nome_produto:
            messagebox.showerror("Erro na Venda", "Por favor, preencha todos os campos.")
            return

        try:
            with self.banco_de_dados.conectar() as conexao:
                conexao.execute("PRAGMA foreign_keys = ON")

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
    
if __name__ == "__main__":
    banco_de_dados = BancoDeDados()
    banco_de_dados.criar_tabelas()
    app = PapelariaApp()
    app.run()

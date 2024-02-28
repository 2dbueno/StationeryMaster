import re
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QComboBox, QDialog, QFormLayout, QInputDialog
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
        self.app = QApplication(sys.argv)
        self.janela_login = QDialog()
        self.janela_login.setWindowTitle("Login")

        layout = QFormLayout()

        self.entry_usuario = QLineEdit()
        self.entry_senha = QLineEdit()
        self.entry_senha.setEchoMode(QLineEdit.Password)
        self.entry_senha.returnPressed.connect(self.fazer_login)

        layout.addRow(QLabel("Usuário:"), self.entry_usuario)
        layout.addRow(QLabel("Senha:"), self.entry_senha)

        self.btn_login = QPushButton("Login")
        self.btn_login.clicked.connect(self.fazer_login)

        layout.addRow(self.btn_login)

        self.janela_login.setLayout(layout)

        self.banco_de_dados = BancoDeDados()
        self.operacoes_bd = OperacoesBancoDeDados(self.banco_de_dados)

    def run(self):
        self.janela_login.exec_()

    def fazer_login(self):
        usuario = self.entry_usuario.text()
        senha = self.entry_senha.text()

        if usuario == "admin" and senha == "admin":
            self.abrir_interface_principal()
        else:
            QMessageBox.critical(self.janela_login, "Erro de Login", "Login incorreto")

    def abrir_interface_principal(self):
        self.janela_login.accept()

        janela_principal = QDialog()
        janela_principal.setWindowTitle("Papelaria")

        layout = QVBoxLayout()

        btn_cadastrar_cliente = QPushButton("Cadastrar Cliente")
        btn_cadastrar_cliente.clicked.connect(self.cadastrar_cliente)

        btn_cadastrar_produto = QPushButton("Cadastrar Produto")
        btn_cadastrar_produto.clicked.connect(self.cadastrar_produto)

        btn_gerar_venda = QPushButton("Gerar Venda")
        btn_gerar_venda.clicked.connect(self.gerar_venda)

        layout.addWidget(btn_cadastrar_cliente)
        layout.addWidget(btn_cadastrar_produto)
        layout.addWidget(btn_gerar_venda)

        janela_principal.setLayout(layout)

        janela_principal.exec_()

    def cadastrar_cliente(self):
        dialog = QDialog()
        dialog.setWindowTitle("Cadastro de Cliente")

        layout = QFormLayout()

        nome_var = QLineEdit()
        cpf_var = QLineEdit()
        email_var = QLineEdit()
        telefone_var = QLineEdit()

        layout.addRow("Nome:", nome_var)
        layout.addRow("CPF:", cpf_var)
        layout.addRow("E-mail:", email_var)
        layout.addRow("Telefone:", telefone_var)

        enviar_button = QPushButton("Enviar")
        enviar_button.clicked.connect(lambda: self.enviar_cliente(dialog, cpf_var.text(), nome_var.text(), email_var.text(), telefone_var.text()))

        layout.addRow(enviar_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def enviar_cliente(self, dialog, cpf, nome, email, telefone):
        if not cpf or not self.cpf_validator.validar_cpf(cpf):
            QMessageBox.critical(dialog, "Erro no Cadastro", "CPF inválido.")
            return

        if not nome or nome.isdigit():
            QMessageBox.critical(dialog, "Erro no Cadastro", "O nome do cliente não pode ser composto apenas por números.")
            return

        if not self.validar_telefone(telefone):
            QMessageBox.critical(dialog, "Erro no Cadastro", "Telefone inválido.")
            return

        with self.banco_de_dados.conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT cpf FROM clientes WHERE cpf = ?", (cpf,))
            existing_cpf = cursor.fetchone()

        if existing_cpf:
            QMessageBox.critical(dialog, "Erro no Cadastro", f"CPF '{cpf}' já cadastrado.")
            return

        self.operacoes_bd.cadastrar_cliente(cpf, nome, email, telefone)
        QMessageBox.information(dialog, "Cadastro de Cliente", "Cliente cadastrado com sucesso.")
        dialog.accept()

    def cadastrar_produto(self):
        dialog = QDialog()
        dialog.setWindowTitle("Cadastro de Produto")

        layout = QFormLayout()

        nome_produto_var = QLineEdit()
        preco_produto_var = QLineEdit()
        quantidade_produto_var = QLineEdit()

        layout.addRow("Nome do Produto:", nome_produto_var)
        layout.addRow("Preço do Produto:", preco_produto_var)
        layout.addRow("Quantidade em Estoque:", quantidade_produto_var)

        enviar_button = QPushButton("Enviar")
        enviar_button.clicked.connect(lambda: self.enviar_produto(dialog, nome_produto_var.text(), preco_produto_var.text(), quantidade_produto_var.text()))

        layout.addRow(enviar_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def enviar_produto(self, dialog, nome_produto, preco_produto, quantidade_produto):
        if not nome_produto or preco_produto == '' or quantidade_produto == '':
            QMessageBox.critical(dialog, "Erro no Cadastro", "Por favor, verifique os dados inseridos.")
            return

        self.operacoes_bd.cadastrar_produto(nome_produto, float(preco_produto), int(quantidade_produto))
        QMessageBox.information(dialog, "Cadastro de Produto", "Produto cadastrado com sucesso.")
        dialog.accept()

    def gerar_venda(self):
        dialog = QDialog()
        dialog.setWindowTitle("Gerar Venda")

        layout = QFormLayout()

        cpf_cliente_var = QLineEdit()
        nome_produto_var = QLineEdit()

        layout.addRow("CPF do Cliente:", cpf_cliente_var)
        layout.addRow("Nome do Produto (comece a digitar):", nome_produto_var)

        enviar_button = QPushButton("Enviar")
        enviar_button.clicked.connect(lambda: self.enviar_venda(dialog, cpf_cliente_var.text(), nome_produto_var.text()))

        layout.addRow(enviar_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def enviar_venda(self, dialog, cpf_cliente, nome_produto):
        if not cpf_cliente or not nome_produto:
            QMessageBox.critical(dialog, "Erro na Venda", "Por favor, preencha todos os campos.")
            return

        try:
            with self.banco_de_dados.conectar() as conexao:
                conexao.execute("PRAGMA foreign_keys = ON")

                cursor = conexao.cursor()
                cursor.execute("SELECT id, nome, preco, quantidade FROM produtos WHERE nome LIKE ?", (f'%{nome_produto}%',))

                resultados_produto = cursor.fetchall()

                if resultados_produto:
                    janela_produtos = QDialog()
                    janela_produtos.setWindowTitle("Escolha um Produto")

                    layout = QVBoxLayout()

                    lista_produtos = QComboBox()
                    lista_produtos.addItems([produto[1] for produto in resultados_produto])

                    layout.addWidget(QLabel("Selecione o produto:"))
                    layout.addWidget(lista_produtos)

                    btn_selecionar = QPushButton("Selecionar")
                    btn_selecionar.clicked.connect(lambda: self.selecionar_produto(janela_produtos, lista_produtos.currentText(), resultados_produto, cpf_cliente))

                    layout.addWidget(btn_selecionar)

                    janela_produtos.setLayout(layout)
                    janela_produtos.exec_()
                else:
                    QMessageBox.critical(dialog, "Erro na Venda", "Nenhum produto encontrado com o nome fornecido.")

        except sqlite3.Error as e:
            QMessageBox.critical(dialog, "Erro na Venda", f"Erro ao realizar venda: {str(e)}")

    def selecionar_produto(self, janela_produtos, produto_selecionado, resultados_produto, cpf_cliente):
        janela_produtos.accept()

        if produto_selecionado:
            produto_escolhido = next((produto for produto in resultados_produto if produto[1] == produto_selecionado), None)

            if produto_escolhido:
                produto_id = produto_escolhido[0]
                quantidade_em_estoque = produto_escolhido[3]

                quantidade_vendida, ok = QInputDialog.getInt(None, "Gerar Venda", f"Quantidade Vendida para '{produto_selecionado}' (Disponível: {quantidade_em_estoque}):", 1, 1, quantidade_em_estoque)

                if ok:
                    if quantidade_vendida <= quantidade_em_estoque:
                        self.operacoes_bd.realizar_venda(produto_id, cpf_cliente, quantidade_vendida)
                        QMessageBox.information(None, "Venda Realizada", "Venda registrada com sucesso.")
                    else:
                        QMessageBox.critical(None, "Erro na Venda", "Quantidade insuficiente em estoque.")
            else:
                QMessageBox.critical(None, "Erro na Venda", "Produto não encontrado.")

    def validar_telefone(self, telefone):
        telefone = re.sub(r'\D', '', telefone)
        return len(telefone) == 11

if __name__ == "__main__":
    banco_de_dados = BancoDeDados()
    banco_de_dados.criar_tabelas()
    app = PapelariaApp()
    app.run()

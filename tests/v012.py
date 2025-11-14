"""
Sistema de Controle de Qualidade Industrial
Versão 0.1.3 - Automação de Inspeção de Peças
Desenvolvido com Python + CustomTkinter

Estrutura de pastas:
    sistema_controle_qualidade/
    ├── main.py (este arquivo)
    ├── src/
    │   ├── __init__.py
    │   ├── models.py
    │   ├── database.py
    │   ├── auth.py
    │   └── interface.py
    ├── data/
    │   ├── usuarios.json
    │   ├── pecas.json
    │   └── logs/
    └── requirements.txt
"""

import subprocess
import sys
import os
from pathlib import Path

# ====================================================================================
# VERIFICAÇÃO E INSTALAÇÃO AUTOMÁTICA DE DEPENDÊNCIAS
# ====================================================================================

def verificar_e_instalar_dependencias():
    """Verifica e instala automaticamente as dependências necessárias"""
    
    print("="*70)
    print("🔍 Verificando dependências do sistema...")
    print("="*70)
    
    dependencias = {
        'customtkinter': 'customtkinter',
        'Pillow': 'Pillow',
        'bcrypt': 'bcrypt'
    }
    
    dependencias_faltando = []
    
    # Verificar quais dependências estão faltando
    for pacote_import, pacote_pip in dependencias.items():
        try:
            __import__(pacote_import)
            print(f"✅ {pacote_pip} - Instalado")
        except ImportError:
            print(f"❌ {pacote_pip} - Não encontrado")
            dependencias_faltando.append(pacote_pip)
    
    # Se houver dependências faltando, tentar instalar
    if dependencias_faltando:
        print("\n" + "="*70)
        print(f"📦 Instalando {len(dependencias_faltando)} dependência(s) faltante(s)...")
        print("="*70)
        
        for pacote in dependencias_faltando:
            try:
                print(f"\n⏳ Instalando {pacote}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])
                print(f"✅ {pacote} instalado com sucesso!")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ ERRO ao instalar {pacote}")
                print(f"Detalhes do erro: {str(e)}")
                print("\n" + "="*70)
                print("🔧 INSTRUÇÕES PARA CORRIGIR O ERRO:")
                print("="*70)
                print(f"1. Abra o terminal/prompt de comando como ADMINISTRADOR")
                print(f"2. Execute o comando: pip install {pacote}")
                print(f"3. Se o erro persistir, execute: python -m pip install --upgrade pip")
                print(f"4. Tente novamente: pip install {pacote}")
                print("\nSe o erro continuar, verifique:")
                print("  • Conexão com a internet")
                print("  • Firewall/Antivírus bloqueando a instalação")
                print("  • Permissões de administrador")
                print("="*70)
                input("\nPressione ENTER para sair...")
                sys.exit(1)
        
        print("\n" + "="*70)
        print("✅ Todas as dependências foram instaladas com sucesso!")
        print("🔄 Reiniciando o sistema para aplicar as mudanças...")
        print("="*70)
        input("\nPressione ENTER para reiniciar...")
        
        # Reiniciar o script
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    print("\n" + "="*70)
    print("✅ Todas as dependências estão instaladas!")
    print("🚀 Iniciando o sistema...")
    print("="*70)
    print()

# Executar verificação antes de importar as bibliotecas
#verificar_e_instalar_dependencias()

# ====================================================================================
# IMPORTAÇÕES
# ====================================================================================

import customtkinter as ctk
from tkinter import messagebox, filedialog
import json
import bcrypt
from datetime import datetime
from typing import List, Dict, Optional
import csv

# ====================================================================================
# CONFIGURAÇÃO DE PASTAS E ESTRUTURA
# ====================================================================================

class ConfiguracaoSistema:
    """Gerencia a estrutura de pastas e configurações do sistema"""
    
    # Diretórios base
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = DATA_DIR / "logs"
    BACKUP_DIR = DATA_DIR / "backups"
    
    # Arquivos de dados
    ARQUIVO_USUARIOS = DATA_DIR / "usuarios.json"
    ARQUIVO_PECAS = DATA_DIR / "pecas.json"
    ARQUIVO_CAIXAS = DATA_DIR / "caixas.json"
    ARQUIVO_CONFIG = DATA_DIR / "config.json"
    
    @classmethod
    def criar_estrutura_pastas(cls):
        """Cria a estrutura de pastas necessária"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.BACKUP_DIR.mkdir(exist_ok=True)
        
        # Criar arquivo de log de inicialização
        log_arquivo = cls.LOGS_DIR / f"log_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(log_arquivo, 'a', encoding='utf-8') as f:
            f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Sistema iniciado\n")
    
    @classmethod
    def registrar_log(cls, mensagem: str, tipo: str = "INFO"):
        """Registra um evento no log"""
        log_arquivo = cls.LOGS_DIR / f"log_{datetime.now().strftime('%Y%m%d')}.txt"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_arquivo, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} - [{tipo}] {mensagem}\n")

# ====================================================================================
# SISTEMA DE AUTENTICAÇÃO
# ====================================================================================

class SistemaAutenticacao:
    """Gerencia autenticação e usuários do sistema"""
    
    def __init__(self):
        self.arquivo_usuarios = ConfiguracaoSistema.ARQUIVO_USUARIOS
        self.usuarios = self.carregar_usuarios()
        
        # Criar usuário padrão se não existir nenhum
        if not self.usuarios:
            self.criar_usuario_padrao()
    
    def carregar_usuarios(self) -> Dict:
        """Carrega usuários do arquivo"""
        if self.arquivo_usuarios.exists():
            try:
                with open(self.arquivo_usuarios, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def salvar_usuarios(self):
        """Salva usuários no arquivo"""
        with open(self.arquivo_usuarios, 'w', encoding='utf-8') as f:
            json.dump(self.usuarios, f, indent=2, ensure_ascii=False)
    
    def criar_usuario_padrao(self):
        """Cria usuário padrão admin/admin"""
        senha_hash = bcrypt.hashpw("admin".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.usuarios['admin'] = {
            'senha': senha_hash,
            'nome_completo': 'Administrador',
            'nivel': 'administrador',
            'data_criacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.salvar_usuarios()
        ConfiguracaoSistema.registrar_log("Usuário padrão 'admin' criado", "SISTEMA")
    
    def autenticar(self, usuario: str, senha: str) -> bool:
        """Autentica um usuário"""
        if usuario in self.usuarios:
            senha_hash = self.usuarios[usuario]['senha']
            if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
                ConfiguracaoSistema.registrar_log(f"Login bem-sucedido: {usuario}", "AUTH")
                return True
        ConfiguracaoSistema.registrar_log(f"Tentativa de login falhou: {usuario}", "AUTH")
        return False
    
    def criar_usuario(self, usuario: str, senha: str, nome_completo: str, nivel: str = "operador") -> bool:
        """Cria um novo usuário"""
        if usuario in self.usuarios:
            return False
        
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.usuarios[usuario] = {
            'senha': senha_hash,
            'nome_completo': nome_completo,
            'nivel': nivel,
            'data_criacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.salvar_usuarios()
        ConfiguracaoSistema.registrar_log(f"Novo usuário criado: {usuario}", "ADMIN")
        return True
    
    def obter_info_usuario(self, usuario: str) -> Optional[Dict]:
        """Obtém informações de um usuário"""
        return self.usuarios.get(usuario)

# ====================================================================================
# MODELOS DE DADOS
# ====================================================================================

class Peca:
    """Classe que representa uma peça"""
    
    def __init__(self, id_peca: str, peso: float, cor: str, comprimento: float, usuario: str = ""):
        self.id_peca = id_peca
        self.peso = peso
        self.cor = cor.lower()
        self.comprimento = comprimento
        self.usuario = usuario
        self.timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.aprovada = False
        self.motivos_reprovacao = []
        
    def validar(self) -> bool:
        """Valida a peça conforme os critérios de qualidade"""
        self.motivos_reprovacao = []
        
        if not (95 <= self.peso <= 105):
            self.motivos_reprovacao.append(f"Peso fora do padrão: {self.peso}g (esperado: 95-105g)")
        
        if self.cor not in ['azul', 'verde']:
            self.motivos_reprovacao.append(f"Cor não aprovada: {self.cor} (esperado: azul ou verde)")
        
        if not (10 <= self.comprimento <= 20):
            self.motivos_reprovacao.append(f"Comprimento fora do padrão: {self.comprimento}cm (esperado: 10-20cm)")
        
        self.aprovada = len(self.motivos_reprovacao) == 0
        return self.aprovada
    
    def to_dict(self) -> Dict:
        """Converte a peça para dicionário"""
        return {
            'id': self.id_peca,
            'peso': self.peso,
            'cor': self.cor,
            'comprimento': self.comprimento,
            'usuario': self.usuario,
            'timestamp': self.timestamp,
            'aprovada': self.aprovada,
            'motivos_reprovacao': self.motivos_reprovacao
        }

class Caixa:
    """Classe que representa uma caixa de peças"""
    
    CAPACIDADE_MAXIMA = 10
    
    def __init__(self, numero: int):
        self.numero = numero
        self.pecas: List[Peca] = []
        self.data_fechamento = None
        self.usuario_fechamento = ""
        
    def adicionar_peca(self, peca: Peca) -> bool:
        """Adiciona uma peça à caixa se houver espaço"""
        if len(self.pecas) < self.CAPACIDADE_MAXIMA:
            self.pecas.append(peca)
            if len(self.pecas) == self.CAPACIDADE_MAXIMA:
                self.fechar(peca.usuario)
            return True
        return False
    
    def fechar(self, usuario: str = ""):
        """Fecha a caixa"""
        self.data_fechamento = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.usuario_fechamento = usuario
    
    def esta_cheia(self) -> bool:
        """Verifica se a caixa está cheia"""
        return len(self.pecas) >= self.CAPACIDADE_MAXIMA
    
    def vagas_disponiveis(self) -> int:
        """Retorna o número de vagas disponíveis"""
        return self.CAPACIDADE_MAXIMA - len(self.pecas)
    
    def to_dict(self) -> Dict:
        """Converte a caixa para dicionário"""
        return {
            'numero': self.numero,
            'pecas': [p.to_dict() for p in self.pecas],
            'data_fechamento': self.data_fechamento,
            'usuario_fechamento': self.usuario_fechamento,
            'quantidade_pecas': len(self.pecas)
        }

# ====================================================================================
# BANCO DE DADOS
# ====================================================================================

class BancoDados:
    """Gerencia o armazenamento de dados do sistema"""
    
    def __init__(self):
        self.arquivo_pecas = ConfiguracaoSistema.ARQUIVO_PECAS
        self.arquivo_caixas = ConfiguracaoSistema.ARQUIVO_CAIXAS
        self.pecas_aprovadas: List[Peca] = []
        self.pecas_reprovadas: List[Peca] = []
        self.caixas_fechadas: List[Caixa] = []
        self.caixa_atual: Caixa = Caixa(1)
        self.carregar_dados()
    
    def carregar_dados(self):
        """Carrega dados dos arquivos"""
        # Carregar peças
        if self.arquivo_pecas.exists():
            try:
                with open(self.arquivo_pecas, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                for p_dict in dados.get('aprovadas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.timestamp = p_dict['timestamp']
                    self.pecas_aprovadas.append(peca)
                
                for p_dict in dados.get('reprovadas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.motivos_reprovacao = p_dict['motivos_reprovacao']
                    peca.timestamp = p_dict['timestamp']
                    self.pecas_reprovadas.append(peca)
            except Exception as e:
                ConfiguracaoSistema.registrar_log(f"Erro ao carregar peças: {e}", "ERRO")
        
        # Carregar caixas
        if self.arquivo_caixas.exists():
            try:
                with open(self.arquivo_caixas, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                for c_dict in dados.get('fechadas', []):
                    caixa = Caixa(c_dict['numero'])
                    caixa.data_fechamento = c_dict['data_fechamento']
                    caixa.usuario_fechamento = c_dict.get('usuario_fechamento', '')
                    for p_dict in c_dict['pecas']:
                        peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                        peca.aprovada = p_dict['aprovada']
                        peca.timestamp = p_dict['timestamp']
                        caixa.pecas.append(peca)
                    self.caixas_fechadas.append(caixa)
                
                c_atual = dados.get('atual', {})
                self.caixa_atual = Caixa(c_atual.get('numero', len(self.caixas_fechadas) + 1))
                for p_dict in c_atual.get('pecas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.timestamp = p_dict['timestamp']
                    self.caixa_atual.pecas.append(peca)
            except Exception as e:
                ConfiguracaoSistema.registrar_log(f"Erro ao carregar caixas: {e}", "ERRO")
    
    def salvar_dados(self):
        """Salva dados nos arquivos"""
        # Salvar peças
        dados_pecas = {
            'aprovadas': [p.to_dict() for p in self.pecas_aprovadas],
            'reprovadas': [p.to_dict() for p in self.pecas_reprovadas]
        }
        with open(self.arquivo_pecas, 'w', encoding='utf-8') as f:
            json.dump(dados_pecas, f, indent=2, ensure_ascii=False)
        
        # Salvar caixas
        dados_caixas = {
            'fechadas': [c.to_dict() for c in self.caixas_fechadas],
            'atual': self.caixa_atual.to_dict()
        }
        with open(self.arquivo_caixas, 'w', encoding='utf-8') as f:
            json.dump(dados_caixas, f, indent=2, ensure_ascii=False)
    
    def adicionar_peca(self, peca: Peca):
        """Adiciona uma peça ao banco"""
        if peca.aprovada:
            self.pecas_aprovadas.append(peca)
            if not self.caixa_atual.adicionar_peca(peca):
                self.caixas_fechadas.append(self.caixa_atual)
                self.caixa_atual = Caixa(len(self.caixas_fechadas) + 1)
                self.caixa_atual.adicionar_peca(peca)
            
            if self.caixa_atual.esta_cheia():
                self.caixas_fechadas.append(self.caixa_atual)
                self.caixa_atual = Caixa(len(self.caixas_fechadas) + 1)
        else:
            self.pecas_reprovadas.append(peca)
        
        self.salvar_dados()
        ConfiguracaoSistema.registrar_log(f"Peça {peca.id_peca} {'aprovada' if peca.aprovada else 'reprovada'} por {peca.usuario}", "INSPECAO")
    
    def remover_peca(self, id_peca: str) -> bool:
        """Remove uma peça do sistema"""
        # Tentar remover de aprovadas
        for i, peca in enumerate(self.pecas_aprovadas):
            if peca.id_peca == id_peca:
                del self.pecas_aprovadas[i]
                self.salvar_dados()
                ConfiguracaoSistema.registrar_log(f"Peça {id_peca} removida (aprovadas)", "REMOCAO")
                return True
        
        # Tentar remover de reprovadas
        for i, peca in enumerate(self.pecas_reprovadas):
            if peca.id_peca == id_peca:
                del self.pecas_reprovadas[i]
                self.salvar_dados()
                ConfiguracaoSistema.registrar_log(f"Peça {id_peca} removida (reprovadas)", "REMOCAO")
                return True
        
        return False
    
    def gerar_relatorio(self) -> Dict:
        """Gera relatório completo"""
        return {
            'data_geracao': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'total_pecas_aprovadas': len(self.pecas_aprovadas),
            'total_pecas_reprovadas': len(self.pecas_reprovadas),
            'total_pecas_inspecionadas': len(self.pecas_aprovadas) + len(self.pecas_reprovadas),
            'caixas_completas': len(self.caixas_fechadas),
            'caixa_atual': {
                'numero': self.caixa_atual.numero,
                'pecas': len(self.caixa_atual.pecas),
                'vagas_disponiveis': self.caixa_atual.vagas_disponiveis()
            },
            'pecas_reprovadas_detalhes': [p.to_dict() for p in self.pecas_reprovadas],
            'caixas_fechadas_detalhes': [c.to_dict() for c in self.caixas_fechadas]
        }

# ====================================================================================
# INTERFACE GRÁFICA
# ====================================================================================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class TelaLogin:
    """Tela de login do sistema"""
    
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.auth = SistemaAutenticacao()
        
        self.frame = ctk.CTkFrame(root)
        self.frame.pack(fill="both", expand=True)
        
        self.criar_interface()
    
    def criar_interface(self):
        """Cria a interface de login"""
        # Container central
        container = ctk.CTkFrame(self.frame, width=400, height=500, fg_color="#1f538d")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo/Título
        titulo = ctk.CTkLabel(
            container,
            text="🏭",
            font=ctk.CTkFont(size=60)
        )
        titulo.pack(pady=(40, 10))
        
        titulo2 = ctk.CTkLabel(
            container,
            text="Sistema de Controle\nde Qualidade Industrial",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        titulo2.pack(pady=(0, 40))
        
        # Campo usuário
        self.entry_usuario = ctk.CTkEntry(
            container,
            width=300,
            height=40,
            placeholder_text="👤 Usuário",
            font=ctk.CTkFont(size=14)
        )
        self.entry_usuario.pack(pady=10)
        
        # Campo senha
        self.entry_senha = ctk.CTkEntry(
            container,
            width=300,
            height=40,
            placeholder_text="🔒 Senha",
            show="●",
            font=ctk.CTkFont(size=14)
        )
        self.entry_senha.pack(pady=10)
        self.entry_senha.bind('<Return>', lambda e: self.fazer_login())
        
        # Botão login
        btn_login = ctk.CTkButton(
            container,
            text="Entrar",
            width=300,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.fazer_login,
            fg_color="white",
            text_color="#1f538d",
            hover_color="#e0e0e0"
        )
        btn_login.pack(pady=20)
        
        # Info padrão
        info = ctk.CTkLabel(
            container,
            text="Usuário padrão: admin / Senha: admin",
            font=ctk.CTkFont(size=11),
            text_color="#e0e0e0"
        )
        info.pack(pady=(20, 40))
    
    def fazer_login(self):
        """Processa o login"""
        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get()
        
        if not usuario or not senha:
            messagebox.showerror("Erro", "Por favor, preencha usuário e senha!")
            return
        
        if self.auth.autenticar(usuario, senha):
            info_usuario = self.auth.obter_info_usuario(usuario)
            self.frame.destroy()
            self.on_login_success(usuario, info_usuario)
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos!")
            self.entry_senha.delete(0, 'end')

class TelaPrincipal:
    """Tela principal do sistema"""
    
    def __init__(self, root, usuario: str, info_usuario: Dict):
        self.root = root
        self.usuario = usuario
        self.info_usuario = info_usuario
        self.db = BancoDados()
        
        self.frame_principal = ctk.CTkFrame(root)
        self.frame_principal.pack(fill="both", expand=True)
        
        self.criar_menu_principal()
    
    def criar_menu_principal(self):
        """Cria o menu principal"""
        # Limpar frame
        for widget in self.frame_principal.winfo_children():
            widget.destroy()
        
        # Header
        header = ctk.CTkFrame(self.frame_principal, fg_color="#1f538d", height=80)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)
        
        titulo = ctk.CTkLabel(
            header,
            text="🏭 Sistema de Controle de Qualidade Industrial",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        titulo.pack(side="left", padx=20)
        
        info_user = ctk.CTkLabel(
            header,
            text=f"👤 {self.info_usuario['nome_completo']}\n📋 {self.info_usuario['nivel'].title()}",
            font=ctk.CTkFont(size=11),
            text_color="white",
            justify="right"
        )
        info_user.pack(side="right", padx=20)
        
        # Dashboard
        dash_frame = ctk.CTkFrame(self.frame_principal)
        dash_frame.pack(fill="x", padx=10, pady=10)
        
        self.criar_card(dash_frame, "Peças Aprovadas", str(len(self.db.pecas_aprovadas)), "#2ecc71").pack(side="left", fill="both", expand=True, padx=5)
        self.criar_card(dash_frame, "Peças Reprovadas", str(len(self.db.pecas_reprovadas)), "#e74c3c").pack(side="left", fill="both", expand=True, padx=5)
        self.criar_card(dash_frame, "Caixas Completas", str(len(self.db.caixas_fechadas)), "#3498db").pack(side="left", fill="both", expand=True, padx=5)
        
        # Menu de opções
        menu_frame = ctk.CTkFrame(self.frame_principal)
        menu_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        titulo_menu = ctk.CTkLabel(
            menu_frame,
            text="Escolha uma opção:",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        titulo_menu.pack(pady=20)
        
        opcoes = [
            ("📝 1. Cadastrar Nova Peça", self.tela_cadastrar_peca, "#1f538d"),
            ("📋 2. Listar Peças (Aprovadas/Reprovadas)", self.tela_listar_pecas, "#2980b9"),
            ("🗑️ 3. Remover Peça Cadastrada", self.tela_remover_peca, "#e67e22"),
            ("📦 4. Listar Caixas Fechadas", self.tela_listar_caixas, "#27ae60"),
            ("📊 5. Gerar Relatório Final", self.tela_relatorio, "#8e44ad"),
            ("🚪 Sair", self.root.quit, "#c0392b")
        ]
        
        for texto, comando, cor in opcoes:
            btn = ctk.CTkButton(
                menu_frame,
                text=texto,
                width=500,
                height=50,
                font=ctk.CTkFont(size=14, weight="bold"),
                command=comando,
                fg_color=cor,
                hover_color=self.escurecer_cor(cor)
            )
            btn.pack(pady=5)
    
    def criar_card(self, parent, titulo, valor, cor):
        """Cria card para dashboard"""
        card = ctk.CTkFrame(parent, fg_color=cor, height=100)
        card.pack_propagate(False)
        
        ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=12), text_color="white").pack(pady=(15, 5))
        ctk.CTkLabel(card, text=valor, font=ctk.CTkFont(size=36, weight="bold"), text_color="white").pack(pady=(5, 15))
        
        return card
    
    def escurecer_cor(self, cor):
        """Escurece uma cor hex"""
        cor = cor.lstrip('#')
        r, g, b = int(cor[0:2], 16), int(cor[2:4], 16), int(cor[4:6], 16)
        r, g, b = max(0, r-30), max(0, g-30), max(0, b-30)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def tela_cadastrar_peca(self):
        """Tela de cadastro de nova peça"""
        # Limpar frame
        for widget in self.frame_principal.winfo_children():
            widget.destroy()
        
        # Header
        self.criar_header("📝 Cadastrar Nova Peça")
        
        # Formulário
        form_frame = ctk.CTkFrame(self.frame_principal)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ID
        ctk.CTkLabel(form_frame, text="ID da Peça:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        entry_id = ctk.CTkEntry(form_frame, width=400, height=40, placeholder_text="Ex: PCA001")
        entry_id.pack(padx=20, pady=5)
        
        # Peso
        ctk.CTkLabel(form_frame, text="Peso (g) - Padrão: 95g a 105g:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        entry_peso = ctk.CTkEntry(form_frame, width=400, height=40, placeholder_text="Ex: 100")
        entry_peso.pack(padx=20, pady=5)
        
        # Cor
        ctk.CTkLabel(form_frame, text="Cor - Aprovadas: Azul ou Verde:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        combo_cor = ctk.CTkComboBox(form_frame, width=400, height=40, values=["azul", "verde", "vermelho", "amarelo", "preto", "branco"])
        combo_cor.set("azul")
        combo_cor.pack(padx=20, pady=5)
        
        # Comprimento
        ctk.CTkLabel(form_frame, text="Comprimento (cm) - Padrão: 10cm a 20cm:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        entry_comp = ctk.CTkEntry(form_frame, width=400, height=40, placeholder_text="Ex: 15")
        entry_comp.pack(padx=20, pady=5)
        
        # Botões
        btn_frame = ctk.CTkFrame(form_frame)
        btn_frame.pack(pady=30)
        
        def cadastrar():
            try:
                id_peca = entry_id.get().strip()
                peso = float(entry_peso.get().strip())
                cor = combo_cor.get()
                comp = float(entry_comp.get().strip())
                
                if not id_peca:
                    messagebox.showerror("Erro", "ID da peça é obrigatório!")
                    return
                
                peca = Peca(id_peca, peso, cor, comp, self.usuario)
                peca.validar()
                self.db.adicionar_peca(peca)
                
                if peca.aprovada:
                    messagebox.showinfo("Sucesso", f"✅ Peça {id_peca} APROVADA!\n\nAdicionada à caixa #{self.db.caixa_atual.numero}")
                else:
                    motivos = "\n".join([f"• {m}" for m in peca.motivos_reprovacao])
                    messagebox.showwarning("Reprovada", f"❌ Peça {id_peca} REPROVADA!\n\nMotivos:\n{motivos}")
                
                self.criar_menu_principal()
            except ValueError:
                messagebox.showerror("Erro", "Peso e comprimento devem ser números válidos!")
        
        ctk.CTkButton(btn_frame, text="✅ Cadastrar Peça", width=200, height=50, command=cadastrar, font=ctk.CTkFont(size=14, weight="bold"), fg_color="#2ecc71").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔙 Voltar", width=200, height=50, command=self.criar_menu_principal, font=ctk.CTkFont(size=14, weight="bold"), fg_color="#95a5a6").pack(side="left", padx=10)
    
    def tela_listar_pecas(self):
        """Tela de listagem de peças"""
        for widget in self.frame_principal.winfo_children():
            widget.destroy()
        
        self.criar_header("📋 Listar Peças")
        
        # Tabs
        tab_frame = ctk.CTkFrame(self.frame_principal)
        tab_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tabs = ctk.CTkTabview(tab_frame)
        tabs.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab Aprovadas
        tab_aprov = tabs.add("✅ Aprovadas")
        text_aprov = ctk.CTkTextbox(tab_aprov, font=ctk.CTkFont(size=11))
        text_aprov.pack(fill="both", expand=True, padx=10, pady=10)
        
        if self.db.pecas_aprovadas:
            text_aprov.insert("end", f"Total: {len(self.db.pecas_aprovadas)} peças aprovadas\n")
            text_aprov.insert("end", "="*80 + "\n\n")
            for i, peca in enumerate(self.db.pecas_aprovadas, 1):
                text_aprov.insert("end", f"{i}. ID: {peca.id_peca}\n")
                text_aprov.insert("end", f"   Peso: {peca.peso}g | Cor: {peca.cor} | Comprimento: {peca.comprimento}cm\n")
                text_aprov.insert("end", f"   Inspetor: {peca.usuario} | Data: {peca.timestamp}\n")
                text_aprov.insert("end", "-"*80 + "\n")
        else:
            text_aprov.insert("end", "Nenhuma peça aprovada cadastrada.")
        text_aprov.configure(state="disabled")
        
        # Tab Reprovadas
        tab_reprov = tabs.add("❌ Reprovadas")
        text_reprov = ctk.CTkTextbox(tab_reprov, font=ctk.CTkFont(size=11))
        text_reprov.pack(fill="both", expand=True, padx=10, pady=10)
        
        if self.db.pecas_reprovadas:
            text_reprov.insert("end", f"Total: {len(self.db.pecas_reprovadas)} peças reprovadas\n")
            text_reprov.insert("end", "="*80 + "\n\n")
            for i, peca in enumerate(self.db.pecas_reprovadas, 1):
                text_reprov.insert("end", f"{i}. ID: {peca.id_peca}\n")
                text_reprov.insert("end", f"   Peso: {peca.peso}g | Cor: {peca.cor} | Comprimento: {peca.comprimento}cm\n")
                text_reprov.insert("end", f"   Inspetor: {peca.usuario} | Data: {peca.timestamp}\n")
                text_reprov.insert("end", f"   Motivos:\n")
                for motivo in peca.motivos_reprovacao:
                    text_reprov.insert("end", f"   • {motivo}\n")
                text_reprov.insert("end", "-"*80 + "\n")
        else:
            text_reprov.insert("end", "Nenhuma peça reprovada cadastrada.")
        text_reprov.configure(state="disabled")
        
        # Botão voltar
        ctk.CTkButton(tab_frame, text="🔙 Voltar ao Menu", width=200, height=50, command=self.criar_menu_principal, font=ctk.CTkFont(size=14, weight="bold"), fg_color="#95a5a6").pack(pady=10)
    
    def tela_remover_peca(self):
        """Tela de remoção de peça"""
        for widget in self.frame_principal.winfo_children():
            widget.destroy()
        
        self.criar_header("🗑️ Remover Peça Cadastrada")
        
        form_frame = ctk.CTkFrame(self.frame_principal)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(form_frame, text="Digite o ID da peça a ser removida:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=30)
        
        entry_id = ctk.CTkEntry(form_frame, width=400, height=50, placeholder_text="Ex: PCA001", font=ctk.CTkFont(size=14))
        entry_id.pack(pady=10)
        
        def remover():
            id_peca = entry_id.get().strip()
            if not id_peca:
                messagebox.showerror("Erro", "Digite um ID válido!")
                return
            
            resposta = messagebox.askyesno("Confirmar", f"Tem certeza que deseja remover a peça {id_peca}?\n\nEsta ação não pode ser desfeita!")
            if resposta:
                if self.db.remover_peca(id_peca):
                    messagebox.showinfo("Sucesso", f"Peça {id_peca} removida com sucesso!")
                    self.criar_menu_principal()
                else:
                    messagebox.showerror("Erro", f"Peça {id_peca} não encontrada!")
        
        btn_frame = ctk.CTkFrame(form_frame)
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(btn_frame, text="🗑️ Remover Peça", width=200, height=50, command=remover, font=ctk.CTkFont(size=14, weight="bold"), fg_color="#e74c3c").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔙 Voltar", width=200, height=50, command=self.criar_menu_principal, font=ctk.CTkFont(size=14, weight="bold"), fg_color="#95a5a6").pack(side="left", padx=10)
    
    def tela_listar_caixas(self):
        """Tela de listagem de caixas fechadas"""
        for widget in self.frame_principal.winfo_children():
            widget.destroy()
        
        self.criar_header("📦 Caixas Fechadas")
        
        content_frame = ctk.CTkFrame(self.frame_principal)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Caixa atual
        ctk.CTkLabel(content_frame, text="📦 Caixa Atual:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        info_frame = ctk.CTkFrame(content_frame, fg_color="#3498db", height=100)
        info_frame.pack(fill="x", padx=10, pady=10)
        info_frame.pack_propagate(False)
        
        ctk.CTkLabel(info_frame, text=f"Caixa #{self.db.caixa_atual.numero}", font=ctk.CTkFont(size=18, weight="bold"), text_color="white").pack(pady=5)
        ctk.CTkLabel(info_frame, text=f"Peças: {len(self.db.caixa_atual.pecas)}/10 | Vagas: {self.db.caixa_atual.vagas_disponiveis()}", font=ctk.CTkFont(size=14), text_color="white").pack(pady=5)
        
        # Caixas fechadas
        ctk.CTkLabel(content_frame, text="📦 Caixas Fechadas:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        text_caixas = ctk.CTkTextbox(content_frame, font=ctk.CTkFont(size=11))
        text_caixas.pack(fill="both", expand=True, padx=10, pady=10)
        
        if self.db.caixas_fechadas:
            text_caixas.insert("end", f"Total: {len(self.db.caixas_fechadas)} caixas completas\n")
            text_caixas.insert("end", "="*80 + "\n\n")
            for caixa in self.db.caixas_fechadas:
                text_caixas.insert("end", f"📦 Caixa #{caixa.numero}\n")
                text_caixas.insert("end", f"   Data de Fechamento: {caixa.data_fechamento}\n")
                text_caixas.insert("end", f"   Fechada por: {caixa.usuario_fechamento}\n")
                text_caixas.insert("end", f"   Quantidade de Peças: {len(caixa.pecas)}\n")
                text_caixas.insert("end", f"   Peças: {', '.join([p.id_peca for p in caixa.pecas])}\n")
                text_caixas.insert("end", "-"*80 + "\n\n")
        else:
            text_caixas.insert("end", "Nenhuma caixa fechada ainda.")
        text_caixas.configure(state="disabled")
        
        ctk.CTkButton(content_frame, text="🔙 Voltar ao Menu", width=200, height=50, command=self.criar_menu_principal, font=ctk.CTkFont(size=14, weight="bold"), fg_color="#95a5a6").pack(pady=10)
    
    def tela_relatorio(self):
        """Tela de relatório final"""
        for widget in self.frame_principal.winfo_children():
            widget.destroy()
        
        self.criar_header("📊 Relatório Final")
        
        content_frame = ctk.CTkFrame(self.frame_principal)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Relatório
        text_relatorio = ctk.CTkTextbox(content_frame, font=ctk.CTkFont(size=11))
        text_relatorio.pack(fill="both", expand=True, padx=10, pady=10)
        
        relatorio = self.db.gerar_relatorio()
        
        text_relatorio.insert("end", "="*80 + "\n")
        text_relatorio.insert("end", "           RELATÓRIO FINAL - CONTROLE DE QUALIDADE INDUSTRIAL\n")
        text_relatorio.insert("end", "="*80 + "\n\n")
        text_relatorio.insert("end", f"Data de Geração: {relatorio['data_geracao']}\n")
        text_relatorio.insert("end", f"Gerado por: {self.info_usuario['nome_completo']} ({self.usuario})\n\n")
        
        text_relatorio.insert("end", "📈 RESUMO GERAL\n")
        text_relatorio.insert("end", "-"*80 + "\n")
        text_relatorio.insert("end", f"Total de Peças Inspecionadas: {relatorio['total_pecas_inspecionadas']}\n")
        text_relatorio.insert("end", f"✅ Peças Aprovadas: {relatorio['total_pecas_aprovadas']}\n")
        text_relatorio.insert("end", f"❌ Peças Reprovadas: {relatorio['total_pecas_reprovadas']}\n")
        text_relatorio.insert("end", f"📦 Caixas Completas: {relatorio['caixas_completas']}\n\n")
        
        if relatorio['total_pecas_inspecionadas'] > 0:
            taxa = (relatorio['total_pecas_aprovadas'] / relatorio['total_pecas_inspecionadas']) * 100
            text_relatorio.insert("end", f"📊 Taxa de Aprovação: {taxa:.2f}%\n\n")
        
        text_relatorio.insert("end", "📦 CAIXA ATUAL\n")
        text_relatorio.insert("end", "-"*80 + "\n")
        text_relatorio.insert("end", f"Número: #{relatorio['caixa_atual']['numero']}\n")
        text_relatorio.insert("end", f"Peças: {relatorio['caixa_atual']['pecas']}/10\n")
        text_relatorio.insert("end", f"Vagas Disponíveis: {relatorio['caixa_atual']['vagas_disponiveis']}\n\n")
        
        if relatorio['total_pecas_reprovadas'] > 0:
            text_relatorio.insert("end", "❌ ANÁLISE DE REPROVAÇÕES\n")
            text_relatorio.insert("end", "-"*80 + "\n")
            motivos_count = {}
            for peca in relatorio['pecas_reprovadas_detalhes']:
                for motivo in peca['motivos_reprovacao']:
                    if 'Peso' in motivo:
                        motivos_count['Peso fora do padrão'] = motivos_count.get('Peso fora do padrão', 0) + 1
                    elif 'Cor' in motivo:
                        motivos_count['Cor não aprovada'] = motivos_count.get('Cor não aprovada', 0) + 1
                    elif 'Comprimento' in motivo:
                        motivos_count['Comprimento fora do padrão'] = motivos_count.get('Comprimento fora do padrão', 0) + 1
            
            for motivo, count in motivos_count.items():
                text_relatorio.insert("end", f"• {motivo}: {count} ocorrências\n")
            text_relatorio.insert("end", "\n")
        
        text_relatorio.insert("end", "="*80 + "\n")
        text_relatorio.insert("end", "Relatório gerado automaticamente - Sistema v2.0\n")
        text_relatorio.insert("end", "="*80 + "\n")
        text_relatorio.configure(state="disabled")
        
        # Botões de exportação
        btn_frame = ctk.CTkFrame(content_frame)
        btn_frame.pack(pady=10)
        
        def exportar_json():
            try:
                caminho = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json")],
                    initialfile=f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                if caminho:
                    with open(caminho, 'w', encoding='utf-8') as f:
                        json.dump(relatorio, f, indent=2, ensure_ascii=False)
                    messagebox.showinfo("Sucesso", f"Relatório exportado:\n{caminho}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar: {e}")
        
        def exportar_csv():
            try:
                caminho = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")],
                    initialfile=f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                if caminho:
                    with open(caminho, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f, delimiter=';')
                        writer.writerow(['ID', 'Peso', 'Cor', 'Comprimento', 'Status', 'Inspetor', 'Data', 'Motivos'])
                        
                        for peca in self.db.pecas_aprovadas:
                            writer.writerow([peca.id_peca, peca.peso, peca.cor, peca.comprimento, 'APROVADA', peca.usuario, peca.timestamp, ''])
                        
                        for peca in self.db.pecas_reprovadas:
                            motivos = ' | '.join(peca.motivos_reprovacao)
                            writer.writerow([peca.id_peca, peca.peso, peca.cor, peca.comprimento, 'REPROVADA', peca.usuario, peca.timestamp, motivos])
                    
                    messagebox.showinfo("Sucesso", f"Relatório exportado:\n{caminho}\n\nAbra com Excel!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar: {e}")
        
        ctk.CTkButton(btn_frame, text="💾 Exportar JSON", width=180, height=45, command=exportar_json, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#2ecc71").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📄 Exportar CSV", width=180, height=45, command=exportar_csv, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#27ae60").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🔙 Voltar", width=180, height=45, command=self.criar_menu_principal, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#95a5a6").pack(side="left", padx=5)
    
    def criar_header(self, titulo: str):
        """Cria o header padrão"""
        header = ctk.CTkFrame(self.frame_principal, fg_color="#1f538d", height=60)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text=titulo, font=ctk.CTkFont(size=20, weight="bold"), text_color="white").pack(side="left", padx=20)

# ====================================================================================
# APLICAÇÃO PRINCIPAL
# ====================================================================================

class Aplicacao:
    """Classe principal da aplicação"""
    
    def __init__(self):
        # Criar estrutura de pastas
        ConfiguracaoSistema.criar_estrutura_pastas()
        ConfiguracaoSistema.registrar_log("Aplicação iniciada", "SISTEMA")
        
        # Criar janela principal
        self.root = ctk.CTk()
        self.root.title("Sistema de Controle de Qualidade Industrial v2.0")
        self.root.geometry("1200x800")
        
        # Centralizar janela
        self.centralizar_janela()
        
        # Iniciar com tela de login
        TelaLogin(self.root, self.on_login_success)
    
    def centralizar_janela(self):
        """Centraliza a janela na tela"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_login_success(self, usuario: str, info_usuario: Dict):
        """Callback após login bem-sucedido"""
        TelaPrincipal(self.root, usuario, info_usuario)
    
    def executar(self):
        """Executa a aplicação"""
        self.root.mainloop()
        ConfiguracaoSistema.registrar_log("Aplicação encerrada", "SISTEMA")

# ====================================================================================
# PONTO DE ENTRADA
# ====================================================================================

def main():
    """Função principal"""
    print("\n" + "="*70)
    print("  Sistema de Controle de Qualidade Industrial v2.0")
    print("  Automação de Inspeção de Peças - Linha de Montagem")
    print("="*70 + "\n")
    
    app = Aplicacao()
    app.executar()

if __name__ == "__main__":
    main()
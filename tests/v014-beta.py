"""
Sistema de Controle de Qualidade Industrial
Versão 3.0 - Profissional Completo
Desenvolvido com CustomTkinter, Matplotlib, ReportLab
"""

import subprocess
import sys
import os
from pathlib import Path
import json
import bcrypt
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import csv
import threading
from collections import Counter
from functools import wraps

# Verificar e importar dependências
try:
    import customtkinter as ctk
    from tkinter import messagebox, filedialog
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
except ImportError as e:
    print(f"❌ Erro ao importar dependências: {e}")
    print("⏳ Instalando dependências necessárias...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter", "Pillow", "bcrypt", "matplotlib", "reportlab"])
    print("🔄 Reinicie o programa após a instalação")
    sys.exit(1)

# ====================================================================================
# CONFIGURAÇÃO DO SISTEMA
# ====================================================================================

class ConfiguracaoSistema:
    """Gerencia configurações e estrutura de pastas"""
    
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = DATA_DIR / "logs"
    BACKUP_DIR = DATA_DIR / "backups"
    REPORTS_DIR = DATA_DIR / "reports"
    
    ARQUIVO_USUARIOS = DATA_DIR / "usuarios.json"
    ARQUIVO_PECAS = DATA_DIR / "pecas.json"
    ARQUIVO_CAIXAS = DATA_DIR / "caixas.json"
    ARQUIVO_CONFIG = DATA_DIR / "config.json"
    ARQUIVO_AUDITORIA = DATA_DIR / "auditoria.json"
    
    CONFIG_PADRAO = {
        'criterios_qualidade': {
            'peso_min': 95,
            'peso_max': 105,
            'cores_aceitas': ['azul', 'verde'],
            'comprimento_min': 10,
            'comprimento_max': 20
        },
        'capacidade_caixa': 10,
        'auto_backup': True,
        'backup_interval_hours': 24,
        'interface': {
            'tema': 'light',
            'cor_primaria': 'blue'
        },
        'metas': {
            'diaria': 500,
            'taxa_aprovacao_minima': 85
        },
        'alertas': {
            'taxa_reprovacao_alta': 15,
            'som_enabled': True
        },
        'timeout_sessao_minutos': 30
    }
    
    @classmethod
    def criar_estrutura_pastas(cls):
        """Cria estrutura de pastas"""
        try:
            cls.DATA_DIR.mkdir(exist_ok=True)
            cls.LOGS_DIR.mkdir(exist_ok=True)
            cls.BACKUP_DIR.mkdir(exist_ok=True)
            cls.REPORTS_DIR.mkdir(exist_ok=True)
            
            if not cls.ARQUIVO_CONFIG.exists():
                with open(cls.ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
                    json.dump(cls.CONFIG_PADRAO, f, indent=2, ensure_ascii=False)
            
            if not cls.ARQUIVO_AUDITORIA.exists():
                with open(cls.ARQUIVO_AUDITORIA, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=2, ensure_ascii=False)
            
            cls.registrar_log("Sistema inicializado", "SISTEMA")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar estrutura: {e}")
            return False
    
    @classmethod
    def carregar_configuracao(cls) -> Dict:
        """Carrega configurações"""
        try:
            if cls.ARQUIVO_CONFIG.exists():
                with open(cls.ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for key, value in cls.CONFIG_PADRAO.items():
                        if key not in config:
                            config[key] = value
                    return config
            return cls.CONFIG_PADRAO.copy()
        except:
            return cls.CONFIG_PADRAO.copy()
    
    @classmethod
    def salvar_configuracao(cls, config: Dict):
        """Salva configurações"""
        try:
            with open(cls.ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            cls.registrar_log(f"Erro ao salvar config: {e}", "ERRO")
            return False
    
    @classmethod
    def registrar_log(cls, mensagem: str, tipo: str = "INFO"):
        """Registra log"""
        try:
            log_arquivo = cls.LOGS_DIR / f"log_{datetime.now().strftime('%Y%m%d')}.txt"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(log_arquivo, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} - [{tipo}] {mensagem}\n")
        except:
            pass
    
    @classmethod
    def registrar_auditoria(cls, usuario: str, acao: str, detalhes: str = ""):
        """Registra ação para auditoria"""
        try:
            auditoria = []
            if cls.ARQUIVO_AUDITORIA.exists():
                with open(cls.ARQUIVO_AUDITORIA, 'r', encoding='utf-8') as f:
                    auditoria = json.load(f)
            
            auditoria.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'usuario': usuario,
                'acao': acao,
                'detalhes': detalhes
            })
            
            # Manter apenas últimos 1000 registros
            auditoria = auditoria[-1000:]
            
            with open(cls.ARQUIVO_AUDITORIA, 'w', encoding='utf-8') as f:
                json.dump(auditoria, f, indent=2, ensure_ascii=False)
        except:
            pass

# ====================================================================================
# DECORADOR DE PERMISSÕES
# ====================================================================================

def requer_permissao(nivel_minimo: str):
    """Decorador para verificar permissões"""
    niveis = {'operador': 0, 'supervisor': 1, 'administrador': 2}
    
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            nivel_usuario = niveis.get(self.info_usuario.get('nivel', 'operador'), 0)
            nivel_requerido = niveis.get(nivel_minimo, 0)
            
            if nivel_usuario >= nivel_requerido:
                return func(self, *args, **kwargs)
            else:
                messagebox.showerror(
                    "Acesso Negado",
                    f"Você precisa ser {nivel_minimo.upper()} para acessar esta função!"
                )
                ConfiguracaoSistema.registrar_auditoria(
                    self.usuario,
                    "ACESSO_NEGADO",
                    f"Tentativa de acessar {func.__name__}"
                )
        return wrapper
    return decorator

# ====================================================================================
# SISTEMA DE AUTENTICAÇÃO
# ====================================================================================

class SistemaAutenticacao:
    """Gerencia autenticação e usuários"""
    
    def __init__(self):
        self.arquivo_usuarios = ConfiguracaoSistema.ARQUIVO_USUARIOS
        self.usuarios = self.carregar_usuarios()
        
        if not self.usuarios:
            self.criar_usuario_padrao()
    
    def carregar_usuarios(self) -> Dict:
        """Carrega usuários"""
        try:
            if self.arquivo_usuarios.exists():
                with open(self.arquivo_usuarios, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except:
            return {}
    
    def salvar_usuarios(self):
        """Salva usuários"""
        try:
            with open(self.arquivo_usuarios, 'w', encoding='utf-8') as f:
                json.dump(self.usuarios, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
    
    def criar_usuario_padrao(self):
        """Cria usuário admin padrão"""
        try:
            senha_hash = bcrypt.hashpw("admin".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.usuarios['admin'] = {
                'senha': senha_hash,
                'nome_completo': 'Administrador do Sistema',
                'nivel': 'administrador',
                'data_criacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ultimo_login': None,
                'ativo': True
            }
            self.salvar_usuarios()
            ConfiguracaoSistema.registrar_log("Usuário admin criado", "SISTEMA")
        except Exception as e:
            print(f"❌ Erro ao criar admin: {e}")
    
    def autenticar(self, usuario: str, senha: str) -> Tuple[bool, Optional[Dict]]:
        """Autentica usuário"""
        try:
            if usuario in self.usuarios:
                user_data = self.usuarios[usuario]
                
                if not user_data.get('ativo', True):
                    return False, None
                
                senha_hash = user_data['senha']
                if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
                    user_data['ultimo_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.salvar_usuarios()
                    ConfiguracaoSistema.registrar_log(f"Login: {usuario}", "AUTH")
                    ConfiguracaoSistema.registrar_auditoria(usuario, "LOGIN", "Login bem-sucedido")
                    return True, user_data
            
            ConfiguracaoSistema.registrar_log(f"Login falhou: {usuario}", "AUTH")
            return False, None
        except:
            return False, None
    
    def criar_usuario(self, usuario: str, senha: str, nome_completo: str, nivel: str) -> Tuple[bool, str]:
        """Cria novo usuário"""
        try:
            if usuario in self.usuarios:
                return False, "Usuário já existe"
            
            if len(senha) < 4:
                return False, "Senha muito curta (mínimo 4 caracteres)"
            
            if nivel not in ['administrador', 'supervisor', 'operador']:
                return False, "Nível inválido"
            
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.usuarios[usuario] = {
                'senha': senha_hash,
                'nome_completo': nome_completo,
                'nivel': nivel,
                'data_criacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ultimo_login': None,
                'ativo': True
            }
            self.salvar_usuarios()
            ConfiguracaoSistema.registrar_log(f"Usuário criado: {usuario}", "ADMIN")
            return True, "Usuário criado com sucesso"
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def atualizar_usuario(self, usuario: str, dados: Dict) -> Tuple[bool, str]:
        """Atualiza usuário existente"""
        try:
            if usuario not in self.usuarios:
                return False, "Usuário não encontrado"
            
            if 'senha' in dados and dados['senha']:
                if len(dados['senha']) < 4:
                    return False, "Senha muito curta"
                dados['senha'] = bcrypt.hashpw(dados['senha'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            else:
                dados.pop('senha', None)
            
            self.usuarios[usuario].update(dados)
            self.salvar_usuarios()
            return True, "Usuário atualizado"
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def deletar_usuario(self, usuario: str) -> Tuple[bool, str]:
        """Deleta usuário"""
        try:
            if usuario == 'admin':
                return False, "Não pode deletar admin"
            
            if usuario in self.usuarios:
                del self.usuarios[usuario]
                self.salvar_usuarios()
                return True, "Usuário deletado"
            return False, "Usuário não encontrado"
        except Exception as e:
            return False, f"Erro: {str(e)}"

# ====================================================================================
# MODELOS DE DADOS
# ====================================================================================

class Peca:
    """Representa uma peça"""
    
    def __init__(self, id_peca: str, peso: float, cor: str, comprimento: float, usuario: str = ""):
        self.id_peca = id_peca.upper().strip()
        self.peso = peso
        self.cor = cor.lower().strip()
        self.comprimento = comprimento
        self.usuario = usuario
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.aprovada = False
        self.motivos_reprovacao = []
        self.turno = self.obter_turno_atual()
        
    def obter_turno_atual(self) -> str:
        """Determina turno"""
        hora = datetime.now().hour
        if 6 <= hora < 14:
            return "Manhã"
        elif 14 <= hora < 22:
            return "Tarde"
        else:
            return "Noite"
    
    def validar(self, criterios: Dict) -> bool:
        """Valida peça"""
        self.motivos_reprovacao = []
        
        if not (criterios['peso_min'] <= self.peso <= criterios['peso_max']):
            self.motivos_reprovacao.append(
                f"Peso: {self.peso}g (esperado: {criterios['peso_min']}-{criterios['peso_max']}g)"
            )
        
        if self.cor not in criterios['cores_aceitas']:
            cores = ", ".join(criterios['cores_aceitas'])
            self.motivos_reprovacao.append(f"Cor: {self.cor} (esperado: {cores})")
        
        if not (criterios['comprimento_min'] <= self.comprimento <= criterios['comprimento_max']):
            self.motivos_reprovacao.append(
                f"Comprimento: {self.comprimento}cm (esperado: {criterios['comprimento_min']}-{criterios['comprimento_max']}cm)"
            )
        
        self.aprovada = len(self.motivos_reprovacao) == 0
        return self.aprovada
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'id': self.id_peca,
            'peso': self.peso,
            'cor': self.cor,
            'comprimento': self.comprimento,
            'usuario': self.usuario,
            'timestamp': self.timestamp,
            'turno': self.turno,
            'aprovada': self.aprovada,
            'motivos_reprovacao': self.motivos_reprovacao
        }

class Caixa:
    """Representa uma caixa"""
    
    def __init__(self, numero: int, capacidade: int = 10):
        self.numero = numero
        self.capacidade = capacidade
        self.pecas: List[Peca] = []
        self.data_fechamento = None
        self.usuario_fechamento = ""
        self.data_criacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def adicionar_peca(self, peca: Peca) -> bool:
        """Adiciona peça à caixa"""
        if len(self.pecas) < self.capacidade:
            self.pecas.append(peca)
            if len(self.pecas) >= self.capacidade:
                self.fechar(peca.usuario)
            return True
        return False
    
    def fechar(self, usuario: str = ""):
        """Fecha caixa"""
        self.data_fechamento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.usuario_fechamento = usuario
    
    def esta_cheia(self) -> bool:
        return len(self.pecas) >= self.capacidade
    
    def vagas_disponiveis(self) -> int:
        return max(0, self.capacidade - len(self.pecas))
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'numero': self.numero,
            'capacidade': self.capacidade,
            'pecas': [p.to_dict() for p in self.pecas],
            'data_fechamento': self.data_fechamento,
            'usuario_fechamento': self.usuario_fechamento,
            'data_criacao': self.data_criacao,
            'quantidade_pecas': len(self.pecas),
            'percentual_cheio': (len(self.pecas) / self.capacidade) * 100
        }

# ====================================================================================
# BANCO DE DADOS
# ====================================================================================

class BancoDados:
    """Gerencia dados do sistema"""
    
    def __init__(self):
        self.arquivo_pecas = ConfiguracaoSistema.ARQUIVO_PECAS
        self.arquivo_caixas = ConfiguracaoSistema.ARQUIVO_CAIXAS
        self.config = ConfiguracaoSistema.carregar_configuracao()
        self.pecas_aprovadas: List[Peca] = []
        self.pecas_reprovadas: List[Peca] = []
        self.caixas_fechadas: List[Caixa] = []
        
        capacidade = self.config.get('capacidade_caixa', 10)
        self.caixa_atual: Caixa = Caixa(1, capacidade)
        
        self.carregar_dados()
        self.iniciar_backup_automatico()
    
    def carregar_dados(self):
        """Carrega dados dos arquivos"""
        if self.arquivo_pecas.exists():
            try:
                with open(self.arquivo_pecas, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                self.pecas_aprovadas.clear()
                self.pecas_reprovadas.clear()
                
                for p_dict in dados.get('aprovadas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.timestamp = p_dict.get('timestamp', '')
                    peca.turno = p_dict.get('turno', '')
                    self.pecas_aprovadas.append(peca)
                
                for p_dict in dados.get('reprovadas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.motivos_reprovacao = p_dict.get('motivos_reprovacao', [])
                    peca.timestamp = p_dict.get('timestamp', '')
                    peca.turno = p_dict.get('turno', '')
                    self.pecas_reprovadas.append(peca)
            except Exception as e:
                ConfiguracaoSistema.registrar_log(f"Erro ao carregar peças: {e}", "ERRO")
        
        if self.arquivo_caixas.exists():
            try:
                with open(self.arquivo_caixas, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                self.caixas_fechadas.clear()
                
                for c_dict in dados.get('fechadas', []):
                    capacidade = c_dict.get('capacidade', self.config.get('capacidade_caixa', 10))
                    caixa = Caixa(c_dict['numero'], capacidade)
                    caixa.data_fechamento = c_dict.get('data_fechamento')
                    caixa.usuario_fechamento = c_dict.get('usuario_fechamento', '')
                    caixa.data_criacao = c_dict.get('data_criacao', '')
                    
                    for p_dict in c_dict.get('pecas', []):
                        peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                        peca.aprovada = p_dict['aprovada']
                        peca.timestamp = p_dict.get('timestamp', '')
                        peca.turno = p_dict.get('turno', '')
                        caixa.pecas.append(peca)
                    self.caixas_fechadas.append(caixa)
                
                c_atual = dados.get('atual', {})
                capacidade_atual = c_atual.get('capacidade', self.config.get('capacidade_caixa', 10))
                self.caixa_atual = Caixa(c_atual.get('numero', len(self.caixas_fechadas) + 1), capacidade_atual)
                
                for p_dict in c_atual.get('pecas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.timestamp = p_dict.get('timestamp', '')
                    peca.turno = p_dict.get('turno', '')
                    self.caixa_atual.pecas.append(peca)
            except Exception as e:
                ConfiguracaoSistema.registrar_log(f"Erro ao carregar caixas: {e}", "ERRO")
    
    def salvar_dados(self):
        """Salva dados"""
        try:
            self.fazer_backup()
            
            dados_pecas = {
                'aprovadas': [p.to_dict() for p in self.pecas_aprovadas],
                'reprovadas': [p.to_dict() for p in self.pecas_reprovadas],
                'ultima_atualizacao': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.arquivo_pecas, 'w', encoding='utf-8') as f:
                json.dump(dados_pecas, f, indent=2, ensure_ascii=False)
            
            dados_caixas = {
                'fechadas': [c.to_dict() for c in self.caixas_fechadas],
                'atual': self.caixa_atual.to_dict(),
                'ultima_atualizacao': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.arquivo_caixas, 'w', encoding='utf-8') as f:
                json.dump(dados_caixas, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao salvar: {e}", "ERRO")
            return False
    
    def fazer_backup(self):
        """Faz backup"""
        try:
            if not self.config.get('auto_backup', True):
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.arquivo_pecas.exists():
                backup_pecas = ConfiguracaoSistema.BACKUP_DIR / f"pecas_backup_{timestamp}.json"
                with open(self.arquivo_pecas, 'r', encoding='utf-8') as origem:
                    with open(backup_pecas, 'w', encoding='utf-8') as destino:
                        destino.write(origem.read())
            
            if self.arquivo_caixas.exists():
                backup_caixas = ConfiguracaoSistema.BACKUP_DIR / f"caixas_backup_{timestamp}.json"
                with open(self.arquivo_caixas, 'r', encoding='utf-8') as origem:
                    with open(backup_caixas, 'w', encoding='utf-8') as destino:
                        destino.write(origem.read())
                        
            ConfiguracaoSistema.registrar_log("Backup realizado", "BACKUP")
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro backup: {e}", "ERRO")
    
    def iniciar_backup_automatico(self):
        """Inicia thread de backup automático"""
        def backup_thread():
            while True:
                try:
                    ultimo_backup = getattr(self, '_ultimo_backup', None)
                    intervalo_horas = self.config.get('backup_interval_hours', 24)
                    
                    if not ultimo_backup or (datetime.now() - ultimo_backup) > timedelta(hours=intervalo_horas):
                        self.fazer_backup()
                        self._ultimo_backup = datetime.now()
                    
                    threading.Event().wait(3600)
                except:
                    pass
        
        if self.config.get('auto_backup', True):
            thread = threading.Thread(target=backup_thread, daemon=True)
            thread.start()
    
    def adicionar_peca(self, peca: Peca) -> Tuple[bool, str]:
        """Adiciona peça"""
        try:
            for p in self.pecas_aprovadas + self.pecas_reprovadas:
                if p.id_peca == peca.id_peca:
                    return False, f"ID {peca.id_peca} já existe"
            
            criterios = self.config.get('criterios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['criterios_qualidade'])
            peca.validar(criterios)
            
            if peca.aprovada:
                self.pecas_aprovadas.append(peca)
                
                if not self.caixa_atual.adicionar_peca(peca):
                    self.caixas_fechadas.append(self.caixa_atual)
                    self.caixa_atual = Caixa(len(self.caixas_fechadas) + 1, self.config.get('capacidade_caixa', 10))
                    self.caixa_atual.adicionar_peca(peca)
                
                if self.caixa_atual.esta_cheia():
                    self.caixas_fechadas.append(self.caixa_atual)
                    self.caixa_atual = Caixa(len(self.caixas_fechadas) + 1, self.config.get('capacidade_caixa', 10))
            else:
                self.pecas_reprovadas.append(peca)
            
            self.salvar_dados()
            ConfiguracaoSistema.registrar_log(f"Peça {peca.id_peca} {'aprovada' if peca.aprovada else 'reprovada'}", "INSPECAO")
            
            return True, "Peça adicionada"
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def remover_peca(self, id_peca: str, usuario: str = "", justificativa: str = "") -> Tuple[bool, str]:
        """Remove peça"""
        id_peca = id_peca.upper().strip()
        
        for i, peca in enumerate(self.pecas_aprovadas):
            if peca.id_peca == id_peca:
                del self.pecas_aprovadas[i]
                
                for j, p_caixa in enumerate(self.caixa_atual.pecas):
                    if p_caixa.id_peca == id_peca:
                        del self.caixa_atual.pecas[j]
                        break
                
                self.salvar_dados()
                ConfiguracaoSistema.registrar_auditoria(usuario, "REMOVER_PECA", f"ID: {id_peca} - {justificativa}")
                return True, f"Peça {id_peca} removida"
        
        for i, peca in enumerate(self.pecas_reprovadas):
            if peca.id_peca == id_peca:
                del self.pecas_reprovadas[i]
                self.salvar_dados()
                ConfiguracaoSistema.registrar_auditoria(usuario, "REMOVER_PECA", f"ID: {id_peca} - {justificativa}")
                return True, f"Peça {id_peca} removida"
        
        return False, f"Peça {id_peca} não encontrada"
    
    def filtrar_pecas_por_data(self, pecas: List[Peca], data_inicio: str = None, data_fim: str = None) -> List[Peca]:
        """Filtra peças por período"""
        if not data_inicio and not data_fim:
            return pecas
        
        pecas_filtradas = []
        for peca in pecas:
            try:
                data_peca = datetime.strptime(peca.timestamp, "%Y-%m-%d %H:%M:%S")
                
                if data_inicio:
                    dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
                    if data_peca < dt_inicio:
                        continue
                
                if data_fim:
                    dt_fim = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
                    if data_peca >= dt_fim:
                        continue
                
                pecas_filtradas.append(peca)
            except:
                pass
        
        return pecas_filtradas
    
    def gerar_relatorio(self, data_inicio: str = None, data_fim: str = None) -> Dict:
        """Gera relatório completo"""
        aprovadas = self.filtrar_pecas_por_data(self.pecas_aprovadas, data_inicio, data_fim)
        reprovadas = self.filtrar_pecas_por_data(self.pecas_reprovadas, data_inicio, data_fim)
        
        total_pecas = len(aprovadas) + len(reprovadas)
        taxa_aprovacao = (len(aprovadas) / total_pecas * 100) if total_pecas > 0 else 0
        
        estatisticas_turno = {}
        todas_pecas = aprovadas + reprovadas
        
        for peca in todas_pecas:
            turno = peca.turno
            if turno not in estatisticas_turno:
                estatisticas_turno[turno] = {'aprovadas': 0, 'reprovadas': 0, 'total': 0}
            
            if peca.aprovada:
                estatisticas_turno[turno]['aprovadas'] += 1
            else:
                estatisticas_turno[turno]['reprovadas'] += 1
            estatisticas_turno[turno]['total'] += 1
        
        motivos_reprovacao = Counter()
        for peca in reprovadas:
            for motivo in peca.motivos_reprovacao:
                if 'Peso' in motivo:
                    motivos_reprovacao['Peso'] += 1
                elif 'Cor' in motivo:
                    motivos_reprovacao['Cor'] += 1
                elif 'Comprimento' in motivo:
                    motivos_reprovacao['Comprimento'] += 1
        
        return {
            'data_geracao': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'periodo': {
                'inicio': data_inicio or 'Início',
                'fim': data_fim or 'Hoje'
            },
            'total_pecas_aprovadas': len(aprovadas),
            'total_pecas_reprovadas': len(reprovadas),
            'total_pecas_inspecionadas': total_pecas,
            'taxa_aprovacao': round(taxa_aprovacao, 2),
            'caixas_completas': len(self.caixas_fechadas),
            'caixa_atual': {
                'numero': self.caixa_atual.numero,
                'pecas': len(self.caixa_atual.pecas),
                'vagas_disponiveis': self.caixa_atual.vagas_disponiveis(),
                'capacidade': self.caixa_atual.capacidade,
                'percentual_cheio': (len(self.caixa_atual.pecas) / self.caixa_atual.capacidade) * 100
            },
            'estatisticas_turno': estatisticas_turno,
            'analise_motivos_reprovacao': dict(motivos_reprovacao),
            'pecas_aprovadas': [p.to_dict() for p in aprovadas[-100:]],
            'pecas_reprovadas': [p.to_dict() for p in reprovadas[-100:]],
            'meta_diaria': self.config.get('metas', {}).get('diaria', 500),
            'progresso_meta': (len(aprovadas) / self.config.get('metas', {}).get('diaria', 500) * 100) if self.config.get('metas', {}).get('diaria', 500) > 0 else 0
        }

# ====================================================================================
# GERADOR DE RELATÓRIOS PDF
# ====================================================================================

class GeradorRelatoriosPDF:
    """Gera relatórios em PDF profissional"""
    
    @staticmethod
    def gerar_relatorio_executivo(relatorio: Dict, caminho: str, usuario: str):
        """Gera PDF executivo completo"""
        try:
            doc = SimpleDocTemplate(
                caminho,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            styles = getSampleStyleSheet()
            
            # Título
            titulo_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f538d'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            story.append(Paragraph("🏭 RELATÓRIO DE CONTROLE DE QUALIDADE", titulo_style))
            story.append(Paragraph(f"Sistema Industrial - Versão 3.0", styles['Normal']))
            story.append(Spacer(1, 0.5*cm))
            
            # Informações do relatório
            info_data = [
                ['Data de Geração:', relatorio['data_geracao']],
                ['Período Analisado:', f"{relatorio['periodo']['inicio']} até {relatorio['periodo']['fim']}"],
                ['Gerado por:', usuario],
            ]
            
            info_table = Table(info_data, colWidths=[5*cm, 10*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8e8e8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 1*cm))
            
            # Resumo Executivo
            resumo_style = ParagraphStyle(
                'ResumoTitle',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#1f538d'),
                spaceAfter=15
            )
            
            story.append(Paragraph("📈 RESUMO EXECUTIVO", resumo_style))
            
            resumo_data = [
                ['Métrica', 'Valor', 'Status'],
                ['Total de Peças Inspecionadas', f"{relatorio['total_pecas_inspecionadas']:,}", '✓'],
                ['Peças Aprovadas', f"{relatorio['total_pecas_aprovadas']:,}", '✅'],
                ['Peças Reprovadas', f"{relatorio['total_pecas_reprovadas']:,}", '❌'],
                ['Taxa de Aprovação', f"{relatorio['taxa_aprovacao']:.2f}%", 
                 '🟢' if relatorio['taxa_aprovacao'] >= 85 else '🟡' if relatorio['taxa_aprovacao'] >= 70 else '🔴'],
                ['Caixas Completas', f"{relatorio['caixas_completas']:,}", '📦'],
                ['Meta Diária', f"{relatorio['meta_diaria']:,} peças", '🎯'],
                ['Progresso da Meta', f"{relatorio['progresso_meta']:.1f}%", 
                 '✓' if relatorio['progresso_meta'] >= 100 else '⏳']
            ]
            
            resumo_table = Table(resumo_data, colWidths=[7*cm, 5*cm, 3*cm])
            resumo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f538d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(resumo_table)
            story.append(Spacer(1, 1*cm))
            
            # Estatísticas por Turno
            if relatorio['estatisticas_turno']:
                story.append(Paragraph("🕒 ANÁLISE POR TURNO", resumo_style))
                
                turno_data = [['Turno', 'Aprovadas', 'Reprovadas', 'Total', 'Taxa Aprov.']]
                for turno, stats in relatorio['estatisticas_turno'].items():
                    taxa = (stats['aprovadas'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    turno_data.append([
                        turno,
                        str(stats['aprovadas']),
                        str(stats['reprovadas']),
                        str(stats['total']),
                        f"{taxa:.1f}%"
                    ])
                
                turno_table = Table(turno_data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 3*cm])
                turno_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                story.append(turno_table)
                story.append(Spacer(1, 0.8*cm))
            
            # Análise de Reprovações
            if relatorio['analise_motivos_reprovacao']:
                story.append(Paragraph("❌ ANÁLISE DE MOTIVOS DE REPROVAÇÃO", resumo_style))
                
                motivos_data = [['Motivo', 'Quantidade', 'Percentual']]
                total_reprov = sum(relatorio['analise_motivos_reprovacao'].values())
                
                for motivo, qtd in relatorio['analise_motivos_reprovacao'].items():
                    perc = (qtd / total_reprov * 100) if total_reprov > 0 else 0
                    motivos_data.append([motivo, str(qtd), f"{perc:.1f}%"])
                
                motivos_table = Table(motivos_data, colWidths=[6*cm, 4*cm, 5*cm])
                motivos_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                story.append(motivos_table)
                story.append(Spacer(1, 1*cm))
            
            # Rodapé
            story.append(Spacer(1, 2*cm))
            rodape = Paragraph(
                f"Relatório gerado automaticamente - Sistema de Controle de Qualidade v3.0<br/>"
                f"© {datetime.now().year} - Todos os direitos reservados",
                styles['Normal']
            )
            story.append(rodape)
            
            # Gerar PDF
            doc.build(story)
            ConfiguracaoSistema.registrar_log(f"Relatório PDF gerado: {caminho}", "RELATORIO")
            return True, caminho
            
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao gerar PDF: {e}", "ERRO")
            return False, f"Erro: {str(e)}"

# ====================================================================================
# INTERFACE GRÁFICA - TELA DE LOGIN
# ====================================================================================

class TelaLogin:
    """Tela de login"""
    
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.auth = SistemaAutenticacao()
        
        self.root.title("Sistema de Controle de Qualidade - Login")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        self.centralizar_janela()
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.frame = ctk.CTkFrame(root, fg_color="transparent")
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.criar_interface()
    
    def centralizar_janela(self):
        """Centraliza janela"""
        self.root.update_idletasks()
        width, height = 500, 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def criar_interface(self):
        """Cria interface de login"""
        container = ctk.CTkFrame(self.frame, width=460, height=560, fg_color="#1f538d", corner_radius=15)
        container.pack(pady=20, padx=20, fill="both", expand=True)
        container.pack_propagate(False)
        
        ctk.CTkLabel(container, text="🏭", font=ctk.CTkFont(size=80), text_color="white").pack(pady=(40, 10))
        ctk.CTkLabel(container, text="Sistema de Controle\nde Qualidade Industrial", 
                     font=ctk.CTkFont(size=20, weight="bold"), text_color="white", justify="center").pack(pady=(0, 40))
        
        form_frame = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
        form_frame.pack(pady=10, padx=40, fill="both", expand=True)
        
        ctk.CTkLabel(form_frame, text="👤 Usuário", font=ctk.CTkFont(size=14, weight="bold"), text_color="#333333").pack(pady=(30, 5))
        self.entry_usuario = ctk.CTkEntry(form_frame, width=300, height=45, placeholder_text="Digite seu usuário", font=ctk.CTkFont(size=14), corner_radius=8)
        self.entry_usuario.pack(pady=5)
        self.entry_usuario.focus()
        
        ctk.CTkLabel(form_frame, text="🔒 Senha", font=ctk.CTkFont(size=14, weight="bold"), text_color="#333333").pack(pady=(20, 5))
        self.entry_senha = ctk.CTkEntry(form_frame, width=300, height=45, placeholder_text="Digite sua senha", show="●", font=ctk.CTkFont(size=14), corner_radius=8)
        self.entry_senha.pack(pady=5)
        self.entry_senha.bind('<Return>', lambda e: self.fazer_login())
        
        ctk.CTkButton(form_frame, text="Entrar no Sistema", width=300, height=45, font=ctk.CTkFont(size=16, weight="bold"),
                      command=self.fazer_login, fg_color="#1f538d", text_color="white", hover_color="#164276", corner_radius=8).pack(pady=30)
        
        ctk.CTkLabel(form_frame, text="Usuário padrão: admin\nSenha: admin", font=ctk.CTkFont(size=12), 
                     text_color="#666666", justify="center").pack(pady=(10, 20))
        
        ctk.CTkLabel(container, text="v3.0 - Sistema Profissional Completo", font=ctk.CTkFont(size=10), text_color="#e0e0e0").pack(pady=10)
    
    def fazer_login(self):
        """Processa login"""
        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get()
        
        if not usuario or not senha:
            messagebox.showerror("Erro", "Preencha usuário e senha!")
            return
        
        sucesso, info_usuario = self.auth.autenticar(usuario, senha)
        
        if sucesso and info_usuario:
            self.frame.destroy()
            self.on_login_success(usuario, info_usuario)
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos!")
            self.entry_senha.delete(0, 'end')
            self.entry_senha.focus()

# ====================================================================================
# INTERFACE GRÁFICA - TELA PRINCIPAL
# ====================================================================================

class TelaPrincipal:
    """Tela principal do sistema"""
    
    def __init__(self, root, usuario: str, info_usuario: Dict):
        self.root = root
        self.usuario = usuario
        self.info_usuario = info_usuario
        self.db = BancoDados()
        self.auth = SistemaAutenticacao()
        
        self.root.title(f"Sistema de Controle de Qualidade - {info_usuario['nome_completo']}")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.centralizar_janela()
        
        # Timeout de sessão
        self.ultima_atividade = datetime.now()
        self.verificar_timeout()
        
        self.frame_principal = ctk.CTkFrame(root, fg_color="transparent")
        self.frame_principal.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.criar_menu_principal()
    
    def centralizar_janela(self):
        """Centraliza janela"""
        self.root.update_idletasks()
        width, height = 1200, 800
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def verificar_timeout(self):
        """Verifica timeout de sessão"""
        timeout_minutos = self.db.config.get('timeout_sessao_minutos', 30)
        tempo_inativo = (datetime.now() - self.ultima_atividade).total_seconds() / 60
        
        if tempo_inativo > timeout_minutos:
            messagebox.showwarning("Sessão Expirada", "Sua sessão expirou por inatividade.")
            self.fazer_logout()
        else:
            self.root.after(60000, self.verificar_timeout)  # Verificar a cada minuto
    
    def resetar_timeout(self):
        """Reseta contador de inatividade"""
        self.ultima_atividade = datetime.now()
    
    def fazer_logout(self):
        """Faz logout do usuário"""
        resposta = messagebox.askyesno("Sair", "Deseja realmente sair do sistema?")
        if resposta:
            ConfiguracaoSistema.registrar_auditoria(self.usuario, "LOGOUT", "Logout manual")
            for widget in self.root.winfo_children():
                widget.destroy()
            TelaLogin(self.root, lambda u, i: TelaPrincipal(self.root, u, i))
    
    def criar_menu_principal(self):
        """Cria menu principal"""
        self.resetar_timeout()
        self.limpar_tela()
        
        # Header com botão sair
        header = ctk.CTkFrame(self.frame_principal, fg_color="#1f538d", height=80, corner_radius=10)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)
        
        titulo_frame = ctk.CTkFrame(header, fg_color="transparent")
        titulo_frame.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(titulo_frame, text="🏭 Sistema de Controle de Qualidade Industrial", 
                     font=ctk.CTkFont(size=22, weight="bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(titulo_frame, text="Versão 3.0 - Profissional Completo", 
                     font=ctk.CTkFont(size=12), text_color="#e0e0e0").pack(anchor="w")
        
        # Info usuário e botão sair
        user_frame = ctk.CTkFrame(header, fg_color="transparent")
        user_frame.pack(side="right", padx=20, pady=10)
        
        ctk.CTkLabel(user_frame, text=f"👤 {self.info_usuario['nome_completo']}", 
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="white", justify="right").pack(anchor="e")
        ctk.CTkLabel(user_frame, text=f"📋 {self.info_usuario['nivel'].title()} | Turno: {self.obter_turno_atual()}", 
                     font=ctk.CTkFont(size=10), text_color="#e0e0e0", justify="right").pack(anchor="e")
        
        # Botão SAIR
        ctk.CTkButton(user_frame, text="🚪 SAIR", width=100, height=35, command=self.fazer_logout,
                      font=ctk.CTkFont(size=12, weight="bold"), fg_color="white", text_color="#1f538d",
                      hover_color="#e0e0e0").pack(anchor="e", pady=(5, 0))
        
        # Dashboard
        self.criar_dashboard()
        
        # Menu de opções por nível
        self.criar_menu_opcoes()
    
    def obter_turno_atual(self) -> str:
        """Determina turno"""
        hora = datetime.now().hour
        if 6 <= hora < 14:
            return "Manhã"
        elif 14 <= hora < 22:
            return "Tarde"
        else:
            return "Noite"
    
    def criar_dashboard(self):
        """Cria dashboard"""
        dash_frame = ctk.CTkFrame(self.frame_principal, height=120)
        dash_frame.pack(fill="x", padx=10, pady=10)
        dash_frame.pack_propagate(False)
        
        total_pecas = len(self.db.pecas_aprovadas) + len(self.db.pecas_reprovadas)
        taxa_aprov = (len(self.db.pecas_aprovadas)/total_pecas*100 if total_pecas > 0 else 0)
        meta = self.db.config.get('metas', {}).get('diaria', 500)
        prog_meta = (len(self.db.pecas_aprovadas)/meta*100 if meta > 0 else 0)
        
        metrics = [
            ("✅ Aprovadas", len(self.db.pecas_aprovadas), "#2ecc71"),
            ("❌ Reprovadas", len(self.db.pecas_reprovadas), "#e74c3c"),
            ("📦 Caixas", len(self.db.caixas_fechadas), "#3498db"),
            ("📊 Taxa", f"{taxa_aprov:.1f}%", "#9b59b6"),
            ("🎯 Meta", f"{prog_meta:.1f}%", "#f39c12"),
            ("🔧 Caixa", f"#{self.db.caixa_atual.numero} ({len(self.db.caixa_atual.pecas)}/{self.db.caixa_atual.capacidade})", "#1abc9c")
        ]
        
        for i, (titulo, valor, cor) in enumerate(metrics):
            card = ctk.CTkFrame(dash_frame, fg_color=cor, height=100, corner_radius=10)
            card.grid(row=0, column=i, padx=5, pady=10, sticky="nsew")
            dash_frame.columnconfigure(i, weight=1)
            
            ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=11, weight="bold"), text_color="white").pack(pady=(15, 5))
            ctk.CTkLabel(card, text=str(valor), font=ctk.CTkFont(size=24, weight="bold"), text_color="white").pack(pady=(5, 15))
    
    def criar_menu_opcoes(self):
        """Cria menu de opções baseado no nível"""
        self.resetar_timeout()
        menu_frame = ctk.CTkFrame(self.frame_principal)
        menu_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(menu_frame, text="Menu Principal - Escolha uma operação:", 
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        nivel = self.info_usuario.get('nivel', 'operador')
        
        # Opções para TODOS
        opcoes = [
            ("📝 Cadastrar Nova Peça", self.tela_cadastrar_peca, "#1f538d", 'operador'),
            ("📋 Listar Peças", self.tela_listar_pecas, "#2980b9", 'operador'),
            ("📦 Ver Caixas", self.tela_listar_caixas, "#27ae60", 'operador'),
        ]
        
        # Opções para SUPERVISOR e ADMIN
        if nivel in ['supervisor', 'administrador']:
            opcoes.append(("🗑️ Remover Peça", self.tela_remover_peca, "#e67e22", 'supervisor'))
        
        # Opções APENAS para ADMIN
        if nivel == 'administrador':
            opcoes.extend([
                ("📊 Relatório Completo", self.tela_relatorio, "#8e44ad", 'administrador'),
                ("👥 Gestão de Usuários", self.tela_gestao_usuarios, "#c0392b", 'administrador'),
                ("⚙️ Configurações", self.tela_configuracoes, "#34495e", 'administrador'),
            ])
        
        for texto, comando, cor, _ in opcoes:
            btn = ctk.CTkButton(menu_frame, text=texto, width=400, height=50, font=ctk.CTkFont(size=14, weight="bold"),
                               command=comando, fg_color=cor, hover_color=self.escurecer_cor(cor), corner_radius=8)
            btn.pack(pady=6)
        
        # Botão SAIR sempre visível
        ctk.CTkButton(menu_frame, text="🚪 Sair do Sistema", width=400, height=45, font=ctk.CTkFont(size=13),
                     command=self.fazer_logout, fg_color="#c0392b", hover_color="#a93226", corner_radius=8).pack(pady=20)
    
    def escurecer_cor(self, cor: str) -> str:
        """Escurece cor hex"""
        try:
            cor = cor.lstrip('#')
            if len(cor) == 6:
                r, g, b = int(cor[0:2], 16), int(cor[2:4], 16), int(cor[4:6], 16)
                r, g, b = max(0, r-30), max(0, g-30), max(0, b-30)
                return f'#{r:02x}{g:02x}{b:02x}'
        except:
            pass
        return cor
    
    def tela_cadastrar_peca(self):
        """Tela de cadastro"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("📝 Cadastrar Nova Peça")
        
        form_frame = ctk.CTkFrame(self.frame_principal)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="Preencha os dados da peça:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        
        campos_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        campos_frame.pack(pady=20, padx=50, fill="both", expand=True)
        
        criterios = self.db.config.get('criterios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['criterios_qualidade'])
        
        # ID
        ctk.CTkLabel(campos_frame, text="🔢 ID da Peça:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        entry_id = ctk.CTkEntry(campos_frame, width=400, height=45, placeholder_text="Ex: PECA001", font=ctk.CTkFont(size=14))
        entry_id.pack(fill="x", pady=5)
        entry_id.focus()
        
        # Peso
        ctk.CTkLabel(campos_frame, text=f"⚖️ Peso (g) - Padrão: {criterios['peso_min']}g a {criterios['peso_max']}g:", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        entry_peso = ctk.CTkEntry(campos_frame, width=400, height=45, placeholder_text=f"Ex: 100.0", font=ctk.CTkFont(size=14))
        entry_peso.pack(fill="x", pady=5)
        
        # Cor
        ctk.CTkLabel(campos_frame, text=f"🎨 Cor - Aprovadas: {', '.join(criterios['cores_aceitas'])}:", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        combo_cor = ctk.CTkComboBox(campos_frame, width=400, height=45, 
                                    values=["azul", "verde", "vermelho", "amarelo", "preto", "branco"], 
                                    font=ctk.CTkFont(size=14))
        combo_cor.set("azul")
        combo_cor.pack(fill="x", pady=5)
        
        # Comprimento
        ctk.CTkLabel(campos_frame, text=f"📏 Comprimento (cm) - Padrão: {criterios['comprimento_min']}cm a {criterios['comprimento_max']}cm:", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        entry_comp = ctk.CTkEntry(campos_frame, width=400, height=45, placeholder_text=f"Ex: 15.0", font=ctk.CTkFont(size=14))
        entry_comp.pack(fill="x", pady=5)
        
        def cadastrar():
            self.resetar_timeout()
            try:
                id_peca = entry_id.get().strip()
                peso_str = entry_peso.get().strip()
                cor = combo_cor.get().strip()
                comp_str = entry_comp.get().strip()
                
                if not id_peca:
                    messagebox.showerror("Erro", "ID é obrigatório!")
                    return
                
                if not peso_str or not comp_str:
                    messagebox.showerror("Erro", "Peso e comprimento são obrigatórios!")
                    return
                
                peso = float(peso_str.replace(',', '.'))
                comprimento = float(comp_str.replace(',', '.'))
                
                peca = Peca(id_peca, peso, cor, comprimento, self.usuario)
                sucesso, mensagem = self.db.adicionar_peca(peca)
                
                if sucesso:
                    ConfiguracaoSistema.registrar_auditoria(self.usuario, "CADASTRAR_PECA", f"ID: {id_peca} - {'APROVADA' if peca.aprovada else 'REPROVADA'}")
                    
                    if peca.aprovada:
                        messagebox.showinfo("✅ Peça Aprovada!", 
                            f"Peça {id_peca} APROVADA!\n\n"
                            f"• Caixa #{self.db.caixa_atual.numero}\n"
                            f"• Vagas: {self.db.caixa_atual.vagas_disponiveis()}\n"
                            f"• Turno: {peca.turno}")
                    else:
                        motivos = "\n".join([f"• {m}" for m in peca.motivos_reprovacao])
                        messagebox.showwarning("❌ Peça Reprovada", f"Peça {id_peca} REPROVADA!\n\nMotivos:\n{motivos}")
                    
                    self.criar_menu_principal()
                else:
                    messagebox.showerror("Erro", mensagem)
            except ValueError:
                messagebox.showerror("Erro", "Peso e comprimento devem ser números!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro: {str(e)}")
        
        btn_frame = ctk.CTkFrame(campos_frame, fg_color="transparent")
        btn_frame.pack(pady=40)
        
        ctk.CTkButton(btn_frame, text="✅ Cadastrar", width=200, height=50, command=cadastrar, 
                     font=ctk.CTkFont(size=14, weight="bold"), fg_color="#2ecc71", hover_color="#27ae60").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔙 Voltar", width=200, height=50, command=self.criar_menu_principal, 
                     font=ctk.CTkFont(size=14, weight="bold"), fg_color="#95a5a6", hover_color="#7f8c8d").pack(side="left", padx=10)
    
    def tela_listar_pecas(self):
        """Tela de listagem com filtros"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("📋 Listar Peças")
        
        main_frame = ctk.CTkFrame(self.frame_principal)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Filtros
        filtro_frame = ctk.CTkFrame(main_frame)
        filtro_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(filtro_frame, text="📅 Filtrar por período:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10)
        
        combo_periodo = ctk.CTkComboBox(filtro_frame, width=150, 
                                       values=["Todos", "Hoje", "Ontem", "Última Semana", "Último Mês", "Personalizado"])
        combo_periodo.set("Todos")
        combo_periodo.pack(side="left", padx=5)
        
        def aplicar_filtro():
            self.resetar_timeout()
            periodo = combo_periodo.get()
            data_inicio, data_fim = None, None
            
            if periodo == "Hoje":
                data_inicio = data_fim = datetime.now().strftime("%Y-%m-%d")
            elif periodo == "Ontem":
                ontem = datetime.now() - timedelta(days=1)
                data_inicio = data_fim = ontem.strftime("%Y-%m-%d")
            elif periodo == "Última Semana":
                data_inicio = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                data_fim = datetime.now().strftime("%Y-%m-%d")
            elif periodo == "Último Mês":
                data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                data_fim = datetime.now().strftime("%Y-%m-%d")
            
            atualizar_listas(data_inicio, data_fim)
        
        ctk.CTkButton(filtro_frame, text="🔍 Filtrar", width=100, command=aplicar_filtro, fg_color="#3498db").pack(side="left", padx=5)
        
        # Tabs
        tabview = ctk.CTkTabview(main_frame)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        tab_aprovadas = tabview.add("✅ Aprovadas")
        tab_reprovadas = tabview.add("❌ Reprovadas")
        
        def atualizar_listas(data_inicio=None, data_fim=None):
            for widget in tab_aprovadas.winfo_children():
                widget.destroy()
            for widget in tab_reprovadas.winfo_children():
                widget.destroy()
            
            aprovadas = self.db.filtrar_pecas_por_data(self.db.pecas_aprovadas, data_inicio, data_fim)
            reprovadas = self.db.filtrar_pecas_por_data(self.db.pecas_reprovadas, data_inicio, data_fim)
            
            self.criar_lista_pecas(tab_aprovadas, aprovadas, "aprovadas")
            self.criar_lista_pecas(tab_reprovadas, reprovadas, "reprovadas")
        
        atualizar_listas()
        
        ctk.CTkButton(main_frame, text="🔙 Voltar", width=200, height=45, command=self.criar_menu_principal,
                     font=ctk.CTkFont(size=14, weight="bold"), fg_color="#95a5a6").pack(pady=10)
    
    def criar_lista_pecas(self, parent, pecas: List[Peca], tipo: str):
        """Cria lista de peças com botão de remoção"""
        self.resetar_timeout()
        frame = ctk.CTkScrollableFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        if not pecas:
            ctk.CTkLabel(frame, text=f"Nenhuma peça {tipo}.", font=ctk.CTkFont(size=14), text_color="#666666").pack(pady=50)
            return
        
        # Cabeçalho
        header_frame = ctk.CTkFrame(frame, fg_color="#34495e")
        header_frame.pack(fill="x", pady=(0, 10))
        
        headers = ["ID", "Peso", "Cor", "Comp.", "Turno", "Inspetor", "Data"]
        
        # Adicionar coluna de ação se for admin/supervisor
        if self.info_usuario.get('nivel') in ['administrador', 'supervisor']:
            headers.append("Ação")
        
        for i, header in enumerate(headers):
            ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=12, weight="bold"), text_color="white").grid(
                row=0, column=i, padx=10, pady=8, sticky="w")
            header_frame.columnconfigure(i, weight=1)
        
        # Linhas
        for idx, peca in enumerate(pecas[-100:], 1):
            row_frame = ctk.CTkFrame(frame, fg_color="#f8f9fa" if idx % 2 == 0 else "white")
            row_frame.pack(fill="x", pady=2)
            
            dados = [
                peca.id_peca,
                f"{peca.peso}g",
                peca.cor.title(),
                f"{peca.comprimento}cm",
                peca.turno,
                peca.usuario,
                peca.timestamp[:16]
            ]
            
            for i, dado in enumerate(dados):
                ctk.CTkLabel(row_frame, text=dado, font=ctk.CTkFont(size=11), text_color="#2c3e50").grid(
                    row=0, column=i, padx=10, pady=6, sticky="w")
                row_frame.columnconfigure(i, weight=1)
            
            # Botão remover (apenas admin/supervisor)
            if self.info_usuario.get('nivel') in ['administrador', 'supervisor']:
                btn_remover = ctk.CTkButton(row_frame, text="🗑️", width=40, height=30, 
                                           command=lambda p=peca: self.remover_peca_rapido(p.id_peca),
                                           fg_color="#e74c3c", hover_color="#c0392b")
                btn_remover.grid(row=0, column=len(dados), padx=10, pady=6)
    
    def remover_peca_rapido(self, id_peca: str):
        """Remove peça com confirmação"""
        self.resetar_timeout()
        
        # Buscar peça
        peca = None
        for p in self.db.pecas_aprovadas + self.db.pecas_reprovadas:
            if p.id_peca == id_peca:
                peca = p
                break
        
        if not peca:
            messagebox.showerror("Erro", "Peça não encontrada!")
            return
        
        # Diálogo de confirmação
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("⚠️ Confirmar Remoção")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="⚠️ CONFIRMAR REMOÇÃO", font=ctk.CTkFont(size=18, weight="bold"), 
                    text_color="#e74c3c").pack(pady=20)
        
        info_frame = ctk.CTkFrame(dialog)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        info_text = f"""
Peça: {peca.id_peca}
Peso: {peca.peso}g | Cor: {peca.cor} | Comprimento: {peca.comprimento}cm
Status: {'APROVADA' if peca.aprovada else 'REPROVADA'}
Inspetor: {peca.usuario}
Data: {peca.timestamp}

⚠️ Esta ação não pode ser desfeita!
        """
        
        ctk.CTkLabel(info_frame, text=info_text, font=ctk.CTkFont(size=12), justify="left").pack(pady=10)
        
        ctk.CTkLabel(dialog, text="Justificativa (opcional):", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(20, 5))
        entry_justificativa = ctk.CTkTextbox(dialog, width=450, height=80)
        entry_justificativa.pack(padx=20, pady=5)
        
        def confirmar():
            justificativa = entry_justificativa.get("1.0", "end-1c").strip()
            sucesso, msg = self.db.remover_peca(id_peca, self.usuario, justificativa)
            
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                dialog.destroy()
                self.tela_listar_pecas()
            else:
                messagebox.showerror("Erro", msg)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="❌ Cancelar", width=150, height=40, command=dialog.destroy,
                     fg_color="#95a5a6", hover_color="#7f8c8d").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🗑️ Confirmar", width=150, height=40, command=confirmar,
                     fg_color="#e74c3c", hover_color="#c0392b").pack(side="left", padx=10)
    
    @requer_permissao('supervisor')
    def tela_remover_peca(self):
        """Tela de remoção de peça"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("🗑️ Remover Peça")
        
        form_frame = ctk.CTkFrame(self.frame_principal)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="Digite o ID da peça:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=30)
        
        entry_id = ctk.CTkEntry(form_frame, width=400, height=50, placeholder_text="Ex: PECA001", font=ctk.CTkFont(size=14))
        entry_id.pack(pady=10)
        entry_id.focus()
        
        info_frame = ctk.CTkFrame(form_frame, height=100)
        info_frame.pack(fill="x", pady=10, padx=50)
        info_frame.pack_propagate(False)
        
        info_label = ctk.CTkLabel(info_frame, text="Digite um ID para ver informações...", 
                                 font=ctk.CTkFont(size=12), text_color="#666666", wraplength=500)
        info_label.pack(pady=20)
        
        def buscar_peca(event=None):
            self.resetar_timeout()
            id_peca = entry_id.get().strip().upper()
            if not id_peca:
                info_label.configure(text="Digite um ID...", text_color="#666666")
                return
            
            for peca in self.db.pecas_aprovadas + self.db.pecas_reprovadas:
                if peca.id_peca == id_peca:
                    status = "✅ APROVADA" if peca.aprovada else "❌ REPROVADA"
                    info_label.configure(
                        text=f"Peça encontrada:\n"
                             f"ID: {peca.id_peca} | Status: {status}\n"
                             f"Peso: {peca.peso}g | Cor: {peca.cor} | Comp: {peca.comprimento}cm\n"
                             f"Inspetor: {peca.usuario} | Data: {peca.timestamp}",
                        text_color="#2c3e50")
                    return
            
            info_label.configure(text=f"Peça {id_peca} não encontrada.", text_color="#e74c3c")
        
        entry_id.bind('<KeyRelease>', buscar_peca)
        
        ctk.CTkLabel(form_frame, text="Justificativa:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(20, 5))
        entry_justificativa = ctk.CTkTextbox(form_frame, width=400, height=80)
        entry_justificativa.pack(pady=5)
        
        def remover():
            self.resetar_timeout()
            id_peca = entry_id.get().strip().upper()
            if not id_peca:
                messagebox.showerror("Erro", "Digite um ID!")
                return
            
            resposta = messagebox.askyesno("Confirmar", f"Remover peça {id_peca}?\n\n⚠️ Não pode ser desfeito!")
            
            if resposta:
                justificativa = entry_justificativa.get("1.0", "end-1c").strip()
                sucesso, msg = self.db.remover_peca(id_peca, self.usuario, justificativa)
                if sucesso:
                    messagebox.showinfo("Sucesso", msg)
                    self.criar_menu_principal()
                else:
                    messagebox.showerror("Erro", msg)
        
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(btn_frame, text="🗑️ Remover", width=200, height=50, command=remover,
                     font=ctk.CTkFont(size=14, weight="bold"), fg_color="#e74c3c", hover_color="#c0392b").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔙 Voltar", width=200, height=50, command=self.criar_menu_principal,
                     font=ctk.CTkFont(size=14, weight="bold"), fg_color="#95a5a6").pack(side="left", padx=10)
    
    def tela_listar_caixas(self):
        """Tela de listagem de caixas"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("📦 Gerenciar Caixas")
        
        content_frame = ctk.CTkFrame(self.frame_principal)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Caixa atual
        ctk.CTkLabel(content_frame, text="📦 Caixa Atual:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        info_frame = ctk.CTkFrame(content_frame, fg_color="#3498db", height=120, corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=10)
        info_frame.pack_propagate(False)
        
        ctk.CTkLabel(info_frame, text=f"Caixa #{self.db.caixa_atual.numero}", 
                    font=ctk.CTkFont(size=22, weight="bold"), text_color="white").pack(pady=5)
        
        progresso = (len(self.db.caixa_atual.pecas) / self.db.caixa_atual.capacidade) * 100
        ctk.CTkLabel(info_frame, text=f"{len(self.db.caixa_atual.pecas)}/{self.db.caixa_atual.capacidade} peças ({progresso:.1f}%)",
                    font=ctk.CTkFont(size=14), text_color="white").pack(pady=2)
        ctk.CTkLabel(info_frame, text=f"Vagas: {self.db.caixa_atual.vagas_disponiveis()}",
                    font=ctk.CTkFont(size=12), text_color="#e0e0e0").pack(pady=2)
        
        # Caixas fechadas
        ctk.CTkLabel(content_frame, text="📦 Caixas Fechadas:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        
        if not self.db.caixas_fechadas:
            ctk.CTkLabel(content_frame, text="Nenhuma caixa fechada.", font=ctk.CTkFont(size=14), 
                        text_color="#666666").pack(pady=50)
        else:
            scroll_frame = ctk.CTkScrollableFrame(content_frame, height=300)
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            for caixa in reversed(self.db.caixas_fechadas[-20:]):
                caixa_frame = ctk.CTkFrame(scroll_frame, fg_color="#ecf0f1")
                caixa_frame.pack(fill="x", pady=5, padx=5)
                
                header_caixa = ctk.CTkFrame(caixa_frame, fg_color="#34495e")
                header_caixa.pack(fill="x", padx=2, pady=2)
                
                ctk.CTkLabel(header_caixa, text=f"📦 Caixa #{caixa.numero} - {len(caixa.pecas)} peças - {caixa.data_fechamento}",
                            font=ctk.CTkFont(size=12, weight="bold"), text_color="white").pack(pady=8, padx=10, anchor="w")
                
                pecas_text = ", ".join([p.id_peca for p in caixa.pecas])
                ctk.CTkLabel(caixa_frame, text=f"Peças: {pecas_text}", font=ctk.CTkFont(size=10),
                            text_color="#2c3e50", wraplength=800).pack(pady=5, padx=10, anchor="w")
        
        ctk.CTkButton(content_frame, text="🔙 Voltar", width=200, height=45, command=self.criar_menu_principal,
                     font=ctk.CTkFont(size=14, weight="bold"), fg_color="#95a5a6").pack(pady=20)
    
    @requer_permissao('administrador')
    def tela_relatorio(self):
        """Tela de relatórios"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("📊 Relatório Completo")
        
        content_frame = ctk.CTkFrame(self.frame_principal)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Filtros
        filtro_frame = ctk.CTkFrame(content_frame)
        filtro_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(filtro_frame, text="📅 Período:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10)
        combo_periodo = ctk.CTkComboBox(filtro_frame, width=150, 
                                       values=["Todos", "Hoje", "Última Semana", "Último Mês"])
        combo_periodo.set("Todos")
        combo_periodo.pack(side="left", padx=5)
        
        def gerar():
            self.resetar_timeout()
            periodo = combo_periodo.get()
            data_inicio, data_fim = None, None
            
            if periodo == "Hoje":
                data_inicio = data_fim = datetime.now().strftime("%Y-%m-%d")
            elif periodo == "Última Semana":
                data_inicio = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                data_fim = datetime.now().strftime("%Y-%m-%d")
            elif periodo == "Último Mês":
                data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                data_fim = datetime.now().strftime("%Y-%m-%d")
            
            relatorio = self.db.gerar_relatorio(data_inicio, data_fim)
            mostrar_relatorio(relatorio)
        
        ctk.CTkButton(filtro_frame, text="📊 Gerar", width=100, command=gerar, fg_color="#8e44ad").pack(side="left", padx=5)
        
        text_frame = ctk.CTkFrame(content_frame)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_relatorio = ctk.CTkTextbox(text_frame, font=ctk.CTkFont(size=11))
        text_relatorio.pack(fill="both", expand=True, padx=10, pady=10)
        
        def mostrar_relatorio(relatorio):
            text_relatorio.delete("1.0", "end")
            texto = self.formatar_relatorio(relatorio)
            text_relatorio.insert("1.0", texto)
            text_relatorio.configure(state="disabled")
        
        def exportar_pdf():
            self.resetar_timeout()
            relatorio = self.db.gerar_relatorio()
            caminho = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            if caminho:
                sucesso, msg = GeradorRelatoriosPDF.gerar_relatorio_executivo(relatorio, caminho, self.usuario)
                if sucesso:
                    messagebox.showinfo("Sucesso", f"Relatório PDF gerado:\n{caminho}")
                    ConfiguracaoSistema.registrar_auditoria(self.usuario, "GERAR_PDF", caminho)
                else:
                    messagebox.showerror("Erro", msg)
        
        # Botões
        btn_frame = ctk.CTkFrame(content_frame)
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="📄 Exportar PDF", width=150, height=40, command=exportar_pdf,
                     fg_color="#e74c3c").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🔙 Voltar", width=150, height=40, command=self.criar_menu_principal,
                     fg_color="#95a5a6").pack(side="left", padx=5)
        
        # Gerar relatório inicial
        gerar()
    
    @requer_permissao('administrador')
    def tela_gestao_usuarios(self):
        """Tela de gestão de usuários"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("👥 Gestão de Usuários")
        
        content_frame = ctk.CTkFrame(self.frame_principal)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Barra de ações
        acao_frame = ctk.CTkFrame(content_frame)
        acao_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(acao_frame, text="➕ Novo Usuário", width=150, height=40,
                     command=self.dialog_novo_usuario, fg_color="#27ae60").pack(side="left", padx=5)
        
        combo_filtro = ctk.CTkComboBox(acao_frame, width=150, 
                                      values=["Todos", "Ativos", "Inativos", "Administradores", "Supervisores", "Operadores"])
        combo_filtro.set("Todos")
        combo_filtro.pack(side="left", padx=5)
        
        def atualizar_lista():
            self.resetar_timeout()
            for widget in lista_frame.winfo_children():
                widget.destroy()
            
            filtro = combo_filtro.get()
            usuarios_filtrados = {}
            
            for user, data in self.auth.usuarios.items():
                if filtro == "Ativos" and not data.get('ativo', True):
                    continue
                if filtro == "Inativos" and data.get('ativo', True):
                    continue
                if filtro == "Administradores" and data.get('nivel') != 'administrador':
                    continue
                if filtro == "Supervisores" and data.get('nivel') != 'supervisor':
                    continue
                if filtro == "Operadores" and data.get('nivel') != 'operador':
                    continue
                usuarios_filtrados[user] = data
            
            if not usuarios_filtrados:
                ctk.CTkLabel(lista_frame, text="Nenhum usuário encontrado.", 
                           font=ctk.CTkFont(size=14), text_color="#666666").pack(pady=50)
                return
            
            # Cabeçalho
            header = ctk.CTkFrame(lista_frame, fg_color="#34495e")
            header.pack(fill="x", pady=(0, 10))
            
            headers = ["Username", "Nome", "Nível", "Status", "Último Login", "Ações"]
            for i, h in enumerate(headers):
                ctk.CTkLabel(header, text=h, font=ctk.CTkFont(size=12, weight="bold"), 
                           text_color="white").grid(row=0, column=i, padx=10, pady=8, sticky="w")
                header.columnconfigure(i, weight=1)
            
            # Usuários
            for idx, (user, data) in enumerate(usuarios_filtrados.items(), 1):
                row = ctk.CTkFrame(lista_frame, fg_color="#f8f9fa" if idx % 2 == 0 else "white")
                row.pack(fill="x", pady=2)
                
                ctk.CTkLabel(row, text=user, font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=10, pady=6, sticky="w")
                ctk.CTkLabel(row, text=data['nome_completo'], font=ctk.CTkFont(size=11)).grid(row=0, column=1, padx=10, pady=6, sticky="w")
                ctk.CTkLabel(row, text=data['nivel'].title(), font=ctk.CTkFont(size=11)).grid(row=0, column=2, padx=10, pady=6, sticky="w")
                
                status = "✅ Ativo" if data.get('ativo', True) else "❌ Inativo"
                ctk.CTkLabel(row, text=status, font=ctk.CTkFont(size=11)).grid(row=0, column=3, padx=10, pady=6, sticky="w")
                
                ultimo_login = data.get('ultimo_login', 'Nunca')[:16] if data.get('ultimo_login') else 'Nunca'
                ctk.CTkLabel(row, text=ultimo_login, font=ctk.CTkFont(size=11)).grid(row=0, column=4, padx=10, pady=6, sticky="w")
                
                # Botões de ação
                acao_btn_frame = ctk.CTkFrame(row, fg_color="transparent")
                acao_btn_frame.grid(row=0, column=5, padx=10, pady=6)
                
                if user != 'admin':  # Não pode editar/deletar admin
                    ctk.CTkButton(acao_btn_frame, text="✏️", width=35, height=25, 
                                command=lambda u=user: self.dialog_editar_usuario(u),
                                fg_color="#3498db", hover_color="#2980b9").pack(side="left", padx=2)
                    ctk.CTkButton(acao_btn_frame, text="🗑️", width=35, height=25,
                                command=lambda u=user: self.deletar_usuario(u),
                                fg_color="#e74c3c", hover_color="#c0392b").pack(side="left", padx=2)
                
                for i in range(6):
                    row.columnconfigure(i, weight=1)
        
        ctk.CTkButton(acao_frame, text="🔄 Atualizar", width=100, height=40, 
                     command=atualizar_lista, fg_color="#3498db").pack(side="left", padx=5)
        
        # Lista de usuários
        lista_frame = ctk.CTkScrollableFrame(content_frame)
        lista_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        atualizar_lista()
        
        ctk.CTkButton(content_frame, text="🔙 Voltar", width=200, height=45, 
                     command=self.criar_menu_principal, fg_color="#95a5a6").pack(pady=10)
    
    def dialog_novo_usuario(self):
        """Diálogo para criar novo usuário"""
        self.resetar_timeout()
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("➕ Novo Usuário")
        dialog.geometry("500x550")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="➕ CRIAR NOVO USUÁRIO", 
                    font=ctk.CTkFont(size=18, weight="bold"), text_color="#27ae60").pack(pady=20)
        
        form = ctk.CTkFrame(dialog)
        form.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(form, text="Username:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))
        entry_user = ctk.CTkEntry(form, width=450, height=40, placeholder_text="Ex: joao.silva")
        entry_user.pack(pady=5)
        entry_user.focus()
        
        ctk.CTkLabel(form, text="Nome Completo:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))
        entry_nome = ctk.CTkEntry(form, width=450, height=40, placeholder_text="Ex: João Silva")
        entry_nome.pack(pady=5)
        
        ctk.CTkLabel(form, text="Senha:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))
        entry_senha = ctk.CTkEntry(form, width=450, height=40, placeholder_text="Mínimo 4 caracteres", show="●")
        entry_senha.pack(pady=5)
        
        ctk.CTkLabel(form, text="Confirmar Senha:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))
        entry_senha2 = ctk.CTkEntry(form, width=450, height=40, placeholder_text="Digite novamente", show="●")
        entry_senha2.pack(pady=5)
        
        ctk.CTkLabel(form, text="Nível de Acesso:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))
        combo_nivel = ctk.CTkComboBox(form, width=450, height=40, 
                                     values=["operador", "supervisor", "administrador"])
        combo_nivel.set("operador")
        combo_nivel.pack(pady=5)
        
        def criar():
            self.resetar_timeout()
            user = entry_user.get().strip()
            nome = entry_nome.get().strip()
            senha = entry_senha.get()
            senha2 = entry_senha2.get()
            nivel = combo_nivel.get()
            
            if not user or not nome or not senha:
                messagebox.showerror("Erro", "Preencha todos os campos!")
                return
            
            if senha != senha2:
                messagebox.showerror("Erro", "As senhas não coincidem!")
                return
            
            sucesso, msg = self.auth.criar_usuario(user, senha, nome, nivel)
            
            if sucesso:
                ConfiguracaoSistema.registrar_auditoria(self.usuario, "CRIAR_USUARIO", f"Criou usuário: {user}")
                messagebox.showinfo("Sucesso", msg)
                dialog.destroy()
                self.tela_gestao_usuarios()
            else:
                messagebox.showerror("Erro", msg)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="❌ Cancelar", width=150, height=40, command=dialog.destroy,
                     fg_color="#95a5a6").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="✅ Criar", width=150, height=40, command=criar,
                     fg_color="#27ae60", hover_color="#229954").pack(side="left", padx=10)
    
    def dialog_editar_usuario(self, username: str):
        """Diálogo para editar usuário"""
        self.resetar_timeout()
        
        user_data = self.auth.usuarios.get(username)
        if not user_data:
            messagebox.showerror("Erro", "Usuário não encontrado!")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("✏️ Editar Usuário")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=f"✏️ EDITAR: {username}", 
                    font=ctk.CTkFont(size=18, weight="bold"), text_color="#3498db").pack(pady=20)
        
        form = ctk.CTkFrame(dialog)
        form.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(form, text="Nome Completo:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))
        entry_nome = ctk.CTkEntry(form, width=450, height=40)
        entry_nome.insert(0, user_data['nome_completo'])
        entry_nome.pack(pady=5)
        
        ctk.CTkLabel(form, text="Nova Senha (deixe vazio para não alterar):", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))
        entry_senha = ctk.CTkEntry(form, width=450, height=40, placeholder_text="Nova senha (opcional)", show="●")
        entry_senha.pack(pady=5)
        
        ctk.CTkLabel(form, text="Nível de Acesso:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))
        combo_nivel = ctk.CTkComboBox(form, width=450, height=40, 
                                     values=["operador", "supervisor", "administrador"])
        combo_nivel.set(user_data['nivel'])
        combo_nivel.pack(pady=5)
        
        var_ativo = ctk.BooleanVar(value=user_data.get('ativo', True))
        ctk.CTkSwitch(form, text="Usuário Ativo", variable=var_ativo, 
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=20)
        
        def salvar():
            self.resetar_timeout()
            dados = {
                'nome_completo': entry_nome.get().strip(),
                'nivel': combo_nivel.get(),
                'ativo': var_ativo.get()
            }
            
            senha = entry_senha.get()
            if senha:
                dados['senha'] = senha
            
            sucesso, msg = self.auth.atualizar_usuario(username, dados)
            
            if sucesso:
                ConfiguracaoSistema.registrar_auditoria(self.usuario, "EDITAR_USUARIO", f"Editou usuário: {username}")
                messagebox.showinfo("Sucesso", msg)
                dialog.destroy()
                self.tela_gestao_usuarios()
            else:
                messagebox.showerror("Erro", msg)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="❌ Cancelar", width=150, height=40, command=dialog.destroy,
                     fg_color="#95a5a6").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="💾 Salvar", width=150, height=40, command=salvar,
                     fg_color="#3498db", hover_color="#2980b9").pack(side="left", padx=10)
    
    def deletar_usuario(self, username: str):
        """Deleta usuário"""
        self.resetar_timeout()
        
        resposta = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja deletar o usuário '{username}'?\n\n⚠️ Esta ação não pode ser desfeita!"
        )
        
        if resposta:
            sucesso, msg = self.auth.deletar_usuario(username)
            if sucesso:
                ConfiguracaoSistema.registrar_auditoria(self.usuario, "DELETAR_USUARIO", f"Deletou usuário: {username}")
                messagebox.showinfo("Sucesso", msg)
                self.tela_gestao_usuarios()
            else:
                messagebox.showerror("Erro", msg)
    
    @requer_permissao('administrador')
    def tela_configuracoes(self):
        """Tela de configurações"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("⚙️ Configurações do Sistema")
        
        content_frame = ctk.CTkFrame(self.frame_principal)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tabview = ctk.CTkTabview(content_frame)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        tab_criterios = tabview.add("🎯 Critérios")
        tab_sistema = tabview.add("⚙️ Sistema")
        tab_metas = tabview.add("📊 Metas")
        
        self.criar_config_criterios(tab_criterios)
        self.criar_config_sistema(tab_sistema)
        self.criar_config_metas(tab_metas)
        
        ctk.CTkButton(content_frame, text="🔙 Voltar", width=200, height=45, 
                     command=self.criar_menu_principal, fg_color="#95a5a6").pack(pady=10)
    
    def criar_config_criterios(self, parent):
        """Configuração de critérios de qualidade"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        criterios = self.db.config.get('criterios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['criterios_qualidade'])
        
        ctk.CTkLabel(frame, text="Configurar Critérios de Qualidade:", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Peso
        ctk.CTkLabel(frame, text="Peso (g):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        peso_frame = ctk.CTkFrame(frame, fg_color="transparent")
        peso_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(peso_frame, text="Mínimo:").pack(side="left", padx=(0, 10))
        entry_peso_min = ctk.CTkEntry(peso_frame, width=100)
        entry_peso_min.insert(0, str(criterios['peso_min']))
        entry_peso_min.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(peso_frame, text="Máximo:").pack(side="left", padx=(0, 10))
        entry_peso_max = ctk.CTkEntry(peso_frame, width=100)
        entry_peso_max.insert(0, str(criterios['peso_max']))
        entry_peso_max.pack(side="left")
        
        # Comprimento
        ctk.CTkLabel(frame, text="Comprimento (cm):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        comp_frame = ctk.CTkFrame(frame, fg_color="transparent")
        comp_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(comp_frame, text="Mínimo:").pack(side="left", padx=(0, 10))
        entry_comp_min = ctk.CTkEntry(comp_frame, width=100)
        entry_comp_min.insert(0, str(criterios['comprimento_min']))
        entry_comp_min.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(comp_frame, text="Máximo:").pack(side="left", padx=(0, 10))
        entry_comp_max = ctk.CTkEntry(comp_frame, width=100)
        entry_comp_max.insert(0, str(criterios['comprimento_max']))
        entry_comp_max.pack(side="left")
        
        # Cores
        ctk.CTkLabel(frame, text="Cores Aprovadas (separadas por vírgula):", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        entry_cores = ctk.CTkEntry(frame, width=400)
        entry_cores.insert(0, ", ".join(criterios['cores_aceitas']))
        entry_cores.pack(anchor="w", pady=5)
        
        def salvar_criterios():
            self.resetar_timeout()
            try:
                novos_criterios = {
                    'peso_min': float(entry_peso_min.get()),
                    'peso_max': float(entry_peso_max.get()),
                    'comprimento_min': float(entry_comp_min.get()),
                    'comprimento_max': float(entry_comp_max.get()),
                    'cores_aceitas': [cor.strip().lower() for cor in entry_cores.get().split(',')]
                }
                
                self.db.config['criterios_qualidade'] = novos_criterios
                ConfiguracaoSistema.salvar_configuracao(self.db.config)
                ConfiguracaoSistema.registrar_auditoria(self.usuario, "ALTERAR_CONFIG", "Critérios de qualidade")
                
                messagebox.showinfo("Sucesso", "Critérios atualizados!")
            except ValueError:
                messagebox.showerror("Erro", "Valores numéricos inválidos!")
        
        ctk.CTkButton(frame, text="💾 Salvar Critérios", width=200, height=45, command=salvar_criterios,
                     fg_color="#27ae60", hover_color="#229954").pack(pady=30)
    
    def criar_config_sistema(self, parent):
        """Configuração do sistema"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Configurações do Sistema:", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Capacidade da caixa
        ctk.CTkLabel(frame, text="Capacidade de Peças por Caixa:", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        entry_capacidade = ctk.CTkEntry(frame, width=100)
        entry_capacidade.insert(0, str(self.db.config.get('capacidade_caixa', 10)))
        entry_capacidade.pack(anchor="w", pady=5)
        
        # Backup automático
        var_backup = ctk.BooleanVar(value=self.db.config.get('auto_backup', True))
        ctk.CTkSwitch(frame, text="Backup Automático", variable=var_backup, 
                     font=ctk.CTkFont(size=14)).pack(anchor="w", pady=10)
        
        # Intervalo de backup
        ctk.CTkLabel(frame, text="Intervalo de Backup (horas):", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        entry_intervalo = ctk.CTkEntry(frame, width=100)
        entry_intervalo.insert(0, str(self.db.config.get('backup_interval_hours', 24)))
        entry_intervalo.pack(anchor="w", pady=5)
        
        # Timeout de sessão
        ctk.CTkLabel(frame, text="Timeout de Sessão (minutos):", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        entry_timeout = ctk.CTkEntry(frame, width=100)
        entry_timeout.insert(0, str(self.db.config.get('timeout_sessao_minutos', 30)))
        entry_timeout.pack(anchor="w", pady=5)
        
        def salvar_sistema():
            self.resetar_timeout()
            try:
                self.db.config['capacidade_caixa'] = int(entry_capacidade.get())
                self.db.config['auto_backup'] = var_backup.get()
                self.db.config['backup_interval_hours'] = int(entry_intervalo.get())
                self.db.config['timeout_sessao_minutos'] = int(entry_timeout.get())
                
                ConfiguracaoSistema.salvar_configuracao(self.db.config)
                ConfiguracaoSistema.registrar_auditoria(self.usuario, "ALTERAR_CONFIG", "Sistema")
                
                messagebox.showinfo("Sucesso", "Configurações salvas!")
            except ValueError:
                messagebox.showerror("Erro", "Valores inválidos!")
        
        ctk.CTkButton(frame, text="💾 Salvar Configurações", width=200, height=45, command=salvar_sistema,
                     fg_color="#3498db", hover_color="#2980b9").pack(pady=30)
    
    def criar_config_metas(self, parent):
        """Configuração de metas"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Configurar Metas de Produção:", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        metas = self.db.config.get('metas', ConfiguracaoSistema.CONFIG_PADRAO['metas'])
        
        ctk.CTkLabel(frame, text="Meta Diária (peças aprovadas):", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        entry_meta = ctk.CTkEntry(frame, width=100)
        entry_meta.insert(0, str(metas.get('diaria', 500)))
        entry_meta.pack(anchor="w", pady=5)
        
        ctk.CTkLabel(frame, text="Taxa de Aprovação Mínima (%):", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        entry_taxa = ctk.CTkEntry(frame, width=100)
        entry_taxa.insert(0, str(metas.get('taxa_aprovacao_minima', 85)))
        entry_taxa.pack(anchor="w", pady=5)
        
        alertas = self.db.config.get('alertas', ConfiguracaoSistema.CONFIG_PADRAO['alertas'])
        
        ctk.CTkLabel(frame, text="Alerta de Taxa de Reprovação Alta (%):", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        entry_alerta = ctk.CTkEntry(frame, width=100)
        entry_alerta.insert(0, str(alertas.get('taxa_reprovacao_alta', 15)))
        entry_alerta.pack(anchor="w", pady=5)
        
        def salvar_metas():
            self.resetar_timeout()
            try:
                self.db.config['metas'] = {
                    'diaria': int(entry_meta.get()),
                    'taxa_aprovacao_minima': float(entry_taxa.get())
                }
                self.db.config['alertas'] = {
                    'taxa_reprovacao_alta': float(entry_alerta.get()),
                    'som_enabled': True
                }
                
                ConfiguracaoSistema.salvar_configuracao(self.db.config)
                ConfiguracaoSistema.registrar_auditoria(self.usuario, "ALTERAR_CONFIG", "Metas")
                
                messagebox.showinfo("Sucesso", "Metas atualizadas!")
            except ValueError:
                messagebox.showerror("Erro", "Valores inválidos!")
        
        ctk.CTkButton(frame, text="💾 Salvar Metas", width=200, height=45, command=salvar_metas,
                     fg_color="#f39c12", hover_color="#e67e22").pack(pady=30)
    
    def formatar_relatorio(self, relatorio: Dict) -> str:
        """Formata relatório para exibição"""
        texto = "="*80 + "\n"
        texto += "           RELATÓRIO COMPLETO - CONTROLE DE QUALIDADE\n"
        texto += "="*80 + "\n\n"
        
        texto += f"📅 Data: {relatorio['data_geracao']}\n"
        texto += f"👤 Gerado por: {self.info_usuario['nome_completo']}\n"
        texto += f"📊 Período: {relatorio['periodo']['inicio']} até {relatorio['periodo']['fim']}\n\n"
        
        texto += "📈 RESUMO GERAL\n"
        texto += "-"*80 + "\n"
        texto += f"• Total Inspecionadas: {relatorio['total_pecas_inspecionadas']:,}\n"
        texto += f"• ✅ Aprovadas: {relatorio['total_pecas_aprovadas']:,}\n"
        texto += f"• ❌ Reprovadas: {relatorio['total_pecas_reprovadas']:,}\n"
        texto += f"• 📊 Taxa de Aprovação: {relatorio['taxa_aprovacao']}%\n"
        texto += f"• 📦 Caixas Completas: {relatorio['caixas_completas']:,}\n"
        texto += f"• 🎯 Meta Diária: {relatorio['meta_diaria']:,} peças\n"
        texto += f"• 📈 Progresso: {relatorio['progresso_meta']:.1f}%\n\n"
        
        texto += "📦 CAIXA ATUAL\n"
        texto += "-"*80 + "\n"
        texto += f"• Número: #{relatorio['caixa_atual']['numero']}\n"
        texto += f"• Peças: {relatorio['caixa_atual']['pecas']}/{relatorio['caixa_atual']['capacidade']}\n"
        texto += f"• Ocupação: {relatorio['caixa_atual']['percentual_cheio']:.1f}%\n\n"
        
        if relatorio['estatisticas_turno']:
            texto += "🕒 ESTATÍSTICAS POR TURNO\n"
            texto += "-"*80 + "\n"
            for turno, stats in relatorio['estatisticas_turno'].items():
                taxa = (stats['aprovadas'] / stats['total'] * 100) if stats['total'] > 0 else 0
                texto += f"• {turno}: {stats['aprovadas']} aprov., {stats['reprovadas']} reprov. ({taxa:.1f}%)\n"
            texto += "\n"
        
        if relatorio['analise_motivos_reprovacao']:
            texto += "❌ MOTIVOS DE REPROVAÇÃO\n"
            texto += "-"*80 + "\n"
            total = sum(relatorio['analise_motivos_reprovacao'].values())
            for motivo, qtd in relatorio['analise_motivos_reprovacao'].items():
                perc = (qtd / total * 100) if total > 0 else 0
                texto += f"• {motivo}: {qtd} ({perc:.1f}%)\n"
            texto += "\n"
        
        texto += "="*80 + "\n"
        return texto
    
    def criar_header(self, titulo: str):
        """Cria header padrão"""
        self.resetar_timeout()
        header = ctk.CTkFrame(self.frame_principal, fg_color="#1f538d", height=70, corner_radius=10)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text=titulo, font=ctk.CTkFont(size=20, weight="bold"), 
                    text_color="white").pack(side="left", padx=20, pady=15)
        
        ctk.CTkButton(header, text="🔙 Voltar", width=100, height=35, command=self.criar_menu_principal,
                     font=ctk.CTkFont(size=12, weight="bold"), fg_color="white", text_color="#1f538d",
                     hover_color="#e0e0e0").pack(side="right", padx=20, pady=15)
    
    def limpar_tela(self):
        """Limpa tela"""
        for widget in self.frame_principal.winfo_children():
            widget.destroy()

# ====================================================================================
# APLICAÇÃO PRINCIPAL
# ====================================================================================

class Aplicacao:
    """Aplicação principal"""
    
    def __init__(self):
        if not ConfiguracaoSistema.criar_estrutura_pastas():
            messagebox.showerror("Erro", "Não foi possível criar estrutura de pastas!")
            return
        
        self.root = ctk.CTk()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        TelaLogin(self.root, self.on_login_success)
    
    def on_login_success(self, usuario: str, info_usuario: Dict):
        """Callback após login"""
        TelaPrincipal(self.root, usuario, info_usuario)
    
    def executar(self):
        """Executa aplicação"""
        self.root.mainloop()

# ====================================================================================
# PONTO DE ENTRADA
# ====================================================================================

def main():
    """Função principal"""
    print("\n" + "="*70)
    print("  🏭 Sistema de Controle de Qualidade Industrial v3.0")
    print("  📊 Profissional Completo")
    print("  ✨ Desenvolvido com CustomTkinter + Matplotlib + ReportLab")
    print("="*70 + "\n")
    
    print("🔧 Funcionalidades:")
    print("  ✅ Gestão completa de usuários (CRUD)")
    print("  ✅ Hierarquia de permissões (Operador/Supervisor/Admin)")
    print("  ✅ Filtros por data em todas as telas")
    print("  ✅ Remoção rápida com botão na listagem")
    print("  ✅ Relatórios em PDF profissional")
    print("  ✅ Dashboard em tempo real")
    print("  ✅ Sistema de auditoria completo")
    print("  ✅ Timeout de sessão automático")
    print("  ✅ Backup automático")
    print("  ✅ Botão SAIR sempre visível")
    print("\n" + "="*70 + "\n")
    
    try:
        app = Aplicacao()
        app.executar()
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        messagebox.showerror("Erro Fatal", f"Erro crítico:\n\n{str(e)}")
    finally:
        ConfiguracaoSistema.registrar_log("Aplicação encerrada", "SISTEMA")

if __name__ == "__main__":
    main()
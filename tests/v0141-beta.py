"""
Sistema de Controle de Qualidade Industrial
Versão 2.0 - Corrigida e Melhorada
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
import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
from collections import Counter

# ====================================================================================
# CONFIGURAÇÃO INICIAL E DEPENDÊNCIAS
# ====================================================================================

def verificar_e_instalar_dependencias():
    """Verifica e instala automaticamente as dependências necessárias - CORRIGIDA"""
    
    print("="*70)
    print("🔍 Verificando dependências do sistema...")
    print("="*70)
    
    # Lista corrigida de dependências
    dependencias = [
        'customtkinter',
        'Pillow',
        'bcrypt'
    ]
    
    dependencias_faltando = []
    
    # Verificar quais dependências estão faltando
    for pacote in dependencias:
        try:
            if pacote == 'Pillow':
                __import__('PIL')  # Pillow usa PIL como nome de import
            else:
                __import__(pacote)
            print(f"✅ {pacote} - Instalado")
        except ImportError:
            print(f"❌ {pacote} - Não encontrado")
            dependencias_faltando.append(pacote)
    
    # Se houver dependências faltando, tentar instalar
    if dependencias_faltando:
        print("\n" + "="*70)
        print(f"📦 Instalando {len(dependencias_faltando)} dependência(s) faltante(s)...")
        print("="*70)
        
        for pacote in dependencias_faltando:
            try:
                print(f"⏳ Instalando {pacote}...")
                # Usar pip diretamente com o executável atual do Python
                subprocess.check_call([sys.executable, "-m", "pip", "install", pacote, "--user"])
                print(f"✅ {pacote} instalado com sucesso!")
            except subprocess.CalledProcessError as e:
                print(f"❌ ERRO ao instalar {pacote}: {e}")
                print("\nTentando método alternativo...")
                try:
                    import pip
                    pip.main(['install', pacote])
                    print(f"✅ {pacote} instalado com sucesso (método alternativo)!")
                except:
                    print(f"❌ Falha crítica na instalação de {pacote}")
                    return False
        
        print("\n" + "="*70)
        print("🔄 Reiniciando o sistema para aplicar as mudanças...")
        print("="*70)
        
        # Dar tempo para o usuário ver as mensagens
        import time
        time.sleep(2)
        
        # Reiniciar o script
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    print("\n" + "="*70)
    print("✅ Todas as dependências estão instaladas!")
    print("🚀 Iniciando o sistema...")
    print("="*70)
    return True

# Executar verificação (descomente se necessário)
# if not verificar_e_instalar_dependencias():
#     input("Pressione ENTER para sair...")
#     sys.exit(1)

# ====================================================================================
# CONFIGURAÇÃO DO SISTEMA
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
    
    # Configurações padrão
    CONFIG_PADRAO = {
        'critérios_qualidade': {
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
        }
    }
    
    @classmethod
    def criar_estrutura_pastas(cls):
        """Cria a estrutura de pastas necessária"""
        try:
            cls.DATA_DIR.mkdir(exist_ok=True)
            cls.LOGS_DIR.mkdir(exist_ok=True)
            cls.BACKUP_DIR.mkdir(exist_ok=True)
            
            # Criar arquivo de configuração padrão se não existir
            if not cls.ARQUIVO_CONFIG.exists():
                with open(cls.ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
                    json.dump(cls.CONFIG_PADRAO, f, indent=2, ensure_ascii=False)
            
            # Criar arquivo de log de inicialização
            cls.registrar_log("Sistema inicializado", "SISTEMA")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar estrutura de pastas: {e}")
            return False
    
    @classmethod
    def carregar_configuracao(cls) -> Dict:
        """Carrega as configurações do sistema"""
        try:
            if cls.ARQUIVO_CONFIG.exists():
                with open(cls.ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Garantir que todas as chaves padrão existam
                    for key, value in cls.CONFIG_PADRAO.items():
                        if key not in config:
                            config[key] = value
                    return config
            return cls.CONFIG_PADRAO.copy()
        except:
            return cls.CONFIG_PADRAO.copy()
    
    @classmethod
    def salvar_configuracao(cls, config: Dict):
        """Salva as configurações do sistema"""
        try:
            with open(cls.ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            cls.registrar_log(f"Erro ao salvar configuração: {e}", "ERRO")
            return False
    
    @classmethod
    def registrar_log(cls, mensagem: str, tipo: str = "INFO"):
        """Registra um evento no log"""
        try:
            log_arquivo = cls.LOGS_DIR / f"log_{datetime.now().strftime('%Y%m%d')}.txt"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(log_arquivo, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} - [{tipo}] {mensagem}\n")
        except Exception as e:
            print(f"❌ Erro ao registrar log: {e}")

# ====================================================================================
# SISTEMA DE AUTENTICAÇÃO MELHORADO
# ====================================================================================

class SistemaAutenticacao:
    """Gerencia autenticação e usuários do sistema - MELHORADO"""
    
    def __init__(self):
        self.arquivo_usuarios = ConfiguracaoSistema.ARQUIVO_USUARIOS
        self.usuarios = self.carregar_usuarios()
        
        # Criar usuário padrão se não existir nenhum
        if not self.usuarios:
            self.criar_usuario_padrao()
    
    def carregar_usuarios(self) -> Dict:
        """Carrega usuários do arquivo"""
        try:
            if self.arquivo_usuarios.exists():
                with open(self.arquivo_usuarios, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao carregar usuários: {e}", "ERRO")
            return {}
    
    def salvar_usuarios(self):
        """Salva usuários no arquivo"""
        try:
            with open(self.arquivo_usuarios, 'w', encoding='utf-8') as f:
                json.dump(self.usuarios, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao salvar usuários: {e}", "ERRO")
            return False
    
    def criar_usuario_padrao(self):
        """Cria usuário padrão admin/admin"""
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
            ConfiguracaoSistema.registrar_log("Usuário padrão 'admin' criado", "SISTEMA")
        except Exception as e:
            print(f"❌ Erro ao criar usuário padrão: {e}")
    
    def autenticar(self, usuario: str, senha: str) -> Tuple[bool, Optional[Dict]]:
        """Autentica um usuário - RETORNA MELHORADO"""
        try:
            if usuario in self.usuarios:
                user_data = self.usuarios[usuario]
                
                # Verificar se usuário está ativo
                if not user_data.get('ativo', True):
                    ConfiguracaoSistema.registrar_log(f"Tentativa de login com usuário inativo: {usuario}", "AUTH")
                    return False, None
                
                # Verificar senha
                senha_hash = user_data['senha']
                if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
                    # Atualizar último login
                    user_data['ultimo_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.salvar_usuarios()
                    
                    ConfiguracaoSistema.registrar_log(f"Login bem-sucedido: {usuario}", "AUTH")
                    return True, user_data
            
            ConfiguracaoSistema.registrar_log(f"Tentativa de login falhou: {usuario}", "AUTH")
            return False, None
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro na autenticação: {e}", "ERRO")
            return False, None
    
    def criar_usuario(self, usuario: str, senha: str, nome_completo: str, nivel: str = "operador") -> Tuple[bool, str]:
        """Cria um novo usuário - MELHORADO COM VALIDAÇÃO"""
        try:
            if usuario in self.usuarios:
                return False, "Usuário já existe"
            
            if len(senha) < 4:
                return False, "Senha deve ter pelo menos 4 caracteres"
            
            if nivel not in ['administrador', 'supervisor', 'operador']:
                return False, "Nível de acesso inválido"
            
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
            ConfiguracaoSistema.registrar_log(f"Novo usuário criado: {usuario} ({nivel})", "ADMIN")
            return True, "Usuário criado com sucesso"
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao criar usuário: {e}", "ERRO")
            return False, f"Erro interno: {str(e)}"

# ====================================================================================
# MODELOS DE DADOS MELHORADOS
# ====================================================================================

class Peca:
    """Classe que representa uma peça - MELHORADA"""
    
    def __init__(self, id_peca: str, peso: float, cor: str, comprimento: float, usuario: str = ""):
        self.id_peca = id_peca.upper().strip()
        self.peso = peso
        self.cor = cor.lower().strip()
        self.comprimento = comprimento
        self.usuario = usuario
        self.timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.aprovada = False
        self.motivos_reprovacao = []
        self.turno = self.obter_turno_atual()
        
    def obter_turno_atual(self) -> str:
        """Determina o turno baseado na hora atual"""
        hora = datetime.now().hour
        if 6 <= hora < 14:
            return "Manhã"
        elif 14 <= hora < 22:
            return "Tarde"
        else:
            return "Noite"
    
    def validar(self, criterios: Dict) -> bool:
        """Valida a peça conforme os critérios de qualidade - MELHORADA"""
        self.motivos_reprovacao = []
        
        # Validar peso
        if not (criterios['peso_min'] <= self.peso <= criterios['peso_max']):
            self.motivos_reprovacao.append(
                f"Peso fora do padrão: {self.peso}g (esperado: {criterios['peso_min']}-{criterios['peso_max']}g)"
            )
        
        # Validar cor
        if self.cor not in criterios['cores_aceitas']:
            cores_aceitas = ", ".join(criterios['cores_aceitas'])
            self.motivos_reprovacao.append(
                f"Cor não aprovada: {self.cor} (esperado: {cores_aceitas})"
            )
        
        # Validar comprimento
        if not (criterios['comprimento_min'] <= self.comprimento <= criterios['comprimento_max']):
            self.motivos_reprovacao.append(
                f"Comprimento fora do padrão: {self.comprimento}cm (esperado: {criterios['comprimento_min']}-{criterios['comprimento_max']}cm)"
            )
        
        self.aprovada = len(self.motivos_reprovacao) == 0
        return self.aprovada
    
    def to_dict(self) -> Dict:
        """Converte a peça para dicionário - MELHORADA"""
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
    """Classe que representa uma caixa de peças - MELHORADA"""
    
    def __init__(self, numero: int, capacidade: int = 10):
        self.numero = numero
        self.capacidade = capacidade
        self.pecas: List[Peca] = []
        self.data_fechamento = None
        self.usuario_fechamento = ""
        self.data_criacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
    def adicionar_peca(self, peca: Peca) -> bool:
        """Adiciona uma peça à caixa se houver espaço"""
        if len(self.pecas) < self.capacidade:
            self.pecas.append(peca)
            
            # Verificar se fechou a caixa
            if len(self.pecas) >= self.capacidade:
                self.fechar(peca.usuario)
                ConfiguracaoSistema.registrar_log(f"Caixa #{self.numero} fechada automaticamente", "SISTEMA")
            
            return True
        return False
    
    def fechar(self, usuario: str = ""):
        """Fecha a caixa"""
        self.data_fechamento = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.usuario_fechamento = usuario
        ConfiguracaoSistema.registrar_log(f"Caixa #{self.numero} fechada por {usuario}", "SISTEMA")
    
    def esta_cheia(self) -> bool:
        """Verifica se a caixa está cheia"""
        return len(self.pecas) >= self.capacidade
    
    def vagas_disponiveis(self) -> int:
        """Retorna o número de vagas disponíveis"""
        return max(0, self.capacidade - len(self.pecas))
    
    def to_dict(self) -> Dict:
        """Converte a caixa para dicionário - MELHORADA"""
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
# BANCO DE DADOS MELHORADO
# ====================================================================================

class BancoDados:
    """Gerencia o armazenamento de dados do sistema - MELHORADO"""
    
    def __init__(self):
        self.arquivo_pecas = ConfiguracaoSistema.ARQUIVO_PECAS
        self.arquivo_caixas = ConfiguracaoSistema.ARQUIVO_CAIXAS
        self.config = ConfiguracaoSistema.carregar_configuracao()
        self.pecas_aprovadas: List[Peca] = []
        self.pecas_reprovadas: List[Peca] = []
        self.caixas_fechadas: List[Caixa] = []
        
        # Inicializar caixa atual com capacidade configurada
        capacidade = self.config.get('capacidade_caixa', 10)
        self.caixa_atual: Caixa = Caixa(1, capacidade)
        
        self.carregar_dados()
        self.iniciar_backup_automatico()
    
    def carregar_dados(self):
        """Carrega dados dos arquivos - MELHORADO COM TRATAMENTO DE ERROS"""
        # Carregar peças
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
                    
                ConfiguracaoSistema.registrar_log(f"Dados de peças carregados: {len(self.pecas_aprovadas)} aprovadas, {len(self.pecas_reprovadas)} reprovadas", "SISTEMA")
            except Exception as e:
                ConfiguracaoSistema.registrar_log(f"Erro ao carregar peças: {e}", "ERRO")
                messagebox.showerror("Erro", f"Erro ao carregar dados de peças: {e}")
        
        # Carregar caixas
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
                
                # Carregar caixa atual
                c_atual = dados.get('atual', {})
                capacidade_atual = c_atual.get('capacidade', self.config.get('capacidade_caixa', 10))
                self.caixa_atual = Caixa(c_atual.get('numero', len(self.caixas_fechadas) + 1), capacidade_atual)
                
                for p_dict in c_atual.get('pecas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.timestamp = p_dict.get('timestamp', '')
                    peca.turno = p_dict.get('turno', '')
                    self.caixa_atual.pecas.append(peca)
                    
                ConfiguracaoSistema.registrar_log(f"Dados de caixas carregados: {len(self.caixas_fechadas)} fechadas", "SISTEMA")
            except Exception as e:
                ConfiguracaoSistema.registrar_log(f"Erro ao carregar caixas: {e}", "ERRO")
                messagebox.showerror("Erro", f"Erro ao carregar dados de caixas: {e}")
    
    def salvar_dados(self):
        """Salva dados nos arquivos - MELHORADO COM BACKUP"""
        try:
            # Fazer backup antes de salvar
            self.fazer_backup()
            
            # Salvar peças
            dados_pecas = {
                'aprovadas': [p.to_dict() for p in self.pecas_aprovadas],
                'reprovadas': [p.to_dict() for p in self.pecas_reprovadas],
                'ultima_atualizacao': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            with open(self.arquivo_pecas, 'w', encoding='utf-8') as f:
                json.dump(dados_pecas, f, indent=2, ensure_ascii=False)
            
            # Salvar caixas
            dados_caixas = {
                'fechadas': [c.to_dict() for c in self.caixas_fechadas],
                'atual': self.caixa_atual.to_dict(),
                'ultima_atualizacao': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            with open(self.arquivo_caixas, 'w', encoding='utf-8') as f:
                json.dump(dados_caixas, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao salvar dados: {e}", "ERRO")
            messagebox.showerror("Erro", f"Erro ao salvar dados: {e}")
            return False
    
    def fazer_backup(self):
        """Faz backup dos arquivos de dados"""
        try:
            if not self.config.get('auto_backup', True):
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup de peças
            if self.arquivo_pecas.exists():
                backup_pecas = ConfiguracaoSistema.BACKUP_DIR / f"pecas_backup_{timestamp}.json"
                with open(self.arquivo_pecas, 'r', encoding='utf-8') as origem:
                    with open(backup_pecas, 'w', encoding='utf-8') as destino:
                        destino.write(origem.read())
            
            # Backup de caixas
            if self.arquivo_caixas.exists():
                backup_caixas = ConfiguracaoSistema.BACKUP_DIR / f"caixas_backup_{timestamp}.json"
                with open(self.arquivo_caixas, 'r', encoding='utf-8') as origem:
                    with open(backup_caixas, 'w', encoding='utf-8') as destino:
                        destino.write(origem.read())
                        
            ConfiguracaoSistema.registrar_log("Backup automático realizado", "BACKUP")
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro no backup: {e}", "ERRO")
    
    def iniciar_backup_automatico(self):
        """Inicia thread para backup automático periódico"""
        def backup_thread():
            while True:
                try:
                    # Verificar se é hora do backup
                    ultimo_backup = getattr(self, '_ultimo_backup', None)
                    intervalo_horas = self.config.get('backup_interval_hours', 24)
                    
                    if not ultimo_backup or (datetime.now() - ultimo_backup) > timedelta(hours=intervalo_horas):
                        self.fazer_backup()
                        self._ultimo_backup = datetime.now()
                    
                    # Esperar 1 hora antes de verificar novamente
                    threading.Event().wait(3600)
                except Exception as e:
                    ConfiguracaoSistema.registrar_log(f"Erro no thread de backup: {e}", "ERRO")
        
        if self.config.get('auto_backup', True):
            thread = threading.Thread(target=backup_thread, daemon=True)
            thread.start()
    
    def adicionar_peca(self, peca: Peca) -> Tuple[bool, str]:
        """Adiciona uma peça ao banco - MELHORADO COM VALIDAÇÃO"""
        try:
            # Verificar se ID já existe
            for p in self.pecas_aprovadas + self.pecas_reprovadas:
                if p.id_peca == peca.id_peca:
                    return False, f"ID {peca.id_peca} já existe no sistema"
            
            # Validar peça com critérios atuais
            criterios = self.config.get('critérios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['critérios_qualidade'])
            peca.validar(criterios)
            
            if peca.aprovada:
                self.pecas_aprovadas.append(peca)
                
                # Tentar adicionar à caixa atual
                if not self.caixa_atual.adicionar_peca(peca):
                    # Caixa atual está cheia, criar nova
                    self.caixas_fechadas.append(self.caixa_atual)
                    self.caixa_atual = Caixa(len(self.caixas_fechadas) + 1, self.config.get('capacidade_caixa', 10))
                    self.caixa_atual.adicionar_peca(peca)
                
                # Verificar novamente se a caixa atual ficou cheia
                if self.caixa_atual.esta_cheia():
                    self.caixas_fechadas.append(self.caixa_atual)
                    self.caixa_atual = Caixa(len(self.caixas_fechadas) + 1, self.config.get('capacidade_caixa', 10))
            else:
                self.pecas_reprovadas.append(peca)
            
            self.salvar_dados()
            ConfiguracaoSistema.registrar_log(f"Peça {peca.id_peca} {'aprovada' if peca.aprovada else 'reprovada'} por {peca.usuario}", "INSPECAO")
            
            return True, "Peça adicionada com sucesso"
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao adicionar peça: {e}", "ERRO")
            return False, f"Erro interno: {str(e)}"
    
    def remover_peca(self, id_peca: str) -> Tuple[bool, str]:
        """Remove uma peça do sistema - MELHORADO"""
        id_peca = id_peca.upper().strip()
        
        # Buscar em peças aprovadas
        for i, peca in enumerate(self.pecas_aprovadas):
            if peca.id_peca == id_peca:
                del self.pecas_aprovadas[i]
                
                # Remover também da caixa atual se estiver lá
                for j, p_caixa in enumerate(self.caixa_atual.pecas):
                    if p_caixa.id_peca == id_peca:
                        del self.caixa_atual.pecas[j]
                        break
                
                self.salvar_dados()
                ConfiguracaoSistema.registrar_log(f"Peça {id_peca} removida (aprovadas)", "REMOCAO")
                return True, f"Peça {id_peca} removida com sucesso"
        
        # Buscar em peças reprovadas
        for i, peca in enumerate(self.pecas_reprovadas):
            if peca.id_peca == id_peca:
                del self.pecas_reprovadas[i]
                self.salvar_dados()
                ConfiguracaoSistema.registrar_log(f"Peça {id_peca} removida (reprovadas)", "REMOCAO")
                return True, f"Peça {id_peca} removida com sucesso"
        
        return False, f"Peça {id_peca} não encontrada"
    
    def gerar_relatorio(self) -> Dict:
        """Gera relatório completo - MELHORADO"""
        total_pecas = len(self.pecas_aprovadas) + len(self.pecas_reprovadas)
        taxa_aprovacao = (len(self.pecas_aprovadas) / total_pecas * 100) if total_pecas > 0 else 0
        
        # Estatísticas por turno
        estatisticas_turno = {}
        todas_pecas = self.pecas_aprovadas + self.pecas_reprovadas
        
        for peca in todas_pecas:
            turno = peca.turno
            if turno not in estatisticas_turno:
                estatisticas_turno[turno] = {'aprovadas': 0, 'reprovadas': 0, 'total': 0}
            
            if peca.aprovada:
                estatisticas_turno[turno]['aprovadas'] += 1
            else:
                estatisticas_turno[turno]['reprovadas'] += 1
            estatisticas_turno[turno]['total'] += 1
        
        # Análise de motivos de reprovação
        motivos_reprovacao = Counter()
        for peca in self.pecas_reprovadas:
            for motivo in peca.motivos_reprovacao:
                if 'Peso' in motivo:
                    motivos_reprovacao['Peso'] += 1
                elif 'Cor' in motivo:
                    motivos_reprovacao['Cor'] += 1
                elif 'Comprimento' in motivo:
                    motivos_reprovacao['Comprimento'] += 1
        
        return {
            'data_geracao': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'total_pecas_aprovadas': len(self.pecas_aprovadas),
            'total_pecas_reprovadas': len(self.pecas_reprovadas),
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
            'pecas_reprovadas_detalhes': [p.to_dict() for p in self.pecas_reprovadas[-10:]],  # Últimas 10
            'caixas_fechadas_detalhes': [c.to_dict() for c in self.caixas_fechadas[-5:]]  # Últimas 5
        }

# ====================================================================================
# INTERFACE GRÁFICA CORRIGIDA E MELHORADA
# ====================================================================================

class TelaLogin:
    """Tela de login do sistema - CORRIGIDA"""
    
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.auth = SistemaAutenticacao()
        
        # Configurar janela CORRIGIDA
        self.root.title("Sistema de Controle de Qualidade Industrial - Login")
        self.root.geometry("500x600")
        self.root.resizable(True, True)
        self.centralizar_janela()
        
        # Aplicar tema
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.frame = ctk.CTkFrame(root, fg_color="transparent")
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.criar_interface()
    
    def centralizar_janela(self):
        """Centraliza a janela na tela - CORRIGIDA"""
        self.root.update_idletasks()
        width = 500
        height = 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def criar_interface(self):
        """Cria a interface de login - MELHORADA"""
        # Container principal
        container = ctk.CTkFrame(
            self.frame, 
            width=460, 
            height=560,
            fg_color="#1f538d",
            corner_radius=15
        )
        container.pack(pady=20, padx=20, fill="both", expand=True)
        container.pack_propagate(False)
        
        # Logo/Título
        titulo = ctk.CTkLabel(
            container,
            text="🏭",
            font=ctk.CTkFont(size=80),
            text_color="white"
        )
        titulo.pack(pady=(40, 10))
        
        titulo2 = ctk.CTkLabel(
            container,
            text="Sistema de Controle\nde Qualidade Industrial",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white",
            justify="center"
        )
        titulo2.pack(pady=(0, 40))
        
        # Frame do formulário
        form_frame = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
        form_frame.pack(pady=10, padx=40, fill="both", expand=True)
        
        # Campo usuário
        ctk.CTkLabel(
            form_frame,
            text="👤 Usuário",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#333333"
        ).pack(pady=(30, 5))
        
        self.entry_usuario = ctk.CTkEntry(
            form_frame,
            width=300,
            height=45,
            placeholder_text="Digite seu usuário",
            font=ctk.CTkFont(size=14),
            corner_radius=8
        )
        self.entry_usuario.pack(pady=5)
        self.entry_usuario.focus()
        
        # Campo senha
        ctk.CTkLabel(
            form_frame,
            text="🔒 Senha",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#333333"
        ).pack(pady=(20, 5))
        
        self.entry_senha = ctk.CTkEntry(
            form_frame,
            width=300,
            height=45,
            placeholder_text="Digite sua senha",
            show="●",
            font=ctk.CTkFont(size=14),
            corner_radius=8
        )
        self.entry_senha.pack(pady=5)
        self.entry_senha.bind('<Return>', lambda e: self.fazer_login())
        
        # Botão login
        btn_login = ctk.CTkButton(
            form_frame,
            text="Entrar no Sistema",
            width=300,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.fazer_login,
            fg_color="#1f538d",
            text_color="white",
            hover_color="#164276",
            corner_radius=8
        )
        btn_login.pack(pady=30)
        
        # Info padrão
        info = ctk.CTkLabel(
            form_frame,
            text="Usuário padrão: admin\nSenha: admin",
            font=ctk.CTkFont(size=12),
            text_color="#666666",
            justify="center"
        )
        info.pack(pady=(10, 20))
        
        # Versão
        versao = ctk.CTkLabel(
            container,
            text="v2.0 - Sistema Corrigido e Melhorado",
            font=ctk.CTkFont(size=10),
            text_color="#e0e0e0"
        )
        versao.pack(pady=10)
    
    def fazer_login(self):
        """Processa o login - MELHORADO"""
        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get()
        
        if not usuario or not senha:
            messagebox.showerror("Erro", "Por favor, preencha usuário e senha!")
            return
        
        sucesso, info_usuario = self.auth.autenticar(usuario, senha)
        
        if sucesso and info_usuario:
            self.frame.destroy()
            self.on_login_success(usuario, info_usuario)
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos!")
            self.entry_senha.delete(0, 'end')
            self.entry_senha.focus()

class TelaPrincipal:
    """Tela principal do sistema - CORRIGIDA E MELHORADA"""
    
    def __init__(self, root, usuario: str, info_usuario: Dict):
        self.root = root
        self.usuario = usuario
        self.info_usuario = info_usuario
        self.db = BancoDados()
        
        # Configurar janela CORRIGIDA
        self.root.title(f"Sistema de Controle de Qualidade Industrial - {info_usuario['nome_completo']}")
        self.root.geometry("1200x850")
        self.root.minsize(1000, 850)
        self.centralizar_janela()
        
        self.frame_principal = ctk.CTkFrame(root, fg_color="transparent")
        self.frame_principal.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.criar_menu_principal()
    
    def centralizar_janela(self):
        """Centraliza a janela na tela - CORRIGIDA"""
        self.root.update_idletasks()
        width = 1200
        height = 850
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def criar_menu_principal(self):
        """Cria o menu principal - MELHORADO"""
        # Limpar frame
        for widget in self.frame_principal.winfo_children():
            widget.destroy()
        
        # Header
        header = ctk.CTkFrame(self.frame_principal, fg_color="#1f538d", height=80, corner_radius=10)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)
        
        # Título
        titulo_frame = ctk.CTkFrame(header, fg_color="transparent")
        titulo_frame.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(
            titulo_frame,
            text="🏭 Sistema de Controle de Qualidade Industrial",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="white"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            titulo_frame,
            text="Controle de Produção e Qualidade - Linha de Montagem",
            font=ctk.CTkFont(size=12),
            text_color="#e0e0e0"
        ).pack(anchor="w")
        
        # Info usuário
        user_frame = ctk.CTkFrame(header, fg_color="transparent")
        user_frame.pack(side="right", padx=20, pady=10)
        
        ctk.CTkLabel(
            user_frame,
            text=f"👤 {self.info_usuario['nome_completo']}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white",
            justify="right"
        ).pack(anchor="e")
        
        ctk.CTkLabel(
            user_frame,
            text=f"📋 {self.info_usuario['nivel'].title()} | Turno: {self.obter_turno_atual()}",
            font=ctk.CTkFont(size=10),
            text_color="#e0e0e0",
            justify="right"
        ).pack(anchor="e")
        
        ctk.CTkButton(
            header, 
            text="🚪 Sair", 
            width=200, 
            height=50, 
            command=self.root.quit,
            font=ctk.CTkFont(size=14, weight="bold"), 
            fg_color="#c0392b"
        ).pack(side="left", padx=10)
        
        # Dashboard em tempo real
        self.criar_dashboard()
        
        # Menu de opções
        self.criar_menu_opcoes()
    
    def obter_turno_atual(self) -> str:
        """Determina o turno atual"""
        hora = datetime.now().hour
        if 6 <= hora < 14:
            return "Manhã"
        elif 14 <= hora < 22:
            return "Tarde"
        else:
            return "Noite"
    
    def criar_dashboard(self):
        """Cria dashboard com métricas em tempo real - NOVO"""
        dash_frame = ctk.CTkFrame(self.frame_principal, height=120)
        dash_frame.pack(fill="x", padx=10, pady=10)
        dash_frame.pack_propagate(False)
        
        # Métricas
        metrics = [
            ("✅ Peças Aprovadas", len(self.db.pecas_aprovadas), "#2ecc71"),
            ("❌ Peças Reprovadas", len(self.db.pecas_reprovadas), "#e74c3c"),
            ("📦 Caixas Completas", len(self.db.caixas_fechadas), "#3498db"),
            ("📊 Taxa de Aprovação", f"{(len(self.db.pecas_aprovadas)/(len(self.db.pecas_aprovadas)+len(self.db.pecas_reprovadas))*100 if (len(self.db.pecas_aprovadas)+len(self.db.pecas_reprovadas)) > 0 else 0):.1f}%", "#9b59b6"),
            ("🔧 Caixa Atual", f"#{self.db.caixa_atual.numero} ({len(self.db.caixa_atual.pecas)}/{self.db.caixa_atual.capacidade})", "#f39c12"),
            ("🕒 Turno Atual", self.obter_turno_atual(), "#1abc9c")
        ]
        
        for i, (titulo, valor, cor) in enumerate(metrics):
            card = self.criar_card(dash_frame, titulo, str(valor), cor)
            card.grid(row=0, column=i, padx=5, pady=10, sticky="nsew")
            dash_frame.columnconfigure(i, weight=1)
    
    def criar_card(self, parent, titulo: str, valor: str, cor: str):
        """Cria card para dashboard - MELHORADO"""
        card = ctk.CTkFrame(parent, fg_color=cor, height=100, corner_radius=10)
        card.pack_propagate(False)
        
        ctk.CTkLabel(
            card, 
            text=titulo, 
            font=ctk.CTkFont(size=11, weight="bold"), 
            text_color="white"
        ).pack(pady=(15, 5))
        
        ctk.CTkLabel(
            card, 
            text=valor, 
            font=ctk.CTkFont(size=24, weight="bold"), 
            text_color="white"
        ).pack(pady=(5, 15))
        
        return card
    
    def criar_menu_opcoes(self):
        """Cria o menu de opções - MELHORADO"""
        menu_frame = ctk.CTkFrame(self.frame_principal)
        menu_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        titulo_menu = ctk.CTkLabel(
            menu_frame,
            text="Menu Principal - Escolha uma operação:",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        titulo_menu.pack(pady=20)
        
        # Opções principais
        opcoes_principais = [
            ("📝 Cadastrar Nova Peça", self.tela_cadastrar_peca, "#1f538d"),
            ("📋 Listar Peças Inspecionadas", self.tela_listar_pecas, "#2980b9"),
            ("🗑️ Remover Peça do Sistema", self.tela_remover_peca, "#e67e22"),
            ("📦 Gerenciar Caixas", self.tela_listar_caixas, "#27ae60"),
            ("🚪 Sair", self.root.quit, "#c0392b")
        ]
        
        for texto, comando, cor in opcoes_principais:
            btn = ctk.CTkButton(
                menu_frame,
                text=texto,
                width=400,
                height=50,
                font=ctk.CTkFont(size=14, weight="bold"),
                command=comando,
                fg_color=cor,
                hover_color=self.escurecer_cor(cor),
                corner_radius=8
            )
            btn.pack(pady=6)
        
        # Separador
        ctk.CTkLabel(
            menu_frame,
            text="Relatórios e Ferramentas",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(20, 10))
        
        # Opções secundárias
        opcoes_secundarias = [
            ("📊 Gerar Relatório Completo", self.tela_relatorio, "#8e44ad"),
            ("⚙️ Configurações do Sistema", self.tela_configuracoes, "#34495e"),
        ]
        
        for texto, comando, cor in opcoes_secundarias:
            btn = ctk.CTkButton(
                menu_frame,
                text=texto,
                width=400,
                height=45,
                font=ctk.CTkFont(size=13),
                command=comando,
                fg_color=cor,
                hover_color=self.escurecer_cor(cor),
                corner_radius=8
            )
            btn.pack(pady=4)
        
        # Botão sair
        # ctk.CTkButton(
        #     menu_frame,
        #     text="🚪 Sair do Sistema",
        #     width=400,
        #     height=45,
        #     font=ctk.CTkFont(size=13),
        #     command=self.root.quit,
        #     fg_color="#c0392b",
        #     hover_color="#a93226",
        #     corner_radius=8
        # ).pack(pady=20)
    
    def escurecer_cor(self, cor: str) -> str:
        """Escurece uma cor hex - CORRIGIDA"""
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
        """Tela de cadastro de nova peça - MELHORADA"""
        self.limpar_tela()
        self.criar_header("📝 Cadastrar Nova Peça")
        
        # Frame do formulário
        form_frame = ctk.CTkFrame(self.frame_principal)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título do formulário
        ctk.CTkLabel(
            form_frame,
            text="Preencha os dados da peça:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=20)
        
        # Container dos campos
        campos_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        campos_frame.pack(pady=20, padx=50, fill="both", expand=True)
        
        # Critérios atuais para referência
        criterios = self.db.config.get('critérios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['critérios_qualidade'])
        
        # ID da Peça
        ctk.CTkLabel(
            campos_frame, 
            text="🔢 ID da Peça (Obrigatório):", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        entry_id = ctk.CTkEntry(
            campos_frame, 
            width=400, 
            height=45, 
            placeholder_text="Ex: PECA001, ABC123, etc.",
            font=ctk.CTkFont(size=14)
        )
        entry_id.pack(fill="x", pady=5)
        entry_id.focus()
        
        # Peso
        ctk.CTkLabel(
            campos_frame, 
            text=f"⚖️ Peso (g) - Padrão: {criterios['peso_min']}g a {criterios['peso_max']}g:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(15, 5))
        
        entry_peso = ctk.CTkEntry(
            campos_frame, 
            width=400, 
            height=45, 
            placeholder_text=f"Ex: 100.0 (entre {criterios['peso_min']} e {criterios['peso_max']})",
            font=ctk.CTkFont(size=14)
        )
        entry_peso.pack(fill="x", pady=5)
        
        # Cor
        ctk.CTkLabel(
            campos_frame, 
            text=f"🎨 Cor - Aprovadas: {', '.join(criterios['cores_aceitas'])}:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(15, 5))
        
        combo_cor = ctk.CTkComboBox(
            campos_frame, 
            width=400, 
            height=45,
            values=["azul", "verde", "vermelho", "amarelo", "preto", "branco", "cinza", "laranja"],
            font=ctk.CTkFont(size=14)
        )
        combo_cor.set("azul")
        combo_cor.pack(fill="x", pady=5)
        
        # Comprimento
        ctk.CTkLabel(
            campos_frame, 
            text=f"📏 Comprimento (cm) - Padrão: {criterios['comprimento_min']}cm a {criterios['comprimento_max']}cm:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(15, 5))
        
        entry_comp = ctk.CTkEntry(
            campos_frame, 
            width=400, 
            height=45, 
            placeholder_text=f"Ex: 15.0 (entre {criterios['comprimento_min']} e {criterios['comprimento_max']})",
            font=ctk.CTkFont(size=14)
        )
        entry_comp.pack(fill="x", pady=5)
        
        # Botões
        btn_frame = ctk.CTkFrame(campos_frame, fg_color="transparent")
        btn_frame.pack(pady=40)
        
        def cadastrar():
            try:
                id_peca = entry_id.get().strip()
                peso_str = entry_peso.get().strip()
                cor = combo_cor.get().strip()
                comp_str = entry_comp.get().strip()
                
                # Validações
                if not id_peca:
                    messagebox.showerror("Erro", "ID da peça é obrigatório!")
                    entry_id.focus()
                    return
                
                if not peso_str or not comp_str:
                    messagebox.showerror("Erro", "Peso e comprimento são obrigatórios!")
                    return
                
                try:
                    peso = float(peso_str.replace(',', '.'))
                    comprimento = float(comp_str.replace(',', '.'))
                except ValueError:
                    messagebox.showerror("Erro", "Peso e comprimento devem ser números válidos!")
                    return
                
                # Criar e validar peça
                peca = Peca(id_peca, peso, cor, comprimento, self.usuario)
                sucesso, mensagem = self.db.adicionar_peca(peca)
                
                if sucesso:
                    if peca.aprovada:
                        messagebox.showinfo(
                            "✅ Peça Aprovada!", 
                            f"Peça {id_peca} foi APROVADA!\n\n"
                            f"• Adicionada à caixa #{self.db.caixa_atual.numero}\n"
                            f"• Vagas restantes: {self.db.caixa_atual.vagas_disponiveis()}\n"
                            f"• Turno: {peca.turno}"
                        )
                    else:
                        motivos = "\n".join([f"• {m}" for m in peca.motivos_reprovacao])
                        messagebox.showwarning(
                            "❌ Peça Reprovada", 
                            f"Peça {id_peca} foi REPROVADA!\n\nMotivos:\n{motivos}"
                        )
                    
                    self.criar_menu_principal()
                else:
                    messagebox.showerror("Erro", mensagem)
                    
            except Exception as e:
                messagebox.showerror("Erro", f"Erro inesperado: {str(e)}")
                ConfiguracaoSistema.registrar_log(f"Erro no cadastro: {e}", "ERRO")
        
        ctk.CTkButton(
            btn_frame, 
            text="✅ Cadastrar Peça", 
            width=200, 
            height=50, 
            command=cadastrar,
            font=ctk.CTkFont(size=14, weight="bold"), 
            fg_color="#2ecc71",
            hover_color="#27ae60"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, 
            text="🔙 Voltar ao Menu", 
            width=200, 
            height=50, 
            command=self.criar_menu_principal,
            font=ctk.CTkFont(size=14, weight="bold"), 
            fg_color="#95a5a6",
            hover_color="#7f8c8d"
        ).pack(side="left", padx=10)
    
    def tela_listar_pecas(self):
        """Tela de listagem de peças - MELHORADA"""
        self.limpar_tela()
        self.criar_header("📋 Peças Inspecionadas")
        
        # Frame principal com tabs
        main_frame = ctk.CTkFrame(self.frame_principal)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Criar abas
        tabview = ctk.CTkTabview(main_frame)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Aba de peças aprovadas
        tab_aprovadas = tabview.add("✅ Aprovadas")
        self.criar_lista_pecas(tab_aprovadas, self.db.pecas_aprovadas, "aprovadas")
        
        # Aba de peças reprovadas
        tab_reprovadas = tabview.add("❌ Reprovadas")
        self.criar_lista_pecas(tab_reprovadas, self.db.pecas_reprovadas, "reprovadas")
        
        # Botão voltar
        ctk.CTkButton(
            main_frame,
            text="🔙 Voltar ao Menu",
            width=200,
            height=45,
            command=self.criar_menu_principal,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#95a5a6"
        ).pack(pady=10)
    
    def criar_lista_pecas(self, parent, pecas: List[Peca], tipo: str):
        """Cria lista de peças em um frame - MELHORADA"""
        # Frame com scroll
        frame = ctk.CTkScrollableFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        if not pecas:
            ctk.CTkLabel(
                frame,
                text=f"Nenhuma peça {tipo} cadastrada.",
                font=ctk.CTkFont(size=14),
                text_color="#666666"
            ).pack(pady=50)
            return
        
        # Cabeçalho
        header_frame = ctk.CTkFrame(frame, fg_color="#34495e")
        header_frame.pack(fill="x", pady=(0, 10))
        
        headers = ["ID", "Peso", "Cor", "Comprimento", "Turno", "Inspetor", "Data"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white"
            ).grid(row=0, column=i, padx=10, pady=8, sticky="w")
            header_frame.columnconfigure(i, weight=1)
        
        # Lista de peças
        for idx, peca in enumerate(pecas[-100:], 1):  # Mostrar últimas 100
            row_frame = ctk.CTkFrame(frame, fg_color="#f8f9fa" if idx % 2 == 0 else "white")
            row_frame.pack(fill="x", pady=2)
            
            dados = [
                peca.id_peca,
                f"{peca.peso}g",
                peca.cor.title(),
                f"{peca.comprimento}cm",
                peca.turno,
                peca.usuario,
                peca.timestamp
            ]
            
            for i, dado in enumerate(dados):
                ctk.CTkLabel(
                    row_frame,
                    text=dado,
                    font=ctk.CTkFont(size=11),
                    text_color="#2c3e50"
                ).grid(row=0, column=i, padx=10, pady=6, sticky="w")
                row_frame.columnconfigure(i, weight=1)
    
    def tela_remover_peca(self):
        """Tela de remoção de peça - MELHORADA"""
        self.limpar_tela()
        self.criar_header("🗑️ Remover Peça do Sistema")
        
        form_frame = ctk.CTkFrame(self.frame_principal)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            form_frame,
            text="Digite o ID da peça que deseja remover:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=30)
        
        entry_id = ctk.CTkEntry(
            form_frame, 
            width=400, 
            height=50, 
            placeholder_text="Ex: PECA001",
            font=ctk.CTkFont(size=14)
        )
        entry_id.pack(pady=10)
        entry_id.focus()
        
        # Informações da peça (serão preenchidas dinamicamente)
        info_frame = ctk.CTkFrame(form_frame, height=100)
        info_frame.pack(fill="x", pady=10, padx=50)
        info_frame.pack_propagate(False)
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="Digite um ID para ver informações da peça...",
            font=ctk.CTkFont(size=12),
            text_color="#666666",
            wraplength=500
        )
        info_label.pack(pady=20)
        
        def buscar_peca(event=None):
            id_peca = entry_id.get().strip().upper()
            if not id_peca:
                info_label.configure(text="Digite um ID para ver informações da peça...", text_color="#666666")
                return
            
            # Buscar peça
            for peca in self.db.pecas_aprovadas + self.db.pecas_reprovadas:
                if peca.id_peca == id_peca:
                    status = "✅ APROVADA" if peca.aprovada else "❌ REPROVADA"
                    info_label.configure(
                        text=f"Peça encontrada:\n"
                             f"ID: {peca.id_peca} | Status: {status}\n"
                             f"Peso: {peca.peso}g | Cor: {peca.cor.title()} | Comprimento: {peca.comprimento}cm\n"
                             f"Inspetor: {peca.usuario} | Data: {peca.timestamp} | Turno: {peca.turno}",
                        text_color="#2c3e50"
                    )
                    return
            
            info_label.configure(
                text=f"Peça {id_peca} não encontrada no sistema.",
                text_color="#e74c3c"
            )
        
        entry_id.bind('<KeyRelease>', buscar_peca)
        
        def remover():
            id_peca = entry_id.get().strip().upper()
            if not id_peca:
                messagebox.showerror("Erro", "Digite um ID válido!")
                return
            
            # Confirmar remoção
            resposta = messagebox.askyesno(
                "Confirmar Remoção", 
                f"Tem certeza que deseja remover a peça {id_peca}?\n\n"
                f"⚠️  ESTA AÇÃO NÃO PODE SER DESFEITA!"
            )
            
            if resposta:
                sucesso, mensagem = self.db.remover_peca(id_peca)
                if sucesso:
                    messagebox.showinfo("Sucesso", mensagem)
                    self.criar_menu_principal()
                else:
                    messagebox.showerror("Erro", mensagem)
        
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(
            btn_frame, 
            text="🗑️ Remover Peça", 
            width=200, 
            height=50, 
            command=remover,
            font=ctk.CCTkFont(size=14, weight="bold"), 
            fg_color="#e74c3c",
            hover_color="#c0392b"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, 
            text="🔙 Voltar", 
            width=200, 
            height=50, 
            command=self.criar_menu_principal,
            font=ctk.CTkFont(size=14, weight="bold"), 
            fg_color="#95a5a6"
        ).pack(side="left", padx=10)
    
    def tela_listar_caixas(self):
        """Tela de listagem de caixas - MELHORADA"""
        self.limpar_tela()
        self.criar_header("📦 Gerenciar Caixas")
        
        content_frame = ctk.CTkFrame(self.frame_principal)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Caixa atual
        ctk.CTkLabel(
            content_frame,
            text="📦 Caixa Atual em Produção:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        info_frame = ctk.CTkFrame(content_frame, fg_color="#3498db", height=120, corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=10)
        info_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            info_frame,
            text=f"Caixa #{self.db.caixa_atual.numero}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="white"
        ).pack(pady=5)
        
        progresso = (len(self.db.caixa_atual.pecas) / self.db.caixa_atual.capacidade) * 100
        ctk.CTkLabel(
            info_frame,
            text=f"Progresso: {len(self.db.caixa_atual.pecas)}/{self.db.caixa_atual.capacidade} peças ({progresso:.1f}%)",
            font=ctk.CTkFont(size=14),
            text_color="white"
        ).pack(pady=2)
        
        ctk.CTkLabel(
            info_frame,
            text=f"Vagas disponíveis: {self.db.caixa_atual.vagas_disponiveis()}",
            font=ctk.CTkFont(size=12),
            text_color="#e0e0e0"
        ).pack(pady=2)
        
        # Caixas fechadas
        ctk.CTkLabel(
            content_frame,
            text="📦 Caixas Fechadas e Completas:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=20)
        
        if not self.db.caixas_fechadas:
            ctk.CTkLabel(
                content_frame,
                text="Nenhuma caixa foi fechada ainda.",
                font=ctk.CTkFont(size=14),
                text_color="#666666"
            ).pack(pady=50)
        else:
            # Lista de caixas fechadas
            scroll_frame = ctk.CTkScrollableFrame(content_frame, height=300)
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            for caixa in self.db.caixas_fechadas[-20:]:  # Últimas 20 caixas
                caixa_frame = ctk.CTkFrame(scroll_frame, fg_color="#ecf0f1")
                caixa_frame.pack(fill="x", pady=5, padx=5)
                
                # Header da caixa
                header_caixa = ctk.CTkFrame(caixa_frame, fg_color="#34495e")
                header_caixa.pack(fill="x", padx=2, pady=2)
                
                ctk.CTkLabel(
                    header_caixa,
                    text=f"📦 Caixa #{caixa.numero} - {len(caixa.pecas)} peças - Fechada em: {caixa.data_fechamento}",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="white"
                ).pack(pady=8, padx=10, anchor="w")
                
                # Peças da caixa
                pecas_text = ", ".join([p.id_peca for p in caixa.pecas])
                ctk.CTkLabel(
                    caixa_frame,
                    text=f"Peças: {pecas_text}",
                    font=ctk.CTkFont(size=10),
                    text_color="#2c3e50",
                    wraplength=800
                ).pack(pady=5, padx=10, anchor="w")
        
        # Botão voltar
        ctk.CTkButton(
            content_frame,
            text="🔙 Voltar ao Menu",
            width=200,
            height=45,
            command=self.criar_menu_principal,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#95a5a6"
        ).pack(pady=20)
    
    def tela_relatorio(self):
        """Tela de relatório final - MELHORADA"""
        self.limpar_tela()
        self.criar_header("📊 Relatório Completo do Sistema")
        
        content_frame = ctk.CTkFrame(self.frame_principal)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Gerar relatório
        relatorio = self.db.gerar_relatorio()
        
        # Área de texto com scroll
        text_frame = ctk.CTkFrame(content_frame)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_relatorio = ctk.CTkTextbox(text_frame, font=ctk.CTkFont(size=11))
        text_relatorio.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Formatar relatório
        relatorio_formatado = self.formatar_relatorio(relatorio)
        text_relatorio.insert("1.0", relatorio_formatado)
        text_relatorio.configure(state="disabled")
        
        # Botões de exportação
        btn_frame = ctk.CTkFrame(content_frame)
        btn_frame.pack(pady=10)
        
        def exportar_json():
            try:
                caminho = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json")],
                    initialfile=f"relatorio_qualidade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                if caminho:
                    with open(caminho, 'w', encoding='utf-8') as f:
                        json.dump(relatorio, f, indent=2, ensure_ascii=False)
                    messagebox.showinfo("Sucesso", f"Relatório exportado:\n{caminho}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar JSON: {e}")
        
        def exportar_csv():
            try:
                caminho = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")],
                    initialfile=f"relatorio_qualidade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                if caminho:
                    with open(caminho, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f, delimiter=';')
                        writer.writerow(['ID', 'Peso (g)', 'Cor', 'Comprimento (cm)', 'Status', 'Inspetor', 'Turno', 'Data', 'Motivos'])
                        
                        for peca in self.db.pecas_aprovadas:
                            writer.writerow([
                                peca.id_peca, peca.peso, peca.cor, peca.comprimento, 
                                'APROVADA', peca.usuario, peca.turno, peca.timestamp, ''
                            ])
                        
                        for peca in self.db.pecas_reprovadas:
                            motivos = ' | '.join(peca.motivos_reprovacao)
                            writer.writerow([
                                peca.id_peca, peca.peso, peca.cor, peca.comprimento, 
                                'REPROVADA', peca.usuario, peca.turno, peca.timestamp, motivos
                            ])
                    
                    messagebox.showinfo("Sucesso", f"Relatório exportado:\n{caminho}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar CSV: {e}")
        
        def imprimir_tela():
            try:
                # Criar arquivo texto simples com o relatório
                caminho = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text files", "*.txt")],
                    initialfile=f"relatorio_qualidade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                )
                if caminho:
                    with open(caminho, 'w', encoding='utf-8') as f:
                        f.write(relatorio_formatado)
                    messagebox.showinfo("Sucesso", f"Relatório salvo:\n{caminho}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar relatório: {e}")
        
        ctk.CTkButton(
            btn_frame, 
            text="💾 Exportar JSON", 
            width=150, 
            height=40, 
            command=exportar_json,
            font=ctk.CTkFont(size=12, weight="bold"), 
            fg_color="#2ecc71"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame, 
            text="📄 Exportar CSV", 
            width=150, 
            height=40, 
            command=exportar_csv,
            font=ctk.CTkFont(size=12, weight="bold"), 
            fg_color="#27ae60"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame, 
            text="🖨️ Salvar Texto", 
            width=150, 
            height=40, 
            command=imprimir_tela,
            font=ctk.CTkFont(size=12, weight="bold"), 
            fg_color="#3498db"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame, 
            text="🔙 Voltar", 
            width=150, 
            height=40, 
            command=self.criar_menu_principal,
            font=ctk.CTkFont(size=12, weight="bold"), 
            fg_color="#95a5a6"
        ).pack(side="left", padx=5)
    
    def tela_configuracoes(self):
        """Tela de configurações do sistema - NOVA"""
        self.limpar_tela()
        self.criar_header("⚙️ Configurações do Sistema")
        
        content_frame = ctk.CTkFrame(self.frame_principal)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Abas para diferentes configurações
        tabview = ctk.CTkTabview(content_frame)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Aba de critérios de qualidade
        tab_criterios = tabview.add("🎯 Critérios de Qualidade")
        self.criar_config_criterios(tab_criterios)
        
        # Aba de sistema
        tab_sistema = tabview.add("⚙️ Sistema")
        self.criar_config_sistema(tab_sistema)
        
        # Botão voltar
        ctk.CTkButton(
            content_frame,
            text="🔙 Voltar ao Menu",
            width=200,
            height=45,
            command=self.criar_menu_principal,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#95a5a6"
        ).pack(pady=10)
    
    def criar_config_criterios(self, parent):
        """Cria interface de configuração de critérios"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        criterios = self.db.config.get('critérios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['critérios_qualidade'])
        
        ctk.CTkLabel(
            frame,
            text="Configurar Critérios de Qualidade:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
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
        ctk.CTkLabel(frame, text="Cores Aprovadas (separadas por vírgula):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        entry_cores = ctk.CTkEntry(frame, width=400)
        entry_cores.insert(0, ", ".join(criterios['cores_aceitas']))
        entry_cores.pack(anchor="w", pady=5)
        
        def salvar_criterios():
            try:
                novos_criterios = {
                    'peso_min': float(entry_peso_min.get()),
                    'peso_max': float(entry_peso_max.get()),
                    'comprimento_min': float(entry_comp_min.get()),
                    'comprimento_max': float(entry_comp_max.get()),
                    'cores_aceitas': [cor.strip().lower() for cor in entry_cores.get().split(',')]
                }
                
                self.db.config['critérios_qualidade'] = novos_criterios
                ConfiguracaoSistema.salvar_configuracao(self.db.config)
                
                messagebox.showinfo("Sucesso", "Critérios de qualidade atualizados!")
                
            except ValueError:
                messagebox.showerror("Erro", "Por favor, insira valores numéricos válidos.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar critérios: {e}")
        
        ctk.CTkButton(
            frame,
            text="💾 Salvar Critérios",
            width=200,
            height=45,
            command=salvar_criterios,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27ae60"
        ).pack(pady=30)
    
    def criar_config_sistema(self, parent):
        """Cria interface de configuração do sistema"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame,
            text="Configurações do Sistema:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # Capacidade da caixa
        ctk.CTkLabel(frame, text="Capacidade de Peças por Caixa:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        entry_capacidade = ctk.CTkEntry(frame, width=100)
        entry_capacidade.insert(0, str(self.db.config.get('capacidade_caixa', 10)))
        entry_capacidade.pack(anchor="w", pady=5)
        
        # Backup automático
        var_backup = ctk.BooleanVar(value=self.db.config.get('auto_backup', True))
        switch_backup = ctk.CTkSwitch(
            frame, 
            text="Backup Automático", 
            variable=var_backup,
            font=ctk.CTkFont(size=14)
        )
        switch_backup.pack(anchor="w", pady=10)
        
        # Intervalo de backup
        ctk.CTkLabel(frame, text="Intervalo de Backup (horas):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        entry_intervalo = ctk.CTkEntry(frame, width=100)
        entry_intervalo.insert(0, str(self.db.config.get('backup_interval_hours', 24)))
        entry_intervalo.pack(anchor="w", pady=5)
        
        def salvar_config_sistema():
            try:
                self.db.config['capacidade_caixa'] = int(entry_capacidade.get())
                self.db.config['auto_backup'] = var_backup.get()
                self.db.config['backup_interval_hours'] = int(entry_intervalo.get())
                
                ConfiguracaoSistema.salvar_configuracao(self.db.config)
                
                messagebox.showinfo("Sucesso", "Configurações do sistema atualizadas!")
                
            except ValueError:
                messagebox.showerror("Erro", "Por favor, insira valores numéricos válidos.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")
        
        ctk.CTkButton(
            frame,
            text="💾 Salvar Configurações",
            width=200,
            height=45,
            command=salvar_config_sistema,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3498db"
        ).pack(pady=30)
    
    def formatar_relatorio(self, relatorio: Dict) -> str:
        """Formata o relatório para exibição - MELHORADA"""
        texto = "="*80 + "\n"
        texto += "           RELATÓRIO COMPLETO - SISTEMA DE CONTROLE DE QUALIDADE\n"
        texto += "="*80 + "\n\n"
        
        texto += f"📅 Data de Geração: {relatorio['data_geracao']}\n"
        texto += f"👤 Gerado por: {self.info_usuario['nome_completo']} ({self.usuario})\n"
        texto += f"🏭 Sistema: Controle de Qualidade Industrial v2.0\n\n"
        
        texto += "📈 RESUMO GERAL DA PRODUÇÃO\n"
        texto += "-"*80 + "\n"
        texto += f"• Total de Peças Inspecionadas: {relatorio['total_pecas_inspecionadas']:,}\n"
        texto += f"• ✅ Peças Aprovadas: {relatorio['total_pecas_aprovadas']:,}\n"
        texto += f"• ❌ Peças Reprovadas: {relatorio['total_pecas_reprovadas']:,}\n"
        texto += f"• 📊 Taxa de Aprovação: {relatorio['taxa_aprovacao']}%\n"
        texto += f"• 📦 Caixas Completas: {relatorio['caixas_completas']:,}\n\n"
        
        texto += "📦 SITUAÇÃO DA CAIXA ATUAL\n"
        texto += "-"*80 + "\n"
        texto += f"• Número: #{relatorio['caixa_atual']['numero']}\n"
        texto += f"• Peças: {relatorio['caixa_atual']['pecas']}/{relatorio['caixa_atual']['capacidade']}\n"
        texto += f"• Vagas Disponíveis: {relatorio['caixa_atual']['vagas_disponiveis']}\n"
        texto += f"• Percentual de Ocupação: {relatorio['caixa_atual']['percentual_cheio']:.1f}%\n\n"
        
        if relatorio['estatisticas_turno']:
            texto += "🕒 ESTATÍSTICAS POR TURNO\n"
            texto += "-"*80 + "\n"
            for turno, stats in relatorio['estatisticas_turno'].items():
                taxa_turno = (stats['aprovadas'] / stats['total'] * 100) if stats['total'] > 0 else 0
                texto += f"• {turno}: {stats['aprovadas']} aprovadas, {stats['reprovadas']} reprovadas "
                texto += f"({taxa_turno:.1f}% de aprovação)\n"
            texto += "\n"
        
        if relatorio['analise_motivos_reprovacao']:
            texto += "❌ ANÁLISE DOS MOTIVOS DE REPROVAÇÃO\n"
            texto += "-"*80 + "\n"
            total_reprovacoes = sum(relatorio['analise_motivos_reprovacao'].values())
            for motivo, quantidade in relatorio['analise_motivos_reprovacao'].items():
                percentual = (quantidade / total_reprovacoes * 100) if total_reprovacoes > 0 else 0
                texto += f"• {motivo}: {quantidade} ocorrências ({percentual:.1f}%)\n"
            texto += "\n"
        
        texto += "="*80 + "\n"
        texto += "Relatório gerado automaticamente - Sistema de Controle de Qualidade v2.0\n"
        texto += "="*80 + "\n"
        
        return texto
    
    def criar_header(self, titulo: str):
        """Cria o header padrão - MELHORADO"""
        header = ctk.CTkFrame(self.frame_principal, fg_color="#1f538d", height=70, corner_radius=10)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text=titulo,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=15)
        
        # Botão voltar no header
        ctk.CTkButton(
            header,
            text="🔙 Voltar",
            width=100,
            height=35,
            command=self.criar_menu_principal,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="white",
            text_color="#1f538d",
            hover_color="#e0e0e0"
        ).pack(side="right", padx=20, pady=15)
    
    def limpar_tela(self):
        """Limpa a tela atual - CORRIGIDA"""
        for widget in self.frame_principal.winfo_children():
            widget.destroy()

# ====================================================================================
# APLICAÇÃO PRINCIPAL CORRIGIDA
# ====================================================================================

class Aplicacao:
    """Classe principal da aplicação - CORRIGIDA"""
    
    def __init__(self):
        # Criar estrutura de pastas
        if not ConfiguracaoSistema.criar_estrutura_pastas():
            messagebox.showerror("Erro", "Não foi possível criar a estrutura de pastas do sistema!")
            return
        
        # Criar janela principal
        self.root = ctk.CTk()
        
        # Aplicar tema
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Iniciar com tela de login
        TelaLogin(self.root, self.on_login_success)
    
    def on_login_success(self, usuario: str, info_usuario: Dict):
        """Callback após login bem-sucedido"""
        TelaPrincipal(self.root, usuario, info_usuario)
    
    def executar(self):
        """Executa a aplicação"""
        self.root.mainloop()

# ====================================================================================
# PONTO DE ENTRADA
# ====================================================================================

def main():
    """Função principal"""
    print("\n" + "="*70)
    print("  🏭 Sistema de Controle de Qualidade Industrial v2.0")
    print("  📊 Automação de Inspeção de Peças - Linha de Montagem")
    print("  🔧 Versão Corrigida e Melhorada")
    print("="*70 + "\n")
    
    try:
        app = Aplicacao()
        app.executar()
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        messagebox.showerror("Erro Fatal", f"O sistema encontrou um erro e precisa fechar:\n\n{str(e)}")
    finally:
        ConfiguracaoSistema.registrar_log("Aplicação encerrada", "SISTEMA")

if __name__ == "__main__":
    main()
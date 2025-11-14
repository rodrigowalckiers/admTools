"""
Sistema de Controle de Qualidade Industrial
Versão 2.2 - Corrigida e Melhorada
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
        'sistema': {
            'nome_sistema': 'Sistema de Controle de Qualidade Industrial',
            'versao': '2.2'
        },
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
            
            if nivel not in ['administrador', 'operador']:
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
    
    def editar_usuario(self, usuario_antigo: str, usuario_novo: str, nome_completo: str, nivel: str, ativo: bool) -> Tuple[bool, str]:
        """Edita um usuário existente"""
        try:
            if usuario_antigo not in self.usuarios:
                return False, "Usuário não encontrado"
            
            # Se o usuário está mudando de nome, verificar se novo nome já existe
            if usuario_antigo != usuario_novo and usuario_novo in self.usuarios:
                return False, "Novo nome de usuário já existe"
            
            # Manter a senha existente
            senha = self.usuarios[usuario_antigo]['senha']
            
            # Remover o usuário antigo e adicionar com novos dados
            if usuario_antigo != usuario_novo:
                del self.usuarios[usuario_antigo]
            
            self.usuarios[usuario_novo] = {
                'senha': senha,
                'nome_completo': nome_completo,
                'nivel': nivel,
                'data_criacao': self.usuarios.get(usuario_antigo, {}).get('data_criacao', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'ultimo_login': self.usuarios.get(usuario_antigo, {}).get('ultimo_login'),
                'ativo': ativo
            }
            
            self.salvar_usuarios()
            ConfiguracaoSistema.registrar_log(f"Usuário editado: {usuario_antigo} -> {usuario_novo}", "ADMIN")
            return True, "Usuário editado com sucesso"
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao editar usuário: {e}", "ERRO")
            return False, f"Erro interno: {str(e)}"
    
    def redefinir_senha(self, usuario: str, nova_senha: str) -> Tuple[bool, str]:
        """Redefine a senha de um usuário"""
        try:
            if usuario not in self.usuarios:
                return False, "Usuário não encontrado"
            
            if len(nova_senha) < 4:
                return False, "Senha deve ter pelo menos 4 caracteres"
            
            senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.usuarios[usuario]['senha'] = senha_hash
            self.salvar_usuarios()
            ConfiguracaoSistema.registrar_log(f"Senha redefinida para usuário: {usuario}", "ADMIN")
            return True, "Senha redefinida com sucesso"
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao redefinir senha: {e}", "ERRO")
            return False, f"Erro interno: {str(e)}"
    
    def excluir_usuario(self, usuario: str) -> Tuple[bool, str]:
        """Exclui um usuário do sistema"""
        try:
            if usuario not in self.usuarios:
                return False, "Usuário não encontrado"
            
            if usuario == 'admin':
                return False, "Não é possível excluir o usuário administrador principal"
            
            del self.usuarios[usuario]
            self.salvar_usuarios()
            ConfiguracaoSistema.registrar_log(f"Usuário excluído: {usuario}", "ADMIN")
            return True, "Usuário excluído com sucesso"
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao excluir usuário: {e}", "ERRO")
            return False, f"Erro interno: {str(e)}"
    
    def listar_usuarios(self) -> List[Dict]:
        """Lista todos os usuários do sistema"""
        usuarios_lista = []
        for username, data in self.usuarios.items():
            usuarios_lista.append({
                'usuario': username,
                'nome_completo': data['nome_completo'],
                'nivel': data['nivel'],
                'data_criacao': data['data_criacao'],
                'ultimo_login': data.get('ultimo_login', 'Nunca'),
                'ativo': data.get('ativo', True)
            })
        return usuarios_lista

# ====================================================================================
# MODELOS DE DADOS (mantidos iguais)
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
        self.data_inspecao = datetime.now().strftime("%Y-%m-%d")
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
            'data_inspecao': self.data_inspecao,
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
                    peca.data_inspecao = p_dict.get('data_inspecao', '')
                    peca.turno = p_dict.get('turno', '')
                    self.pecas_aprovadas.append(peca)
                
                for p_dict in dados.get('reprovadas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.motivos_reprovacao = p_dict.get('motivos_reprovacao', [])
                    peca.timestamp = p_dict.get('timestamp', '')
                    peca.data_inspecao = p_dict.get('data_inspecao', '')
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
                        peca.data_inspecao = p_dict.get('data_inspecao', '')
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
                    peca.data_inspecao = p_dict.get('data_inspecao', '')
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
    
    def editar_peca(self, id_peca: str, novo_peso: float, nova_cor: str, novo_comprimento: float) -> Tuple[bool, str]:
        """Edita uma peça existente"""
        try:
            id_peca = id_peca.upper().strip()
            
            # Buscar em peças aprovadas
            for peca in self.pecas_aprovadas:
                if peca.id_peca == id_peca:
                    peca.peso = novo_peso
                    peca.cor = nova_cor.lower()
                    peca.comprimento = novo_comprimento
                    
                    # Revalidar a peça
                    criterios = self.config.get('critérios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['critérios_qualidade'])
                    peca.validar(criterios)
                    
                    # Se foi reprovada após edição, mover para lista de reprovadas
                    if not peca.aprovada:
                        self.pecas_aprovadas.remove(peca)
                        self.pecas_reprovadas.append(peca)
                        # Remover da caixa atual se estiver lá
                        for p_caixa in self.caixa_atual.pecas:
                            if p_caixa.id_peca == id_peca:
                                self.caixa_atual.pecas.remove(p_caixa)
                                break
                    
                    self.salvar_dados()
                    ConfiguracaoSistema.registrar_log(f"Peça {id_peca} editada", "EDICAO")
                    return True, "Peça editada com sucesso"
            
            # Buscar em peças reprovadas
            for peca in self.pecas_reprovadas:
                if peca.id_peca == id_peca:
                    peca.peso = novo_peso
                    peca.cor = nova_cor.lower()
                    peca.comprimento = novo_comprimento
                    
                    # Revalidar a peça
                    criterios = self.config.get('critérios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['critérios_qualidade'])
                    peca.validar(criterios)
                    
                    # Se foi aprovada após edição, mover para lista de aprovadas
                    if peca.aprovada:
                        self.pecas_reprovadas.remove(peca)
                        self.pecas_aprovadas.append(peca)
                        # Adicionar à caixa atual
                        self.caixa_atual.adicionar_peca(peca)
                    
                    self.salvar_dados()
                    ConfiguracaoSistema.registrar_log(f"Peça {id_peca} editada", "EDICAO")
                    return True, "Peça editada com sucesso"
            
            return False, f"Peça {id_peca} não encontrada"
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao editar peça: {e}", "ERRO")
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
    
    def buscar_pecas_por_filtro(self, data_inicio: str = None, data_fim: str = None, 
                               usuario: str = None, status: str = None, turno: str = None) -> List[Peca]:
        """Busca peças com filtros avançados"""
        todas_pecas = self.pecas_aprovadas + self.pecas_reprovadas
        pecas_filtradas = []
        
        for peca in todas_pecas:
            # Filtro por data
            if data_inicio and data_fim:
                data_peca = datetime.strptime(peca.data_inspecao, "%Y-%m-%d")
                data_i = datetime.strptime(data_inicio, "%Y-%m-%d")
                data_f = datetime.strptime(data_fim, "%Y-%m-%d")
                if not (data_i <= data_peca <= data_f):
                    continue
            
            # Filtro por usuário
            if usuario and peca.usuario != usuario:
                continue
            
            # Filtro por status
            if status == "aprovadas" and not peca.aprovada:
                continue
            if status == "reprovadas" and peca.aprovada:
                continue
            
            # Filtro por turno
            if turno and peca.turno != turno:
                continue
            
            pecas_filtradas.append(peca)
        
        return pecas_filtradas
    
    def gerar_relatorio(self, data_inicio: str = None, data_fim: str = None, usuario: str = None) -> Dict:
        """Gera relatório completo - MELHORADO COM FILTROS"""
        # Aplicar filtros se fornecidos
        if data_inicio or data_fim or usuario:
            pecas_filtradas = self.buscar_pecas_por_filtro(data_inicio, data_fim, usuario)
            aprovadas_filtradas = [p for p in pecas_filtradas if p.aprovada]
            reprovadas_filtradas = [p for p in pecas_filtradas if not p.aprovada]
        else:
            pecas_filtradas = self.pecas_aprovadas + self.pecas_reprovadas
            aprovadas_filtradas = self.pecas_aprovadas
            reprovadas_filtradas = self.pecas_reprovadas
        
        total_pecas = len(pecas_filtradas)
        taxa_aprovacao = (len(aprovadas_filtradas) / total_pecas * 100) if total_pecas > 0 else 0
        
        # Estatísticas por turno
        estatisticas_turno = {}
        for peca in pecas_filtradas:
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
        for peca in reprovadas_filtradas:
            for motivo in peca.motivos_reprovacao:
                if 'Peso' in motivo:
                    motivos_reprovacao['Peso'] += 1
                elif 'Cor' in motivo:
                    motivos_reprovacao['Cor'] += 1
                elif 'Comprimento' in motivo:
                    motivos_reprovacao['Comprimento'] += 1
        
        return {
            'data_geracao': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'filtros_aplicados': {
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'usuario': usuario
            },
            'total_pecas_aprovadas': len(aprovadas_filtradas),
            'total_pecas_reprovadas': len(reprovadas_filtradas),
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
            'pecas_reprovadas_detalhes': [p.to_dict() for p in reprovadas_filtradas[-10:]],  # Últimas 10
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
        self.config = ConfiguracaoSistema.carregar_configuracao()
        
        # Configurar janela CORRIGIDA
        nome_sistema = self.config.get('sistema', {}).get('nome_sistema', 'Sistema de Controle de Qualidade Industrial')
        self.root.title(f"{nome_sistema} - Login")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
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
        
        nome_sistema = self.config.get('sistema', {}).get('nome_sistema', 'Sistema de Controle de Qualidade Industrial')
        titulo2 = ctk.CTkLabel(
            container,
            text=nome_sistema,
            font=ctk.CTkFont(size=16, weight="bold"),
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
        versao = self.config.get('sistema', {}).get('versao', '2.2')
        versao_label = ctk.CTkLabel(
            container,
            text=f"v{versao} - Sistema Corrigido e Melhorado",
            font=ctk.CTkFont(size=10),
            text_color="#e0e0e0"
        )
        versao_label.pack(pady=10)
    
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
        self.auth = SistemaAutenticacao()
        self.config = ConfiguracaoSistema.carregar_configuracao()
        
        # Configurar janela CORRIGIDA
        nome_sistema = self.config.get('sistema', {}).get('nome_sistema', 'Sistema de Controle de Qualidade Industrial')
        self.root.title(f"{nome_sistema} - {info_usuario['nome_completo']}")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.centralizar_janela()
        
        self.frame_principal = ctk.CTkFrame(root, fg_color="transparent")
        self.frame_principal.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.criar_menu_principal()
    
    def centralizar_janela(self):
        """Centraliza a janela na tela - CORRIGIDA"""
        self.root.update_idletasks()
        width = 1200
        height = 800
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def criar_menu_principal(self):
        """Cria o menu principal - MELHORADO COM PERMISSÕES"""
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
        
        nome_sistema = self.config.get('sistema', {}).get('nome_sistema', 'Sistema de Controle de Qualidade Industrial')
        ctk.CTkLabel(
            titulo_frame,
            text=nome_sistema,
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
        
        nivel = self.info_usuario['nivel'].title()
        ctk.CTkLabel(
            user_frame,
            text=f"📋 {nivel} | Turno: {self.obter_turno_atual()}",
            font=ctk.CTkFont(size=10),
            text_color="#e0e0e0",
            justify="right"
        ).pack(anchor="e")
        
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
        total_pecas = len(self.db.pecas_aprovadas) + len(self.db.pecas_reprovadas)
        taxa_aprovacao = (len(self.db.pecas_aprovadas) / total_pecas * 100) if total_pecas > 0 else 0
        
        metrics = [
            ("✅ Peças Aprovadas", str(len(self.db.pecas_aprovadas)), "#2ecc71"),
            ("❌ Peças Reprovadas", str(len(self.db.pecas_reprovadas)), "#e74c3c"),
            ("📦 Caixas Completas", str(len(self.db.caixas_fechadas)), "#3498db"),
            ("📊 Taxa de Aprovação", f"{taxa_aprovacao:.1f}%", "#9b59b6"),
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
        """Cria o menu de opções - MELHORADO COM PERMISSÕES"""
        menu_frame = ctk.CTkFrame(self.frame_principal)
        menu_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        titulo_menu = ctk.CTkLabel(
            menu_frame,
            text="Menu Principal - Escolha uma operação:",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        titulo_menu.pack(pady=20)
        
        # Opções principais (disponíveis para todos)
        opcoes_principais = [
            ("📝 Cadastrar Nova Peça", self.tela_cadastrar_peca, "#1f538d"),
            ("📋 Listar Peças Inspecionadas", self.tela_listar_pecas, "#2980b9"),
            ("🔧 Gerenciar Peças (CRUD)", self.tela_gerenciar_pecas, "#e67e22"),
            ("📦 Gerenciar Caixas", self.tela_listar_caixas, "#27ae60"),
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
        
        # Separador para Relatórios e Ferramentas (apenas admin)
        if self.info_usuario['nivel'] == 'administrador':
            ctk.CTkLabel(
                menu_frame,
                text="Relatórios e Ferramentas Administrativas",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=(20, 10))
            
            # Opções administrativas
            opcoes_admin = [
                ("📊 Relatórios Avançados", self.tela_relatorios_avancados, "#8e44ad"),
                ("👥 Gestão de Usuários", self.tela_gestao_usuarios, "#34495e"),
                ("⚙️ Configurações do Sistema", self.tela_configuracoes, "#16a085"),
            ]
            
            for texto, comando, cor in opcoes_admin:
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
        
        # Botão sair em vermelho
        ctk.CTkButton(
            menu_frame,
            text="🚪 Sair do Sistema",
            width=400,
            height=45,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.root.quit,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            corner_radius=8
        ).pack(pady=20)
    
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

    # ... (mantenha as funções existentes como tela_cadastrar_peca, tela_gerenciar_pecas, etc.)
    
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
        """Tela de listagem de peças - MELHORADA COM FILTROS"""
        self.limpar_tela()
        self.criar_header("📋 Peças Inspecionadas")
        
        main_frame = ctk.CTkFrame(self.frame_principal)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame de filtros
        filtros_frame = ctk.CTkFrame(main_frame)
        filtros_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            filtros_frame,
            text="Filtros:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10)
        
        # Filtro por data
        ctk.CTkLabel(filtros_frame, text="Data:").pack(side="left", padx=(20, 5))
        entry_data = ctk.CTkEntry(
            filtros_frame,
            width=120,
            height=35,
            placeholder_text="DD/MM/AAAA"
        )
        entry_data.pack(side="left", padx=5)
        
        # Filtro por status
        ctk.CTkLabel(filtros_frame, text="Status:").pack(side="left", padx=(20, 5))
        combo_status = ctk.CTkComboBox(
            filtros_frame,
            width=120,
            height=35,
            values=["Todos", "Aprovadas", "Reprovadas"]
        )
        combo_status.set("Todos")
        combo_status.pack(side="left", padx=5)
        
        # Botão aplicar filtros
        btn_aplicar = ctk.CTkButton(
            filtros_frame,
            text="Aplicar Filtros",
            width=120,
            height=35,
            command=lambda: self.aplicar_filtros_lista(entry_data.get(), combo_status.get(), tabview)
        )
        btn_aplicar.pack(side="left", padx=10)
        
        # Botão limpar filtros
        btn_limpar = ctk.CTkButton(
            filtros_frame,
            text="Limpar Filtros",
            width=120,
            height=35,
            command=lambda: self.aplicar_filtros_lista("", "Todos", tabview),
            fg_color="#95a5a6"
        )
        btn_limpar.pack(side="left", padx=5)
        
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
    
    
    def tela_gestao_usuarios(self):
        """Tela de gestão de usuários - CORRIGIDA E MELHORADA"""
        if self.info_usuario['nivel'] != 'administrador':
            messagebox.showerror("Acesso Negado", "Apenas administradores podem acessar esta funcionalidade!")
            return
        
        self.limpar_tela()
        self.criar_header("👥 Gestão de Usuários")
        
        main_frame = ctk.CTkFrame(self.frame_principal)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame de botões superiores
        botoes_superiores = ctk.CTkFrame(main_frame)
        botoes_superiores.pack(fill="x", padx=10, pady=10)
        
        # Botão para novo usuário
        btn_novo = ctk.CTkButton(
            botoes_superiores,
            text="➕ Novo Usuário",
            width=150,
            height=40,
            command=self.criar_novo_usuario,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#27ae60",
            hover_color="#219a52"
        )
        btn_novo.pack(side="left", padx=5)
        
        # Botão para recarregar lista
        btn_recarregar = ctk.CTkButton(
            botoes_superiores,
            text="🔄 Recarregar",
            width=120,
            height=40,
            command=lambda: self.atualizar_lista_usuarios(scroll_frame),
            font=ctk.CTkFont(size=13),
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        btn_recarregar.pack(side="left", padx=5)
        
        # Frame da lista de usuários
        lista_frame = ctk.CTkFrame(main_frame)
        lista_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        ctk.CTkLabel(
            lista_frame,
            text="Lista de Usuários do Sistema:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # Container scrollable para a lista
        scroll_frame = ctk.CTkScrollableFrame(lista_frame, height=400)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Carregar lista inicial
        self.atualizar_lista_usuarios(scroll_frame)
        
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
    
    def atualizar_lista_usuarios(self, scroll_frame: ctk.CTkScrollableFrame):
        """Atualiza a lista de usuários no frame"""
        # Limpar frame
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        
        # Obter lista de usuários
        usuarios = self.auth.listar_usuarios()
        
        if not usuarios:
            ctk.CTkLabel(
                scroll_frame,
                text="Nenhum usuário cadastrado.",
                font=ctk.CTkFont(size=14),
                text_color="#666666"
            ).pack(pady=50)
            return
        
        # Cabeçalho
        header_frame = ctk.CTkFrame(scroll_frame, fg_color="#34495e")
        header_frame.pack(fill="x", pady=(0, 10))
        
        headers = ["Usuário", "Nome Completo", "Nível", "Status", "Último Login", "Ações"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="white"
            ).grid(row=0, column=i, padx=8, pady=8, sticky="w")
            header_frame.columnconfigure(i, weight=1 if i < len(headers)-1 else 0)
        
        # Lista de usuários
        for idx, usuario in enumerate(usuarios):
            row_frame = ctk.CTkFrame(scroll_frame, fg_color="#f8f9fa" if idx % 2 == 0 else "white")
            row_frame.pack(fill="x", pady=2)
            
            # Dados do usuário
            dados = [
                usuario['usuario'],
                usuario['nome_completo'],
                usuario['nivel'].title(),
                "✅ Ativo" if usuario['ativo'] else "❌ Inativo",
                usuario['ultimo_login'] if usuario['ultimo_login'] != 'Nunca' else 'Nunca'
            ]
            
            for i, dado in enumerate(dados):
                ctk.CTkLabel(
                    row_frame,
                    text=dado,
                    font=ctk.CTkFont(size=10),
                    text_color="#2c3e50"
                ).grid(row=0, column=i, padx=8, pady=6, sticky="w")
                row_frame.columnconfigure(i, weight=1 if i < len(dados)-1 else 0)
            
            # Botões de ação
            btn_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            btn_frame.grid(row=0, column=5, padx=8, pady=6, sticky="e")
            
            # Botão editar
            ctk.CTkButton(
                btn_frame,
                text="✏️ Editar",
                width=80,
                height=30,
                command=lambda u=usuario: self.editar_usuario(u),
                font=ctk.CTkFont(size=10),
                fg_color="#3498db",
                hover_color="#2980b9"
            ).pack(side="left", padx=2)
            
            # Botão excluir (não mostrar para admin principal)
            if usuario['usuario'] != 'admin':
                ctk.CTkButton(
                    btn_frame,
                    text="🗑️ Excluir",
                    width=80,
                    height=30,
                    command=lambda u=usuario: self.excluir_usuario(u),
                    font=ctk.CTkFont(size=10),
                    fg_color="#e74c3c",
                    hover_color="#c0392b"
                ).pack(side="left", padx=2)
    
    def criar_novo_usuario(self):
        """Cria interface para novo usuário - MELHORADA"""
        janela = ctk.CTkToplevel(self.root)
        janela.title("Cadastrar Novo Usuário")
        janela.geometry("500x600")
        janela.transient(self.root)
        janela.grab_set()
        janela.resizable(False, False)
        
        # Centralizar janela
        janela.update_idletasks()
        width = 500
        height = 600
        x = (janela.winfo_screenwidth() // 2) - (width // 2)
        y = (janela.winfo_screenheight() // 2) - (height // 2)
        janela.geometry(f'{width}x{height}+{x}+{y}')
        
        frame = ctk.CTkFrame(janela)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame,
            text="Cadastrar Novo Usuário",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        
        # Campos
        campos_frame = ctk.CTkFrame(frame, fg_color="transparent")
        campos_frame.pack(fill="both", expand=True, pady=10)
        
        # Usuário
        ctk.CTkLabel(campos_frame, text="Usuário*:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        entry_usuario = ctk.CTkEntry(campos_frame, width=400, height=45, placeholder_text="Nome de usuário para login")
        entry_usuario.pack(fill="x", pady=5)
        entry_usuario.focus()
        
        # Senha
        ctk.CTkLabel(campos_frame, text="Senha*:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        entry_senha = ctk.CTkEntry(campos_frame, width=400, height=45, show="●", placeholder_text="Mínimo 4 caracteres")
        entry_senha.pack(fill="x", pady=5)
        
        # Nome Completo
        ctk.CTkLabel(campos_frame, text="Nome Completo*:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        entry_nome = ctk.CTkEntry(campos_frame, width=400, height=45, placeholder_text="Nome completo do usuário")
        entry_nome.pack(fill="x", pady=5)
        
        # Nível
        ctk.CTkLabel(campos_frame, text="Nível de Acesso*:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        combo_nivel = ctk.CTkComboBox(campos_frame, width=400, height=45, values=["operador", "administrador"])
        combo_nivel.set("operador")
        combo_nivel.pack(fill="x", pady=5)
        
        # Status
        var_ativo = ctk.BooleanVar(value=True)
        switch_ativo = ctk.CTkSwitch(
            campos_frame, 
            text="Usuário Ativo", 
            variable=var_ativo,
            font=ctk.CTkFont(size=14)
        )
        switch_ativo.pack(anchor="w", pady=15)
        
        def salvar_usuario():
            usuario = entry_usuario.get().strip()
            senha = entry_senha.get()
            nome = entry_nome.get().strip()
            nivel = combo_nivel.get()
            ativo = var_ativo.get()
            
            # Validações
            if not usuario or not senha or not nome:
                messagebox.showerror("Erro", "Todos os campos marcados com * são obrigatórios!")
                return
            
            if len(senha) < 4:
                messagebox.showerror("Erro", "A senha deve ter pelo menos 4 caracteres!")
                return
            
            sucesso, mensagem = self.auth.criar_usuario(usuario, senha, nome, nivel)
            if sucesso:
                messagebox.showinfo("Sucesso", mensagem)
                janela.destroy()
                self.tela_gestao_usuarios()  # Recarregar a tela
            else:
                messagebox.showerror("Erro", mensagem)
        
        # Botões
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Salvar Usuário",
            width=200,
            height=50,
            command=salvar_usuario,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27ae60",
            hover_color="#219a52"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Cancelar",
            width=200,
            height=50,
            command=janela.destroy,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#95a5a6",
            hover_color="#7f8c8d"
        ).pack(side="left", padx=10)
    
    def editar_usuario(self, usuario_data: Dict):
        """Edita um usuário existente - MELHORADA"""
        janela = ctk.CTkToplevel(self.root)
        janela.title(f"Editar Usuário - {usuario_data['usuario']}")
        janela.geometry("500x650")
        janela.transient(self.root)
        janela.grab_set()
        janela.resizable(False, False)
        
        # Centralizar janela
        janela.update_idletasks()
        width = 500
        height = 650
        x = (janela.winfo_screenwidth() // 2) - (width // 2)
        y = (janela.winfo_screenheight() // 2) - (height // 2)
        janela.geometry(f'{width}x{height}+{x}+{y}')
        
        frame = ctk.CTkFrame(janela)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame,
            text=f"Editar Usuário: {usuario_data['usuario']}",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        
        # Campos
        campos_frame = ctk.CTkFrame(frame, fg_color="transparent")
        campos_frame.pack(fill="both", expand=True, pady=10)
        
        # Usuário
        ctk.CTkLabel(campos_frame, text="Usuário*:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        entry_usuario = ctk.CTkEntry(campos_frame, width=400, height=45)
        entry_usuario.insert(0, usuario_data['usuario'])
        entry_usuario.pack(fill="x", pady=5)
        
        # Nome Completo
        ctk.CTkLabel(campos_frame, text="Nome Completo*:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        entry_nome = ctk.CTkEntry(campos_frame, width=400, height=45)
        entry_nome.insert(0, usuario_data['nome_completo'])
        entry_nome.pack(fill="x", pady=5)
        
        # Nível
        ctk.CTkLabel(campos_frame, text="Nível de Acesso*:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        combo_nivel = ctk.CTkComboBox(campos_frame, width=400, height=45, values=["operador", "administrador"])
        combo_nivel.set(usuario_data['nivel'])
        combo_nivel.pack(fill="x", pady=5)
        
        # Status
        var_ativo = ctk.BooleanVar(value=usuario_data['ativo'])
        switch_ativo = ctk.CTkSwitch(
            campos_frame, 
            text="Usuário Ativo", 
            variable=var_ativo,
            font=ctk.CTkFont(size=14)
        )
        switch_ativo.pack(anchor="w", pady=15)
        
        # Frame para redefinir senha
        senha_frame = ctk.CTkFrame(campos_frame)
        senha_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(senha_frame, text="Redefinir Senha:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(senha_frame, text="Deixe em branco para manter a senha atual", font=ctk.CTkFont(size=11), text_color="#666666").pack(anchor="w")
        entry_nova_senha = ctk.CTkEntry(senha_frame, width=400, height=45, show="●", placeholder_text="Nova senha (mínimo 4 caracteres)")
        entry_nova_senha.pack(fill="x", pady=5)
        
        def salvar_edicao():
            usuario_novo = entry_usuario.get().strip()
            nome = entry_nome.get().strip()
            nivel = combo_nivel.get()
            ativo = var_ativo.get()
            nova_senha = entry_nova_senha.get()
            
            # Validações
            if not usuario_novo or not nome:
                messagebox.showerror("Erro", "Usuário e nome são obrigatórios!")
                return
            
            if nova_senha and len(nova_senha) < 4:
                messagebox.showerror("Erro", "A senha deve ter pelo menos 4 caracteres!")
                return
            
            # Primeiro, editar os dados básicos
            sucesso, mensagem = self.auth.editar_usuario(
                usuario_data['usuario'], usuario_novo, nome, nivel, ativo
            )
            
            if not sucesso:
                messagebox.showerror("Erro", mensagem)
                return
            
            # Se foi fornecida uma nova senha, redefinir
            if nova_senha:
                sucesso_senha, mensagem_senha = self.auth.redefinir_senha(usuario_novo, nova_senha)
                if not sucesso_senha:
                    messagebox.showwarning("Aviso", f"Dados salvos, mas erro na senha: {mensagem_senha}")
                else:
                    messagebox.showinfo("Sucesso", "Usuário e senha atualizados com sucesso!")
            else:
                messagebox.showinfo("Sucesso", "Usuário atualizado com sucesso!")
            
            janela.destroy()
            self.tela_gestao_usuarios()  # Recarregar a tela
        
        # Botões
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Salvar Alterações",
            width=200,
            height=50,
            command=salvar_edicao,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3498db",
            hover_color="#2980b9"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Cancelar",
            width=200,
            height=50,
            command=janela.destroy,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#95a5a6",
            hover_color="#7f8c8d"
        ).pack(side="left", padx=10)
    
    def excluir_usuario(self, usuario_data: Dict):
        """Exclui um usuário - MELHORADA"""
        if usuario_data['usuario'] == self.usuario:
            messagebox.showerror("Erro", "Você não pode excluir seu próprio usuário!")
            return
        
        resposta = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o usuário {usuario_data['usuario']}?\n\n"
            f"Nome: {usuario_data['nome_completo']}\n"
            f"Nível: {usuario_data['nivel'].title()}\n\n"
            f"⚠️  ESTA AÇÃO NÃO PODE SER DESFEITA!"
        )
        
        if resposta:
            sucesso, mensagem = self.auth.excluir_usuario(usuario_data['usuario'])
            if sucesso:
                messagebox.showinfo("Sucesso", mensagem)
                self.tela_gestao_usuarios()  # Recarregar a tela
            else:
                messagebox.showerror("Erro", mensagem)

    def tela_configuracoes(self):
        """Tela de configurações do sistema - MELHORADA COM NOME DO SISTEMA"""
        if self.info_usuario['nivel'] != 'administrador':
            messagebox.showerror("Acesso Negado", "Apenas administradores podem acessar esta funcionalidade!")
            return
        
        self.limpar_tela()
        self.criar_header("⚙️ Configurações do Sistema")
        
        content_frame = ctk.CTkFrame(self.frame_principal)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Abas para diferentes configurações
        tabview = ctk.CTkTabview(content_frame)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Aba de sistema
        tab_sistema = tabview.add("🏭 Sistema")
        self.criar_config_sistema(tab_sistema)
        
        # Aba de critérios de qualidade
        tab_criterios = tabview.add("🎯 Critérios de Qualidade")
        self.criar_config_criterios(tab_criterios)
        
        # Aba de backup
        tab_backup = tabview.add("💾 Backup")
        self.criar_config_backup(tab_backup)
        
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
    
    def criar_config_sistema(self, parent):
        """Cria interface de configuração do sistema - MELHORADA"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame,
            text="Configurações Gerais do Sistema:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # Nome do sistema
        ctk.CTkLabel(frame, text="Nome do Sistema:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        entry_nome_sistema = ctk.CTkEntry(frame, width=400, height=45)
        nome_atual = self.config.get('sistema', {}).get('nome_sistema', 'Sistema de Controle de Qualidade Industrial')
        entry_nome_sistema.insert(0, nome_atual)
        entry_nome_sistema.pack(anchor="w", pady=5)
        
        # Capacidade da caixa
        ctk.CTkLabel(frame, text="Capacidade de Peças por Caixa:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        entry_capacidade = ctk.CTkEntry(frame, width=100)
        entry_capacidade.insert(0, str(self.config.get('capacidade_caixa', 10)))
        entry_capacidade.pack(anchor="w", pady=5)
        
        def salvar_config_sistema():
            try:
                # Atualizar configurações
                if 'sistema' not in self.config:
                    self.config['sistema'] = {}
                
                self.config['sistema']['nome_sistema'] = entry_nome_sistema.get().strip()
                self.config['capacidade_caixa'] = int(entry_capacidade.get())
                
                ConfiguracaoSistema.salvar_configuracao(self.config)
                
                messagebox.showinfo("Sucesso", "Configurações do sistema atualizadas!\n\nO sistema será reiniciado para aplicar as mudanças.")
                
                # Reiniciar aplicação
                self.root.destroy()
                import os
                import sys
                os.execl(sys.executable, sys.executable, *sys.argv)
                
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
    
    def criar_config_criterios(self, parent):
        """Cria interface de configuração de critérios"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        criterios = self.config.get('critérios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['critérios_qualidade'])
        
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
                
                self.config['critérios_qualidade'] = novos_criterios
                ConfiguracaoSistema.salvar_configuracao(self.config)
                
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
    
    def criar_config_backup(self, parent):
        """Cria interface de configuração de backup"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame,
            text="Configurações de Backup:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # Backup automático
        var_backup = ctk.BooleanVar(value=self.config.get('auto_backup', True))
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
        entry_intervalo.insert(0, str(self.config.get('backup_interval_hours', 24)))
        entry_intervalo.pack(anchor="w", pady=5)
        
        def salvar_config_backup():
            try:
                self.config['auto_backup'] = var_backup.get()
                self.config['backup_interval_hours'] = int(entry_intervalo.get())
                
                ConfiguracaoSistema.salvar_configuracao(self.config)
                
                messagebox.showinfo("Sucesso", "Configurações de backup atualizadas!")
                
            except ValueError:
                messagebox.showerror("Erro", "Por favor, insira valores numéricos válidos.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")
        
        ctk.CTkButton(
            frame,
            text="💾 Salvar Configurações",
            width=200,
            height=45,
            command=salvar_config_backup,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3498db"
        ).pack(pady=30)
        
        # Botão para backup manual
        ctk.CTkButton(
            frame,
            text="🔧 Fazer Backup Manual",
            width=200,
            height=45,
            command=self.db.fazer_backup,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#f39c12"
        ).pack(pady=10)

    # ... (mantenha as outras funções existentes)

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
    config = ConfiguracaoSistema.carregar_configuracao()
    nome_sistema = config.get('sistema', {}).get('nome_sistema', 'Sistema de Controle de Qualidade Industrial')
    versao = config.get('sistema', {}).get('versao', '2.2')
    
    print("\n" + "="*70)
    print(f"  🏭 {nome_sistema} v{versao}")
    print("  📊 Automação de Inspeção de Peças - Linha de Montagem")
    print("  🔧 Versão com Gestão de Usuários Corrigida")
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
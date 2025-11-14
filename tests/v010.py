"""
Sistema de Controle de Qualidade Industrial
Versão 1.0 - Automação de Inspeção de Peças
Desenvolvido com Python + CustomTkinter
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import json
import os
from datetime import datetime
from typing import List, Dict
import csv

# Configurações do CustomTkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class Peca:
    """Classe que representa uma peça"""
    
    def __init__(self, id_peca: str, peso: float, cor: str, comprimento: float):
        self.id_peca = id_peca
        self.peso = peso
        self.cor = cor.lower()
        self.comprimento = comprimento
        self.timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.aprovada = False
        self.motivos_reprovacao = []
        
    def validar(self) -> bool:
        """Valida a peça conforme os critérios de qualidade"""
        self.motivos_reprovacao = []
        
        # Validação de peso
        if not (95 <= self.peso <= 105):
            self.motivos_reprovacao.append(f"Peso fora do padrão: {self.peso}g (esperado: 95-105g)")
        
        # Validação de cor
        if self.cor not in ['azul', 'verde']:
            self.motivos_reprovacao.append(f"Cor não aprovada: {self.cor} (esperado: azul ou verde)")
        
        # Validação de comprimento
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
        
    def adicionar_peca(self, peca: Peca) -> bool:
        """Adiciona uma peça à caixa se houver espaço"""
        if len(self.pecas) < self.CAPACIDADE_MAXIMA:
            self.pecas.append(peca)
            if len(self.pecas) == self.CAPACIDADE_MAXIMA:
                self.fechar()
            return True
        return False
    
    def fechar(self):
        """Fecha a caixa"""
        self.data_fechamento = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
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
            'quantidade_pecas': len(self.pecas)
        }


class SistemaControleQualidade:
    """Sistema principal de controle de qualidade"""
    
    ARQUIVO_DADOS = 'dados_controle_qualidade.json'
    
    def __init__(self):
        self.pecas_aprovadas: List[Peca] = []
        self.pecas_reprovadas: List[Peca] = []
        self.caixas_fechadas: List[Caixa] = []
        self.caixa_atual: Caixa = Caixa(1)
        self.carregar_dados()
    
    def inspecionar_peca(self, id_peca: str, peso: float, cor: str, comprimento: float) -> tuple:
        """Inspeciona uma peça e a adiciona ao sistema"""
        peca = Peca(id_peca, peso, cor, comprimento)
        
        if peca.validar():
            self.pecas_aprovadas.append(peca)
            
            if not self.caixa_atual.adicionar_peca(peca):
                # Caixa cheia, criar nova
                self.caixas_fechadas.append(self.caixa_atual)
                self.caixa_atual = Caixa(len(self.caixas_fechadas) + 1)
                self.caixa_atual.adicionar_peca(peca)
            
            # Verifica se a caixa atual ficou cheia
            if self.caixa_atual.esta_cheia():
                self.caixas_fechadas.append(self.caixa_atual)
                self.caixa_atual = Caixa(len(self.caixas_fechadas) + 1)
            
            self.salvar_dados()
            return (True, "✅ Peça APROVADA e adicionada à caixa!")
        else:
            self.pecas_reprovadas.append(peca)
            self.salvar_dados()
            motivos = "\n".join([f"• {m}" for m in peca.motivos_reprovacao])
            return (False, f"❌ Peça REPROVADA\n\nMotivos:\n{motivos}")
    
    def gerar_relatorio_completo(self) -> Dict:
        """Gera relatório completo do sistema"""
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
    
    def salvar_dados(self):
        """Salva os dados em arquivo JSON"""
        dados = {
            'pecas_aprovadas': [p.to_dict() for p in self.pecas_aprovadas],
            'pecas_reprovadas': [p.to_dict() for p in self.pecas_reprovadas],
            'caixas_fechadas': [c.to_dict() for c in self.caixas_fechadas],
            'caixa_atual': self.caixa_atual.to_dict()
        }
        
        try:
            with open(self.ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
    
    def carregar_dados(self):
        """Carrega os dados do arquivo JSON"""
        if os.path.exists(self.ARQUIVO_DADOS):
            try:
                with open(self.ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                # Reconstruir peças aprovadas
                for p_dict in dados.get('pecas_aprovadas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'])
                    peca.aprovada = p_dict['aprovada']
                    peca.timestamp = p_dict['timestamp']
                    self.pecas_aprovadas.append(peca)
                
                # Reconstruir peças reprovadas
                for p_dict in dados.get('pecas_reprovadas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'])
                    peca.aprovada = p_dict['aprovada']
                    peca.motivos_reprovacao = p_dict['motivos_reprovacao']
                    peca.timestamp = p_dict['timestamp']
                    self.pecas_reprovadas.append(peca)
                
                # Reconstruir caixas fechadas
                for c_dict in dados.get('caixas_fechadas', []):
                    caixa = Caixa(c_dict['numero'])
                    caixa.data_fechamento = c_dict['data_fechamento']
                    for p_dict in c_dict['pecas']:
                        peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'])
                        peca.aprovada = p_dict['aprovada']
                        peca.timestamp = p_dict['timestamp']
                        caixa.pecas.append(peca)
                    self.caixas_fechadas.append(caixa)
                
                # Reconstruir caixa atual
                c_atual = dados.get('caixa_atual', {})
                self.caixa_atual = Caixa(c_atual.get('numero', len(self.caixas_fechadas) + 1))
                for p_dict in c_atual.get('pecas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'])
                    peca.aprovada = p_dict['aprovada']
                    peca.timestamp = p_dict['timestamp']
                    self.caixa_atual.pecas.append(peca)
                
            except Exception as e:
                print(f"Erro ao carregar dados: {e}")
    
    def limpar_dados(self):
        """Limpa todos os dados do sistema"""
        self.pecas_aprovadas = []
        self.pecas_reprovadas = []
        self.caixas_fechadas = []
        self.caixa_atual = Caixa(1)
        
        if os.path.exists(self.ARQUIVO_DADOS):
            os.remove(self.ARQUIVO_DADOS)
    
    def exportar_relatorio_json(self, caminho: str):
        """Exporta o relatório em formato JSON"""
        relatorio = self.gerar_relatorio_completo()
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
    
    def exportar_relatorio_csv(self, caminho: str):
        """Exporta o relatório em formato CSV"""
        with open(caminho, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            
            # Cabeçalho
            writer.writerow(['ID', 'Peso (g)', 'Cor', 'Comprimento (cm)', 'Status', 'Data/Hora', 'Motivos Reprovação'])
            
            # Peças aprovadas
            for peca in self.pecas_aprovadas:
                writer.writerow([
                    peca.id_peca,
                    peca.peso,
                    peca.cor,
                    peca.comprimento,
                    'APROVADA',
                    peca.timestamp,
                    ''
                ])
            
            # Peças reprovadas
            for peca in self.pecas_reprovadas:
                motivos = ' | '.join(peca.motivos_reprovacao)
                writer.writerow([
                    peca.id_peca,
                    peca.peso,
                    peca.cor,
                    peca.comprimento,
                    'REPROVADA',
                    peca.timestamp,
                    motivos
                ])


class InterfaceGrafica:
    """Interface gráfica do sistema"""
    
    def __init__(self):
        self.sistema = SistemaControleQualidade()
        self.root = ctk.CTk()
        self.root.title("Sistema de Controle de Qualidade Industrial v1.0")
        self.root.geometry("1200x800")
        
        self.criar_interface()
        self.atualizar_dashboard()
    
    def criar_interface(self):
        """Cria a interface gráfica"""
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== HEADER =====
        header_frame = ctk.CTkFrame(main_frame, fg_color="#1f538d")
        header_frame.pack(fill="x", padx=5, pady=5)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🏭 Sistema de Controle de Qualidade Industrial",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        title_label.pack(pady=15)
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Automação de Inspeção de Peças - Linha de Montagem",
            font=ctk.CTkFont(size=12),
            text_color="#e0e0e0"
        )
        subtitle_label.pack(pady=(0, 15))
        
        # ===== DASHBOARD =====
        dashboard_frame = ctk.CTkFrame(main_frame)
        dashboard_frame.pack(fill="x", padx=5, pady=5)
        
        # Cards do dashboard
        self.card_aprovadas = self.criar_card(dashboard_frame, "Peças Aprovadas", "0", "#2ecc71")
        self.card_aprovadas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.card_reprovadas = self.criar_card(dashboard_frame, "Peças Reprovadas", "0", "#e74c3c")
        self.card_reprovadas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.card_caixas = self.criar_card(dashboard_frame, "Caixas Completas", "0", "#3498db")
        self.card_caixas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # ===== ÁREA DE CONTEÚDO =====
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Coluna esquerda - Formulário
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        form_title = ctk.CTkLabel(
            left_frame,
            text="📋 Inspeção de Peça",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        form_title.pack(pady=10)
        
        # Campos do formulário
        form_frame = ctk.CTkFrame(left_frame)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ID da Peça
        ctk.CTkLabel(form_frame, text="ID da Peça:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.entry_id = ctk.CTkEntry(form_frame, placeholder_text="Ex: PCA001", height=35)
        self.entry_id.pack(fill="x", padx=10, pady=(5, 10))
        
        # Peso
        ctk.CTkLabel(form_frame, text="Peso (g) - Padrão: 95g a 105g:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.entry_peso = ctk.CTkEntry(form_frame, placeholder_text="Ex: 100", height=35)
        self.entry_peso.pack(fill="x", padx=10, pady=(5, 10))
        
        # Cor
        ctk.CTkLabel(form_frame, text="Cor - Aprovadas: Azul ou Verde:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.combo_cor = ctk.CTkComboBox(
            form_frame,
            values=["azul", "verde", "vermelho", "amarelo", "preto", "branco"],
            height=35
        )
        self.combo_cor.set("azul")
        self.combo_cor.pack(fill="x", padx=10, pady=(5, 10))
        
        # Comprimento
        ctk.CTkLabel(form_frame, text="Comprimento (cm) - Padrão: 10cm a 20cm:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.entry_comprimento = ctk.CTkEntry(form_frame, placeholder_text="Ex: 15", height=35)
        self.entry_comprimento.pack(fill="x", padx=10, pady=(5, 10))
        
        # Botão de inspeção
        btn_inspecionar = ctk.CTkButton(
            form_frame,
            text="🔍 Inspecionar Peça",
            command=self.inspecionar_peca,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color="#1f538d",
            hover_color="#174270"
        )
        btn_inspecionar.pack(fill="x", padx=10, pady=20)
        
        # Coluna direita - Caixa Atual e Ações
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Caixa Atual
        caixa_title = ctk.CTkLabel(
            right_frame,
            text="📦 Caixa Atual",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        caixa_title.pack(pady=10)
        
        caixa_info_frame = ctk.CTkFrame(right_frame)
        caixa_info_frame.pack(fill="x", padx=10, pady=5)
        
        self.label_caixa_numero = ctk.CTkLabel(
            caixa_info_frame,
            text="Caixa #1",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.label_caixa_numero.pack(pady=5)
        
        self.label_capacidade = ctk.CTkLabel(
            caixa_info_frame,
            text="Capacidade: 0/10",
            font=ctk.CTkFont(size=12)
        )
        self.label_capacidade.pack(pady=5)
        
        self.progress_caixa = ctk.CTkProgressBar(caixa_info_frame, width=300)
        self.progress_caixa.set(0)
        self.progress_caixa.pack(pady=10)
        
        # Lista de peças na caixa
        self.text_caixa = ctk.CTkTextbox(right_frame, height=200, font=ctk.CTkFont(size=11))
        self.text_caixa.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Botões de ação
        acoes_frame = ctk.CTkFrame(right_frame)
        acoes_frame.pack(fill="x", padx=10, pady=10)
        
        btn_relatorio = ctk.CTkButton(
            acoes_frame,
            text="📊 Ver Relatório Completo",
            command=self.mostrar_relatorio,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            fg_color="#3498db"
        )
        btn_relatorio.pack(fill="x", pady=5)
        
        btn_exportar_json = ctk.CTkButton(
            acoes_frame,
            text="💾 Exportar Relatório (JSON)",
            command=self.exportar_json,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            fg_color="#2ecc71"
        )
        btn_exportar_json.pack(fill="x", pady=5)
        
        btn_exportar_csv = ctk.CTkButton(
            acoes_frame,
            text="📄 Exportar Relatório (CSV)",
            command=self.exportar_csv,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            fg_color="#27ae60"
        )
        btn_exportar_csv.pack(fill="x", pady=5)
        
        btn_limpar = ctk.CTkButton(
            acoes_frame,
            text="🗑️ Limpar Todos os Dados",
            command=self.limpar_dados,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            fg_color="#e74c3c"
        )
        btn_limpar.pack(fill="x", pady=5)
    
    def criar_card(self, parent, titulo, valor, cor):
        """Cria um card para o dashboard"""
        card = ctk.CTkFrame(parent, fg_color=cor)
        
        titulo_label = ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        titulo_label.pack(pady=(15, 5))
        
        valor_label = ctk.CTkLabel(
            card,
            text=valor,
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="white"
        )
        valor_label.pack(pady=(5, 15))
        
        # Guardar referência ao label de valor
        card.valor_label = valor_label
        
        return card
    
    def atualizar_dashboard(self):
        """Atualiza os valores do dashboard"""
        self.card_aprovadas.valor_label.configure(text=str(len(self.sistema.pecas_aprovadas)))
        self.card_reprovadas.valor_label.configure(text=str(len(self.sistema.pecas_reprovadas)))
        self.card_caixas.valor_label.configure(text=str(len(self.sistema.caixas_fechadas)))
        
        # Atualizar caixa atual
        self.label_caixa_numero.configure(text=f"Caixa #{self.sistema.caixa_atual.numero}")
        capacidade = len(self.sistema.caixa_atual.pecas)
        self.label_capacidade.configure(text=f"Capacidade: {capacidade}/10")
        self.progress_caixa.set(capacidade / 10)
        
        # Atualizar lista de peças na caixa
        self.text_caixa.delete("1.0", "end")
        if self.sistema.caixa_atual.pecas:
            for i, peca in enumerate(self.sistema.caixa_atual.pecas, 1):
                self.text_caixa.insert("end", f"{i}. {peca.id_peca} - {peca.peso}g | {peca.cor} | {peca.comprimento}cm\n")
        else:
            self.text_caixa.insert("end", "Caixa vazia\n")
    
    def inspecionar_peca(self):
        """Processa a inspeção de uma peça"""
        try:
            id_peca = self.entry_id.get().strip()
            peso = float(self.entry_peso.get().strip())
            cor = self.combo_cor.get()
            comprimento = float(self.entry_comprimento.get().strip())
            
            if not id_peca:
                messagebox.showerror("Erro", "Por favor, insira o ID da peça!")
                return
            
            aprovada, mensagem = self.sistema.inspecionar_peca(id_peca, peso, cor, comprimento)
            
            if aprovada:
                messagebox.showinfo("Sucesso", mensagem)
            else:
                messagebox.showwarning("Reprovado", mensagem)
            
            # Limpar formulário
            self.entry_id.delete(0, "end")
            self.entry_peso.delete(0, "end")
            self.entry_comprimento.delete(0, "end")
            self.combo_cor.set("azul")
            
            # Atualizar dashboard
            self.atualizar_dashboard()
            
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira valores numéricos válidos para peso e comprimento!")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
    
    def mostrar_relatorio(self):
        """Mostra o relatório completo em uma nova janela"""
        relatorio_window = ctk.CTkToplevel(self.root)
        relatorio_window.title("Relatório Completo - Controle de Qualidade")
        relatorio_window.geometry("900x700")
        
        # Frame principal
        main_frame = ctk.CTkFrame(relatorio_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="📊 Relatório Completo de Controle de Qualidade",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Área de texto com scroll
        text_relatorio = ctk.CTkTextbox(main_frame, font=ctk.CTkFont(size=11))
        text_relatorio.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Gerar relatório
        relatorio = self.sistema.gerar_relatorio_completo()
        
        text_relatorio.insert("end", "="*80 + "\n")
        text_relatorio.insert("end", f"Data de Geração: {relatorio['data_geracao']}\n")
        text_relatorio.insert("end", "="*80 + "\n\n")
        
        text_relatorio.insert("end", "📈 RESUMO GERAL\n")
        text_relatorio.insert("end", "-"*80 + "\n")
        text_relatorio.insert("end", f"Total de Peças Inspecionadas: {relatorio['total_pecas_inspecionadas']}\n")
        text_relatorio.insert("end", f"✅ Peças Aprovadas: {relatorio['total_pecas_aprovadas']}\n")
        text_relatorio.insert("end", f"❌ Peças Reprovadas: {relatorio['total_pecas_reprovadas']}\n")
        text_relatorio.insert("end", f"📦 Caixas Completas: {relatorio['caixas_completas']}\n\n")
        
        text_relatorio.insert("end", "📦 CAIXA ATUAL\n")
        text_relatorio.insert("end", "-"*80 + "\n")
        text_relatorio.insert("end", f"Número: #{relatorio['caixa_atual']['numero']}\n")
        text_relatorio.insert("end", f"Peças: {relatorio['caixa_atual']['pecas']}/10\n")
        text_relatorio.insert("end", f"Vagas Disponíveis: {relatorio['caixa_atual']['vagas_disponiveis']}\n\n")
        
        if relatorio['total_pecas_reprovadas'] > 0:
            text_relatorio.insert("end", "❌ PEÇAS REPROVADAS - DETALHAMENTO\n")
            text_relatorio.insert("end", "-"*80 + "\n")
            for peca in relatorio['pecas_reprovadas_detalhes']:
                text_relatorio.insert("end", f"\nID: {peca['id']}\n")
                text_relatorio.insert("end", f"Data/Hora: {peca['timestamp']}\n")
                text_relatorio.insert("end", f"Peso: {peca['peso']}g | Cor: {peca['cor']} | Comprimento: {peca['comprimento']}cm\n")
                text_relatorio.insert("end", "Motivos:\n")
                for motivo in peca['motivos_reprovacao']:
                    text_relatorio.insert("end", f"  • {motivo}\n")
                text_relatorio.insert("end", "-"*40 + "\n")
        
        if relatorio['caixas_completas'] > 0:
            text_relatorio.insert("end", "\n📦 CAIXAS COMPLETAS\n")
            text_relatorio.insert("end", "-"*80 + "\n")
            for caixa in relatorio['caixas_fechadas_detalhes']:
                text_relatorio.insert("end", f"\nCaixa #{caixa['numero']}\n")
                text_relatorio.insert("end", f"Data de Fechamento: {caixa['data_fechamento']}\n")
                text_relatorio.insert("end", f"Quantidade de Peças: {caixa['quantidade_pecas']}\n")
                text_relatorio.insert("end", "-"*40 + "\n")
        
        text_relatorio.insert("end", "\n" + "="*80 + "\n")
        text_relatorio.insert("end", "Relatório gerado automaticamente pelo Sistema de Controle de Qualidade v1.0\n")
        text_relatorio.insert("end", "="*80 + "\n")
        
        text_relatorio.configure(state="disabled")
        
        # Botão fechar
        btn_fechar = ctk.CTkButton(
            main_frame,
            text="Fechar",
            command=relatorio_window.destroy,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40
        )
        btn_fechar.pack(pady=10)
    
    def exportar_json(self):
        """Exporta o relatório em formato JSON"""
        try:
            caminho = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"relatorio_qualidade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            if caminho:
                self.sistema.exportar_relatorio_json(caminho)
                messagebox.showinfo("Sucesso", f"Relatório exportado com sucesso!\n\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar relatório: {str(e)}")
    
    def exportar_csv(self):
        """Exporta o relatório em formato CSV"""
        try:
            caminho = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"relatorio_qualidade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            if caminho:
                self.sistema.exportar_relatorio_csv(caminho)
                messagebox.showinfo("Sucesso", f"Relatório exportado com sucesso!\n\nO arquivo pode ser aberto no Excel.\n\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar relatório: {str(e)}")
    
    def limpar_dados(self):
        """Limpa todos os dados do sistema"""
        resposta = messagebox.askyesno(
            "Confirmação",
            "⚠️ ATENÇÃO!\n\nTem certeza que deseja limpar TODOS os dados?\n\n"
            "Esta ação é IRREVERSÍVEL e vai apagar:\n"
            "• Todas as peças aprovadas\n"
            "• Todas as peças reprovadas\n"
            "• Todas as caixas fechadas\n"
            "• A caixa atual\n\n"
            "Deseja continuar?"
        )
        
        if resposta:
            self.sistema.limpar_dados()
            self.atualizar_dashboard()
            messagebox.showinfo("Sucesso", "Todos os dados foram limpos com sucesso!\n\nO sistema está pronto para começar do zero.")
    
    def executar(self):
        """Executa a aplicação"""
        self.root.mainloop()


def main():
    """Função principal"""
    print("="*60)
    print("Sistema de Controle de Qualidade Industrial v1.0")
    print("Iniciando interface gráfica...")
    print("="*60)
    
    app = InterfaceGrafica()
    app.executar()


if __name__ == "__main__":
    main()
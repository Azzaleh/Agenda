import requests 
import os
import sys
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, 
    QCalendarWidget, QListWidget, QLabel, QPushButton,
    QDialog, QFormLayout, QLineEdit, QTimeEdit, QMessageBox,
    QGraphicsDropShadowEffect, QListWidgetItem, QDesktopWidget,
    QComboBox, QTextEdit, QRadioButton # QRadioButton ADICIONADO
)
from PyQt5.QtCore import (
    QDate, Qt, QTime, QSize, QThread, pyqtSignal, 
    QCoreApplication, QUrl, QTimer # QTimer ADICIONADO
) 
from PyQt5.QtGui import QColor,QTextCharFormat 
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from database import DataManager


GITHUB_REPO = "Azzaleh/Agenda"
CURRENT_VERSION = "1.1"
DOWNLOAD_FILENAME = "AgendaDataServis.exe"

# --- QSS STYLES ---
QSS_STYLES = """
    /* Fundo Geral e Fonte */
    QWidget {
        background-color: #f7f7f7;
        font-family: 'Segoe UI', Arial, sans-serif;
        color: #333333;
    }

    /* Calendário (QCalendarWidget) */
    QCalendarWidget {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background-color: white;
    }

    QCalendarWidget QAbstractItemView:disabled { 
        color: #cccccc;
        background-color: transparent;
    }
    
    QCalendarWidget QAbstractItemView:enabled {
        outline: none;
        font-size: 14px;
        color: #333333;
    }
    
    QCalendarWidget QAbstractItemView::item {
        background: transparent;
        color: #333;
    }

    /* 1. DIA SELECIONADO (AZUL ESCURO) - Aplicado SOMENTE se NÃO for o dia atual */
    QCalendarWidget QAbstractItemView::item:selected:!today {
        background-color: #007acc; /* Azul Escuro para Seleção */
        color: white; /* Texto branco */
        border: 1px solid #007acc;
        border-radius: 4px;
    }
    
    /* 2. DIA ATUAL (AZUL CLARO FIXO) - Aplicado quando NÃO ESTÁ selecionado */
    QCalendarWidget QAbstractItemView::item:!selected:today {
        background-color: #90CAF9; /* Azul Claro Fixo */
        color: #333333; /* Texto escuro */
        border-radius: 4px;
        border: 1px solid #64B5F6;
    }

    /* 3. DIA ATUAL E SELECIONADO (AZUL CLARO FIXO) - Aplicado quando você clica no dia atual */
    QCalendarWidget QAbstractItemView::item:selected:today {
        background-color: #90CAF9; /* Azul Claro Fixo */
        color: #333333; /* Texto escuro */
        border-radius: 4px;
        border: 1px solid #64B5F6;
    }

    /* Título (QLabel) do Painel Lateral */
    QLabel#DayTitle {
        font-size: 18pt;
        font-weight: 600;
        padding-bottom: 10px;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 15px;
        color: #1f1f1f;
    }

    /* Lista de Compromissos (QListWidget) */
    QListWidget {
        border: none;
        background-color: white;
        padding: 5px;
        border-radius: 8px;
    }
    
    QListWidget {
        border-bottom: 1px solid #f0f0f0;
    }

    QListWidget::item {
        border-bottom: 1px solid #f0f0f0;
    }

    QListWidget::item:selected {
        border-bottom: 1px solid #f0f0f0;
    }
    
    /* Botões de Ação (Estilo Base) */
    QPushButton {
        border: none;
        border-radius: 10px;
        padding: 10px 15px;
        font-size: 12pt;
    }
    
    /* Hover/Interação */
    QPushButton:hover {
        opacity: 0.8;
    }
    
    /* Estilo para o Botão Adicionar (Cor específica será aplicada via setStyleSheet) */
    QPushButton#AddButton:hover {
        background-color: #005f99; 
    }

    /* Estilo para o Botão Excluir (Cor específica será aplicada via setStyleSheet) */
    QPushButton#DeleteButton:hover {
        background-color: #990000;
    }
    
    /* Estilo do Diálogo de Adição */
    QDialog {
        background-color: white;
    }
    
    /* Estilo para campos de entrada */
    QLineEdit, QTimeEdit, QComboBox {
        padding: 8px;
        border: 1px solid #cccccc;
        border-radius: 5px;
        font-size: 11pt;
    }
    
    QTextEdit {
        padding: 8px;
        border: 1px solid #cccccc;
        border-radius: 5px;
        font-size: 11pt;
    }
    
    QRadioButton {
        padding: 5px;
        font-size: 11pt;
    }
"""

# --- FUNÇÕES AUXILIARES GLOBAIS ---

def get_color_by_type(tipo_visita):
    """ Mapeia o tipo de visita para uma cor de fundo. """
    colors = {
        "Treinamento": "#c6ffc6",   
        "Visita Técnica": "#ffecc2", 
        "Outro": "#96fffa",          
    }
    return colors.get(tipo_visita, "#ffffff")

def _center_window(widget):
    """ Centraliza o widget (QDialog ou QWidget) na tela. """
    qr = widget.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    widget.move(qr.topLeft())

def _apply_shadow(widget, blur_radius=15, color_alpha=80):
    """ Aplica o efeito de sombra gráfica ao widget. """
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setXOffset(0)
    shadow.setYOffset(4)
    shadow.setColor(QColor(0, 0, 0, color_alpha))
    widget.setGraphicsEffect(shadow)

# --- CLASSE UPDATER (QThread) ---

class Updater(QThread):
    update_available = pyqtSignal(str, str) # Emite (versão, download_url)
    update_error = pyqtSignal(str)
    verification_finished = pyqtSignal(bool)
    
    def run(self):
        try:
            # Requisição à API do GitHub para pegar a última release
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(api_url, timeout=5)
            
            if response.status_code != 200:
                self.update_error.emit("Erro ao acessar API do GitHub. Código: " + str(response.status_code))
                self.verification_finished.emit(False)
                return

            latest_release = response.json()
            # Remove "v" do início e pega a versão da tag
            latest_version_raw = latest_release.get("tag_name", "v0.0").lstrip('v')
            
            # Comparação de Versões
            if self._is_new_version(latest_version_raw, CURRENT_VERSION):
                
                download_url = None
                # Encontra o arquivo .exe anexo (asset)
                for asset in latest_release.get("assets", []):
                    if asset.get("name") == DOWNLOAD_FILENAME:
                        download_url = asset.get("browser_download_url")
                        break
                
                if download_url:
                    self.update_available.emit(latest_version_raw, download_url)
                else:
                    self.update_error.emit(f"Arquivo '{DOWNLOAD_FILENAME}' não encontrado na release.")
                    self.verification_finished.emit(False)
            else:
                self.verification_finished.emit(True)
            
        except requests.exceptions.ConnectionError:
            self.update_error.emit("Erro de conexão de rede.")
            self.verification_finished.emit(False)
        except Exception as e:
            self.update_error.emit(f"Erro inesperado na verificação: {e}")
            self.verification_finished.emit(False)

    def _is_new_version(self, new_raw, current_raw):
        # Lógica para comparar apenas MAIOR e MENOR.
        
        new_parts = list(map(int, new_raw.split('.')))[:2]
        current_parts = list(map(int, current_raw.split('.')))[:2]
        
        # Preenche com zeros se for necessário
        max_len = max(len(new_parts), len(current_parts))
        new_parts.extend([0] * (max_len - len(new_parts)))
        current_parts.extend([0] * (max_len - len(current_parts)))
        
        return new_parts > current_parts

# --- WIDGET PERSONALIZADO PARA O ITEM DA LISTA (3 LINHAS DE LAYOUT) ---

class AppointmentItemWidget(QWidget):
    def __init__(self, hora, nome_cliente, tipo_visita, local_visita, observacoes, endereco, quem_vai, parent=None):
        """ Inicializa o widget com os detalhes do agendamento em três linhas. """
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5) 
        main_layout.setSpacing(4) 

        title_style = 'font-weight: bold; color: #333333; margin-right: 5px;'
        content_style = 'font-size: 10pt;'

        # 1. LINHA PRINCIPAL (HORA E CLIENTE)
        main_line = QHBoxLayout()
        main_line.setSpacing(15) 
        
        hour_label = QLabel(f'<b><span style="font-size: 14pt;">{hora}</span></b>')
        main_line.addWidget(hour_label)
        
        client_label = QLabel(f'<b><span style="color: #00CED1; font-size: 14pt;">{nome_cliente}</span></b>')
        client_label.setWordWrap(True)
        main_line.addWidget(client_label, 1) 
        
        main_layout.addLayout(main_line)
        
        # 2. SEGUNDA LINHA (TIPO E LOCAL/ENDEREÇO)
        location_line = QHBoxLayout()
        location_line.setSpacing(15) 
        
        # LÓGICA DE EXIBIÇÃO DO LOCAL/ENDEREÇO
        local_display = local_visita
        if local_visita == "No Cliente" and endereco:
            local_display = f"No Cliente ({endereco})"

        # Tipo
        type_label = QLabel(f'<span style="{title_style}">Tipo:</span><span style="{content_style}"> {tipo_visita}</span>')
        location_line.addWidget(type_label)
        
        # Local
        local_label = QLabel(f'<span style="{title_style}">Local:</span><span style="{content_style}"> {local_display}</span>')
        local_label.setWordWrap(True)
        location_line.addWidget(local_label, 1) 
        
        main_layout.addLayout(location_line)

        # 3. TERCEIRA LINHA (QUEM VAI? E OBSERVAÇÕES)
        detail_line = QHBoxLayout()
        detail_line.setSpacing(15)
        
        # CAMPO: QUEM VAI?
        quem_vai_display = quem_vai if quem_vai else 'Não Definido'
        quem_vai_label = QLabel(f'<span style="{title_style}">Quem vai?:</span><span style="{content_style}"> {quem_vai_display}</span>')
        detail_line.addWidget(quem_vai_label)
        
        # Observações (Ocupa o restante da linha)
        obs_display = observacoes
        if not observacoes:
             obs_display = 'Nenhuma'

        obs_label = QLabel(f'<span style="{title_style}">Obs:</span><span style="{content_style}"> {obs_display}</span>')
        obs_label.setWordWrap(True)
        detail_line.addWidget(obs_label, 1) 
        
        main_layout.addLayout(detail_line)
        
        self.setMinimumHeight(80)
        self.setStyleSheet("background-color: transparent;")

# --- DIÁLOGO DE ADIÇÃO/EDIÇÃO DE EVENTO ---

class AddEventDialog(QDialog):
    def __init__(self, selected_date, appointment_details=None, parent=None):
        """ Diálogo para adicionar ou editar um compromisso. """
        super().__init__(parent)
        self.setWindowTitle(f"Agendar Compromisso para {selected_date.toString('dd/MM/yyyy')}")
        self.resize(500, 420) 
        _center_window(self)
        
        self.data_selecionada = selected_date.toString("yyyy-MM-dd")
        self.novo_compromisso = None
        self.compromisso_id = None 

        layout = QFormLayout()

        # 1. Hora
        self.time_input = QTimeEdit(self)
        self.time_input.setTime(QTime.currentTime())
        self.time_input.setDisplayFormat("HH:mm")
        layout.addRow("Hora da Visita:", self.time_input)

        # 2. Nome do Cliente
        self.cliente_input = QLineEdit(self)
        layout.addRow("Nome do Cliente:", self.cliente_input)
        
        # 3. Tipo de Visita (ComboBox)
        self.tipo_visita_input = QComboBox(self)
        self.tipo_visita_input.addItems(["Treinamento", "Visita Técnica", "Outro"])
        layout.addRow("Tipo de Compromisso:", self.tipo_visita_input)

        # 4. Local da Visita (ComboBox)
        self.local_visita_input = QComboBox(self)
        self.local_visita_input.addItems(["Escritório", "No Cliente"])
        self.local_visita_input.currentTextChanged.connect(self._toggle_endereco_field)
        layout.addRow("Local:", self.local_visita_input)
        
        # 5. Endereço (Visível apenas se "No Cliente")
        self.endereco_input = QLineEdit(self)
        self.endereco_input.setPlaceholderText("Ex: Praça Exemplo, 44, Centro, Barbacena MG")
        layout.addRow("Endereço:", self.endereco_input)
        
        # 6. Campo: QUEM VAI?
        self.quem_vai_input = QLineEdit(self)
        layout.addRow("Quem vai? (Responsável):", self.quem_vai_input)

        # 7. Observações (Multi-linha)
        self.obs_input = QTextEdit(self)
        self.obs_input.setFixedHeight(60)
        layout.addRow("Observações (Motivo):", self.obs_input)

        self.save_button = QPushButton("Salvar Agendamento")
        self.save_button.clicked.connect(self.save_compromisso)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.cancel_button)
        btn_layout.addWidget(self.save_button)
        
        layout.addRow(btn_layout)
        self.setLayout(layout)

        self.save_button.setStyleSheet("background-color: #007acc; color: white;")
        _apply_shadow(self.save_button, blur_radius=10, color_alpha=80)
        
        self._toggle_endereco_field(self.local_visita_input.currentText())

        # Preenche os dados se for Edição
        if appointment_details:
            self._load_details_for_editing(appointment_details)

    def _toggle_endereco_field(self, local_text):
        """ Controla a visibilidade do campo Endereço. """
        is_client_visit = (local_text == "No Cliente")
        self.endereco_input.setVisible(is_client_visit)
        if self.endereco_input.parentWidget():
            label = self.layout().labelForField(self.endereco_input)
            if label:
                label.setVisible(is_client_visit)
    
    def _load_details_for_editing(self, details_tuple):
        """ Carrega os dados para o modo de edição. """
        # data_str, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes
        data_str, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes = details_tuple
        
        self.setWindowTitle(f"Editar Visita de {nome_cliente} ({QDate.fromString(data_str, 'yyyy-MM-dd').toString('dd/MM/yyyy')})")
        self.data_selecionada = data_str 
        
        self.time_input.setTime(QTime.fromString(hora, "HH:mm"))
        self.cliente_input.setText(nome_cliente)
        self.obs_input.setText(observacoes)
        self.endereco_input.setText(endereco)
        
        self.tipo_visita_input.setCurrentText(tipo_visita)
        self.local_visita_input.setCurrentText(local_visita)
        
        self.quem_vai_input.setText(quem_vai)
        
        self._toggle_endereco_field(local_visita)


    def save_compromisso(self):
        """ Salva os dados do formulário no dicionário novo_compromisso. """
        hora = self.time_input.time().toString("HH:mm")
        cliente = self.cliente_input.text().strip()
        tipo_visita = self.tipo_visita_input.currentText()
        local_visita = self.local_visita_input.currentText()
        observacoes = self.obs_input.toPlainText().strip()
        
        endereco = self.endereco_input.text().strip() if local_visita == "No Cliente" else ""
        quem_vai = self.quem_vai_input.text().strip()
        
        if not cliente:
            QMessageBox.warning(self, "Erro de Entrada", "O nome do cliente não pode ser vazio.")
            return

        self.novo_compromisso = {
            "data": self.data_selecionada,
            "hora": hora,
            "nome_cliente": cliente,
            "tipo_visita": tipo_visita,
            "local_visita": local_visita,
            "endereco": endereco,           
            "quem_vai": quem_vai,           
            "observacoes": observacoes
        }
        
        self.accept()
        
    def set_compromisso_details(self, data_str, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes):
        """ Método auxiliar para carregar dados para edição. """
        self._load_details_for_editing((data_str, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes))


# --- NOVO: DIÁLOGO DE CONSULTA DE AGENDAMENTOS ---

class QueryDialog(QDialog):
    # Sinal emitido quando o usuário seleciona um compromisso para navegar
    appointment_selected = pyqtSignal(QDate)

    def __init__(self, db_manager, parent=None):
        """ Diálogo para consultar agendamentos passados ou futuros. """
        super().__init__(parent)
        self.setWindowTitle("Consultar Agendamentos")
        self.resize(700, 600)
        _center_window(self)
        
        self.db_manager = db_manager
        self.appointments_data = []

        main_layout = QVBoxLayout(self)

        # 1. LAYOUT DE OPÇÕES (RÁDIOS E BOTÃO)
        options_layout = QHBoxLayout()
        
        self.radio_future = QRadioButton("Agendamentos Futuros")
        self.radio_future.setChecked(True)
        self.radio_future.toggled.connect(self._fetch_appointments) 
        
        self.radio_past = QRadioButton("Agendamentos Passados")
        self.radio_past.toggled.connect(self._fetch_appointments) 

        self.select_button = QPushButton("Visualizar no Calendário")
        self.select_button.clicked.connect(self._select_and_return_date)
        self.select_button.setEnabled(False)
        
        options_layout.addWidget(self.radio_future)
        options_layout.addWidget(self.radio_past)
        options_layout.addStretch(1)
        options_layout.addWidget(self.select_button)
        
        main_layout.addLayout(options_layout)

        # 2. LISTA DE RESULTADOS
        self.result_list = QListWidget()
        self.result_list.itemClicked.connect(self._toggle_select_button)
        self.result_list.itemDoubleClicked.connect(self._select_and_return_date)
        main_layout.addWidget(self.result_list)
        
        self._fetch_appointments()
        
        self.select_button.setStyleSheet("background-color: #6a0dad; color: white; padding: 10px; border-radius: 8px;")
        _apply_shadow(self.select_button, blur_radius=10, color_alpha=80)

    def _toggle_select_button(self):
        """ Ativa/Desativa o botão 'Visualizar' se um item válido estiver selecionado. """
        selected_items = self.result_list.selectedItems()
        self.select_button.setEnabled(bool(selected_items) and selected_items[0].data(Qt.UserRole) is not None)

    def _fetch_appointments(self):
        """ Busca os agendamentos no DB conforme o rádio selecionado. """
        self.result_list.clear()
        self.select_button.setEnabled(False) 
        
        if self.radio_future.isChecked():
            self.appointments_data = self.db_manager.get_future_appointments()
        else:
            self.appointments_data = self.db_manager.get_past_appointments()

        if not self.appointments_data:
            item = QListWidgetItem("Nenhum compromisso encontrado para este período.")
            item.setSizeHint(QSize(self.result_list.width(), 40)) 
            self.result_list.addItem(item)
            return

        for data_tuple in self.appointments_data:
            # data_tuple: (id, data, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes)
            
            # Formato de data legível para o Widget (ex: 28/11)
            display_date_str = QDate.fromString(data_tuple[1], "yyyy-MM-dd").toString("dd/MM")
            
            # Criamos o widget personalizado para exibição
            item_widget = AppointmentItemWidget(
                hora=f"[{display_date_str}] {data_tuple[2]}", # Adiciona a data à hora
                nome_cliente=data_tuple[3], 
                tipo_visita=data_tuple[4], 
                local_visita=data_tuple[5], 
                observacoes=data_tuple[8], 
                endereco=data_tuple[6],
                quem_vai=data_tuple[7] 
            )

            item = QListWidgetItem(self.result_list)
            
            # Cor de fundo: a cor da visita, mas mais suave para a consulta
            color_hex = get_color_by_type(data_tuple[4])
            item.setBackground(QColor(color_hex).lighter(110))
            
            # Armazena a data no formato QDate no UserRole para fácil acesso
            qdate = QDate.fromString(data_tuple[1], "yyyy-MM-dd")
            item.setData(Qt.UserRole, qdate) 
            
            item.setSizeHint(item_widget.sizeHint())
            self.result_list.setItemWidget(item, item_widget)
            self.result_list.addItem(item)

    def _select_and_return_date(self):
        """ Emite o sinal com a data do compromisso selecionado e fecha o diálogo. """
        selected_items = self.result_list.selectedItems()
        if selected_items:
            selected_qdate = selected_items[0].data(Qt.UserRole) 
            if selected_qdate:
                self.appointment_selected.emit(selected_qdate)
                self.accept()

# --- AGENDA APP (PRINCIPAL) ---

class AgendaApp(QWidget):
    def __init__(self):
        super().__init__()
        
        # Inicialização do DB Manager
        self.db_manager = DataManager()
        
        self.set_window_title() 
        self.init_ui()
        
        # Armazena o último dia verificado para o timer
        self.last_checked_date = QDate.currentDate()

    def set_window_title(self, status=""):
        """ Atualiza o título da janela com o status atual. """
        base_title = "Agenda Data Servis"
        if status:
            self.setWindowTitle(f"{base_title} [{status}]")
        else:
            self.setWindowTitle(base_title)
            
    def init_ui(self):
        app.setStyleSheet(QSS_STYLES)
        
        self.set_window_title("Verificando Atualizações...") 
        
        main_layout = QHBoxLayout()

        self.calendar = QCalendarWidget()
        self.highlight_today()

        today_format = QTextCharFormat()
        today_format.setBackground(QColor("#6DFFC2"))
        today_format.setForeground(QColor("#333333"))
        today_format.setFontWeight(75)

        self.calendar.setDateTextFormat(QDate.currentDate(), today_format)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader) 
        self.calendar.setGridVisible(False) 
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.selectionChanged.connect(self.update_daily_appointments)
        main_layout.addWidget(self.calendar, 65) 

        right_panel = QVBoxLayout()
        
        self.day_title = QLabel("Compromissos do Dia:")
        self.day_title.setObjectName("DayTitle")

        self.appointment_list = QListWidget()
        # CONEXÃO: DUPLO CLIQUE PARA EDIÇÃO
        self.appointment_list.itemDoubleClicked.connect(self.open_edit_dialog)

        self.addButton = QPushButton(" + Adicionar Novo Compromisso ")
        self.addButton.clicked.connect(self.open_add_dialog)
        self.addButton.setObjectName("AddButton")
        self.addButton.setStyleSheet("background-color: #007acc; color: white;") 

        self.deleteButton = QPushButton(" - Excluir Compromisso Selecionado ")
        self.deleteButton.setObjectName("DeleteButton") 
        self.deleteButton.clicked.connect(self.delete_selected_appointment)
        self.deleteButton.setStyleSheet("background-color: #cc0000; color: white;") 
        
        # NOVO BOTÃO DE CONSULTA
        self.queryButton = QPushButton(" 🔎 Consultar Agendamentos ")
        self.queryButton.setObjectName("QueryButton") 
        self.queryButton.clicked.connect(self.open_query_dialog)
        self.queryButton.setStyleSheet("background-color: #6a0dad; color: white;") # Roxo
        
        right_panel.addWidget(self.day_title)
        right_panel.addWidget(self.appointment_list)
        right_panel.addWidget(self.addButton)
        right_panel.addWidget(self.queryButton) 
        right_panel.addWidget(self.deleteButton) 

        right_container = QWidget()
        right_container.setStyleSheet("background-color: white; border-radius: 8px;")
        right_container.setLayout(right_panel)
        
        _apply_shadow(right_container)

        main_layout.addWidget(right_container, 35)

        self.setLayout(main_layout)
        
        _apply_shadow(self.addButton)
        _apply_shadow(self.deleteButton) 
        _apply_shadow(self.queryButton) 

        self.update_daily_appointments()
        
        # Timer para atualizar automaticamente o dia atual (a cada 60 segundos)
        self.date_check_timer = QTimer(self)
        self.date_check_timer.timeout.connect(self.check_and_update_day)
        self.date_check_timer.start(60000)
        
        # Inicia o verificador de atualização
        self.updater = Updater()
        self.updater.update_available.connect(self.prompt_update)
        self.updater.update_error.connect(self.handle_updater_error)
        self.updater.verification_finished.connect(self.handle_verification_finished)
        self.updater.start()
        
    def update_daily_appointments(self):
        """ Atualiza a lista de compromissos para a data selecionada. """
        selected_date_qdate = self.calendar.selectedDate()
        selected_date_str = selected_date_qdate.toString("yyyy-MM-dd")
        display_date_str = selected_date_qdate.toString("dd 'de' MMMM 'de' yyyy")
        
        self.day_title.setText(f"Compromissos para:\n{display_date_str}")
        
        daily_events = self.db_manager.get_compromissos_by_date(selected_date_str) 
        
        self.appointment_list.clear()
        
        if daily_events:
            # event_id, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes
            for event_id, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes in daily_events: 
                
                # WIDGET PERSONALIZADO
                item_widget = AppointmentItemWidget(
                    hora=hora, 
                    nome_cliente=nome_cliente, 
                    tipo_visita=tipo_visita, 
                    local_visita=local_visita, 
                    observacoes=observacoes, 
                    endereco=endereco,
                    quem_vai=quem_vai 
                )
                
                item = QListWidgetItem(self.appointment_list)
                
                color_hex = get_color_by_type(tipo_visita)
                item.setBackground(QColor(color_hex))

                item.setSizeHint(item_widget.sizeHint())
                self.appointment_list.setItemWidget(item, item_widget)

                item.setData(Qt.UserRole, event_id) 
                self.appointment_list.addItem(item)
        else:
            item = QListWidgetItem("Nenhum compromisso agendado.")
            item.setSizeHint(QSize(self.appointment_list.width(), 40)) 
            self.appointment_list.addItem(item)
            
    def open_add_dialog(self):
        """ Abre o diálogo para adicionar um novo compromisso. """
        selected_date = self.calendar.selectedDate()
        dialog = AddEventDialog(selected_date, parent=self)
        
        if dialog.exec_() == QDialog.Accepted:
            data_to_save = dialog.novo_compromisso
            
            self.db_manager.add_compromisso(
                data_to_save['data'],
                data_to_save['hora'],
                data_to_save['nome_cliente'],
                data_to_save['tipo_visita'],
                data_to_save['local_visita'],
                data_to_save['endereco'],
                data_to_save['quem_vai'],
                data_to_save['observacoes']
            )
            
            self.update_daily_appointments()
            QMessageBox.information(self, "Sucesso", "Visita agendada com sucesso!")

    def open_edit_dialog(self, item=None):
        """ Abre o diálogo para editar o compromisso selecionado. """
        if item is not None:
            selected_item = item
        else:
            selected_items = self.appointment_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Seleção Inválida", "Por favor, selecione um compromisso para editar.")
                return
            selected_item = selected_items[0]

        compromisso_id = selected_item.data(Qt.UserRole)
        
        if compromisso_id is None:
            QMessageBox.warning(self, "Erro", "Não é um compromisso válido para edição.")
            return
            
        # Busca os dados atuais do banco (retorna 8 campos)
        details_tuple = self.db_manager.get_compromisso_by_id(compromisso_id)
        
        if not details_tuple:
            QMessageBox.critical(self, "Erro", "Não foi possível carregar os dados do compromisso.")
            return

        data_str = details_tuple[0] 
        selected_date_qdate = QDate.fromString(data_str, "yyyy-MM-dd")
        
        # Configura o AddEventDialog para edição
        dialog = AddEventDialog(
            selected_date_qdate, 
            appointment_details=details_tuple, 
            parent=self
        )
        dialog.compromisso_id = compromisso_id 

        # Executa o diálogo e salva se aceito
        if dialog.exec_() == QDialog.Accepted:
            data_to_save = dialog.novo_compromisso
            
            # ATUALIZAÇÃO NO BANCO
            if self.db_manager.update_compromisso(
                dialog.compromisso_id,
                data_to_save['data'],
                data_to_save['hora'],
                data_to_save['nome_cliente'],
                data_to_save['tipo_visita'],
                data_to_save['local_visita'],
                data_to_save['endereco'],
                data_to_save['quem_vai'],
                data_to_save['observacoes']
            ):
                QMessageBox.information(self, "Sucesso", "Compromisso atualizado com sucesso!")
                self.update_daily_appointments()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao atualizar o compromisso no banco de dados.")

    def delete_selected_appointment(self,):
        """ Exclui o compromisso selecionado na lista. """
        selected_items = self.appointment_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "Seleção Inválida", "Por favor, selecione um compromisso para excluir.")
            return

        selected_item = selected_items[0]
        
        compromisso_id = selected_item.data(Qt.UserRole)
        
        if compromisso_id is None:
            QMessageBox.warning(self, "Erro", "Não é um compromisso válido para exclusão.")
            return
            
        confirm = QMessageBox.question(self, "Confirmar Exclusão", 
            f"Tem certeza que deseja excluir o compromisso: '{selected_item.text()}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            if self.db_manager.delete_compromisso(compromisso_id):
                QMessageBox.information(self, "Sucesso", "Compromisso excluído!")
                self.update_daily_appointments()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao excluir o compromisso no banco de dados.")

    def open_query_dialog(self):
        """ Abre o diálogo de consulta de agendamentos. """
        dialog = QueryDialog(self.db_manager, parent=self)
        
        # Conecta o sinal do diálogo ao método de navegação
        dialog.appointment_selected.connect(self.navigate_to_date) 
        
        dialog.exec_()
        
    def navigate_to_date(self, target_date: QDate):
        """ Navega o calendário para a data selecionada no QueryDialog. """
        self.calendar.setSelectedDate(target_date)
        self.update_daily_appointments()

    # --- MÉTODOS DE ATUALIZAÇÃO DE STATUS ---
    
    def handle_verification_finished(self, success):
        """ Atualiza o título da janela após a verificação estar completa. """
        if success:
            self.set_window_title(f"Versão {CURRENT_VERSION} Atualizada")
        else:
            self.set_window_title() 
            
    def handle_updater_error(self, message):
        print(f"Erro do Updater: {message}")
        QMessageBox.warning(self, "Erro de Atualização", f"Falha ao verificar atualizações. {message}")

    def prompt_update(self, version, download_url):
        """ Pergunta ao usuário se deseja atualizar. """
        reply = QMessageBox.question(self, "Atualização Disponível", 
            f"Uma nova versão ({version}) está disponível. Deseja atualizar agora?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Inicia o download (usando QNetworkAccessManager para não travar a UI)
            self.download_manager = QNetworkAccessManager(self)
            self.download_manager.finished.connect(self.handle_download_finished)
            
            request = QNetworkRequest(QUrl(download_url))
            self.reply = self.download_manager.get(request)
            
            self.download_msg = QMessageBox(self)
            self.download_msg.setText("Baixando atualização... Por favor, aguarde.")
            self.download_msg.setWindowTitle("Baixando")
            self.download_msg.setStandardButtons(QMessageBox.NoButton)
            self.download_msg.show()

    def handle_download_finished(self, reply: QNetworkReply):
        """ Gerencia o download da atualização. """
        if hasattr(self, 'download_msg'):
            self.download_msg.close()

        if reply.error() != QNetworkReply.NoError:
            QMessageBox.critical(self, "Erro de Download", f"Falha ao baixar arquivo: {reply.errorString()}")
            return
            
        new_exe_data = reply.readAll()
        current_exe_path = os.path.abspath(sys.argv[0])
        new_exe_name = "AgendaDataServis_new.exe"
        temp_new_exe_path = os.path.join(os.path.dirname(current_exe_path), new_exe_name)

        try:
            # Salva o novo .exe com um nome temporário
            with open(temp_new_exe_path, 'wb') as f:
                f.write(new_exe_data.data())
        except Exception as e:
            QMessageBox.critical(self, "Erro de Arquivo", f"Não foi possível salvar o novo executável: {e}")
            return

        self.execute_update_script(current_exe_path, temp_new_exe_path)


    def execute_update_script(self, old_path, new_path):
        """ Cria e executa um script temporário para substituir o executável e reiniciar. """
        
        # Cria o script de atualização (Exemplo Windows Batch)
        script_content = r"""
@echo off
ECHO Aguardando o aplicativo principal fechar...
timeout /t 3 /nobreak >nul

ECHO Excluindo a versão antiga...
del /f /q "{old_path}"

ECHO Renomeando nova versão...
ren "{new_path}" "{os.path.basename(old_path)}"

ECHO Criando atalho na Área de Trabalho e iniciando nova versão...
call :CreateShortcutAndRun "{os.path.dirname(old_path)}\\{os.path.basename(old_path)}" "{DOWNLOAD_FILENAME}"

ECHO Limpando script...
del /f /q "%~f0"
EXIT

:CreateShortcutAndRun
    SET "TargetExe=%~1"
    SET "ShortcutName=Agenda Data Servis"
    
    ECHO Set WshShell = CreateObject("WScript.Shell") > tmp.vbs
    ECHO DesktopPath = WshShell.SpecialFolders("Desktop") >> tmp.vbs
    ECHO Set oShellLink = WshShell.CreateShortcut(DesktopPath ^& "\%ShortcutName%.lnk") >> tmp.vbs
    ECHO oShellLink.TargetPath = "%TargetExe%" >> tmp.vbs
    ECHO oShellLink.Save >> tmp.vbs
    ECHO WshShell.Run Chr(34) ^& "%TargetExe%" ^& Chr(34), 1, False >> tmp.vbs
    cscript //nologo tmp.vbs
    del tmp.vbs
goto :EOF
"""
        
        script_path = os.path.join(os.path.dirname(old_path), "update_script.bat")
        
        try:
            with open(script_path, "w") as f:
                f.write(script_content.format(
                    old_path=old_path, 
                    new_path=new_path, 
                    DOWNLOAD_FILENAME=DOWNLOAD_FILENAME,
                    os=os # Passa o módulo os para usar o path.basename/dirname
                ))
            subprocess.Popen([script_path], creationflags=subprocess.CREATE_NO_WINDOW)
            QCoreApplication.quit()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro de Execução", f"Falha ao executar script de atualização: {e}")

    def highlight_today(self):
        """ Aplica o formato de destaque ao dia atual no calendário. """
        today = QDate.currentDate()
        today_format = QTextCharFormat()
        today_format.setBackground(QColor("#90CAF9"))
        today_format.setForeground(QColor("#DD8888"))
        today_format.setFontWeight(75)

        self.calendar.setDateTextFormat(today, today_format)
        
    def check_and_update_day(self):
        """ Verifica se a data do sistema mudou e atualiza o destaque do calendário. """
        today = QDate.currentDate()

        if today != self.last_checked_date:
            self.highlight_today()  
            self.calendar.setSelectedDate(today)  
            self.update_daily_appointments()  
            
        self.last_checked_date = today
        
    def closeEvent(self, event):
        self.db_manager.close()
        event.accept()

if __name__ == '__main__':
    # Verifica se está sendo executado como um executável PyInstaller
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    app = QApplication(sys.argv)
    window = AgendaApp()
    window.showMaximized()
    sys.exit(app.exec_())
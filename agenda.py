import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, 
    QCalendarWidget, QListWidget, QLabel, QPushButton,
    QDialog, QFormLayout, QLineEdit, QTimeEdit, QMessageBox,
    QGraphicsDropShadowEffect, QListWidgetItem, QDesktopWidget,
    QComboBox, QTextEdit
)
from PyQt5.QtCore import QDate, Qt, QTime, QSize
from PyQt5.QtGui import QColor 

# IMPORTAÇÃO DO BACKEND SEPARADO
from database import DataManager

# --- QSS STYLES (Mantido) ---
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
    
    /* 1. DIA SELECIONADO (VERDE CLARO) - MAIOR PRIORIDADE */
    QCalendarWidget QAbstractItemView::item:selected {
        background-color: #ccffcc; /* Verde Claro */
        color: #333333; /* Texto escuro */
        border: 1px solid #99cc99;
        border-radius: 4px;
    }

    /* 2. DIA ATUAL (AZUL) - Aplicado SOMENTE se não estiver selecionado */
    QCalendarWidget QAbstractItemView::item:!selected:today {
        background-color: #007acc; /* Azul escuro para Hoje */
        color: white; /* Texto branco */
        border-radius: 4px;
        border: 1px solid #007acc;
    }
    
    /* 3. Estilo para o dia atual quando estiver selecionado */
    QCalendarWidget QAbstractItemView::item:selected:today {
        background-color: #ccffcc;
        color: #333333;
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
    
    QListWidget::item {
        padding: 10px;
        border-bottom: 1px solid #f0f0f0;
        font-size: 11pt;
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
"""

# --- FUNÇÕES AUXILIARES GLOBAIS (CORREÇÃO DE ESCOPO) ---

def get_color_by_type(tipo_visita):
    """ Mapeia o tipo de visita para uma cor de fundo. """
    colors = {
        "Treinamento": "#c6ffc6",   
        "Visita Técnica": "#ffecc2", 
        "Outro": "#96fffa",          
    }
    # Retorna a cor mapeada ou um branco/cinza claro padrão
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

# --- WIDGET PERSONALIZADO PARA O ITEM DA LISTA (3 LINHAS DE LAYOUT) ---

class AppointmentItemWidget(QWidget):
    def __init__(self, hora, nome_cliente, tipo_visita, local_visita, observacoes, endereco, quem_vai, parent=None):
        super().__init__(parent)
        
        # O layout principal do item será vertical
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5) 
        main_layout.setSpacing(4) 

        # Estilos comuns
        title_style = 'font-weight: bold; color: #333333; margin-right: 5px;'
        content_style = 'font-size: 10pt;'

        # 1. LINHA PRINCIPAL (HORA E CLIENTE)
        main_line = QHBoxLayout()
        main_line.setSpacing(15) 
        
        hour_label = QLabel(f'<b><span style="font-size: 14pt;">{hora}</span></b>')
        main_line.addWidget(hour_label)
        
        # Cor: #00CED1 (Turquesa)
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
        
        # AUMENTO DE ALTURA (Mínimo de 80px para comportar 3 linhas)
        self.setMinimumHeight(80) 
        self.setStyleSheet("background-color: transparent;")

# --- DIÁLOGO DE ADIÇÃO/EDIÇÃO DE EVENTO ---

class AddEventDialog(QDialog):
    def __init__(self, selected_date, appointment_details=None, parent=None):
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
        
        # 6. NOVO CAMPO: QUEM VAI?
        self.quem_vai_input = QLineEdit(self)
        self.quem_vai_input.setPlaceholderText("Ex: César, João, Equipe X...")
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
        
        # Inicializa a visibilidade do campo Endereço
        self._toggle_endereco_field(self.local_visita_input.currentText())

        # Preenche os dados se for Edição (appointment_details é a tupla do DB)
        if appointment_details:
            self._load_details_for_editing(appointment_details)

    def _toggle_endereco_field(self, local_text):
        """ Controla a visibilidade do campo Endereço. """
        is_client_visit = (local_text == "No Cliente")
        self.endereco_input.setVisible(is_client_visit)
        # O label do Endereço também precisa ser ajustado
        if self.endereco_input.parentWidget():
            label = self.layout().labelForField(self.endereco_input)
            if label:
                label.setVisible(is_client_visit)
    
    def _load_details_for_editing(self, details_tuple):
        # Desempacota a tupla de 8 elementos retornada pelo DB
        data_str, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes = details_tuple
        
        self.setWindowTitle(f"Editar Visita de {nome_cliente} ({QDate.fromString(data_str, 'yyyy-MM-dd').toString('dd/MM/yyyy')})")
        self.data_selecionada = data_str 
        
        self.time_input.setTime(QTime.fromString(hora, "HH:mm"))
        self.cliente_input.setText(nome_cliente)
        self.obs_input.setText(observacoes)
        self.endereco_input.setText(endereco)
        
        self.tipo_visita_input.setCurrentText(tipo_visita)
        self.local_visita_input.setCurrentText(local_visita)
        
        # Pré-popula o novo campo Quem Vai?
        self.quem_vai_input.setText(quem_vai)
        
        self._toggle_endereco_field(local_visita)


    def save_compromisso(self):
        hora = self.time_input.time().toString("HH:mm")
        cliente = self.cliente_input.text().strip()
        tipo_visita = self.tipo_visita_input.currentText()
        local_visita = self.local_visita_input.currentText()
        observacoes = self.obs_input.toPlainText().strip()
        
        # Campo Endereço (só pega se for "No Cliente")
        endereco = self.endereco_input.text().strip() if local_visita == "No Cliente" else ""
        
        # Campo Quem Vai?
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
        
    # Método mantido para compatibilidade, embora o _load_details_for_editing seja preferido na edição
    # O AddEventDialog.__init__ agora o utiliza se appointment_details for passado.
    def set_compromisso_details(self, data_str, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes):
        """ Método auxiliar para carregar dados para edição. """
        self.setWindowTitle(f"Editar Visita de {nome_cliente} ({QDate.fromString(data_str, 'yyyy-MM-dd').toString('dd/MM/yyyy')})")
        self.data_selecionada = data_str 
        
        self.time_input.setTime(QTime.fromString(hora, "HH:mm"))
        self.cliente_input.setText(nome_cliente)
        self.obs_input.setText(observacoes)
        self.endereco_input.setText(endereco)
        
        self.tipo_visita_input.setCurrentText(tipo_visita)
        self.local_visita_input.setCurrentText(local_visita)
        
        self.quem_vai_input.setText(quem_vai)
        
        # Garante que o campo de endereço esteja visível/oculto corretamente
        self._toggle_endereco_field(local_visita)


# --- AGENDA APP (PRINCIPAL) ---

class AgendaApp(QWidget):
    def __init__(self):
        super().__init__()
        
        # Inicialização do DB Manager
        self.db_manager = DataManager()
        
        self.setWindowTitle("Agenda Data Servis")
        self.init_ui()
        
    def init_ui(self):
        app.setStyleSheet(QSS_STYLES)
        
        main_layout = QHBoxLayout()

        self.calendar = QCalendarWidget()
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
        
        # O BOTÃO DE EDIÇÃO FOI REMOVIDO DA UI

        self.deleteButton = QPushButton(" - Excluir Compromisso Selecionado ")
        self.deleteButton.setObjectName("DeleteButton") 
        self.deleteButton.clicked.connect(self.delete_selected_appointment)
        self.deleteButton.setStyleSheet("background-color: #cc0000; color: white;") 
        
        right_panel.addWidget(self.day_title)
        right_panel.addWidget(self.appointment_list)
        right_panel.addWidget(self.addButton)
        right_panel.addWidget(self.deleteButton) 

        right_container = QWidget()
        right_container.setStyleSheet("background-color: white; border-radius: 8px;")
        right_container.setLayout(right_panel)
        
        _apply_shadow(right_container)

        main_layout.addWidget(right_container, 35)

        self.setLayout(main_layout)
        
        _apply_shadow(self.addButton)
        _apply_shadow(self.deleteButton) 

        self.update_daily_appointments()
        
    # MÉTODO DE ATUALIZAÇÃO (CORRIGIDO: Horizontal + Cor)
    def update_daily_appointments(self):
        selected_date_qdate = self.calendar.selectedDate()
        selected_date_str = selected_date_qdate.toString("yyyy-MM-dd")
        display_date_str = selected_date_qdate.toString("dd 'de' MMMM 'de' yyyy")
        
        self.day_title.setText(f"Compromissos para:\n{display_date_str}")
        
        daily_events = self.db_manager.get_compromissos_by_date(selected_date_str) 
        
        self.appointment_list.clear()
        
        if daily_events:
            # 🛑 ATUALIZADO: Inclui endereco e quem_vai (8 campos)
            for event_id, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes in daily_events: 
                
                # 🛑 WIDGET PERSONALIZADO
                item_widget = AppointmentItemWidget(
                    hora=hora, 
                    nome_cliente=nome_cliente, 
                    tipo_visita=tipo_visita, 
                    local_visita=local_visita, 
                    observacoes=observacoes, 
                    endereco=endereco,
                    quem_vai=quem_vai 
                )
                
                # Cria o QListWidgetItem
                item = QListWidgetItem(self.appointment_list)
                
                # Define a cor do fundo
                color_hex = get_color_by_type(tipo_visita)
                item.setBackground(QColor(color_hex))
                
                # Define o tamanho e atribui o widget
                item.setSizeHint(item_widget.sizeHint())
                self.appointment_list.setItemWidget(item, item_widget)

                item.setData(Qt.UserRole, event_id) 
                self.appointment_list.addItem(item)
        else:
            item = QListWidgetItem("Nenhum compromisso agendado.")
            item.setSizeHint(QSize(self.appointment_list.width(), 40)) 
            self.appointment_list.addItem(item)
            
    def open_add_dialog(self):
        selected_date = self.calendar.selectedDate()
        dialog = AddEventDialog(selected_date, parent=self)
        
        if dialog.exec_() == QDialog.Accepted:
            data_to_save = dialog.novo_compromisso
            
            # 🛑 ATUALIZADO: add_compromisso com 8 argumentos
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

    # MÉTODO DE EDIÇÃO (CHAMADO PELO DUPLO CLIQUE)
    def open_edit_dialog(self, item=None):
        
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
            
        # 1. Busca os dados atuais do banco (retorna 8 campos)
        details_tuple = self.db_manager.get_compromisso_by_id(compromisso_id)
        
        if not details_tuple:
            QMessageBox.critical(self, "Erro", "Não foi possível carregar os dados do compromisso.")
            return

        # data_str é o primeiro elemento da tupla (índice 0)
        data_str = details_tuple[0] 
        selected_date_qdate = QDate.fromString(data_str, "yyyy-MM-dd")
        
        # 2. Configura o AddEventDialog para edição
        # Passamos a tupla completa como 'appointment_details' para o construtor
        dialog = AddEventDialog(
            selected_date_qdate, 
            appointment_details=details_tuple, 
            parent=self
        )
        # O ID é salvo no dialog para ser usado na atualização
        dialog.compromisso_id = compromisso_id 

        # 3. Executa o diálogo e salva se aceito
        if dialog.exec_() == QDialog.Accepted:
            data_to_save = dialog.novo_compromisso
            
            # 🛑 ATUALIZAÇÃO NO BANCO (com 8 argumentos)
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


    def closeEvent(self, event):
        self.db_manager.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AgendaApp()
    window.showMaximized()
    sys.exit(app.exec_())
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
        padding: 8px;
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
"""

# --- FUNÇÕES AUXILIARES GLOBAIS (CORREÇÃO DE ESCOPO) ---

def get_color_by_type(tipo_visita):
    """ Mapeia o tipo de visita para uma cor de fundo. """
    colors = {
        "Treinamento": "#e6f7ff",   # Azul Claro (Sky Blue)
        "Visita Técnica": "#fff7e6", # Amarelo Claro (Light Orange/Gold)
        "Outro": "#f0fff0",          # Verde Claro Quase Branco (Honeydew)
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

# --- DIÁLOGO DE ADIÇÃO/EDIÇÃO DE EVENTO ---

class AddEventDialog(QDialog):
    def __init__(self, selected_date, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Agendar Visita para {selected_date.toString('dd/MM/yyyy')}")
        self.resize(500, 380)
        _center_window(self)
        
        self.data_selecionada = selected_date.toString("yyyy-MM-dd")
        self.novo_compromisso = None

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
        layout.addRow("Tipo de Visita:", self.tipo_visita_input)

        # 4. Local da Visita (ComboBox)
        self.local_visita_input = QComboBox(self)
        self.local_visita_input.addItems(["Escritório", "No Cliente"])
        layout.addRow("Local:", self.local_visita_input)
        
        # 5. Observações (Multi-linha)
        self.obs_input = QTextEdit(self)
        self.obs_input.setFixedHeight(80)
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

    def save_compromisso(self):
        hora = self.time_input.time().toString("HH:mm")
        cliente = self.cliente_input.text().strip()
        tipo_visita = self.tipo_visita_input.currentText()
        local_visita = self.local_visita_input.currentText()
        observacoes = self.obs_input.toPlainText().strip()
        
        if not cliente:
            QMessageBox.warning(self, "Erro de Entrada", "O nome do cliente não pode ser vazio.")
            return

        self.novo_compromisso = {
            "data": self.data_selecionada,
            "hora": hora,
            "nome_cliente": cliente,
            "tipo_visita": tipo_visita,
            "local_visita": local_visita,
            "observacoes": observacoes
        }
        
        self.accept()

# --- AGENDA APP (PRINCIPAL) ---

class AgendaApp(QWidget):
    def __init__(self):
        super().__init__()
        
        # Inicialização do DB Manager
        self.db_manager = DataManager()
        
        self.setWindowTitle("Agenda Moderna (PyQt5) - Gerenciamento de Visitas")
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

        self.addButton = QPushButton(" + Adicionar Nova Visita ")
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
            for event_id, hora, nome_cliente, tipo_visita, local_visita, observacoes in daily_events:
                
                obs_limit = 40
                obs_display = observacoes
                if observacoes and len(observacoes) > obs_limit:
                    obs_display = observacoes[:obs_limit] + '...'
                elif not observacoes:
                    obs_display = 'Nenhuma'

                # FORMATAÇÃO HORIZONTAL (COMPACTA)
                item_text = (
                    f"**[ {hora} ]** | "
                    f"**Cliente:** {nome_cliente} | "
                    f"**Tipo:** {tipo_visita} | "
                    f"**Local:** {local_visita} | "
                    f"**Obs:** {obs_display}"
                )
                
                item = QListWidgetItem(item_text)
                
                # APLICAÇÃO DA COR DE FUNDO (Usando a função global)
                color_hex = get_color_by_type(tipo_visita)
                item.setBackground(QColor(color_hex))
                
                # DEFINE A ALTURA PARA UMA ÚNICA LINHA
                item.setSizeHint(QSize(self.appointment_list.width(), 30))
                
                item.setData(Qt.UserRole, event_id) 
                
                self.appointment_list.addItem(item)
        else:
            item = QListWidgetItem("Nenhum compromisso agendado.")
            self.appointment_list.addItem(item)
            
    def open_add_dialog(self):
        selected_date = self.calendar.selectedDate()
        dialog = AddEventDialog(selected_date, self)
        
        if dialog.exec_() == QDialog.Accepted:
            data_to_save = dialog.novo_compromisso
            
            self.db_manager.add_compromisso(
                data_to_save['data'],
                data_to_save['hora'],
                data_to_save['nome_cliente'],
                data_to_save['tipo_visita'],
                data_to_save['local_visita'],
                data_to_save['observacoes']
            )
            
            self.update_daily_appointments()
            QMessageBox.information(self, "Sucesso", "Visita agendada com sucesso!")

    # MÉTODO DE EDIÇÃO (CHAMADO PELO DUPLO CLIQUE)
    def open_edit_dialog(self, item=None):
        
        if item is not None:
            # Se chamado pelo duplo clique, o item é passado diretamente
            selected_item = item
        else:
            # Se chamado de outra forma (ex: botão, mas foi removido), busca o item selecionado
            selected_items = self.appointment_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Seleção Inválida", "Por favor, selecione um compromisso para editar.")
                return
            selected_item = selected_items[0]

        compromisso_id = selected_item.data(Qt.UserRole)
        
        # Certifica que não estamos tentando editar a linha "Nenhum compromisso agendado."
        if compromisso_id is None:
            QMessageBox.warning(self, "Erro", "Não é um compromisso válido para edição.")
            return
            
        # 1. Busca os dados atuais do banco
        details_tuple = self.db_manager.get_compromisso_by_id(compromisso_id)
        
        if not details_tuple:
            QMessageBox.critical(self, "Erro", "Não foi possível carregar os dados do compromisso.")
            return

        data_str, hora, nome_cliente, tipo_visita, local_visita, observacoes = details_tuple
        
        # 2. Configura o AddEventDialog para edição
        selected_date_qdate = QDate.fromString(data_str, "yyyy-MM-dd")
        dialog = AddEventDialog(selected_date_qdate, self)
        
        # 3. Pré-popular o diálogo com os dados existentes
        dialog.setWindowTitle(f"Editar Visita de {nome_cliente} ({selected_date_qdate.toString('dd/MM/yyyy')})")
        dialog.data_selecionada = data_str 
        
        dialog.time_input.setTime(QTime.fromString(hora, "HH:mm"))
        dialog.cliente_input.setText(nome_cliente)
        dialog.obs_input.setText(observacoes)
        
        dialog.tipo_visita_input.setCurrentText(tipo_visita)
        dialog.local_visita_input.setCurrentText(local_visita)

        # 4. Executa o diálogo e salva se aceito
        if dialog.exec_() == QDialog.Accepted:
            data_to_save = dialog.novo_compromisso
            
            # ATUALIZAÇÃO NO BANCO
            if self.db_manager.update_compromisso(
                compromisso_id,
                data_to_save['data'],
                data_to_save['hora'],
                data_to_save['nome_cliente'],
                data_to_save['tipo_visita'],
                data_to_save['local_visita'],
                data_to_save['observacoes']
            ):
                QMessageBox.information(self, "Sucesso", "Compromisso atualizado com sucesso!")
                self.update_daily_appointments()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao atualizar o compromisso no banco de dados.")

    def delete_selected_appointment(self):
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
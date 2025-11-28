import sqlite3
import os
import sys
from datetime import date # Importado para obter a data atual

class DataManager:
    def __init__(self, db_name='agenda.db'):
        # Determinar o diretório base do aplicativo
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        # Definir e criar a pasta 'Data'
        data_folder = os.path.join(base_dir, 'Data')
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        
        # Definir o caminho completo do banco de dados
        db_path = os.path.join(data_folder, db_name)
        
        # Conectar ao banco de dados
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        self._create_table()

    def _create_table(self):
        """ Cria a tabela 'compromissos' com todos os campos necessários. """
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS compromissos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                hora TEXT NOT NULL,
                nome_cliente TEXT NOT NULL,          
                tipo_visita TEXT NOT NULL,          
                local_visita TEXT NOT NULL,          
                endereco TEXT,                      
                quem_vai TEXT,                      
                observacoes TEXT                     
            );
        """)
        self.conn.commit()
    
    def add_compromisso(self, data, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes):
        """ Adiciona um novo agendamento com todos os detalhes. """
        try:
            self.cursor.execute("""
                INSERT INTO compromissos (data, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (data, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Erro ao adicionar compromisso: {e}")
            return None

    def get_compromissos_by_date(self, data):
        """ Retorna todos os compromissos para a data, incluindo os novos campos. """
        self.cursor.execute("""
            SELECT id, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes 
            FROM compromissos 
            WHERE data = ?
            ORDER BY hora ASC;
        """, (data,))
        return self.cursor.fetchall()
    
    def delete_compromisso(self, compromisso_id):
        """ Remove um compromisso do banco de dados pelo seu ID. """
        try:
            self.cursor.execute("""
                DELETE FROM compromissos WHERE id = ?;
            """, (compromisso_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao excluir compromisso: {e}")
            return False
    
    def get_compromisso_by_id(self, compromisso_id):
        """ Retorna todos os detalhes de um compromisso pelo seu ID. """
        self.cursor.execute("""
            SELECT data, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes 
            FROM compromissos 
            WHERE id = ?;
        """, (compromisso_id,))
        return self.cursor.fetchone()

    def update_compromisso(self, compromisso_id, data, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes):
        """ Atualiza um compromisso existente no banco de dados. """
        try:
            self.cursor.execute("""
                UPDATE compromissos
                SET data=?, hora=?, nome_cliente=?, tipo_visita=?, local_visita=?, endereco=?, quem_vai=?, observacoes=?
                WHERE id=?;
            """, (data, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes, compromisso_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao atualizar compromisso: {e}")
            return False

    def get_future_appointments(self):
        """ Retorna todos os compromissos com data estritamente MAIOR que a data atual. """
        today_str = date.today().strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT id, data, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes 
            FROM compromissos 
            WHERE data > ?
            ORDER BY data ASC, hora ASC;
        """, (today_str,))
        return self.cursor.fetchall()

    def get_past_appointments(self):
        """ Retorna todos os compromissos com data MENOR ou IGUAL à data atual. """
        today_str = date.today().strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT id, data, hora, nome_cliente, tipo_visita, local_visita, endereco, quem_vai, observacoes 
            FROM compromissos 
            WHERE data <= ?
            ORDER BY data DESC, hora DESC;
        """, (today_str,))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()
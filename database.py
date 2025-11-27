import sqlite3
import os
import sys

class DataManager:
    def __init__(self, db_name='agenda.db'):
        # 1. Determinar o diretório base do aplicativo (onde o .py ou .exe está)
        if getattr(sys, 'frozen', False):
            # Se for executável (.exe), use o diretório temporário
            base_dir = os.path.dirname(sys.executable)
        else:
            # Se for script (.py), use o diretório do script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        # 2. Definir o caminho completo da pasta 'Data'
        data_folder = os.path.join(base_dir, 'Data')
        
        # 3. Criar a pasta 'Data' se ela não existir
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        
        # 4. Definir o caminho completo do banco de dados
        db_path = os.path.join(data_folder, db_name)
        
        # Conectar ao banco de dados no novo caminho
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        self._create_table()

    def _create_table(self):
        """
        Cria a tabela 'compromissos' com a nova estrutura de 6 campos.
        (Remover o arquivo agenda.db antigo é ESSENCIAL para que esta nova estrutura seja criada!)
        """
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS compromissos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                hora TEXT NOT NULL,
                nome_cliente TEXT NOT NULL,          
                tipo_visita TEXT NOT NULL,          
                local_visita TEXT NOT NULL,          
                observacoes TEXT                     
            );
        """)
        self.conn.commit()
    
    def add_compromisso(self, data, hora, nome_cliente, tipo_visita, local_visita, observacoes):
        """ Adiciona um novo agendamento com todos os detalhes. """
        try:
            self.cursor.execute("""
                INSERT INTO compromissos (data, hora, nome_cliente, tipo_visita, local_visita, observacoes)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (data, hora, nome_cliente, tipo_visita, local_visita, observacoes))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Erro ao adicionar compromisso: {e}")
            return None

    def get_compromissos_by_date(self, data):
        """ Retorna todos os compromissos para a data, incluindo os novos campos. """
        self.cursor.execute("""
            SELECT id, hora, nome_cliente, tipo_visita, local_visita, observacoes 
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
            SELECT data, hora, nome_cliente, tipo_visita, local_visita, observacoes 
            FROM compromissos 
            WHERE id = ?;
        """, (compromisso_id,))
        # Retorna o primeiro (e único) resultado
        return self.cursor.fetchone()

    def update_compromisso(self, compromisso_id, data, hora, nome_cliente, tipo_visita, local_visita, observacoes):
        """ Atualiza um compromisso existente no banco de dados. """
        try:
            self.cursor.execute("""
                UPDATE compromissos
                SET data=?, hora=?, nome_cliente=?, tipo_visita=?, local_visita=?, observacoes=?
                WHERE id=?;
            """, (data, hora, nome_cliente, tipo_visita, local_visita, observacoes, compromisso_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao atualizar compromisso: {e}")
            return False

    def close(self):
        self.conn.close()

# FIM do arquivo database.py
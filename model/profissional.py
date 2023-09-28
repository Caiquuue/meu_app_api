from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Union

from  model import Base, Conhecimento


class Profissional(Base):
    __tablename__ = 'profissional'

    id = Column(Integer, primary_key=True)
    celular = Column(String)
    email = Column(String)
    nome = Column(String(140), unique=True)
    data_insercao = Column(DateTime, default=datetime.now())

    # Definição do relacionamento entre o profissional e o conhecimento.
    # Essa relação é implicita, não está salva na tabela 'profissional',
    # mas aqui estou deixando para SQLAlchemy a responsabilidade
    # de reconstruir esse relacionamento.
    conhecimentos = relationship("Conhecimento")

    def __init__(self, nome:str, celular:str, email:str,
                 data_insercao:Union[DateTime, None] = None):
        """
        Cria um profissional

        Arguments:
            nome: nome do profissional.
            celular: celular do profissional
            email: email do profissional
            data_insercao: data de quando o profissional foi inserido à base
        """
        self.nome = nome
        self.celular = celular
        self.email = email

        # se não for informada, será o data exata da inserção no banco
        if data_insercao:
            self.data_insercao = data_insercao

    def adiciona_conhecimento(self, conhecimento:Conhecimento):
        """ Adiciona um novo conhecimento ao profissional
        """
        self.conhecimentos.append(conhecimento)


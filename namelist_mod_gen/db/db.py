from contextlib import contextmanager

from sqlalchemy import Column, create_engine, DateTime, String
from sqlalchemy.ext.declarative import AbstractConcreteBase, declared_attr
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


class Language(AbstractConcreteBase, Base):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    english = Column(String, primary_key=True)
    translation = Column(String)
    translators = Column(String)
    translator_mode = Column(String)
    namelist_category = Column(String)
    translation_date = Column(DateTime)


class French(Language):
    pass


class German(Language):
    pass


class Japanese(Language):
    pass


class Korean(Language):
    pass


class Polish(Language):
    pass


class Russian(Language):
    pass


class Spanish(Language):
    pass


class Chinese(Language):
    __tablename__ = 'simp_chinese'


class Portuguese(Language):
    __tablename__ = 'braz_por'


class Connection:
    def __init__(self, db_path):
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)

        try:
            Base.metadata.create_all(self.engine)
        except Exception as e:
            raise RuntimeError(f"Error creating tables: {str(e)}")

    def get_language(self, language_name):
        # Get the language class corresponding to the given name
        if language_name == 'french':
            return French
        elif language_name == 'german':
            return German
        elif language_name == 'japanese':
            return Japanese
        elif language_name == 'korean':
            return Korean
        elif language_name == 'polish':
            return Polish
        elif language_name == 'russian':
            return Russian
        elif language_name == 'spanish':
            return Spanish
        elif language_name == 'simp_chinese':
            return Chinese
        elif language_name == 'braz_por':
            return Portuguese
        else:
            raise ValueError(f"Unsupported language: {language_name}")

    @contextmanager
    def session_scope(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def get_language_dict(self, language):
        """
        Given a language name, return a dictionary containing all the entries
        for that language in the database.

        :param language: the name of the language
        :return: a dictionary containing all the entries for that language
        """
        language = self.get_language(language)
        result = {}
        with self.session_scope() as session:
            query = session.query(language)
            for row in query.all():
                result[row.english] = row.translation
        return result

    def add_row(self, language, english, translation, translators, translator_mode, namelist_category,
                translation_date):
        with self.session_scope() as session:
            row = language(english=english, translation=translation, translators=translators,
                           translator_mode=translator_mode, namelist_category=namelist_category,
                           translation_date=translation_date)
            session.add(row)

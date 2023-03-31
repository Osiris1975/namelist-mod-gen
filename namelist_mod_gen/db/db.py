from contextlib import contextmanager

from sqlalchemy import Column, create_engine, DateTime, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


class Translation(Base):
    __tablename__ = 'translations'
    id = Column(Integer, primary_key=True)
    localisation_key = Column(String, unique=True)
    language = Column(String)
    english = Column(String)
    translation = Column(String)
    translators = Column(String)
    translator_mode = Column(String)
    namelist_category = Column(String)
    translation_date = Column(DateTime)


class Connection:
    def __init__(self, db_path):
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
        try:
            Base.metadata.create_all(self.engine)
        except Exception as e:
            raise RuntimeError(f"Error creating tables: {str(e)}")

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
        result = {}
        with self.session_scope() as session:
            for t in session.query(Translation).filter(Translation.language == language):
                result[t.english] = t.translation
        return result

    def add_row(self, localisation_key, language, english, translation, translators, translator_mode, namelist_category,
                translation_date):
        with self.session_scope() as session:
            row = Translation(localisation_key=localisation_key, english=english, translation=translation,
                              translators=translators, language=language,
                              translator_mode=translator_mode, namelist_category=namelist_category,
                              translation_date=translation_date)
            session.add(row)

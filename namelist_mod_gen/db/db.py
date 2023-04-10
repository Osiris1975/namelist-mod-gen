import logging

import constants.constants as c
from sqlalchemy import Column, create_engine, DateTime, String, Integer, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

Base = declarative_base()

log = logging.getLogger('NMG')


class Translation(Base):
    __tablename__ = 'translations'
    id = Column(Integer, primary_key=True, autoincrement=True, server_default='int')
    localisation_key = Column(String)
    language = Column(String)
    english = Column(String)
    translated = Column(String)
    translators = Column(String)
    translator_mode = Column(String)
    namelist_category = Column(String)
    translation_date = Column(DateTime)
    __table_args__ = (UniqueConstraint('localisation_key', 'translated', 'language'),)


class Connection(object):
    def __init__(self, db_path, pool_size=10, max_overflow=20, pool_timeout=30):
        try:
            self.engine = create_engine(db_path, pool_size=pool_size, max_overflow=max_overflow,
                                        pool_timeout=pool_timeout)
            self.session_factory = sessionmaker(bind=self.engine)
            Base.metadata.create_all(self.engine)
        except Exception as e:
            raise RuntimeError(f"Error creating tables: {str(e)}")
        self.session = scoped_session(self.session_factory)

    def get_language_dict(self, language):
        """
        Given a language name, return a dictionary containing all the entries
        for that language in the database.

        :param language: the name of the language
        :return: a dictionary containing all the entries for that language
        """
        result = {}
        with self.session() as session:
            for t in session.query(Translation).filter(Translation.language == language):
                result[t.localisation_key] = t.translated
        return result

    def add_many(self, objects, translators, translator_mode, language, translation_date):
        insert_objects = []
        for loc_key, o in objects.items():
            category = None
            for k, v in c.NAMELIST_CATEGORY_TAGS.items():
                if k in loc_key:
                    category = v
            insert_objects.append(
                Translation(
                    localisation_key=loc_key, english=o['detokenized_txt'], translated=o['translation'],
                    translators=translators, language=language,
                    translator_mode=translator_mode, namelist_category=category,
                    translation_date=translation_date
                ))
        self.session.bulk_save_objects(insert_objects)
        self.session.commit()

    def add_row(self, localisation_key, language, english, translation, translators, translator_mode, namelist_category,
                translation_date, replace=False):
        instance = self.session.query(Translation).filter_by(localisation_key=localisation_key, translated=translation,
                                                             language=language).first()
        if instance and not replace:
            log.warning(f'Record with primary keys already exists: {localisation_key, translation, language}')
            return None
        row = Translation(localisation_key=localisation_key, english=english, translated=translation,
                          translators=translators, language=language,
                          translator_mode=translator_mode, namelist_category=namelist_category,
                          translation_date=translation_date)
        row_dict = {key: value for key, value in row.__dict__.items() if
                    key in Translation.__table__.columns.keys()}
        if replace:
            self.session.merge(row)
        else:
            self.session.add(row)
        self.session.commit()
        log.debug(f'Translation row committed: {row_dict}')

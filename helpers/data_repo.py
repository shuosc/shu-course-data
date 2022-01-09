import datetime
import json
import os
from dataclasses import dataclass

from typing import List, Dict


@dataclass
class Term:
    folder_name: str
    term_id: str
    term_name: str
    hash: str
    backend_origin: str
    update_time_ms: int
    num_courses: int

    @property
    def update_time(self):
        return datetime.datetime.fromtimestamp(self.update_time_ms)

    def get_courses(self):
        with open(os.path.join(self.folder_name, 'terms', f'{self.term_id}.json')) as fp:
            return json.load(fp)['courses']


class DataRepo:
    __current_term_id_list: List[str]
    __terms: List[Term]
    __terms_dict: Dict[str, Term]

    def __init__(self, folder_name: str):
        self.__terms = []
        with open(os.path.join(folder_name, 'current.json')) as fp:
            self.__current_term_id_list = json.load(fp)
        term_filename_list = [x for x in os.listdir(os.path.join(folder_name, 'terms')) if x.endswith('.json')]
        for filename in term_filename_list:
            with open(os.path.join(folder_name, 'terms', filename)) as fp:
                data = json.load(fp)
                self.__terms.append(
                    Term(
                        folder_name=folder_name,
                        term_id=filename[:-5],
                        term_name=data['termName'],
                        hash=data['hash'],
                        backend_origin=data['backendOrigin'],
                        update_time_ms=data['updateTimeMs'],
                        num_courses=len(data['courses'])
                    )
                )
        self.__terms_dict = {x.term_id: x for x in self.__terms}

    @property
    def current_term_id_list(self) -> List[str]:
        return self.__current_term_id_list

    @property
    def terms(self) -> List[Term]:
        return self.__terms

    @property
    def terms_dict(self) -> Dict[str, Term]:
        return self.__terms_dict

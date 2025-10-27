from typing import List
from src.core.entity import EntitiesContainer, Entity, collect_docs_entities, collect_files_and_json_entities
from src.core.project import Project
from src.helpers.comparison import fuzzy_intersection
from src.core.base_usecase import BaseUseCase

class PartialMatch(BaseUseCase):

    def __init__(self, project: Project):
        super().__init__(project)

    def find_partials(self, ent1: List[EntitiesContainer], ent2: List[EntitiesContainer]):
        report = ""
        for e1 in ent1:
            e1s = [str(e) for e in e1.entities]
            for e2 in ent2:
                e2s = [str(e) for e in e2.entities]
                # if "embedding" in e1:
                #     print(e1, e2)
                if fuzzy_intersection(e1s, e2s):
                    e1_from = e1.parent + " (" + e1.type + ")"
                    e2_from = e2.parent + " (" + e2.type + ")"
                    report += "Partial match found:\n"
                    report += " - From files: " + ", ".join(e1s) + " " + e1_from + " \n"
                    report += " - From docs:  " + ", ".join(e2s) + " " + e2_from + "\n++++++++++++++++++++++++++++++++++++++++++++++++\n"

        return report


    def report(self):
        files_entities = collect_files_and_json_entities(self.project)
        docs_entities = collect_docs_entities(self.project.documentation)
        return self.find_partials(files_entities, docs_entities)
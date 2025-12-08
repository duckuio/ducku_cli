from typing import List
from src.core.entity import EntitiesContainer, Entity, collect_docs_entities, collect_project_entities
from src.core.project import Project
from src.helpers.comparison import fuzzy_intersection
from src.core.base_usecase import BaseUseCase

class PartialMatch(BaseUseCase):

    def __init__(self, project: Project):
        super().__init__(project)
        self.name = "partial_lists"

    def find_partials(self, ent1: List[EntitiesContainer], ent2: List[EntitiesContainer]):
        report = ""
        for e1 in ent1:
            e1s = [str(e) for e in e1.entities]
            for e2 in ent2:
                e2s = [str(e) for e in e2.entities]
                # if "embedding" in e1:
                #     print(e1, e2)
                if fuzzy_intersection(e1s, e2s):
                    # Skip perfect matches (both lists have same unique items after case-insensitive comparison)
                    e1_unique_lower = set(s.lower() for s in e1s)
                    e2_unique_lower = set(s.lower() for s in e2s)
                    if e1_unique_lower == e2_unique_lower:
                        continue
                    
                    # Calculate differences using case-insensitive comparison
                    # Create mapping of lowercase -> original for both lists
                    e1_map = {s.lower(): s for s in e1s}
                    e2_map = {s.lower(): s for s in e2s}
                    
                    e1_lower_set = set(e1_map.keys())
                    e2_lower_set = set(e2_map.keys())
                    
                    # Find differences and map back to original case
                    only_in_project = sorted([e1_map[k] for k in (e1_lower_set - e2_lower_set)])
                    only_in_docs = sorted([e2_map[k] for k in (e2_lower_set - e1_lower_set)])
                    
                    e1_from = e1.parent + " (" + e1.type + ")"
                    e2_from = e2.parent + " (" + e2.type + ")"
                    report += "Partial match found:\n"
                    report += " - From project: " + ", ".join(e1s) + " " + e1_from + " \n"
                    report += " - From docs:  " + ", ".join(e2s) + " " + e2_from + "\n"
                    
                    if only_in_project:
                        report += " 🔴 Missing in docs: " + ", ".join(only_in_project) + "\n"
                    if only_in_docs:
                        report += " 🔴 Missing in project: " + ", ".join(only_in_docs) + "\n"
                    
                    report += "++++++++++++++++++++++++++++++++++++++++++++++++\n"

        return report


    def report(self):
        files_entities = collect_project_entities(self.project)
        docs_entities = collect_docs_entities(self.project.documentation)
        
        # Remove duplicate docs containers by comparing actual entity string values
        # Also filter out containers with more than 20 entities (generic navigation/menus)
        # Files are kept as-is - they're always unique and meaningful
        seen_entity_sets = []
        unique_docs = []
        for e in docs_entities:
            # Get the actual string values of entities
            entity_strings = sorted([str(entity) for entity in e.entities])
            # Check if this set of strings already exists and size is reasonable
            if entity_strings not in seen_entity_sets and 0 < len(entity_strings) <= 15:
                seen_entity_sets.append(entity_strings)
                unique_docs.append(e)
        
        print(f"{len(files_entities)} files entities collected")
        print(f"{len(docs_entities)} docs entities collected -> {len(unique_docs)} unique (max 20 entities)")
        
        # print([fe.entities for fe in files_entities])
        # print([de.entities for de in unique_docs])

        return self.find_partials(files_entities, unique_docs)
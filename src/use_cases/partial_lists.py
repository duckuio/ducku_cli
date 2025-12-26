from typing import List
from src.core.entity import EntitiesContainer, collect_docs_entities, collect_project_entities
from src.core.project import Project
from src.helpers.comparison import fuzzy_intersection, normalize_string
from src.core.base_usecase import BaseUseCase

class PartialMatch(BaseUseCase):

    def __init__(self, project: Project):
        super().__init__(project)
        self.name = "partial_lists"

    def find_partials(self, project_containers: List[EntitiesContainer], docs_containers: List[EntitiesContainer]):
        '''
        This function compares 2 lists of EntitiesContainer: from project code and from documentation.
        Each containers consists of entities (strings) collected from code or docs.
        2 lists of entities are compared using fuzzy matching to find partial overlaps.
        According to certain rules, if it turns out that lists belong to the same domain,
        then it checks if some entities are missing in documentation compared to project code and
        reports it.
        '''
        report = ""
        seen_pairs = set()
        for e1 in project_containers:
            e1s = [str(e) for e in e1.entities]
            for e2 in docs_containers:
                e2s = [e.content for e in e2.entities]
                # Uncomment only if there are really such cases in reality. For now skipping
                # @TODO Performace improvement, use sorted tuples of indexes instead
                # key = (
                #     frozenset(normalize_string(s) for s in e1s),
                #     frozenset(normalize_string(s) for s in e2s),
                # )

                # # if something has already matched, don't consider it anymore to prevent double comparison
                # if key in seen_pairs:
                #     continue

                match = fuzzy_intersection(e1s, e2s, False)
                
                if not match:
                    continue
                
                e1_from = e1.parent + " (" + e1.type + ")"
                e2_from = e2.parent + " (" + e2.type + ")"
                report += "Partial match found:\n"
                report += " - From project: " + ", ".join(e1s) + " " + e1_from + " \n"
                report += " - From docs:  " + ", ".join(e2s) + " " + e2_from + "\n"
                
                if match.only_a:
                    report += " 🔴 Missing in docs: " + ", ".join(match.only_a) + "\n"
                # Code is the source of truth; do not report items missing in project
                
                report += "Debug: " + ", ".join(match.matched_debug) + "\n"
                report += "++++++++++++++++++++++++++++++++++++++++++++++++\n"

                #seen_pairs.add(key)

        return report


    def report(self):
        files_entities = collect_project_entities(self.project)
        docs_entities = collect_docs_entities(self.project.documentation)
        
        # Deduplicate docs containers by source (parent,type) keeping the largest set
        # Normalize strings to avoid minor formatting differences causing splits
        docs_by_source = {}
        for e in docs_entities:
            key = (e.parent, e.type)
            strings_norm = sorted([normalize_string(str(entity)) for entity in e.entities])
            if 0 < len(strings_norm) <= 20:
                if key not in docs_by_source:
                    docs_by_source[key] = (strings_norm, e)
                else:
                    current_strings, _ = docs_by_source[key]
                    # Prefer the container with more items (likely the complete list)
                    if len(strings_norm) > len(current_strings):
                        docs_by_source[key] = (strings_norm, e)
        unique_docs = [v[1] for v in docs_by_source.values()]
        
        # Deduplicate project containers by normalized entity string sets as well
        seen_proj_sets = []
        unique_proj = []
        for e in files_entities:
            entity_strings = sorted([normalize_string(str(entity)) for entity in e.entities])
            if entity_strings not in seen_proj_sets and 0 < len(entity_strings) <= 50:
                seen_proj_sets.append(entity_strings)
                unique_proj.append(e)

        print(f"{len(files_entities)} files entities collected -> {len(unique_proj)} unique")
        print(f"{len(docs_entities)} docs entities collected -> {len(unique_docs)} unique (kept largest per source)")
        
        # print([fe.entities for fe in files_entities])
        # print([de.entities for de in unique_docs])

        return self.find_partials(unique_proj, unique_docs)
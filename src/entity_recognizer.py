"""
Entity Recognizer Module.
Uses Spacy NER to filter articles and ensure they are about specific persons.
"""
import spacy
import logging

logger = logging.getLogger('news_tracker')

class EntityRecognizer:
    def __init__(self, model_name="en_core_web_sm"):
        try:
            logger.info(f"Loading Spacy model: {model_name}")
            self.nlp = spacy.load(model_name)
        except OSError:
            logger.warning(f"Model {model_name} not found. Downloading...")
            from spacy.cli import download
            download(model_name)
            self.nlp = spacy.load(model_name)

        # Add custom rules for our VIPs
        # Add after NER so we don't overwrite if Spacy already found something better (e.g. Modi Toys -> ORG)
        if "entity_ruler" not in self.nlp.pipe_names:
            ruler = self.nlp.add_pipe("entity_ruler", after="ner")
            patterns = [
                {"label": "PERSON", "pattern": "Narendra Modi"},
                {"label": "PERSON", "pattern": "PM Modi"},
                {"label": "PERSON", "pattern": "Modi"}, 
                {"label": "PERSON", "pattern": "Prime Minister Modi"},
                {"label": "PERSON", "pattern": "CR Patil"},
                {"label": "PERSON", "pattern": "C.R. Patil"},
                {"label": "PERSON", "pattern": "C R Patil"},
            ]
            ruler.add_patterns(patterns)

    def verify_person(self, text, person_name):
        """
        Check if the person is mentioned as a specific entity (PERSON) in the text.
        
        Args:
            text (str): The article text or title.
            person_name (str): The name of the person to verify.
            
        Returns:
            bool: True if the person is found as a named entity.
        """
        if not text:
            return False
            
        doc = self.nlp(text)
        
        # Normalize person name for comparison
        target_parts = person_name.lower().split()
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                ent_text_lower = ent.text.lower()
                # Check match: either full name match OR alias match
                # If the entity is "PM Modi", and we search for "Narendra Modi", 
                # we need to know that "Modi" matches.
                
                # Check intersection of names
                if any(part in ent_text_lower for part in target_parts if len(part) > 2):
                    logger.debug(f"Entity Match: Found '{ent.text}' matching '{person_name}'")
                    return True
                    
        return False

    def extract_entities(self, text):
        """Extract all PERSON and ORG entities from text."""
        if not text:
            return []
            
        doc = self.nlp(text)
        return [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in ["PERSON", "ORG"]]

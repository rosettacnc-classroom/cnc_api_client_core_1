"""Module with a light and simple implementation of Memento pattern."""
#-------------------------------------------------------------------------------
# Name:         cnc_memento
#
# Purpose:      Light and simple implementation of Memento pattern.
#               CNCMemento is used to load & store of fields in a tree structure
#               using Python dictionaries and JSON as final media to store data
#               on any support media (file, buffer, socket, string, etc.)
#
# Note          Checked with Python 3.11.9
#
# Author:       support@rosettacnc.com
#
# Created:      07/12/2024
# Copyright:    RosettaCNC (c) 2016-2024
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
import json

class CncMemento:
    """Class with a light and simple implementation of Memento pattern."""

    document = {'root': {}}
    element = document['root']

    @staticmethod
    def create_write_root(key: str):
        """Xxx..."""
        document = {key: {}}
        element = document[key]
        return CncMemento(document, element)

    @staticmethod
    def create_read_root(file_name: str, key: str):
        """Xxx..."""
        try:
            document = {key: {}}
            element = document[key]
            memento = CncMemento(document, element)
            with open(file_name, "r") as f:
                s = f.read()
            memento.document = json.loads(s)
            memento.element = memento.document[key]
            return memento
        except:
            return None

    def __init__(self, document: dict, element: dict):
        self.document = document
        self.element = element

    def create_child(self, key):
        """Xxx..."""
        element = self.element[key] = {}
        return CncMemento(self.document, element)

    def get_child(self, key):
        """Xxx..."""
        try:
            element = self.element[key]
            return CncMemento(self.document, element)
        except:
            return None

    def get(self, key: str, default=None):
        """Xxx..."""
        try:
            return self.element[key]
        except:
            if default != None:
                return default
            return None

    def load_from_file(self, file_name: str) -> bool:
        """Xxx..."""
        try:
            with open(file_name,"r") as f:
                s = f.read()
            return self.load_from_string(s)
        except:
            return False

    def load_from_string(self, s: str) -> bool:
        """Xxx..."""
        try:
            #s = json.dumps(s)
            self.document = json.loads(s)
            self.element = self.document
            return True
        except:
            return False

    def save_to_file(self, file_name: str, indent=None) -> bool:
        """Xxx..."""
        try:
            with open(file_name, "w") as f:
                f.write(json.dumps(self.document, indent=indent))
            return True
        except Exception as e:
            return False

    def save_to_string(self) -> (str, bool):
        """Xxx..."""
        try:
            return json.dumps(self.document), True
        except:
            return '', False

    def set(self, key: str, value):
        """Xxx..."""
        self.element[key] = value

import threading
from typing import Dict

# Global database tables simulating standard DB tables
inwards_db: Dict[str, dict] = {}
office_notes_db: Dict[str, dict] = {}
enclosures_db: Dict[str, dict] = {}

# Sequence Counters
_inward_seq = 91
_office_note_seq = 0
_enclosure_seq = 0

_db_lock = threading.Lock()

def get_next_inward_seq() -> int:
    global _inward_seq
    with _db_lock:
        _inward_seq += 1
        return _inward_seq

def get_next_office_note_seq() -> int:
    global _office_note_seq
    with _db_lock:
        _office_note_seq += 1
        return _office_note_seq

def get_next_enclosure_seq() -> int:
    global _enclosure_seq
    with _db_lock:
        _enclosure_seq += 1
        return _enclosure_seq

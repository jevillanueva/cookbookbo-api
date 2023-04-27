from enum import Enum


class ReviewState (Enum):
    IGNORE = 0
    REVIEWED = 1
    NOT_REVIEWED = 2
    NOT_REQUESTED = 3
from enum import Enum

class Status(Enum):
    NONE = "none"
    EVALUATING_PARENT = "evaluating parent"
    EVALUATION = "evaluation"
    EVALUATING_DEPENDENCIES = "evaluating dependencies"
    FINISHED = "finished"
    READY = "ready"
    ERROR = "error"
    OBSOLETE = "obsolete"

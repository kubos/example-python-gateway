from enum import Enum

class CommandStatus(str, Enum):
    # The various states that a command can be in.
    # Any of the -ing states can show the operator a progress bar
    PREPARING = "preparing_on_gateway"
    UPLINKING = "uplinking_to_system"
    TRANSMITTED = "transmitted_to_system"
    ACKED = "acked_by_system"
    EXECUTING = "executing_on_system"
    DOWNLINKING = "downlinking_from_system"
    PROCESSING = "processing_on_gateway"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
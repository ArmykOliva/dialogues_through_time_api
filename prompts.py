from characters.entity import *
from characters.entity_test import *
from characters.socrates import *
from characters.jesus import *
from characters.leonardo import *

LANGUAGES = {
    "CS":"Mluv česky. Odpovídej pouze v češtině.",
    "EN":"Speak English. Reply only in English."
}

FLOWS = {
    "entity":ENTITY_FLOW,
    "socrates":SOCRATES_FLOW,
    "entity_test":ENTITY_TEST_FLOW,
    "jesus":JESUS_FLOW,
    "leonardo":LEONARDO_FLOW
}
SYSTEM_MSGS = {
    "entity":ENTITY_SYSTEM,
    "socrates":SOCRATES_SYSTEM_MSG,
    "entity_test":ENTITY_TEST_SYSTEM_MSG,
    "jesus":JESUS_SYSTEM_MSG,
    "leonardo":LEONARDO_SYSTEM_MSG
}
CONFIGS = {
    "entity":ENTITY_CONFIG,
    "socrates":SOCRATES_CONFIG,
    "entity_test":ENTITY_TEST_CONFIG,
    "leonardo":LEONARDO_CONFIG,
    "jesus":JESUS_CONFIG
}
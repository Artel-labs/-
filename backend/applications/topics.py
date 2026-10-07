from dataclasses import dataclass

from applications.models import Topic

CONTACTS = frozenset({"first_name", "last_name", "phone", "email"})
PROGRAM_FIELDS = frozenset({"applicant_type", "employees_count", "timeframe", "company", "program_id", "program_title"})


@dataclass(frozen=True)
class TopicRule:
    allowed: frozenset[str]
    required: frozenset[str]


RULES = {
    Topic.PROGRAM: TopicRule(allowed=PROGRAM_FIELDS, required=CONTACTS),
    Topic.COURSE_IDEA: TopicRule(allowed=frozenset(), required=CONTACTS),
    Topic.TEACHING: TopicRule(allowed=frozenset(), required=CONTACTS),
    Topic.FEEDBACK: TopicRule(allowed=frozenset(), required=CONTACTS),
}


def rule_for(topic: str) -> TopicRule:
    return RULES[Topic(topic)]

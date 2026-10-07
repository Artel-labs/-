from dataclasses import dataclass

from applications.models import Topic

CONTACTS = frozenset({"first_name", "last_name", "phone", "email"})
TEXT_ONLY = frozenset({"comment"})
PROGRAM_FIELDS = frozenset({"applicant_type", "employees_count", "timeframe", "company", "program_id", "program_title"})


@dataclass(frozen=True)
class TopicRule:
    allowed: frozenset[str]
    required: frozenset[str]

    @property
    def anonymous(self) -> bool:
        return not self.required & CONTACTS


RULES = {
    Topic.PROGRAM: TopicRule(allowed=PROGRAM_FIELDS, required=CONTACTS),
    Topic.COURSE_IDEA: TopicRule(allowed=frozenset(), required=TEXT_ONLY),
    Topic.TEACHING: TopicRule(allowed=frozenset(), required=CONTACTS),
    Topic.FEEDBACK: TopicRule(allowed=frozenset(), required=TEXT_ONLY),
}


def rule_for(topic: str) -> TopicRule:
    return RULES[Topic(topic)]


def is_anonymous(topic: str) -> bool:
    return rule_for(topic).anonymous

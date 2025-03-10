"""
Neo4j schema definitions using neomodel
"""
import uuid
from datetime import datetime
from neomodel import (
    StructuredNode, 
    StringProperty, 
    DateTimeProperty, 
    UniqueIdProperty,
    RelationshipTo,
    RelationshipFrom,
    ArrayProperty
)

class Topic(StructuredNode):
    """
    Topic node representing a subject area or category
    """
    # Primary key
    uuid = UniqueIdProperty()

    # Properties
    label = StringProperty(required=True, unique_index=True)
    description = StringProperty(default="")
    created_at = DateTimeProperty(default_now=True)

    # Relationships
    statements = RelationshipTo('Statement', 'CONTAINS')
    #children = RelationshipTo('Topic', 'HAS_CHILD')
    #parents = RelationshipFrom('Topic', 'HAS_CHILD')

    # Meta
    __label__ = "Topic"

    def __str__(self):
        return self.label

    def to_dict(self):
        """Convert topic to dictionary representation"""
        return {
            "uuid": str(self.uuid),
            "label": self.label,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Statement(StructuredNode):
    """
    Statement node representing a semantic triple (subject-predicate-object)
    with additional context information.
    """
    # Primary key
    uuid = UniqueIdProperty()

    # Properties
    label = StringProperty(required=True, index=True)
    subject = StringProperty(required=True, index=True)
    predicate = StringProperty(required=True, index=True)
    object = StringProperty(required=True, index=True)
    context = StringProperty(required=True, index=True)
    created_at = DateTimeProperty(default_now=True)

    # Relationships
    topics = RelationshipFrom('Topic', 'CONTAINS')

    # Meta
    __label__ = "Statement"

    def __init__(self, *args, **kwargs):
        """
        Override initialization to set label if not provided
        """
        if 'subject' in kwargs and 'predicate' in kwargs and 'object' in kwargs and 'context' in kwargs and 'label' not in kwargs:
            # Auto-generate label from subject, predicate, object, and context
            kwargs['label'] = f"{kwargs['subject']} {kwargs['predicate']} {kwargs['object']} {kwargs['context']}"
        super(Statement, self).__init__(*args, **kwargs)

    def pre_save(self):
        """
        Called before save to ensure label is set correctly.
        This is a hook that neomodel calls automatically before saving.
        """
        # Always update the label before saving
        self.label = f"{self.subject} {self.predicate} {self.object} {self.context}"
        # No need to call parent's pre_save as it doesn't exist in StructuredNode

    def save(self):
        """
        Override save method to ensure the label is correctly set and saved
        """
        # Auto-generate label by concatenating subject, predicate, object, and context
        self.label = f"{self.subject} {self.predicate} {self.object} {self.context}"

        # Save the node first to ensure it exists in the database
        saved_node = super().save()

        # After saving, force update the label property directly with Cypher
        query = "MATCH (n) WHERE id(n)=$self SET n.label=$label"
        params = {"self": self.id, "label": self.label}
        self.cypher(query, params)

        return saved_node

    def refresh(self):
        """
        Refresh the node from the database and update label if needed
        """
        super().refresh()
        # Ensure label is correct after refresh
        expected_label = f"{self.subject} {self.predicate} {self.object} {self.context}"
        if self.label != expected_label:
            self.label = expected_label
            self.save()
        return self

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            "uuid": str(self.uuid),
            "label": self.label,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "context": self.context,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
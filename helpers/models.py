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
    
    # Relationships
    statements = RelationshipTo('Statement', 'HAS_STATEMENT')
    children = RelationshipTo('Topic', 'HAS_CHILD')
    parents = RelationshipFrom('Topic', 'HAS_CHILD')
    
    # Meta
    __label__ = "Topic"
    
    def __str__(self):
        return self.label
    
    def to_dict(self):
        """Convert topic to dictionary representation"""
        return {
            "uuid": str(self.uuid),
            "label": self.label
        }
        
    def connect_to_statement(self, statement):
        """
        Connect this topic to a statement using an optimized query to avoid cartesian products.
        
        Args:
            statement: The Statement node to connect to
        """
        from neomodel import db
        
        query = """
        MATCH (t:Topic), (s:Statement)
        WHERE t.uuid = $topic_uuid AND s.uuid = $statement_uuid
        MERGE (t)-[r:HAS_STATEMENT]->(s)
        RETURN r
        """
        
        params = {
            "topic_uuid": str(self.uuid),
            "statement_uuid": str(statement.uuid)
        }
        
        db.cypher_query(query, params)

    def connect_to_child(self, child_topic):
        """
        Connect this topic to a child topic using an optimized query to avoid cartesian products.
        
        Args:
            child_topic: The child Topic node to connect to
        """
        from neomodel import db
        
        query = """
        MATCH (p:Topic), (c:Topic)
        WHERE p.uuid = $parent_uuid AND c.uuid = $child_uuid
        MERGE (p)-[r:HAS_CHILD]->(c)
        RETURN r
        """
        
        params = {
            "parent_uuid": str(self.uuid),
            "child_uuid": str(child_topic.uuid)
        }
        
        db.cypher_query(query, params)

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
    created_at = DateTimeProperty(default=datetime.now)
    
    # Relationships
    topics = RelationshipFrom('Topic', 'HAS_STATEMENT')
    
    # Meta
    __label__ = "Statement"
    
    def __str__(self):
        return f"{self.subject} {self.predicate} {self.object}"
    
    def to_dict(self):
        """Convert statement to dictionary representation"""
        return {
            "uuid": str(self.uuid),
            "label": self.label,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "context": self.context,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
"""
Neo4j database models using neomodel
"""
import uuid
from datetime import datetime
from neomodel import (
    StructuredNode, StringProperty, DateTimeProperty,
    UniqueIdProperty, RelationshipTo, RelationshipFrom
)

class Statement(StructuredNode):
    """
    Statement node represents a subject-predicate-object triple with context
    """
    uuid = UniqueIdProperty()
    label = StringProperty(required=True, index=True)
    subject = StringProperty(required=True, index=True)
    predicate = StringProperty(required=True, index=True)
    object = StringProperty(required=True, index=True)
    context = StringProperty(required=True, index=True)
    created_at = DateTimeProperty(default_now=True)
    
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
        Called before save to ensure label is set correctly
        """
        # Always update the label before saving
        self.label = f"{self.subject} {self.predicate} {self.object} {self.context}"
        super().pre_save()
    
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


class Topic(StructuredNode):
    """
    Topic node represents a category or subject area
    """
    uuid = UniqueIdProperty()
    label = StringProperty(required=True, unique_index=True)
    description = StringProperty(default="")
    created_at = DateTimeProperty(default_now=True)
    
    # Define relationships
    statements = RelationshipTo('Statement', 'CONTAINS')

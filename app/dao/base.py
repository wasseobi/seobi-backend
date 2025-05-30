from typing import Generic, TypeVar, Type, Optional, List

from sqlalchemy.orm import Query

from app.models.db import db

ModelType = TypeVar("ModelType")

class BaseDAO(Generic[ModelType]):
    """Base class for all Data Access Objects"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, id: str) -> Optional[ModelType]:
        """Get a single record by id"""
        return self.model.query.get(id)

    def get_all(self) -> List[ModelType]:
        """Get all records"""
        return self.model.query.all()

    def create(self, **kwargs) -> ModelType:
        """Create a new record"""
        instance = self.model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    def update(self, id: str, **kwargs) -> Optional[ModelType]:
        """Update a record"""
        instance = self.get(id)
        if instance:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(instance, key, value)
            db.session.commit()
        return instance

    def delete(self, id: str) -> bool:
        """Delete a record"""
        instance = self.get(id)
        if instance:
            db.session.delete(instance)
            db.session.commit()
            return True
        return False

    def query(self) -> Query:
        """Get query object for custom queries"""
        return self.model.query 
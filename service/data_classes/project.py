from uuid import UUID
from datetime import datetime
from pydantic import Field
from typing import List, Optional

from service.data_classes.base import BaseClass, Request, ResponseSuccess


# Main data structures
class Project(BaseClass):
    id: UUID = Field(description="Project UUID.")
    name: str = Field(description="Name.")
    created: datetime = Field(description="Created time.")
    updated: Optional[datetime] = Field(description="Updated time.")


class ProjectCreate(BaseClass):
    name: str = Field(description="Name.")


class ProjectUpdate(BaseClass):
    id: UUID = Field(description="Project UUID.")
    name: str = Field(description="Name.")


class ProjectList(BaseClass):
    created_gt: Optional[datetime] = Field(description="Created Greater.")
    created_lt: Optional[datetime] = Field(description="Created Less.")
    updated_gt: Optional[datetime] = Field(description="Updated Greater.")
    updated_lt: Optional[datetime] = Field(description="Updated Less.")


# Requests
class RequestProjectCreate(Request):
    params: ProjectCreate = Field(title="Project.")


class RequestProjectRead(Request):
    params: List[UUID] = Field(title="Project IDs.")


class RequestProjectUpdate(Request):
    params: ProjectUpdate = Field(title="Project.")


class RequestProjectDelete(Request):
    params: List[UUID] = Field(title="Project IDs.")


class RequestProjectList(Request):
    params: ProjectList = Field(title="Project IDs.")


# Responses
class ResponseProject(ResponseSuccess):
    result: Project = Field(description="Project.")


class ResponseProjectSeveral(ResponseSuccess):
    result: List[Project] = Field(description="List of Projects.")

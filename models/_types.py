from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional, TypeAlias

VK_ID: TypeAlias = int

class BaseResponse(BaseModel):
    pass

class FriendsResponse(BaseResponse):
    count: int
    items: List[VK_ID]

class UserResponse(BaseResponse):
    id: VK_ID
    is_verified: Optional[bool] = None
    first_name: str
    last_name: str
    can_access_closed: Optional[bool] = None
    is_closed: bool

class BaseRecord(BaseModel):
    id: VK_ID = Field(alias="_id")
    visit_history: list[datetime]

class FriendsRecord(BaseRecord):
    active_friends: list[VK_ID]
    deleted_friends: list[VK_ID] = []

class UserRecord(BaseRecord):
    first_name: str
    last_name: str
    is_closed: bool
    is_verified: Optional[bool]
    can_access_closed: Optional[bool]

class ResponseToRecordConverter:
    @staticmethod
    def friends(response: BaseResponse) -> BaseRecord:
        pass

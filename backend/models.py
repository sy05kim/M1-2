from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: date
    value: float = Field(allow_inf_nan=False)
    memo: str = Field(default="", max_length=500)
    quality_label: Literal[-1, 1] | None = None  # SECOM: -1=정상, 1=불량


class DataUpdate(DataPayload):
    pass


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message cannot be blank")
        return value.strip()


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(default="새 대화", max_length=100)
    messages: list[Message] = Field(default_factory=list, max_length=30)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    conversation_id: str | None = Field(default=None, pattern=r"^[a-zA-Z0-9_-]{1,100}$")

    @field_validator("question")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question cannot be blank")
        return value.strip()

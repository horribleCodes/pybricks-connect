from pydantic import BaseModel, Field


class InstructRequest(BaseModel):
    instructId: str


class InstructDefinition(BaseModel):
    id: str
    port: int
    function: str
    parameters: list[float | int | str] = Field(default_factory=list)


class Device(BaseModel):
    port: int

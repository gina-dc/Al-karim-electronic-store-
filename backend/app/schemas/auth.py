from pydantic import BaseModel, ConfigDict, Field


class LoginInput(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class UserInput(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)
    username: str = Field(min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_.@-]+$")
    display_name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=12, max_length=128)
    role: str = Field(pattern=r"^(owner|manager|staff)$")


class UserUpdate(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)
    display_name: str = Field(min_length=1, max_length=150)
    role: str = Field(pattern=r"^(owner|manager|staff)$")
    active: bool
    password: str | None = Field(default=None, min_length=12, max_length=128)

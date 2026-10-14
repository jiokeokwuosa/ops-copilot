from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserProfile(BaseModel):
    id: str
    email: str
    display_name: str
    tenant_id: str
    tenant_name: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class CreateThreadRequest(BaseModel):
    title: str | None = None


class ThreadSummary(BaseModel):
    id: str
    title: str | None
    status: str
    updated_at: str


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    steps: list[dict] | None = None
    sources: list[dict] | None = None
    created_at: str


class PendingApprovalOut(BaseModel):
    id: str
    tool_name: str
    payload: dict
    rationale: str
    status: str


class ThreadDetail(ThreadSummary):
    messages: list[MessageOut]
    pending_approval: PendingApprovalOut | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    message_id: str
    content: str
    sources: list[dict] | None = None
    refused: bool = False
    pending_approval: PendingApprovalOut | None = None


class ApprovalDecision(BaseModel):
    decision: str = Field(pattern=r"^(approve|reject)$")


class ApprovalResult(BaseModel):
    status: str
    applied: bool = False

"""
Ledge Language — AST Node Definitions
One node per language construct. No ambiguity.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


@dataclass
class Node:
    pass


# ── Literals ──────────────────────────────────────────────────────────────────

@dataclass
class NumberLit(Node):
    value: float

@dataclass
class StringLit(Node):
    value: str

@dataclass
class BoolLit(Node):
    value: bool

@dataclass
class NothingLit(Node):
    pass

@dataclass
class ListLit(Node):
    elements: List[Node]

@dataclass
class MapLit(Node):
    pairs: List[Tuple[Node, Node]]

@dataclass
class Identifier(Node):
    name: str


# ── Expressions ───────────────────────────────────────────────────────────────

@dataclass
class BinOp(Node):
    op: str
    left: Node
    right: Node

@dataclass
class UnaryOp(Node):
    op: str
    operand: Node

@dataclass
class LogicalOp(Node):
    op: str
    left: Node
    right: Node

@dataclass
class IsOp(Node):
    negated: bool
    left: Node
    right: Node

@dataclass
class Call(Node):
    callee: Node
    args: List[Node]
    kwargs: dict
    using: Optional[str]

@dataclass
class Index(Node):
    obj: Node
    key: Node

@dataclass
class Field(Node):
    obj: Node
    name: str

@dataclass
class Fallback(Node):
    expr: Node
    default: Node

@dataclass
class Lambda(Node):
    params: List[str]
    body: Node

@dataclass
class ParallelExpr(Node):
    exprs: List[Node]

@dataclass
class AnalyzeExpr(Node):
    text: Node
    mode: str

@dataclass
class GenerateExpr(Node):
    prompt: Node
    mode: str

@dataclass
class AskExpr(Node):
    question: Node

@dataclass
class EmbedExpr(Node):
    text: Node

@dataclass
class ClassifyExpr(Node):
    text: Node
    labels: List[Node]


# ── Statements ────────────────────────────────────────────────────────────────

@dataclass
class Block(Node):
    stmts: List[Node]

@dataclass
class FuncDef(Node):
    params: List[Tuple[str, Optional[str]]]
    body: 'Block'
    is_generator: bool = False
    contract: Any = None

@dataclass
class Define(Node):
    name: str
    type_hint: Optional[str]
    value: Node

@dataclass
class Assign(Node):
    name: str
    value: Node

@dataclass
class Show(Node):
    expr: Node
    format: Optional[str]

@dataclass
class If(Node):
    branches: List[Tuple[Node, 'Block']]
    else_block: Optional['Block']

@dataclass
class For(Node):
    var: str
    var2: Optional[str]
    iterable: Node
    body: 'Block'

@dataclass
class While(Node):
    condition: Node
    body: 'Block'

@dataclass
class Repeat(Node):
    count: Optional[Node]
    condition: Optional[Node]
    body: 'Block'

@dataclass
class Match(Node):
    subject: Node
    cases: List[Tuple[Node, 'Block']]
    otherwise: Optional['Block']

@dataclass
class Check(Node):
    body: 'Block'
    recover_var: Optional[str]
    recover_block: Optional['Block']
    always_block: Optional['Block']

@dataclass
class Return(Node):
    value: Optional[Node]

@dataclass
class Break(Node):
    pass

@dataclass
class Continue(Node):
    pass

@dataclass
class Pass(Node):
    pass

@dataclass
class Yield(Node):
    value: Node

@dataclass
class RunStmt(Node):
    expr: Node
    wait: bool

@dataclass
class Import(Node):
    path: str
    alias: Optional[str]
    names: List[str]

@dataclass
class TypeDef(Node):
    name: str
    fields: List[Tuple[str, Optional[str], Optional[Node]]]

@dataclass
class ExprStmt(Node):
    expr: Node

@dataclass
class Program(Node):
    stmts: List[Node]


# ── v1.0 AI-Native Constructs ─────────────────────────────────────────────────

@dataclass
class StreamExpr(Node):
    """stream from "source" | where cond | window N seconds"""
    source: Node              # string URL, list, or generator
    source_type: str = "list" # "url", "list", "generator", "interval"
    filters: List[Node] = None  # where clauses
    transforms: List[Node] = None  # transform clauses
    window_size: Optional[Node] = None
    window_unit: str = "items"  # "items", "seconds", "minutes"
    
    def __post_init__(self):
        if self.filters is None: self.filters = []
        if self.transforms is None: self.transforms = []

@dataclass
class PipelineExpr(Node):
    """pipeline: source | stage1 | stage2"""
    stages: List[Node] = None
    
    def __post_init__(self):
        if self.stages is None: self.stages = []

@dataclass
class PipeStage(Node):
    """A single | stage in a pipeline"""
    operation: str  # "filter", "transform", "analyze", "write", "read", "group_by"
    var_name: Optional[str]  # row/item name
    expr: Optional[Node]  # the stage expression
    mode: Optional[str] = None  # for analyze using X

@dataclass
class WhenStmt(Node):
    """when stream has new item as name: block"""
    source: Node     # the stream/condition
    trigger: str     # "has_new_item", "condition"
    item_name: Optional[str]  # variable name for item
    body: 'Block'

@dataclass
class FuncContract(Node):
    """requires: / ensures: clauses on a function"""
    requires: List[Node]  # list of condition expressions
    ensures: List[Node]   # list of postcondition expressions
    require_descs: List[str] = None   # human-readable descriptions
    ensure_descs: List[str] = None

    def __post_init__(self):
        if self.require_descs is None: self.require_descs = []
        if self.ensure_descs is None: self.ensure_descs = []

@dataclass
class AgentDef(Node):
    """agent with tools, model, behavior"""
    name: str
    tools: List[tuple]   # [(tool_name, mcp_source)]
    model_name: Node     # model string
    behavior: 'Block'    # behavior block

@dataclass
class MCPExpr(Node):
    """mcp "server-name" at "url" """
    server: Node   # server name string
    url: Optional[Node]  # optional explicit URL

@dataclass
class EmitStmt(Node):
    """emit value to stream"""
    value: Node
    target: Optional[Node]

@dataclass
class SubscribeStmt(Node):
    """subscribe to stream as name: block"""
    source: Node
    item_name: str
    body: 'Block'

@dataclass 
class AsyncDef(Node):
    """async define f(): ..."""
    inner: Node  # the Define node

@dataclass
class UncertainExpr(Node):
    """value ~confidence% — inline uncertainty literal"""
    value: Node
    confidence: Node  # 0.0-1.0

@dataclass
class ConfidenceGate(Node):
    """expr when confidence > N else fallback"""
    expr: Node
    threshold: Node
    fallback: Node

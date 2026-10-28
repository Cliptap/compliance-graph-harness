"""Call-level taint analysis for Python: personal data that reaches a sink through variables and calls.

The analyzer builds an in-memory call graph of the functions in the evaluated files and
propagates taint from sensitive expressions (``p.rut``, ``form['rut']``, ``data.get('rut')``,
or a name such as ``rut``) through assignments, containers, return values and calls resolved
by name: functions of the same file, imported functions defined in another evaluated file,
and ``self.method`` inside a class. Each function gets a summary (which parameters reach a
sink, which reach the return value) computed to a fixed point, so flows across several hops
and recursion terminate.

Precision choices, published as limits:
- A call whose name holds a mask marker cleans its result.
- An unresolved call returns only the taint of its receiver (``x.upper()``), except for
  value-preserving builtins (``str``, ``json.dumps``, ``'...'.format``), which also return the
  taint of their arguments. Looking an object up by a RUT therefore does not taint the object.
- Containers are not field-sensitive: a dict holding a RUT is tainted as a whole.
- Only the evaluated files are resolved; a function defined elsewhere is an unresolved call.
"""
from __future__ import annotations

import ast
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

MAX_STEPS = 8
MAX_ROUNDS = 10
LOOP_UNROLL_DEPTH = 3  # deeper loops run their body once, so nested loops stay linear
VALUE_PRESERVING = frozenset({
    "str", "repr", "format", "dumps", "join", "dict", "list", "tuple", "set", "sorted",
    "upper", "lower", "strip", "lstrip", "rstrip", "replace", "title", "encode", "decode",
})

Key = tuple  # ("src", text, file, line) or ("param", name)
Taint = dict  # Key -> tuple of path steps


@dataclass(frozen=True)
class FlowHit:
    file: str
    line: int
    sink: str
    origin: str
    origin_file: str
    origin_line: int
    steps: tuple[str, ...]


@dataclass(frozen=True)
class _SinkRef:
    file: str
    line: int
    sink: str
    steps: tuple[str, ...]


@dataclass
class _Func:
    key: str
    file: str
    name: str
    cls: str | None
    params: list[str]
    body: list[ast.stmt]


@dataclass
class _Summary:
    to_sink: dict[str, dict[tuple[str, int], _SinkRef]] = field(default_factory=dict)
    to_return: dict[str, tuple[str, ...]] = field(default_factory=dict)
    return_sources: Taint = field(default_factory=dict)

    def signature(self) -> tuple:
        sinks = frozenset((p, pos) for p, refs in self.to_sink.items() for pos in refs)
        return sinks, frozenset(self.to_return), frozenset(self.return_sources)


def _merge(*taints: Taint) -> Taint:
    out: Taint = {}
    for t in taints:
        for k, steps in t.items():
            out.setdefault(k, steps)
    return out


def _extend(t: Taint, steps: Iterable[str]) -> Taint:
    add = tuple(steps)
    return {k: (s + add)[:MAX_STEPS] for k, s in t.items()}


def _copy(env: dict[str, Taint]) -> dict[str, Taint]:
    return {k: dict(v) for k, v in env.items()}


def _join(a: dict[str, Taint], b: dict[str, Taint]) -> dict[str, Taint]:
    return {k: _merge(a.get(k, {}), b.get(k, {})) for k in a.keys() | b.keys()}


def _params(node: ast.FunctionDef | ast.AsyncFunctionDef, is_method: bool) -> list[str]:
    args = node.args
    names = [a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs]]
    static = any(isinstance(d, ast.Name) and d.id == "staticmethod" for d in node.decorator_list)
    return names[1:] if is_method and not static and names else names


class _Program:
    """Functions of the evaluated files and the name tables used to resolve calls."""

    def __init__(self, trees: dict[str, ast.Module]):
        self.funcs: dict[str, _Func] = {}
        self.module_funcs: dict[tuple[str, str], str] = {}
        self.methods: dict[tuple[str, str, str], str] = {}
        self.by_name: dict[str, list[str]] = {}
        self.imported: dict[str, dict[str, str]] = {}
        self.modules: dict[str, set[str]] = {}
        for file, tree in trees.items():
            self._index(file, tree)

    def _add(self, func: _Func) -> None:
        self.funcs[func.key] = func

    def _index(self, file: str, tree: ast.Module) -> None:
        self.imported[file], self.modules[file] = {}, set()
        top: list[ast.stmt] = []
        for stmt in tree.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                key = f"{file}::{stmt.name}"
                self._add(_Func(key, file, stmt.name, None, _params(stmt, False), stmt.body))
                self.module_funcs[(file, stmt.name)] = key
                self.by_name.setdefault(stmt.name, []).append(key)
            elif isinstance(stmt, ast.ClassDef):
                for item in stmt.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        key = f"{file}::{stmt.name}.{item.name}"
                        self._add(_Func(key, file, item.name, stmt.name, _params(item, True), item.body))
                        self.methods[(file, stmt.name, item.name)] = key
            else:
                top.append(stmt)
            if isinstance(stmt, ast.ImportFrom):
                for alias in stmt.names:
                    self.imported[file][alias.asname or alias.name] = alias.name
            elif isinstance(stmt, ast.Import):
                self.modules[file].update(a.asname or a.name.split(".")[0] for a in stmt.names)
        self._add(_Func(f"{file}::<module>", file, "<module>", None, [], top))

    def _elsewhere(self, file: str, name: str) -> str | None:
        found = [k for k in self.by_name.get(name, []) if self.funcs[k].file != file]
        return found[0] if len(found) == 1 else None

    def resolve(self, caller: _Func, func: ast.expr) -> str | None:
        if isinstance(func, ast.Name):
            local = self.module_funcs.get((caller.file, func.id))
            if local:
                return local
            original = self.imported[caller.file].get(func.id)
            return self._elsewhere(caller.file, original) if original else None
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            owner = func.value.id
            if owner in ("self", "cls") and caller.cls:
                return self.methods.get((caller.file, caller.cls, func.attr))
            if owner in self.modules[caller.file]:
                return self._elsewhere(caller.file, func.attr)
        return None


class TaintAnalyzer:
    """Finds sensitive values that reach a sink call, across assignments and resolved calls."""

    def __init__(self, sensitive_tokens: Iterable[str], is_sink: Callable[[ast.Call], bool],
                 mask_markers: Iterable[str], ambiguous_names: Iterable[str] = ()):
        self.tokens = frozenset(t.lower() for t in sensitive_tokens)
        self.is_sink = is_sink
        self.mask_markers = tuple(mask_markers)
        # A bare variable with one of these names is not a source (``run`` is also an English
        # word); the same token as an attribute or a key (``p.run``, ``form['run']``) still is.
        self.ambiguous_names = frozenset(n.lower() for n in ambiguous_names)

    def analyze(self, trees: dict[str, ast.Module]) -> list[FlowHit]:
        program = _Program(trees)
        summaries = {k: _Summary() for k in program.funcs}
        for _ in range(MAX_ROUNDS):
            changed = False
            for func in program.funcs.values():
                new = _Run(self, program, summaries, func, None).summary
                if new.signature() != summaries[func.key].signature():
                    summaries[func.key], changed = new, True
            if not changed:
                break
        hits: dict[tuple[str, int], FlowHit] = {}
        for func in program.funcs.values():
            _Run(self, program, summaries, func, hits)
        return sorted(hits.values(), key=lambda h: (h.file, h.line))


class _Run:
    """Abstract interpretation of one function body with the current callee summaries."""

    def __init__(self, analyzer: TaintAnalyzer, program: _Program, summaries: dict[str, _Summary],
                 func: _Func, hits: dict[tuple[str, int], FlowHit] | None):
        self.an, self.program, self.summaries, self.func, self.hits = analyzer, program, summaries, func, hits
        self.summary = _Summary()
        self.loop_depth = 0
        self.assigned: set[str] = set()
        env: dict[str, Taint] = {p: {("param", p): ()} for p in func.params}
        self._stmts(func.body, env)

    # ---- statements -------------------------------------------------------------------
    def _stmts(self, stmts: list[ast.stmt], env: dict[str, Taint]) -> None:
        for stmt in stmts:
            self._stmt(stmt, env)

    def _stmt(self, s: ast.stmt, env: dict[str, Taint]) -> None:
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return
        if isinstance(s, ast.Assign):
            t = self._expr(s.value, env)
            for target in s.targets:
                self._assign(target, t, env)
        elif isinstance(s, ast.AnnAssign) and s.value is not None:
            self._assign(s.target, self._expr(s.value, env), env)
        elif isinstance(s, ast.AugAssign):
            self._assign(s.target, _merge(self._expr(s.target, env), self._expr(s.value, env)), env)
        elif isinstance(s, ast.Return) and s.value is not None:
            self._returns(self._expr(s.value, env))
        elif isinstance(s, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Try, ast.With, ast.AsyncWith)):
            self._compound(s, env)
        elif isinstance(s, ast.Match):
            self._expr(s.subject, env)
            branches = [_copy(env) for _ in s.cases]
            for case, branch in zip(s.cases, branches):
                self._stmts(case.body, branch)
            for branch in branches:
                env.update(_join(env, branch))
        else:
            for child in ast.iter_child_nodes(s):
                if isinstance(child, ast.expr):
                    self._expr(child, env)

    def _compound(self, s: ast.stmt, env: dict[str, Taint]) -> None:
        if isinstance(s, (ast.With, ast.AsyncWith)):
            for item in s.items:
                t = self._expr(item.context_expr, env)
                if item.optional_vars is not None:
                    self._assign(item.optional_vars, t, env)
            self._stmts(s.body, env)
            return
        if isinstance(s, ast.Try):
            body = _copy(env)
            self._stmts(s.body, body)
            joined = _join(env, body)
            for handler in s.handlers:
                branch = _copy(joined)
                self._stmts(handler.body, branch)
                joined = _join(joined, branch)
            self._stmts(s.orelse, joined)
            self._stmts(s.finalbody, joined)
            env.clear()
            env.update(joined)
            return
        is_loop = not isinstance(s, ast.If)
        iterated = self._expr(s.iter, env) if isinstance(s, (ast.For, ast.AsyncFor)) else self._expr(s.test, env)
        body = _copy(env)
        rounds = 2 if is_loop and self.loop_depth < LOOP_UNROLL_DEPTH else 1
        self.loop_depth += is_loop
        for _ in range(rounds):
            if isinstance(s, (ast.For, ast.AsyncFor)):
                self._assign(s.target, iterated, body)
            self._stmts(s.body, body)
        self.loop_depth -= is_loop
        other = _copy(_join(env, body) if is_loop else env)
        self._stmts(s.orelse, other)
        env.clear()
        env.update(_join(body, other))

    def _assign(self, target: ast.expr, t: Taint, env: dict[str, Taint]) -> None:
        if isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._assign(elt.value if isinstance(elt, ast.Starred) else elt, t, env)
            return
        step = (f"{ast.unparse(target)} ({self.func.file}:{target.lineno})",)
        if isinstance(target, (ast.Name, ast.Attribute)):
            key = target.id if isinstance(target, ast.Name) else ast.unparse(target)
            if isinstance(target, ast.Name):
                self.assigned.add(key)
            env[key] = _extend(t, step)
        elif isinstance(target, ast.Subscript):
            key = ast.unparse(target.value)
            env[key] = _merge(env.get(key, {}), _extend(t, step))

    def _returns(self, t: Taint) -> None:
        for key, steps in t.items():
            if key[0] == "param":
                self.summary.to_return.setdefault(key[1], steps)
            else:
                self.summary.return_sources.setdefault(key, steps)

    # ---- expressions ------------------------------------------------------------------
    def _source(self, node: ast.expr) -> Taint:
        return {("src", ast.unparse(node), self.func.file, node.lineno): ()}

    def _expr(self, e: ast.expr | None, env: dict[str, Taint]) -> Taint:
        if e is None or isinstance(e, (ast.Constant, ast.Lambda)):
            return {}
        if isinstance(e, ast.Name):
            t = dict(env.get(e.id, {}))
            name = e.id.lower()
            # A local variable named like a token carries only what was assigned to it.
            is_source = (name in self.an.tokens and name not in self.an.ambiguous_names
                         and e.id not in self.assigned)
            return _merge(t, self._source(e)) if is_source else t
        if isinstance(e, ast.Attribute):
            t = _merge(env.get(ast.unparse(e), {}), self._expr(e.value, env))
            return _merge(t, self._source(e)) if e.attr.lower() in self.an.tokens else t
        if isinstance(e, ast.Subscript):
            t = self._expr(e.value, env)
            key = e.slice
            if isinstance(key, ast.Constant) and isinstance(key.value, str) and key.value.lower() in self.an.tokens:
                t = _merge(t, self._source(e))
            return t
        if isinstance(e, ast.Call):
            return self._call(e, env)
        if isinstance(e, ast.Compare):
            for child in [e.left, *e.comparators]:
                self._expr(child, env)
            return {}
        if isinstance(e, ast.UnaryOp):
            t = self._expr(e.operand, env)
            return {} if isinstance(e.op, ast.Not) else t
        if isinstance(e, ast.NamedExpr):
            t = self._expr(e.value, env)
            self._assign(e.target, t, env)
            return t
        if isinstance(e, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            return self._comprehension(e, env)
        if isinstance(e, ast.Dict):
            return _merge(*(self._expr(v, env) for v in e.values), *(self._expr(k, env) for k in e.keys if k))
        return _merge(*(self._expr(c, env) for c in ast.iter_child_nodes(e) if isinstance(c, ast.expr)))

    def _comprehension(self, e: ast.expr, env: dict[str, Taint]) -> Taint:
        inner = _copy(env)
        for gen in e.generators:
            self._assign(gen.target, self._expr(gen.iter, inner), inner)
        if isinstance(e, ast.DictComp):
            return _merge(self._expr(e.key, inner), self._expr(e.value, inner))
        return self._expr(e.elt, inner)

    def _call(self, e: ast.Call, env: dict[str, Taint]) -> Taint:
        args = [self._expr(a.value if isinstance(a, ast.Starred) else a, env) for a in e.args]
        kwargs = {k.arg: self._expr(k.value, env) for k in e.keywords}
        receiver = self._expr(e.func.value, env) if isinstance(e.func, ast.Attribute) else {}
        name = e.func.id if isinstance(e.func, ast.Name) else getattr(e.func, "attr", "")
        if self.an.is_sink(e):
            self._sink(e, _merge(*args, *kwargs.values()))
            return {}
        if any(m in name.lower() for m in self.an.mask_markers):
            return {}
        callee = self.program.resolve(self.func, e.func)
        if callee:
            return self._apply(callee, e, args, kwargs)
        result = _merge(receiver, *args, *kwargs.values()) if name in VALUE_PRESERVING else receiver
        first = e.args[0] if e.args else None
        if name == "get" and isinstance(first, ast.Constant) and str(first.value).lower() in self.an.tokens:
            result = _merge(result, self._source(e))
        return result

    def _sink(self, e: ast.Call, t: Taint) -> None:
        args_src = " ".join(ast.unparse(a) for a in [*e.args, *(k.value for k in e.keywords)]).lower()
        if any(m in args_src for m in self.an.mask_markers):
            return
        ref = _SinkRef(self.func.file, e.lineno, ast.unparse(e.func), ())
        for key, steps in t.items():
            self._reach(key, steps, ref)

    def _reach(self, key: Key, steps: tuple[str, ...], ref: _SinkRef) -> None:
        path = (steps + ref.steps)[:MAX_STEPS]
        if key[0] == "param":
            refs = self.summary.to_sink.setdefault(key[1], {})
            refs.setdefault((ref.file, ref.line), _SinkRef(ref.file, ref.line, ref.sink, path))
        elif self.hits is not None:
            _, origin, origin_file, origin_line = key
            self.hits.setdefault((ref.file, ref.line),
                                 FlowHit(ref.file, ref.line, ref.sink, origin, origin_file, origin_line, path))

    def _apply(self, callee_key: str, e: ast.Call, args: list[Taint], kwargs: dict) -> Taint:
        callee, summary = self.program.funcs[callee_key], self.summaries[callee_key]
        bound: dict[str, Taint] = dict(zip(callee.params, args))
        bound.update({k: v for k, v in kwargs.items() if k in callee.params})
        result: Taint = dict(summary.return_sources)
        for param, t in bound.items():
            call = (f"{callee.name}({param}) ({self.func.file}:{e.lineno})",)
            if param in summary.to_return:
                result = _merge(result, _extend(t, call + summary.to_return[param]))
            for ref in summary.to_sink.get(param, {}).values():
                for key, steps in t.items():
                    self._reach(key, steps + call, ref)
        return result

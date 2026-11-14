"""Load complete pinned native modules with explicit inert dependency shims.

No native functions are AST-extracted. Package export facades bypass unrelated
eager imports; missing model dependencies raise if called. This is not an
installed One-Eval/DataFlow distribution and does not test model transport.
"""
from __future__ import annotations
import hashlib
import importlib
import importlib.machinery
import json
import logging
import os
from pathlib import Path
import sys
import types

HERE = Path(__file__).resolve().parent
VENDOR = HERE / "vendor"
SHIM_EVENTS = []


def denied(*args, **kwargs):
    SHIM_EVENTS.append("forbidden_optional_dependency_call")
    raise RuntimeError("Optional model dependency shim was called")


class Denied:
    def __init__(self, *args, **kwargs):
        denied(*args, **kwargs)


def package(name, path=None):
    module = types.ModuleType(name)
    module.__path__ = [str(path)] if path else []
    module.__spec__ = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
    sys.modules[name] = module
    return module


def module(name, **attrs):
    item = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(item, key, value)
    sys.modules[name] = item
    return item


def load_native(log_path):
    if any(name in sys.modules for name in ("one_eval", "dataflow")):
        raise RuntimeError("Run native integration in a clean subprocess")
    manifest = json.loads((HERE / "VENDORED_MODULES.json").read_text())
    for rel, meta in manifest.items():
        if hashlib.sha256((VENDOR / rel).read_bytes()).hexdigest() != meta["sha256"]:
            raise RuntimeError("Pinned native source changed: " + rel)
    for name in ["dataflow", "dataflow.operators", "dataflow.operators.core_text",
                 "dataflow.prompts", "dataflow.prompts.model_evaluation",
                 "dataflow.utils", "dataflow.utils.reasoning",
                 "one_eval", "one_eval.core", "one_eval.toolkits"]:
        package(name, VENDOR / name.replace(".", "/"))
    class LogFacade:
        def __init__(self, name):
            self.logger = logging.getLogger(name or "dataflow-native-integration")
        def __getattr__(self, name):
            return getattr(self.logger, "info" if name == "success" else name)
    get_logger = lambda name=None: LogFacade(name)
    sys.modules["dataflow"].get_logger = get_logger
    module("dataflow.logger", get_logger=get_logger)
    module("dataflow.utils.utils", get_logger=get_logger)
    package("torch"); package("torch.nn"); module("torch.nn.functional")
    module("transformers", AutoModelForCausalLM=Denied, AutoTokenizer=Denied)
    module("math_verify", parse=denied, verify=denied)
    module("word2number", w2n=types.SimpleNamespace(word_to_num=denied))
    module("tqdm", tqdm=denied)
    package("rich"); module("rich.console", Console=Denied); module("rich.table", Table=Denied)
    package("langgraph"); package("langgraph.graph")
    module("langgraph.graph.message", add_messages=denied)
    package("langchain_core"); module("langchain_core.messages", BaseMessage=Denied)
    module("dataflow.serving", LocalModelLLMServing_vllm=Denied, APILLMServing_request=Denied)
    package("dataflow.utils.db_pool")
    module("dataflow.utils.db_pool.myscale_pool", ClickHouseConnectionPool=Denied)
    os.environ["ONE_EVAL_LOG_FILE"] = str(log_path)
    core = importlib.import_module("dataflow.core")
    generator = importlib.import_module("dataflow.operators.core_text.generate.bench_answer_generator")
    evaluator = importlib.import_module("dataflow.operators.core_text.eval.unified_bench_dataset_evaluator")
    facade = sys.modules["dataflow.operators.core_text"]
    facade.BenchAnswerGenerator = generator.BenchAnswerGenerator
    facade.UnifiedBenchDatasetEvaluator = evaluator.UnifiedBenchDatasetEvaluator
    tool = importlib.import_module("one_eval.toolkits.dataflow_eval_tool")
    state = importlib.import_module("one_eval.core.state")
    origins = {name: sys.modules[name].__file__ for name in [
        "one_eval.toolkits.dataflow_eval_tool", "one_eval.core.state", "one_eval.logger",
        "dataflow.operators.core_text.generate.bench_answer_generator",
        "dataflow.operators.core_text.eval.unified_bench_dataset_evaluator",
        "dataflow.utils.storage", "dataflow.utils.registry", "dataflow.core",
        "dataflow.core.prompt", "dataflow.prompts.core_text",
        "dataflow.prompts.model_evaluation.general", "dataflow.utils.reasoning.AnswerExtraction"]}
    return types.SimpleNamespace(tool=tool, generator=generator, evaluator=evaluator,
                                 state=state, core=core, origins=origins,
                                 shim_events=SHIM_EVENTS)

import json
import time
from unittest.mock import MagicMock, patch

import pytest

import agy_proxy


def test_strip_ansi():
    assert agy_proxy._strip_ansi("\x1b[32mhello\x1b[0m") == "hello"
    assert agy_proxy._strip_ansi("no ansi here") == "no ansi here"
    assert agy_proxy._strip_ansi("") == ""


def test_messages_to_prompt_simple():
    messages = [
        {"role": "user", "content": "hello"},
    ]
    result = agy_proxy._messages_to_prompt(messages)
    assert result == "hello"


def test_messages_to_prompt_multi_role():
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "How are you?"},
    ]
    result = agy_proxy._messages_to_prompt(messages)
    assert "[System Instructions]\nYou are helpful." in result
    assert "Hi" in result
    assert "[Previous Assistant Response]\nHello!" in result
    assert "How are you?" in result


def test_messages_to_prompt_with_tool_results():
    messages = [
        {"role": "user", "content": "list files"},
        {"role": "assistant", "content": None, "tool_calls": [
            {"function": {"name": "list_dir", "arguments": '{"path": "."}'}}
        ]},
        {"role": "tool", "name": "list_dir", "tool_call_id": "call_123", "content": "file1.py\nfile2.py"},
        {"role": "user", "content": "thanks"},
    ]
    result = agy_proxy._messages_to_prompt(messages)
    assert "[Previous Assistant Action]" in result
    assert "Called list_dir" in result
    assert "[Tool Result: list_dir]" in result
    assert "file1.py" in result


def test_messages_to_prompt_multimodal_content():
    messages = [
        {"role": "user", "content": [
            {"type": "text", "text": "Describe this"},
            {"type": "image_url", "image_url": {"url": "http://example.com/img.png"}},
        ]},
    ]
    result = agy_proxy._messages_to_prompt(messages)
    assert "Describe this" in result


def test_messages_to_prompt_with_tools():
    messages = [{"role": "user", "content": "do something"}]
    tools = [{
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"]
            }
        }
    }]
    result = agy_proxy._messages_to_prompt(messages, tools)
    assert "<<<TOOL_CALLS>>>" in result
    assert "read_file" in result
    assert "File path" in result


def test_parse_tool_calls_none():
    text = "Just a regular response with no tool calls."
    content, calls = agy_proxy._parse_tool_calls(text)
    assert content == text
    assert calls is None


def test_parse_tool_calls_valid():
    text = '<<<TOOL_CALLS>>>\n[{"name": "list_dir", "arguments": {"path": "."}}]\n<<<END_TOOL_CALLS>>>'
    content, calls = agy_proxy._parse_tool_calls(text)
    assert content is None
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "list_dir"
    assert calls[0]["type"] == "function"
    assert "call_" in calls[0]["id"]
    args = json.loads(calls[0]["function"]["arguments"])
    assert args["path"] == "."


def test_parse_tool_calls_with_text_before():
    text = 'Let me check that.\n<<<TOOL_CALLS>>>\n[{"name": "read_file", "arguments": {"path": "test.py"}}]\n<<<END_TOOL_CALLS>>>'
    content, calls = agy_proxy._parse_tool_calls(text)
    assert content == "Let me check that."
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "read_file"


def test_parse_tool_calls_multiple():
    text = '<<<TOOL_CALLS>>>\n[{"name": "read_file", "arguments": {"path": "a.py"}}, {"name": "read_file", "arguments": {"path": "b.py"}}]\n<<<END_TOOL_CALLS>>>'
    content, calls = agy_proxy._parse_tool_calls(text)
    assert len(calls) == 2


def test_parse_tool_calls_invalid_json():
    text = '<<<TOOL_CALLS>>>\nnot valid json\n<<<END_TOOL_CALLS>>>'
    content, calls = agy_proxy._parse_tool_calls(text)
    assert calls is None
    assert content == text


def test_parse_tool_calls_no_end_marker():
    text = '<<<TOOL_CALLS>>>\n[{"name": "test"}]'
    content, calls = agy_proxy._parse_tool_calls(text)
    assert calls is None


def test_tools_to_description():
    tools = [{
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string", "description": "The command"},
                    "cwd": {"type": "string", "description": "Working directory"}
                },
                "required": ["cmd"]
            }
        }
    }]
    result = agy_proxy._tools_to_description(tools)
    assert "run_command" in result
    assert "Execute a shell command" in result
    assert "cmd: string (required)" in result
    assert "cwd: string" in result
    assert "(required)" not in result.split("cwd")[1]


def test_tools_to_description_skips_non_function():
    tools = [{"type": "code_interpreter"}]
    result = agy_proxy._tools_to_description(tools)
    assert result == ""


def test_fetch_models_caching():
    agy_proxy._model_cache["ts"] = time.time()
    agy_proxy._model_cache["models"] = [{"id": "cached-model", "name": "Cached"}]
    result = agy_proxy._fetch_models()
    assert result == [{"id": "cached-model", "name": "Cached"}]
    agy_proxy._model_cache["ts"] = 0.0
    agy_proxy._model_cache["models"] = []


def test_usage_helper():
    result = agy_proxy._usage("one two three", "four five")
    assert result["prompt_tokens"] == 3
    assert result["completion_tokens"] == 2
    assert result["total_tokens"] == 5


def test_completion_response_text():
    resp = agy_proxy._completion_response("abc123", "test-model", "Hello!", prompt="hi", output="Hello!")
    assert resp["model"] == "test-model"
    assert resp["choices"][0]["message"]["content"] == "Hello!"
    assert resp["choices"][0]["finish_reason"] == "stop"
    assert "tool_calls" not in resp["choices"][0]["message"]


def test_completion_response_with_tools():
    tool_calls = [{"id": "call_1", "type": "function", "function": {"name": "test", "arguments": "{}"}}]
    resp = agy_proxy._completion_response("abc123", "test-model", None, tool_calls=tool_calls, prompt="hi", output="x")
    assert resp["choices"][0]["finish_reason"] == "tool_calls"
    assert resp["choices"][0]["message"]["tool_calls"] == tool_calls


@pytest.mark.asyncio
async def test_health_endpoint():
    from fastapi.testclient import TestClient
    with patch.object(agy_proxy, "_find_agy", return_value="/usr/bin/agy"):
        with patch.object(agy_proxy, "_fetch_models", return_value=[{"id": "m1", "name": "M1"}]):
            client = TestClient(agy_proxy.app)
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["models"] == 1


def test_list_models_endpoint():
    from fastapi.testclient import TestClient
    with patch.object(agy_proxy, "_fetch_models", return_value=[
        {"id": "gemini-3.8-flash-medium", "name": "Gemini 3.8 Flash (Medium)"},
    ]):
        client = TestClient(agy_proxy.app)
        response = client.get("/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "gemini-3.8-flash-medium"
        assert data["data"][0]["owned_by"] == "antigravity"


def test_get_model_endpoint():
    from fastapi.testclient import TestClient
    with patch.object(agy_proxy, "_fetch_models", return_value=[
        {"id": "gemini-3.8-flash-medium", "name": "Gemini 3.8 Flash (Medium)"},
    ]):
        client = TestClient(agy_proxy.app)
        response = client.get("/v1/models/gemini-3.8-flash-medium")
        assert response.status_code == 200
        assert response.json()["id"] == "gemini-3.8-flash-medium"

        response = client.get("/v1/models/nonexistent")
        assert response.status_code == 404

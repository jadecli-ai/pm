# pm/tests/neon_docs/test_tracer.py
"""Tests for MLflow tracer."""

from lib.neon_docs.tracer import trace_operation


class TestTraceDecorator:
    async def test_traces_return_value(self) -> None:
        @trace_operation("test.operation")
        async def my_func(x: int = 0) -> dict:
            return {"result": x + 1}

        result = await my_func(x=5)
        assert result == {"result": 6}

    async def test_traces_exception(self) -> None:
        @trace_operation("test.failing")
        async def failing_func() -> None:
            raise ValueError("test error")

        import pytest
        with pytest.raises(ValueError, match="test error"):
            await failing_func()

    async def test_traces_list_result(self) -> None:
        @trace_operation("test.list")
        async def list_func() -> list:
            return [1, 2, 3]

        result = await list_func()
        assert result == [1, 2, 3]

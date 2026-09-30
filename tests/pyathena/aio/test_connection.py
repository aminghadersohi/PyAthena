# Copyright 2026 The PyAthena authors
#
# Licensed under the MIT License.
# See LICENSE or https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

from typing import Any

from pyathena.aio.connection import AioConnection
from pyathena.aio.cursor import AioCursor


class RecordingAioCursor(AioCursor):
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        super().__init__(**kwargs)


class TestAioConnection:
    async def test_cursor_arguments_override_cursor_kwargs(self):
        conn = await AioConnection.create(
            region_name="us-east-1",
            s3_staging_dir="s3://bucket/path/",
            aws_access_key_id="access_key",
            aws_secret_access_key="secret_key",
            cursor_class=RecordingAioCursor,
            cursor_kwargs={"kill_on_interrupt": False, "schema_name": "configured"},
        )

        cursor = conn.cursor(kill_on_interrupt=True)

        assert cursor.kwargs["kill_on_interrupt"] is True
        assert cursor.kwargs["schema_name"] == "configured"
        assert conn.cursor_kwargs == {"kill_on_interrupt": False, "schema_name": "configured"}

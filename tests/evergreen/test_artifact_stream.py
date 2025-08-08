"""Unit tests for Artifact class streams in src/evergreen/task.py"""

from unittest.mock import MagicMock

import pytest
from requests.models import Response

from evergreen.task import Artifact

RESPONSE_DATA = [b"data\nwith\nnew\nlines", b"second\nchunck\nof\ndata"]


@pytest.fixture
def mocked_res():
    mock_res = MagicMock(spec=Response)
    mock_res.request = MagicMock()
    mock_res.__enter__.return_value = mock_res
    mock_res.request.url = "url"
    mock_res.iter_content.return_value = iter(RESPONSE_DATA)
    mock_res.iter_lines.return_value = iter(RESPONSE_DATA)
    return mock_res


class TestArtifactStream(object):
    def test_binary_artifact_stream(self, sample_binary_artifact, mocked_api, mocked_res):
        mocked_api.session.get = MagicMock(return_value=mocked_res)
        artifact = Artifact(sample_binary_artifact, mocked_api)

        stream_output = list(artifact.stream())
        mocked_res.iter_content.assert_called_once()
        mocked_res.iter_lines.assert_not_called()
        assert stream_output == RESPONSE_DATA

    def test_binary_artifact_stream_with_params(
        self, sample_binary_artifact, mocked_api, mocked_res
    ):
        mocked_api.session.get = MagicMock(return_value=mocked_res)
        artifact = Artifact(sample_binary_artifact, mocked_api)

        chunk_size = 2

        stream_output = list(artifact.stream(decode_unicode=False, chunk_size=chunk_size))
        mocked_res.iter_content.assert_called_once_with(decode_unicode=False, chunk_size=chunk_size)
        mocked_res.iter_lines.assert_not_called()
        assert stream_output == RESPONSE_DATA

    def test_nonbinary_artifact_stream(self, sample_nonbinary_artifact, mocked_api, mocked_res):
        mocked_api.session.get = MagicMock(return_value=mocked_res)
        artifact = Artifact(sample_nonbinary_artifact, mocked_api)

        stream_output = list(artifact.stream())
        mocked_res.iter_lines.assert_called_once()
        mocked_res.iter_content.assert_not_called()
        assert stream_output == RESPONSE_DATA

    def test_artifact_stream_override(self, sample_binary_artifact, mocked_api, mocked_res):
        mocked_api.session.get = MagicMock(return_value=mocked_res)
        artifact = Artifact(sample_binary_artifact, mocked_api)
        artifact._is_binary = MagicMock()

        stream_output = list(artifact.stream(is_binary=False))
        artifact._is_binary.assert_not_called()
        mocked_res.iter_lines.assert_called_once()
        mocked_res.iter_content.assert_not_called()
        assert stream_output == RESPONSE_DATA

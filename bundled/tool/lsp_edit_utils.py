# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Utility functions for calculating edits."""

import bisect
import difflib
from threading import Thread
from typing import List, Optional

from lsprotocol import types as lsp

DIFF_TIMEOUT = 1  # 1 second


def _get_diff(old_text: str, new_text: str):
    try:
        import Levenshtein

        return Levenshtein.opcodes(old_text, new_text)
    except ImportError:
        return difflib.SequenceMatcher(a=old_text, b=new_text).get_opcodes()


def get_text_edits(
    old_text: str,
    new_text: str,
    position_encoding: lsp.PositionEncodingKind,
    timeout: Optional[int] = None,
) -> List[lsp.TextEdit]:
    """Return a list of text edits to transform old_text into new_text."""

    def code_units(c: str) -> int:
        if position_encoding == lsp.PositionEncodingKind.Utf16:
            return len(c.encode("utf-16-le")) // 2
        elif position_encoding == lsp.PositionEncodingKind.Utf8:
            return len(c.encode("utf-8"))
        return len(c.encode("utf-32-le")) // 4

    line_offsets = [0]
    code_unit_offsets = []

    for line in old_text.splitlines(True):
        col_offset = [0]
        for c in line:
            col_offset.append(col_offset[-1] + code_units(c))
        code_unit_offsets.append(col_offset)
        line_offsets.append(line_offsets[-1] + len(line))
    code_unit_offsets.append([0])

    def from_offset(offset: int) -> lsp.Position:
        line = bisect.bisect_right(line_offsets, offset) - 1
        col = offset - line_offsets[line]
        character = code_unit_offsets[line][col]
        return lsp.Position(line=line, character=character)

    sequences = []
    try:
        thread = Thread(target=lambda: sequences.extend(_get_diff(old_text, new_text)))
        thread.start()
        thread.join(timeout or DIFF_TIMEOUT)
    except Exception:
        pass

    if sequences:
        edits = [
            lsp.TextEdit(
                range=lsp.Range(start=from_offset(old_start), end=from_offset(old_end)),
                new_text=new_text[new_start:new_end],
            )
            for opcode, old_start, old_end, new_start, new_end in sequences
            if opcode != "equal"
        ]
        return edits

    # return single edit with whole document
    return [
        lsp.TextEdit(
            range=lsp.Range(start=from_offset(0), end=from_offset(len(old_text))),
            new_text=new_text,
        )
    ]

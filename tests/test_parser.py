#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer parser.
'''
import pytest
from liquer.parser import *


class TestParser:
    def test_encode_token(self):
        assert encode_token("") == ""

    def test_decode(self):
        assert decode("abc") == [["abc"]]
        assert decode("/abc") == [["abc"]]
        assert decode("abc/") == [["abc"]]
        assert decode("/abc/") == [["abc"]]
        assert decode("abc/def") == [["abc"], ["def"]]
        assert decode("ab-c/de-f") == [["ab", "c"], ["de", "f"]]
        assert decode("") == []
        assert decode("/") == []
        assert decode("//") == []

    def test_encode_decode_token(self):
        for token in [
            "http://example.com",
            "https://example.com",
            "ftp://example.com",
            "abc-def~ghi/jkl mno",
            "--~~..__",
            "~~I",
            "&+*:\\"
        ]:
            assert decode_token(encode_token(token)) == token

    def test_encode_decode(self):
        for q in [
            "~Hexample.com/abc-def/abcdef",
            "abc-defghi/jkl~_mno/abc-def/abcdef",
        ]:
            assert encode(decode(q)) == q

    def test_all_splits(self):
        assert list(all_splits("")) == [("", "")]
        assert list(all_splits("abc")) == [("abc", ""), ("", "abc")]
        assert list(all_splits("abc/def")
                    ) == [("abc/def", ""), ("abc", "def"), ("", "abc/def")]
        assert list(all_splits("/abc/def/")
                    ) == [("abc/def", ""), ("abc", "def"), ("", "abc/def")]
        assert list(all_splits("/ab-c/de-f/")
                    ) == [("ab-c/de-f", ""), ("ab-c", "de-f"), ("", "ab-c/de-f")]

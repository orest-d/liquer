#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer parser.
"""
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
            "&+*:\\",
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
        assert list(all_splits("abc/def")) == [
            ("abc/def", ""),
            ("abc", "def"),
            ("", "abc/def"),
        ]
        assert list(all_splits("/abc/def/")) == [
            ("abc/def", ""),
            ("abc", "def"),
            ("", "abc/def"),
        ]
        assert list(all_splits("/ab-c/de-f/")) == [
            ("ab-c/de-f", ""),
            ("ab-c", "de-f"),
            ("", "ab-c/de-f"),
        ]


class TestNewParser:
    def test_parse_action(self):
        action = action_request.parseString("abc-def", True)[0]
        assert action.name == "abc"
        assert len(action.parameters) == 1
        assert action.parameters[0].string == "def"

    def test_parse_parameter_entity(self):
        action = action_request.parseString("abc-~~x-~123-~.a~_b~.", True)[0]
        assert action.name == "abc"
        assert action.parameters[0].string == "~x"
        assert action.parameters[1].string == "-123"
        assert action.parameters[2].string == " a-b "

    def test_parse_escaped_parameter(self):
        res = parameter.parseString("abc~~~_~0%21",True)
        assert res[0].string == "abc~--0!"

    def test_parse_filename(self):
        q = parse("abc/def/file.txt")
        assert q.segments[0].filename == "file.txt"
    def test_parse_segments(self):
        q = parse("abc/def/-/xxx/-q/qqq")
        assert len(q.segments) == 3
        assert q.segments[0].header is None
        assert q.segments[1].header.name == ""
        assert q.segments[2].header.name == "q"
    
    def test_predecessor1(self):
        query = parse("ghi/jkl/file.txt")
        p, r = query.predecessor()
        assert p.encode() == "ghi/jkl"
        assert r.encode() == "file.txt"
        assert not r.is_empty()
        assert r.is_filename()
        assert not r.is_action_request()

        p, r = p.predecessor()
        assert p.encode() == "ghi"
        assert r.encode() == "jkl"
        assert not r.is_empty()
        assert not r.is_filename()
        assert r.is_action_request()

        p, r = p.predecessor()
        assert p.is_empty()
        assert r.encode() == "ghi"

        p, r = p.predecessor()
        assert p is None
        assert r is None

    def test_predecessor2(self):
        query = parse("-R/abc/def/-x/ghi/jkl/file.txt")
        p, r = query.predecessor()
        assert p.encode() == "-R/abc/def/-x/ghi/jkl"
        assert r.encode() == "-x/file.txt"
        assert not r.is_empty()
        assert r.is_filename()
        assert not r.is_action_request()

        p, r = p.predecessor()
        assert p.encode() == "-R/abc/def/-x/ghi"
        assert r.encode() == "-x/jkl"
        assert not r.is_empty()
        assert not r.is_filename()
        assert r.is_action_request()

        p, r = p.predecessor()
        assert p.encode() == "-R/abc/def"
        assert r.encode() == "-x/ghi"
        assert not r.is_empty()
        assert not r.is_filename()
        assert r.is_action_request()

        p, r = p.predecessor()
        assert p == None
        assert r == None

    def test_all_predecessors1(self):
        p = [p.encode() for p, r in parse("ghi/jkl/file.txt").all_predecessors()]
        assert p == ["ghi/jkl/file.txt", "ghi/jkl", "ghi", ""]
        r = [(None if r is None else r.encode()) for p, r in parse("ghi/jkl/file.txt").all_predecessors()]
        assert r == [None, "file.txt", "jkl/file.txt", "ghi/jkl/file.txt"]

    def test_all_predecessors2(self):
        p = [p.encode() for p, r in parse("-R/abc/def/-/ghi/jkl/file.txt").all_predecessors()]
        assert p == ["-R/abc/def/-/ghi/jkl/file.txt", "-R/abc/def/-/ghi/jkl", "-R/abc/def/-/ghi", "-R/abc/def"]
        r = [(None if r is None else r.encode()) for p, r in parse("-R/abc/def/-/ghi/jkl/file.txt").all_predecessors()]
        assert r == [None, "-/file.txt", "-/jkl/file.txt", "-/ghi/jkl/file.txt"]

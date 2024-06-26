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
        res = parameter.parseString("abc~~~_~0%21", True)
        assert res[0].string == "abc~--0!"

    def test_parse_filename(self):
        q = parse("abc/def/file.txt")
        assert q.segments[0].filename == "file.txt"
        assert q.filename() == "file.txt"

    def test_parse_filename0(self):
        q = parse("file.txt")
        assert q.segments[0].filename == "file.txt"
        assert q.filename() == "file.txt"

    def test_without_filename(self):
        q = parse("file.txt")
        assert q.without_filename().encode() == ""
        q = parse("abc/def/file.txt")
        assert q.without_filename().encode() == "abc/def"
        q = parse("abc/def")
        assert q.without_filename().encode() == "abc/def"

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
        r = [
            (None if r is None else r.encode())
            for p, r in parse("ghi/jkl/file.txt").all_predecessors()
        ]
        assert r == [None, "file.txt", "jkl/file.txt", "ghi/jkl/file.txt"]

    def test_all_predecessors2(self):
        p = [
            p.encode()
            for p, r in parse("-R/abc/def/-/ghi/jkl/file.txt").all_predecessors()
        ]
        assert p == [
            "-R/abc/def/-/ghi/jkl/file.txt",
            "-R/abc/def/-/ghi/jkl",
            "-R/abc/def/-/ghi",
            "-R/abc/def",
        ]
        r = [
            (None if r is None else r.encode())
            for p, r in parse("-R/abc/def/-/ghi/jkl/file.txt").all_predecessors()
        ]
        assert r == [None, "-/file.txt", "-/jkl/file.txt", "-/ghi/jkl/file.txt"]

    def test_rheader(self):
        q = parse("-R/a/b/-/world")
        assert len(q.segments) == 2
        assert q.segments[0].header.encode() == "-R"
        assert q.segments[0].encode() == "-R/a/b"

    def test_root1(self):
        q = parse("-R/a")
        assert len(q.segments) == 1
        assert q.segments[0].encode() == "-R/a"
        q = parse("-R")
        assert len(q.segments) == 1
        assert q.segments[0].header.encode() == "-R"

    def test_root2(self):
        q = parse("-R/-/dr")
        assert len(q.segments) == 2
        assert q.segments[0].header.encode() == "-R"

    def test_root3(self):
        q = parse("-R-meta/-/dr")
        assert len(q.segments) == 2
        assert q.segments[0].header.encode() == "-R-meta"

    def test_capital_bug(self):
        q = parse("x/Y/-/dr")
        assert len(q.segments) == 2
        assert isinstance(q.segments[0], ResourceQuerySegment)
        assert isinstance(q.segments[1], TransformQuerySegment)
        q = parse("data/BBNO_leads/recipes.yaml/-/dr")
        assert isinstance(q.segments[0], ResourceQuerySegment)
        assert isinstance(q.segments[1], TransformQuerySegment)

    def test_absolute_resource_bug(self):
        q = parse("/-R/a")
        assert q.absolute
        assert q.is_resource_query()
        assert q.encode() == "/-R/a"

    def test_parse_dot(self):
        q = parse("/-R/.")
        assert q.absolute
        assert q.is_resource_query()
        assert q.encode() == "/-R/."

        q = parse("/-R/././x")
        assert q.absolute
        assert q.is_resource_query()
        assert q.encode() == "/-R/././x"

    def test_parse_doubledot(self):
        q = parse("/-R/..")
        assert q.absolute
        assert q.is_resource_query()
        assert q.encode() == "/-R/.."

        q = parse("/-R/../../x")
        assert q.absolute
        assert q.is_resource_query()
        assert q.encode() == "/-R/../../x"

    def test_to_absolute(self):
        q = parse("/-R/./a/b/c")
        assert q.is_resource_query()
        rq = q.resource_query()
        assert rq.to_absolute("x/y").encode() == "-R/x/y/a/b/c"

        q = parse("/-R/../a/b/c")
        assert q.is_resource_query()
        rq = q.resource_query()
        assert rq.to_absolute("x/y").encode() == "-R/x/a/b/c"

        q = parse("/-R/../../a/b/c")
        assert q.is_resource_query()
        rq = q.resource_query()
        assert rq.to_absolute("x/y").encode() == "-R/a/b/c"

        q = parse("/-R/./../a/b/c")
        assert q.is_resource_query()
        rq = q.resource_query()
        assert rq.to_absolute("x/y").encode() == "-R/x/a/b/c"

        q = parse("/-R/.././a/b/c")
        assert q.is_resource_query()
        rq = q.resource_query()
        assert rq.to_absolute("x/y").encode() == "-R/x/a/b/c"

    def test_to_absolute_query(self):
        q = parse("/-R/./a/b/c/-/dr")
        assert q.to_absolute("x/y").encode() == "/-R/x/y/a/b/c/-/dr"

        q = parse("-R/./a/b/c/-/dr")
        assert q.to_absolute("x/y").encode() == "-R/x/y/a/b/c/-/dr"

        q = parse("/-R/../a/b/c")
        assert q.to_absolute("x/y").encode() == "/-R/x/a/b/c"

        q = parse("/-R/../../a/b/c/-/dr")
        assert q.to_absolute("x/y").encode() == "/-R/a/b/c/-/dr"

        q = parse("/-R/./../a/b/c")
        assert q.to_absolute("x/y").encode() == "/-R/x/a/b/c"

        q = parse("/-R/.././a/b/c")
        assert q.to_absolute("x/y").encode() == "/-R/x/a/b/c"


class TestQueryElements:
    def test_simple_action_request(self):
        action = ActionRequest("name")
        assert action.name == "name"
        assert action.encode() == "name"
        assert (
            repr(action).replace(" ", "").replace("\n", "")
            == "ActionRequest('name',[],Position())"
        )

    def test_action_request_from_arguments(self):
        action = ActionRequest.from_arguments("name")
        assert action.name == "name"
        assert action.encode() == "name"
        assert (
            repr(action).replace(" ", "").replace("\n", "")
            == "ActionRequest('name',[],Position())"
        )
        action = ActionRequest.from_arguments("act", 123, 456.7)
        assert action.encode() == "act-123-456.7"
        action = ActionRequest.from_arguments("negative", -123, -456.7)
        assert action.encode() == "negative-~_123-~_456.7"

    def test_action_request_list_conversion(self):
        action = ActionRequest.from_list(["name", 1])
        assert action.name == "name"
        assert action.encode() == "name-1"
        assert action.to_list() == ["name", "1"]

    def test_action_from_query(self):
        action = parse("name-1").action()
        assert action.name == "name"
        assert action.encode() == "name-1"

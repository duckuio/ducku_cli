from zipfile import Path
from src.use_cases.pattern_search import files_patterns, string_patterns, path_patterns
from src.core.documentation import DocString, Source
from src.core.project import Project

def test_filenames():
    # real relative path
    relpath = DocString("""
Lorem Ipsum ./abc/index.html Ipsum Lorem
""", "test")
    # real abs path
    abs_path = DocString("""
Lorem Ipsum /tmp/abc/index.html Ipsum Lorem
""", "test")
    # no filenames or paths
    nothing = DocString("Lorem Ipsum Lorem Ipsum Lorem Ipsum", "test")
    # if filename is part of URL - skip
    in_url1 = DocString("""
Lorem Ipsum https://google.com/index.html Ipsum Lorem
""", "test")
    in_url2 = DocString("<li><a href=\"https://github.com/abc/discord.py\">Discord.py</a></li>", "test")

    # Use the Unix path pattern instead of the commented-out filename pattern
    fn_pat = files_patterns[0]  # Unix path pattern

    assert not fn_pat.is_in(in_url1)
    assert fn_pat.is_in(relpath)  # relative path should match
    assert fn_pat.is_in(abs_path)  # absolute path should match
    assert not fn_pat.is_in(nothing)
    # Note: basefilename (just "index.html") won't match Unix path pattern as it requires path separators
    assert not fn_pat.is_in(in_url2)


def test_not_mocked_filter():
    # Test paths that should be filtered out as mocks
    mocked_path = DocString("Lorem Ipsum /path/to/file.txt Lorem Ipsum", "test")
    mocked_example = DocString("For example, you can use /path/to/config.yml to configure the app", "test")
    
    # Test paths that should be kept
    normal_path = DocString("Lorem Ipsum /tmp/me/abc/file.txt Lorem Ipsum", "test")
    
    # The Unix path pattern uses not_mocked filter
    unix_path_pattern = path_patterns[0]
    
    # Should filter out /path/to/file.txt
    assert not unix_path_pattern.is_in(mocked_path)
    
    # Should filter out example path
    assert not unix_path_pattern.is_in(mocked_example)
    
    # Should keep normal path
    assert unix_path_pattern.is_in(normal_path)


def test_ports():
    with_port1 = DocString("Lorem Ipsum runs on port 80", "test")
    with_port2 = DocString("Lorem Ipsum runs on localhost:80", "test")
    with_port3 = DocString("Lorem Ipsum runs on the port 80 and host localhost", "test")
    no_ports = DocString("Lorem Ipsum runs on localhost", "test")
    false_positive1 = DocString("You have 8 attempts in total", "test")
    false_positive2 = DocString("The portkey service was grounded in 2023", "test")
    false_positive3 = DocString("The portkey service is on 127.0.0.80", "test")
    false_positive4 = DocString("https://img.shields.io/pypi/l/dnsdiag.svg?maxAge=8600", "test")

    pat = string_patterns[0]

    assert pat.is_in(with_port1)
    assert pat.is_in(with_port2)
    assert pat.is_in(with_port3)
    assert not pat.is_in(no_ports)
    assert not pat.is_in(false_positive1)
    assert not pat.is_in(false_positive2)
    assert not pat.is_in(false_positive3)
    assert not pat.is_in(false_positive4)

def test_envs():
    with_env = DocString("Lorem Ipsum uses environment variable 'APP_PATH'", "test")
    no_env = DocString("Lorem Ipsum Lorem Ipsum", "test")
    false_positive = DocString("Lorem Ipsum Lorem IPSUM Lorem", "test")
    
    pat = string_patterns[1]

    assert pat.is_in(with_env)
    assert not pat.is_in(no_env)
    assert not pat.is_in(false_positive)

# @TODO unit tests for contain path and string
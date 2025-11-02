from pathlib import Path
from src.use_cases.pattern_search import all_patterns, PatternSearch
from src.core.documentation import DocString, Source
from src.core.project import Project

def test_filenames():
    # Standalone filename (should match)
    standalone = DocString("Lorem Ipsum index.html Ipsum Lorem", "test")
    
    # filename in relative path (should still match the filename part)
    relpath = DocString("Lorem Ipsum ./abc/index.html Ipsum Lorem", "test")
    
    # filename in absolute path (should still match the filename part)
    abs_path = DocString("Lorem Ipsum /tmp/abc/index.html Ipsum Lorem", "test")
    
    # no filenames
    nothing = DocString("Lorem Ipsum Lorem Ipsum Lorem Ipsum", "test")
    
    # if filename is part of URL - should be filtered out
    in_url1 = DocString("Lorem Ipsum https://google.com/index.html Ipsum Lorem", "test")
    in_url2 = DocString("<li><a href=\"https://github.com/abc/discord.py\">Discord.py</a></li>", "test")

    # Find the filename pattern from all_patterns
    filename_pattern = next(p for p in all_patterns if p.name == "Filename")

    assert filename_pattern.is_in(standalone)  # standalone filename should match
    assert filename_pattern.is_in(relpath)  # filename in path should still match (just the filename part)
    assert filename_pattern.is_in(abs_path)  # filename in path should still match (just the filename part)
    assert not filename_pattern.is_in(nothing)  # no filenames should not match
    assert not filename_pattern.is_in(in_url1)  # URL context should be filtered out
    assert not filename_pattern.is_in(in_url2)  # URL context should be filtered out


def test_unix_paths():
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

    # Find the Unix path pattern from all_patterns
    unix_path_pattern = next(p for p in all_patterns if p.name == "Unix path")

    assert not unix_path_pattern.is_in(in_url1)
    assert unix_path_pattern.is_in(relpath)  # relative path should match
    assert unix_path_pattern.is_in(abs_path)  # absolute path should match
    assert not unix_path_pattern.is_in(nothing)


def test_not_mocked_filter():
    # Test paths that should be filtered out as mocks
    mocked_path = DocString("Lorem Ipsum /path/to/file.txt Lorem Ipsum", "test")
    mocked_example = DocString("For example, you can use /path/to/config.yml to configure the app", "test")
    
    # Test paths that should be kept
    normal_path = DocString("Lorem Ipsum /tmp/me/abc/file.txt Lorem Ipsum", "test")
    
    # Find the Unix path pattern from all_patterns
    unix_path_pattern = next(p for p in all_patterns if p.name == "Unix path")
    
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

    # Find the port pattern from all_patterns
    port_pattern = next(p for p in all_patterns if p.name == "Port Number")

    assert port_pattern.is_in(with_port1)
    assert port_pattern.is_in(with_port2)
    assert port_pattern.is_in(with_port3)
    assert not port_pattern.is_in(no_ports)
    assert not port_pattern.is_in(false_positive1)
    assert not port_pattern.is_in(false_positive2)
    assert not port_pattern.is_in(false_positive3)
    assert not port_pattern.is_in(false_positive4)

def test_envs():
    with_env = DocString("Lorem Ipsum uses environment variable 'APP_PATH'", "test")
    with_env2 = DocString("Use `PROJECT_PATH` environment variable to define the project root", "test")
    no_env = DocString("Lorem Ipsum Lorem Ipsum", "test")
    false_positive = DocString("Lorem Ipsum Lorem IPSUM Lorem", "test")

    # Find the environment variable pattern from all_patterns
    env_pattern = next(p for p in all_patterns if p.name == "Environment variable")

    assert env_pattern.is_in(with_env)
    assert env_pattern.is_in(with_env2)
    assert not env_pattern.is_in(no_env)
    assert not env_pattern.is_in(false_positive)

def test_routes():
    with_route = DocString("Lorem Ipsum defines a route '/api/v1/resource'", "test")
    with_route2 = DocString("Use the `GET /api/v1/resource` endpoint to retrieve data", "test")
    with_route3 = DocString("Use the `curl -X http://localhost/api/v1/resource` endpoint to retrieve data", "test")
    false_positive1 = DocString("Here is just filename path /tmp/abc/123.txt", "test")
    false_positive2 = DocString("No context /abc/def here", "test")
    false_positive3 = DocString("Use the `curl -X http://googl.com/api/v1/resource` endpoint to retrieve data", "test")

    # Find the route pattern from all_patterns
    route_pattern = next(p for p in all_patterns if p.name == "HTTP Route")

    assert route_pattern.is_in(with_route)
    assert route_pattern.is_in(with_route2)
    assert route_pattern.is_in(with_route3)
    assert not route_pattern.is_in(false_positive1)
    assert not route_pattern.is_in(false_positive2)
    assert not route_pattern.is_in(false_positive3)

def test_strings_in_project():
    # README contains an environment variable which is not used in the project
    path = Path(__file__).parent / ".." / "mocks" / "projects" / "patterns"
    p = Project(path)
    uc = PatternSearch(p)
    report = uc.report()
    print(report)
    assert report != ""
    assert "Environment variable" in report

def test_files_in_project():
    # README contains filename which is not used in the project
    path = Path(__file__).parent / ".." / "mocks" / "projects" / "patterns"
    p = Project(path)
    uc = PatternSearch(p)
    report = uc.report()
    print(report)
    assert report != ""
    assert "Filename" in report

def test_filepaths_in_project():
    # README contains path which is not used in the project
    path = Path(__file__).parent / ".." / "mocks" / "projects" / "patterns"
    p = Project(path)
    uc = PatternSearch(p)
    report = uc.report()
    assert report != ""
    assert "path" in report

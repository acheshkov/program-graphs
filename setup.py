from setuptools import setup
from setuptools.command.build_py import build_py
from shutil import copytree
from os.path import join


class BuildCommand(build_py):
    def run(self) -> None:
        build_py.run(self)
        if not self.dry_run:
            target_dir = join(self.build_lib, 'tree-sitter-java')
            copytree('./tree-sitter-java', target_dir)


def parse_requirements_file(filename):
    with open(filename) as fid:
        requires = [line.strip() for line in fid.readlines() if not line.startswith("#")]

    return requires


install_requires = parse_requirements_file("requirements/default.txt")
extras_require = {}


packages = [
    'program_graphs',
    'program_graphs.utils',
    'program_graphs.adg',
    'program_graphs.adg.parser',
    'program_graphs.adg.parser.java',
    # 'program_graphs.cfg',
    # 'program_graphs.cfg.parser',
    # 'program_graphs.cfg.parser.java',
    'program_graphs.ddg',
    'program_graphs.ddg.parser',
    'program_graphs.ddg.parser.java'
]

setup(
    name="program_graphs",
    description="A python library to build graphs for programs written in different programming languages.",
    version="0.1",
    packages=packages,
    author="Anton Cheshkov",
    python_requires=">=3.7",
    install_requires=install_requires,
    extras_require=extras_require,
    include_package_data=True,
    zip_safe=False,
    cmdclass={"build_py": BuildCommand}
)

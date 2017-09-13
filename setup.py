from setuptools import setup

import versioneer

commands = versioneer.get_cmdclass()

setup(name="grilbfs",
      version=versioneer.get_version(),
      description="Encryption layer for FUSE",
      author="Brian Warner",
      author_email="warner-grilbfs@lothar.com",
      license="MIT",
      url="https://github.com/warner/grilbfs",
      package_dir={"": "src"},
      packages=["grilbfs",
                "grilbfs.test",
                ],
      entry_points={
          "console_scripts":
          [
              "grilbfs = grilbfs.cli:run",
          ]
      },
      install_requires=[
          "pynacl",
          "six",
          "attrs >= 16.3.0", # 16.3.0 adds __attrs_post_init__
          "twisted",
          "llfuse",
      ],
      extras_require={
          "dev": ["mock", "tox", "pyflakes"],
      },
      test_suite="grilbfs.test",
      cmdclass=commands,
      )

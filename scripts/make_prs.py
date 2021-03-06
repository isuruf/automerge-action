#!/user/bin/env python
import os
import sys
import github
import subprocess
import yaml


META = """\
{% set name = "cf-autotick-bot-test-package" %}
{% set version = "0.9" %}

package:
  name: {{ name|lower }}
  version: {{ version }}

source:
  url: https://github.com/regro/cf-autotick-bot-test-package/archive/v{{ version }}.tar.gz
  sha256: 74d5197d4ca8afb34b72a36fc8763cfaeb06bdbc3f6d63e55099fe5e64326048

build:
  number: {{ build }}
  string: "{{ cislug }}_py{{ py }}h{{ PKG_HASH }}_{{ build }}"

requirements:
  host:
    - python
    - pip
  run:
    - python

test:
  commands:
    - echo "works!"

about:
  home: https://github.com/regro/cf-scripts
  license: BSD-3-Clause
  license_family: BSD
  license_file: LICENSE
  summary: testing feedstock for the regro-cf-autotick-bot

extra:
  recipe-maintainers:
    - beckermr
    - conda-forge/bot
"""  # noqa

assert sys.argv[3][0] == "v"
assert isinstance(int(sys.argv[3][1:]), int)

BUILD_SLUG = "{% set build = " + str(int(sys.argv[3][1:]) + 14) + " %}\n"

CI_SLUG = '{% set cislug = "' + sys.argv[1] + sys.argv[2] + '" %}\n'

TST = sys.argv[3]
USER = sys.argv[4]

BRANCH = TST + "-" + sys.argv[1] + "-" + sys.argv[2]

print("\n\n=========================================")
print("making the head branch")
subprocess.run(
    ["git", "checkout", "%s-%s" % (sys.argv[1], sys.argv[2])],
    check=True,
)

subprocess.run(
    ["git", "pull", "upstream", "%s-%s" % (sys.argv[1], sys.argv[2])],
    check=True,
)

subprocess.run(
    ["git", "checkout", "-b", BRANCH],
    check=True,
)

print("\n\n=========================================")
print("editing the recipe")

with open("recipe/meta.yaml", "w") as fp:
    fp.write(CI_SLUG)
    fp.write(BUILD_SLUG)
    fp.write(META)

with open("conda-forge.yml", "r") as fp:
    cfg = yaml.safe_load(fp)

cfg["provider"]["linux"] = sys.argv[1]
cfg["provider"]["osx"] = sys.argv[2]
prov = cfg["provider"]
if "linux_ppc64le" in prov:
    del prov["linux_ppc64le"]

with open("conda-forge.yml", "w") as fp:
    yaml.dump(cfg, fp)

with open("recipe/conda_build_config.yaml", "w") as fp:
    fp.write("""\
python:
 - 3.6.* *_cpython
""")

subprocess.run(
    ["git", "add", "conda-forge.yml",
     "recipe/meta.yaml", "recipe/conda_build_config.yaml"],
    check=True,
)

print("\n\n=========================================")
print("rerendering")

subprocess.run(
    ["conda", "smithy", "rerender", "-c", "auto"],
    check=True
)

print("\n\n=========================================")
print("pushing to the fork")

subprocess.run(
    ["git", "push", "--set-upstream", "origin", BRANCH]
)

print("\n\n=========================================")
print("making the PR")

gh = github.Github(os.environ["GITHUB_TOKEN"])
repo = gh.get_repo("conda-forge/cf-autotick-bot-test-package-feedstock")
pr = repo.create_pull(
    title="TST test automerge " + BRANCH,
    body=(
        "This PR is an autogenerated test for automerge. It should merge on its own."),
    head=USER + ":" + BRANCH,
    base="%s-%s" % (sys.argv[1], sys.argv[2]),
    maintainer_can_modify=True,
)
pr.add_to_labels("automerge")

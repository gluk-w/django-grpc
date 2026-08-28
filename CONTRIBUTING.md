# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at https://github.com/gluk-w/django-grpc/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "feature"
is open to whoever wants to implement it.

### Write Documentation

Django gRPC could always use more documentation, whether as part of the
official Django gRPC docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at https://github.com/gluk-w/django-grpc/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Get Started!

Ready to contribute? Here's how to set up `django-grpc` for local development.

1. Fork the `django-grpc` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/django-grpc.git

3. Install your local copy. The project uses `poetry`, which creates the virtualenv for you::

    $ cd django-grpc/
    $ poetry install

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox::

        $ make lint
        $ poetry run tox

   `tox` runs the suite against every supported Python and Django combination.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

### Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.md.
3. The pull request should work for every Python and Django version in
   `tox.ini`. The "Test with tox" workflow checks this on each pull request;
   make sure it is green before asking for a review.

### Tips

To run a single environment or a subset of tests::

    $ poetry run tox -e py313-django52
    $ poetry run pytest tests/test_server.py

## Releasing

Releases are automated. Every push to `master` runs the test suite, builds
`<major>.<minor>.<build number>`, publishes it to PyPI and creates the matching
git tag and GitHub release. Nobody picks a version or creates a tag by hand.

* The `major.minor` pair is read from the `version` field in `pyproject.toml`.
* The patch component is the build number of the "Upload Python Package"
  workflow. It only ever moves forward, so expect gaps in the sequence.

A normal merge to `master` therefore ships `1.2.13`, then `1.2.14`, and so on
with no extra action.

### Starting a new minor series

When the accumulated changes deserve a new minor version, bump it and push::

    $ poetry version minor          # 1.2.0 -> 1.3.0
    $ git commit -am "Bump version to 1.3"
    $ git push

The next release cut from `master` is then `1.3.<build number>`. Use
`poetry version major` to start a new major series.

The third component committed in `pyproject.toml` is only a placeholder. It is
never published: the workflow overwrites it at build time.

### Things not to break

* `.github/workflows/pypi-publish.yml` must keep its filename and its `pypi`
  environment. PyPI trusted publishing is keyed on both, and the build number
  is a per-workflow-file counter, so renaming the file breaks authentication
  and restarts versions at 1.
* The publish step must stay inline in that workflow. Moving it into a reusable
  workflow changes the OIDC claim PyPI checks, and the upload is rejected.
* The build refuses to publish a version that is not ahead of what PyPI already
  has, so a reset counter fails loudly instead of silently mis-tagging a release.

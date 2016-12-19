Maintainer Guide
================

If you are reading this, you probably forgot how to release a new version. Keep
reading.

Too long, won't read
--------------------

1. Start your project with a cookiecutter template.
2. Start your git flow workflow::

    git flow init

3. Start a new feature::

    git flow feature start <feature name>

4. Code, code and code. More coding. Fuck it up several times. Push to feature
branch. Watch Travis go red. Write unit tests. Watch Travis go red again.
5. Finish your feature::

    git flow feature finish <feature name>

6. Repeat 3-5 for every other feature you have planned for this release.
7. When you're done with the features and ready to publish, start a new release::

    git flow release start <release number>

8. Update your changelog (edit HISTORY.rst after to customize)::

    gitchangelog > HISTORY.rst

9. Bump your version (check everything before next step)::

    bumpversion --no-commit --no-tag

10. Commit your changes to version files and changelog::

    git commit -aS

10. Finish your release::

    git flow release finish <release number>

11. Push your tags::

    git push --tags

12. Draft a new release in GitHub (based on the new version tag) and include
a description. Also pick a codename because it makes you cool.

13. Publish your new version to PyPI::

    python setup.py sdist upload

14. Write about your new version in your blog. Tweet it, post it on facebook.

Planning a new release
----------------------

Basically, the process of developing a new release starts with planning. There
are three types of release depending on the magnitude of the features or
bugfixes you are planning to include.

* A *Major* release generally involves a complete rewrite of the application or
  backend. You could also consider it a *Major* release if you add several new
  modules or functionality.
* A *Minor* release is about a couple of new modules or some missing
  functionality. 
* A *Patch* release contains bugfixes or minor patches.

Then you could increment the version number of the release according to 
semantic versioning::

    [MAJOR].[MINOR].[PATCH]

For example, let's say a new Minor release is made for *myprogram 2.4.5*, then
the following increment should be made::

    2.4.5 -> 2.5.0

Now, we're assuming you already manage your project with Git, like everyone.
Let's dig into a little bit of details.

Branches and versioning
-----------------------

The ``develop`` branch is the one you'll be doing most of your work off of; it's also the
branch that represents the code to be deployed in the next release. ``feature`` branches
represent non-trivial features and fixes that have not yet been deployed (a completed
``feature`` branch is merged back into ``develop``). Updating ``master`` is done through
the creation of a ``release``.

This workflow can be automated by using ``git flow``.

Master
~~~~~~

``master`` is always "production ready" code. Commits are never made directly to ``master``. Rather, 
code on ``master`` only gets there after a production release branch is created
and "finished" (more on that in a sec). Thus the code on ``master`` is always able
to be released to production. Also, ``master`` is always in a predictable state,
so you never need to worry if ``master`` (and thus production) has changes one of
your other branches doesn't.

Develop
~~~~~~~

Most of your work is done on the ``develop`` branch. This branch contains all of the completed features and
bug fixes yet to be released; nightly builds or continuous integration servers should target ``develop``,
as it represents the code that will be included in the next release.
For one-off commits, feel free to commit to ``develop`` directly. 

Feature
~~~~~~~

For larger features, a ``feature`` branch should be created. ``feature`` branches are created off of
``develop``. They can be small enhancements for the next release or further out
changes that, nonetheless, need to be worked on now. To start work on a new
feature, use::

    git flow feature start <feature name>

This creates a new branch: ``feature/<feature name>``. Commits are then made to this branch 
as normal. When the feature is complete *and ready to be released to production*, it 
should be merged back into develop using the following command::

    git flow feature finish <feature name>

This merges the code into ``develop`` and deletes the ``feature/<feature name>`` branch.

Release
~~~~~~~

A ``release`` branch is created from ``develop`` when you're ready to begin a
production release. Create one using the following command::

    git flow release start <release number>

Note that this is the first time a version number for the release is created.
All completed and ready to be released features must already be on ``develop``
(and thus ``feature finish``'ed). After your release branch is created, release
your code. Any small bug fixes needed after the release are made directly to the
``release/<release number>`` branch. Once it has settled down and no more bug
fixes seem necessary, run the following command::

    git flow release finish <release number>

This merges your ``release/<release number>`` changes back into both ``master``
*and* ``develop``, meaning you never need to worry about either of those branches
lacking changes that are in production (perhaps as the result of a quick bug
fix).

Hotfix
~~~~~~

While potentially useful, ``hotfix`` branches are, I would guess, little used in
the real world. A ``hotfix`` is like a ``feature`` branch off of ``master``: if you've
already closed a ``release`` branch but realize there are vital changes that need
to be released, create a ``hotfix`` branch off of ``master`` (at the tag created
during ``$ git flow release finish <release number>``) like so::

    git flow hotfix start <release number>

After you make your changes and bump your version number, finalize the ``hotfix`` via::

    git flow hotfix finish <release number>

This, like a ``release`` branch (since it essentially *is* a type of release
branch), commits the changes to both ``master`` and ``develop``.
The reason I assume they're rarely used is because there is already a mechanism
for making changes to released code: committing to an un-``finish``ed release
branch. Sure, in the beginning, teams may ``git flow release finish ...`` too
early, only to find they need to make some quick changes the next day. Over
time, though, they'll settle on a reasonable amount of time for a ``release``
branch to remain open and, thus, won't have a need for ``hotfix`` branches. The
only *other* time you would need a ``hotfix`` branch is if you needed a new
"feature" in production immediately, without picking up the changes already in
``develop``. That strikes me as something that happens (hopefully) very rarely.


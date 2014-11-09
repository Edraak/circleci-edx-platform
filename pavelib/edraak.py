"""
Edraak internationalization tasks
"""
from path import path
from paver.easy import task, needs, sh
import polib
import os
import shutil
from git import Repo

PLATFORM_ROOT = path('.')
git_repo = Repo(PLATFORM_ROOT)

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text  # pylint: disable-msg=invalid-name


@task
def edraak_remove_empty_messages():
    filename = PLATFORM_ROOT / 'conf/locale/ar/LC_MESSAGES/edraak-platform-theme.po'

    pofile = polib.pofile(filename)

    # `reversed()` is used to allow removing from the bottom
    # instead of changing the index and introducing bugs
    for entry in reversed(pofile):
        if not entry.msgstr.strip():
            pofile.remove(entry)
        elif entry.msgid == 'About {course.display_number_with_default}':
            print "Something`s wrong!"

    pofile.save()


@task
def edraak_transifex_pull():
    # Start with clean translation state
    clean_git_repo_msg = "The repo has local modifications. Please stash or commit your changes."
    assert not git_repo.is_dirty(untracked_files=True), clean_git_repo_msg

    # Get Edraak translations
    sh('tx pull --force --mode=reviewed --language=ar --resource=edraak.edraak-platform-theme')


@task
def edraak_generate_files():
    """
    Append all Edraak strings to the original django.mo.
    """
    lc_messages_dir = PLATFORM_ROOT / 'conf/locale/ar/LC_MESSAGES'
    edraak_pofile_name = lc_messages_dir / 'edraak-platform-theme.po'

    django_pofile_name = lc_messages_dir / 'django.po'
    django_mofile_name = lc_messages_dir / 'django.mo'

    django_pofile = polib.pofile(django_pofile_name)
    edraak_pofile = polib.pofile(edraak_pofile_name)

    for entry in edraak_pofile:
        django_pofile.append(entry)

    # Save a backup in git for later inspection, and keep django.po untouched
    customized_pofile_name = lc_messages_dir / 'django-edraak-customized.po'
    django_pofile.save(customized_pofile_name)
    django_pofile.save_as_mofile(django_mofile_name)


@task
@needs(
    'pavelib.edraak.edraak_transifex_pull',
    'pavelib.edraak.edraak_remove_empty_messages',
    'pavelib.edraak.edraak_generate_files',
)
def edraak_i18n_pull():
    """
    Pulls Edraak-specific translation files.
    """
    files_to_add = (
        'conf/locale/ar/LC_MESSAGES/edraak-platform-theme.po',
        'conf/locale/ar/LC_MESSAGES/django.po',
        'conf/locale/ar/LC_MESSAGES/django.mo',
        'conf/locale/ar/LC_MESSAGES/django-edraak-customized.po',
    )

    git_repo.index.add(files_to_add, force=True)
    sh("git commit -m 'Update Edraak translations (autogenerated message)' --edit")


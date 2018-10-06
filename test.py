#!/usr/bin/env python3
from datetime import datetime, date
from os.path import join, getsize
from pathlib import Path
from tempfile import TemporaryDirectory
import pytz
from shutil import copytree
from os import mkdir
from os.path import lexists

import pytest # type: ignore
from pytest import mark # type: ignore
skip = mark.skip

from wereyouhere.common import History
from wereyouhere.render import render

import imp
backup_db = imp.load_source('hdb', 'scripts/backup-chrome-history-db.py')

def assert_got_tzinfo(h: History):
    for url, entry in h.items():
        visits = entry.visits
        for v in visits:
            assert v.dt.tzinfo is not None

def test_takeout():
    test_takeout_path = "testdata/takeout"
    import wereyouhere.generator.takeout as takeout_gen
    histories = takeout_gen.get_takeout_histories(test_takeout_path)
    [hist] = histories
    assert len(hist) > 0 # kinda arbitrary?

    assert_got_tzinfo(hist)

    with TemporaryDirectory() as tdir:
        render([hist], join(tdir, 'res.json'))

def test_takeout_new_zip():
    test_takeout_path = "testdata/takeout.zip"
    import wereyouhere.generator.takeout as tgen
    hists = tgen.get_takeout_histories(test_takeout_path)
    [hist] = hists
    assert len(hist) == 3
    entry = hist['takeout.google.com/settings/takeout']
    vis, = entry.visits

    edt = datetime(
        year=2018,
        month=9,
        day=18,
        hour=5,
        minute=48,
        second=23,
        tzinfo=pytz.utc,
    )
    assert vis.dt == edt

    assert_got_tzinfo(hist)


# TODO run condition?? and flag to force all

def test_chrome():
    import wereyouhere.generator.chrome as chrome_gen

    with TemporaryDirectory() as tdir:
        path = backup_db.backup_to(tdir)

        [hist] = list(chrome_gen.iter_chrome_histories(path, 'sqlite'))
        assert len(hist) > 10 # kinda random sanity check

        render([hist], join(tdir, 'res.json'))

        assert_got_tzinfo(hist)

def test_plaintext_path_extractor():
    import wereyouhere.generator.custom as custom_gen
    from wereyouhere.generator.plaintext import extract_from_path

    hist = custom_gen.get_custom_history(
        extract_from_path('testdata/custom'),
    )
    assert len(hist) == 4

def test_normalise():
    import wereyouhere.generator.custom as custom_gen
    from wereyouhere.generator.plaintext import extract_from_path

    hist = custom_gen.get_custom_history(
        extract_from_path('testdata/normalise'),
    )
    assert len(hist) == 5


@skip("use a different way to specify filter other than class variable..")
def test_filter():
    import wereyouhere.generator.custom as custom_gen
    from wereyouhere.generator.plaintext import extract_from_path

    History.add_filter(r'some-weird-domain')
    hist = custom_gen.get_custom_history(
        extract_from_path('testdata/custom'),
    )
    assert len(hist) == 4 # chrome-error got filtered out

def test_custom():
    import wereyouhere.generator.custom as custom_gen

    hist = custom_gen.get_custom_history(
        """grep -Eo -r --no-filename '(http|https)://\S+' testdata/custom""",
        tag='test',
    )
    assert len(hist) == 4 # https and http are same
    with TemporaryDirectory() as tdir:
        render([hist], join(tdir, 'res.json'))



TESTDATA_CHROME_HISTORY = "/L/data/wereyouhere/testdata/chrome-history"

def get_chrome_history_backup(td: str):
    copytree(TESTDATA_CHROME_HISTORY, join(td, 'backup'))

def test_merge():
    merge = backup_db.merge

    # TODO third is implicit... use merging function
    with TemporaryDirectory() as tdir:
        get_chrome_history_backup(tdir)
        first  = join(tdir, "backup/20180415/History")
        second = join(tdir, "backup/20180417/History")

        mdir = join(tdir, 'merged')
        mkdir(mdir)
        merged_path = join(mdir, 'merged.sql')


        def merged_size() -> int:
            return getsize(merged_path)

        merge(merged_path, first)
        fsize = merged_size()

        merge(merged_path, first)
        fsize_2 = merged_size()

        assert fsize == fsize_2

        merge(merged_path, second)
        ssize = merged_size()

        assert ssize > fsize

        merge(merged_path, second)
        ssize_2 = merged_size()

        assert ssize_2 == ssize

merge_all_from = backup_db.merge_all_from # type: ignore


def _test_merge_all_from(tdir):
    mdir = join(tdir, 'merged')
    mkdir(mdir)
    mfile = join(mdir, 'merged.sql')

    get_chrome_history_backup(tdir)

    merge_all_from(mfile, join(tdir, 'backup'), None)

    first  = join(tdir, "backup/20180415/History")
    second = join(tdir, "backup/20180417/History")

    # should be removed
    assert not lexists(first)
    assert not lexists(second)

    import wereyouhere.generator.chrome as chrome_gen

    [hist] = list(chrome_gen.iter_chrome_histories(mfile, 'sqlite'))
    assert len(hist) > 0

    older = hist['github.com/orgzly/orgzly-android/issues']
    assert any(v.dt.date() < date(year=2018, month=1, day=17) for v in older.visits)
    # in particular, "2018-01-16 19:56:56"

    newer = hist['en.wikipedia.org/wiki/Notice_and_take_down']
    assert any(v.dt.date() >= date(year=2018, month=4, day=16) for v in newer.visits)

    # from implicit db
    newest = hist['feedly.com/i/discover']
    assert any(v.dt.date() >= date(year=2018, month=9, day=27) for v in newest.visits)

def test_merge_all_from():
    with TemporaryDirectory() as tdir:
        _test_merge_all_from(tdir)
        # TODO and also some other unique thing..

if __name__ == '__main__':
    pytest.main(__file__)

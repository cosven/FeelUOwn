import pytest
from PyQt6.QtCore import QModelIndex, Qt

from feeluown.library import SongModel
from feeluown.utils import aio
from feeluown.player import Playlist
from feeluown.gui.components.player_playlist import PlayerPlaylistModel


def _song(identifier):
    return SongModel(
        identifier=str(identifier),
        source="fake",
        title=str(identifier),
        album=None,
        artists=[],
        duration=0,
    )


def _songs(count):
    return [_song(i) for i in range(count)]


@pytest.mark.asyncio
async def test_player_playlist_model_removes_cached_image(app_mock, qtbot, song):
    async def fetch_cover(_, cb):
        cb(b"image content")

    playlist = Playlist(app_mock)
    model = PlayerPlaylistModel(playlist, fetch_cover)

    assert model.rowCount() == 0
    playlist.add(song)
    assert model.rowCount() == 1

    model.data(model.index(0, 0), Qt.ItemDataRole.UserRole)
    await aio.sleep(0.1)
    assert len(model.image_cache) == 1

    playlist.remove(song)
    assert len(model.image_cache) == 0


def test_player_playlist_model_clear_clips_removed_rows(app_mock, qtbot):
    async def fetch_cover(_, cb):
        cb(None)

    playlist = Playlist(app_mock, songs=_songs(12))
    model = PlayerPlaylistModel(playlist, fetch_cover)
    model.fetchMore(QModelIndex())

    assert model.rowCount() == 10

    playlist.clear()

    assert model.rowCount() == 0
    assert not model.canFetchMore(QModelIndex())


def test_player_playlist_model_ignores_add_after_loaded_prefix(app_mock, qtbot):
    async def fetch_cover(_, cb):
        cb(None)

    playlist = Playlist(app_mock, songs=_songs(12))
    model = PlayerPlaylistModel(playlist, fetch_cover)
    model.fetchMore(QModelIndex())

    assert model.rowCount() == 10

    playlist.add(_song(12))

    assert model.rowCount() == 10

    model.fetchMore(QModelIndex())

    assert model.rowCount() == 13

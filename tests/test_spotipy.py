import os.path

from spotisync.spotifyapi.download import download_and_save_mp3


def test_download():
    download_and_save_mp3("4qDHt2ClApBBzDAvhNGWFd", "myfile.mp3", ".", False)
    assert os.path.exists(os.path.join(".", "myfile.mp3")) == True
    os.remove(os.path.join(".", "myfile.mp3"))
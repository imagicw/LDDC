# SPDX-FileCopyrightText: Copyright (C) 2024-2025 沉默の金 <cmzj@cmzj.org>
# SPDX-License-Identifier: GPL-3.0-only

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot

from LDDC.common.models import LyricsFormat

from .helper import create_audio_file, get_tmp_dir, grab, screenshot_path, select_file, verify_lyrics

if TYPE_CHECKING:
    from LDDC.gui.view.main_window import MainWindow


def change_preview_format(qtbot: QtBot, lyrics_format: LyricsFormat, main_window: "MainWindow") -> None:
    if main_window.open_lyrics_widget.lyricsformat_comboBox.currentIndex() != lyrics_format.value:
        orig_text = main_window.open_lyrics_widget.plainTextEdit.toPlainText()
        main_window.open_lyrics_widget.lyricsformat_comboBox.setCurrentIndex(lyrics_format.value)

        def check_preview_result() -> bool:
            return bool(
                len(main_window.open_lyrics_widget.plainTextEdit.toPlainText()) > 20
                and main_window.open_lyrics_widget.plainTextEdit.toPlainText() != orig_text,
            )

        qtbot.waitUntil(check_preview_result)
        qtbot.wait(20)


def test_gui_open_lyrics(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, main_window: "MainWindow") -> None:
    main_window.show()
    main_window.set_current_widget(2)
    qtbot.wait(300)  # 等待窗口加载完成
    grab(main_window, screenshot_path / "open_lyrics")

    # 测试各种歌词文件类型
    files = {
        "qrc": "铃木木乃美 (鈴木このみ) - アスタロア (Asterlore)"
        " - 278 - PCゲーム『Summer Pockets REFLECTION BLUE』オープニングテーマ「アスタロア」 (Asterlore)_qm.qrc",
        "krc": "鈴木このみ - アスタロア (Asterlore).krc",
    }
    monkeypatch.setattr(QFileDialog, "open", lambda *args, **kwargs: None)  # noqa: ARG005
    for file_format, name in files.items():
        path = Path(__file__).parent / "data" / name
        main_window.open_lyrics_widget.open_pushButton.click()
        select_file(main_window.open_lyrics_widget, str(path))
        qtbot.wait(150)
        grab(main_window, screenshot_path / f"open_lyrics_{file_format}")
        main_window.open_lyrics_widget.convert_pushButton.click()
        qtbot.wait(40)
        for lyrics_format in [LyricsFormat.VERBATIMLRC, LyricsFormat.LINEBYLINELRC, LyricsFormat.ENHANCEDLRC, LyricsFormat.ASS, LyricsFormat.SRT]:
            change_preview_format(qtbot, lyrics_format, main_window)
            verify_lyrics(main_window.open_lyrics_widget.plainTextEdit.toPlainText())
            qtbot.wait(40)
            grab(main_window, screenshot_path / f"open_lyrics_{file_format}_{lyrics_format.name.lower()}")
        qtbot.wait(150)

    # 测试翻译功能

    main_window.open_lyrics_widget.translate_pushButton.click()

    def check_translation_done() -> bool:
        return bool(main_window.open_lyrics_widget.lyrics and "LDDC_ts" in main_window.open_lyrics_widget.lyrics)

    qtbot.waitUntil(check_translation_done, timeout=30000)
    grab(main_window, screenshot_path / "open_lyrics_translated")

    # 测试取消翻译
    main_window.open_lyrics_widget.translate_pushButton.click()
    qtbot.wait(100)
    assert main_window.open_lyrics_widget.lyrics
    assert "LDDC_ts" not in main_window.open_lyrics_widget.lyrics

def test_open_lyrics_audio(qtbot: QtBot, main_window: "MainWindow") -> None:

    # 测试音频文件处理
    tmp_dir = get_tmp_dir()
    audio_path = tmp_dir / "test_audio.flac"
    create_audio_file(audio_path, "flac", 30, tags={"LYRICS": "[00:01.00]Test lyrics"})

    main_window.open_lyrics_widget.open_pushButton.click()
    select_file(main_window.open_lyrics_widget, str(audio_path))
    qtbot.wait(150)
    grab(main_window, screenshot_path / "open_lyrics_audio")
    assert "[00:01.00]Test lyrics" in main_window.open_lyrics_widget.plainTextEdit.toPlainText()


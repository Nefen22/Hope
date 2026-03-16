"""
sound.py – Quản lý BGM vòng lặp và SFX cho game
Tự động nạp file nếu tồn tại; bỏ qua (silent) nếu không có.
"""
import os
import pyglet

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'sounds')

# ─── Mapping tên → file ───────────────────────────────────────────────────────
SFX_FILES = {
    'jump':         'jump.mp3',
    'attack':       'attack.mp3',
    'coin':         'coin.mp3',
    'block_break':  'block_break.wav',
    'enemy_hit':    'enemy_hit.wav',
    'boss_hit':     'boss_hit.wav',
    'player_hit':   'player_hit.wav',
    'menu_select':  'menu_select.mp3',
    'boss_enter':   'boss_enter.wav',
    'victory':      'victory.mp3',
    'switch':       'switch.mp3',
    'door_open':    'door_open.mp3',
}

BGM_FILE = 'bgm.mp3'      # nhạc nền chính, vòng lặp
BOSS_BGM  = 'boss_bgm.mp3' # nhạc boss


def _load_or_none(path):
    try:
        return pyglet.media.load(path, streaming=False)
    except Exception:
        return None


class SoundManager:
    _bgm_player = None
    _sfx_cache  = {}
    bgm_volume  = 0.7
    sfx_volume  = 0.8
    _current_bgm = None
    _active_sfx  = [] # Danh sách các Player SFX đang chạy

    @classmethod
    def init(cls):
        """Khởi tạo: nạp SFX vào bộ nhớ đệm."""
        os.makedirs(ASSET_DIR, exist_ok=True)
        for name, fname in SFX_FILES.items():
            path = os.path.join(ASSET_DIR, fname)
            cls._sfx_cache[name] = _load_or_none(path)

    @classmethod
    def play_bgm(cls, which='main'):
        """Phát nhạc nền. which='main' hoặc 'boss'."""
        fname = BOSS_BGM if which == 'boss' else BGM_FILE
        path  = os.path.join(ASSET_DIR, fname)
        if cls._current_bgm == fname and cls._bgm_player:
            return  # đang phát rồi
        cls.stop_bgm()
        source = _load_or_none(path)
        if source is None:
            return
        cls._current_bgm = fname
        
        cls._bgm_player = pyglet.media.Player()
        
        # Hỗ trợ loop cho cả Pyglet 1.5 (SourceGroup) và 2.0+ (Player.loop)
        try:
            cls._bgm_player.loop = True
            cls._bgm_player.queue(source)
        except AttributeError:
            # Pyglet 1.5: Sử dụng cơ chế đơn giản nhất cho StaticSource.
            # Lưu ý: StaticSource trong Pyglet 1.5 không dễ lặp vô tận bằng queue.
            # Giải pháp tạm thời: Phát một lần, hoặc queue nhiều lần.
            cls._bgm_player.queue(source)
            # Thử set eos_action nếu version hỗ trợ
            if hasattr(cls._bgm_player, 'EOS_LOOP'):
                cls._bgm_player.eos_action = cls._bgm_player.EOS_LOOP

        cls._bgm_player.volume = cls.bgm_volume
        try:
            cls._bgm_player.play()
        except Exception:
            pass

    @classmethod
    def stop_bgm(cls):
        if cls._bgm_player:
            try:
                cls._bgm_player.pause()
                cls._bgm_player.delete()
            except Exception:
                pass
            cls._bgm_player  = None
            cls._current_bgm = None

    @classmethod
    def set_bgm_volume(cls, vol):
        cls.bgm_volume = max(0.0, min(1.0, vol))
        if cls._bgm_player:
            try:
                cls._bgm_player.volume = cls.bgm_volume
            except Exception:
                pass

    @classmethod
    def play_sfx(cls, name):
        # Dọn dẹp các player đã phát xong để tránh leak bộ nhớ
        cls._active_sfx = [player for player in cls._active_sfx if player.playing]

        source = cls._sfx_cache.get(name)
        if source is None:
            return
        try:
            p = pyglet.media.Player()
            p.volume = cls.sfx_volume
            p.queue(source)
            p.play()
            # Giữ tham chiếu để tránh Garbage Collector xoá mất khi đang phát
            cls._active_sfx.append(p)
        except Exception:
            pass

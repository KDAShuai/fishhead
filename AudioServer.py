from pydub import AudioSegment
import os
import subprocess
import socket
import librosa
import time
import threading


class UdpServer:
    """服务器"""

    def __init__(self):
        self.port = 8888
        self.ip = '0.0.0.0'
        self.beats_address = ('192.168.0.255', 8866)
        self.vocals_address = ('192.168.0.255', 8877)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.ip, self.port))
        print('Udp Server start on port:', self.port)

    def start(self):
        pass

    def sentBeats(self, drums_beats):
        start = time.perf_counter()
        print('start:', start)
        for i in range(len(drums_beats)):
            while True:
                if time.perf_counter() - start >= drums_beats[i]:
                    break
            self.server_socket.sendto((str(i + 1)).encode('utf-8'), self.beats_address)

    def thread_sentBeats(self, drums_beats):
        print('thread:sentBeats start')
        threading.Thread(target=self.sentBeats, args=(drums_beats,)).start()

    def sentVocals(self, vocals_map):
        start = time.perf_counter()
        time_sec = len(vocals_map - 1)
        self.server_socket.sendto(str(max(vocals_map) * 0.8).encode('utf-8'), self.vocals_address)
        while True:
            delta = int((time.perf_counter() - start) * 1000)
            if delta < time_sec:
                self.server_socket.sendto((str(vocals_map[delta])).encode('utf-8'), self.vocals_address)
            else:
                break

    def thread_sentVocals(self, vocals_map):
        threading.Thread(target=self.sentVocals, args=(vocals_map,)).start()


class AudioHandler:
    """音频处理"""

    # my_dir = 'C:\\Users\\Administrator\\Documents\\Songs\\'
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.save_dir = 'C:\\Users\\Administrator\\Documents\\Output\\'
        self.song = ''
        self.vocals = ''
        self.drums = ''
        self.vocals_map = []
        self.drums_beats = None

    def sync(self):
        print('音频文件名同步中。')
        # 将MP3文件重命名为wav
        if os.listdir(self.target_dir)[0][-3:] == 'mp3':
            os.rename(os.listdir(self.target_dir)[0], os.listdir(self.target_dir)[0][-3:] + 'wav')
        self.song = self.target_dir + os.listdir(self.target_dir)[0]
        self.vocals = self.save_dir + os.listdir(self.target_dir)[0][:-4] + '\\' + 'vocals.wav'
        self.drums = self.save_dir + os.listdir(self.target_dir)[0][:-4] + '\\' + 'drums.wav'
        print('self.song:', self.song, '\nself.vocals:', self.vocals, '\nself.drums:', self.drums)

    def separate(self):
        self.sync()
        command = 'spleeter separate -p spleeter:4stems -o C:\\Users\\Administrator\\Documents\\Output\\ ' + self.song
        result = subprocess.run(command, capture_output=True, text=True)
        print('音频分离完成。')
        print('stdout:', result.stdout)
        print('stderr:', result.stderr)

    def getVocalsMap(self):
        self.vocals_map = [0]
        audio = AudioSegment.from_file(self.vocals)
        for i in range(1, int(audio.duration_seconds * 1000) + 1):
            # 存储毫秒内区间最大响度到数组
            self.vocals_map.append(audio[i:i + i].rms)

    def getDrumsBeats(self):
        audio, sr = librosa.load('drums.wav')
        tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sr)
        beats = librosa.frames_to_time(beat_frames, sr=sr)
        self.drums_beats = beats


udp_server = UdpServer()
song_dir = 'C:\\Users\\Administrator\\Documents\\Pycharm_Files\\FishHead\\songs\\'
audio_handler = AudioHandler(target_dir=song_dir) 
audio_handler.separate()
audio_handler.getDrumsBeats()
audio_handler.getVocalsMap()
udp_server.thread_sentBeats(audio_handler.drums_beats)
udp_server.thread_sentVocals(audio_handler.vocals_map)


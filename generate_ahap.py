import os

# ffmpeg / ffprobe 경로를 PATH에 먼저 추가
FFMPEG_BIN = r"C:\project\ffmpeg-8.0.1-full_build\bin"
os.environ["PATH"] = FFMPEG_BIN + os.pathsep + os.environ["PATH"]

import argparse
import json
import librosa
import numpy as np
from pydub import AudioSegment
import time
from tqdm import tqdm


def convert_wav_to_ahap(input_wav, output_dir, mode, split, mood):
    try:
        start_time = time.time()

        audio = AudioSegment.from_file(
            input_wav,
            format=os.path.splitext(input_wav)[-1][1:]
        )

        # mono / 44.1kHz
        audio = audio.set_channels(1).set_frame_rate(44100)

        # numpy 변환
        audio_data = np.array(audio.get_array_of_samples())
        audio_data = audio_data.astype(np.float32) / 32768.0

        sample_rate = audio.frame_rate
        duration = len(audio_data) / sample_rate

        # HPSS
        harmonic, percussive = librosa.effects.hpss(audio_data)
        bass = librosa.effects.hpss(audio_data, margin=(1.0, 20.0))[0]

        if not output_dir:
            output_dir = os.path.dirname(input_wav)

        os.makedirs(output_dir, exist_ok=True)

        output_files = []

        if split == "none":
            ahap_data = generate_ahap(
                audio_data, sample_rate, mode,
                harmonic, percussive, bass, duration, split, mood
            )
            output_ahap = os.path.join(
                output_dir,
                os.path.basename(input_wav).replace(
                    os.path.splitext(input_wav)[-1],
                    f'_{mood}_combined.ahap'
                )
            )
            write_ahap_file(output_ahap, ahap_data)
            output_files.append(output_ahap)
        else:
            splits = ['bass', 'vocal', 'drums', 'other']
            for split_type in splits:
                if split != "all" and split != split_type:
                    continue

                ahap_data = generate_ahap(
                    audio_data, sample_rate, mode,
                    harmonic, percussive, bass, duration, split_type, mood
                )

                output_ahap = os.path.join(
                    output_dir,
                    os.path.basename(input_wav).replace(
                        os.path.splitext(input_wav)[-1],
                        f'_{mood}_{split_type}.ahap'
                    )
                )
                write_ahap_file(output_ahap, ahap_data)
                output_files.append(output_ahap)

        elapsed_time = time.time() - start_time

        print(f"AHAP files generated successfully in {elapsed_time:.2f} seconds.")
        print("Generated files:")
        for file in output_files:
            print(f" - {file}")

    except Exception as e:
        print("Error:", e)


def write_ahap_file(output_ahap, ahap_data):
    with open(output_ahap, 'w', encoding='utf-8') as f:
        json.dump(ahap_data, f, indent=4)


def generate_ahap(audio_data, sample_rate, mode, harmonic, percussive, bass, duration, split, mood):
    """
    happy / angry -> 오리지널 로직
    sad / relaxed -> 수정 로직
    """
    pattern = []

    onsets = librosa.onset.onset_detect(y=audio_data, sr=sample_rate)
    event_times = librosa.frames_to_time(onsets, sr=sample_rate)

    with tqdm(total=len(event_times), desc="Processing transient events") as pbar:
        for event_time in event_times:
            haptic_mode = determine_haptic_mode(
                audio_data, event_time, sample_rate, mode,
                harmonic, percussive, bass, mood
            )

            if haptic_mode in ['transient', 'both']:
                event = create_event(
                    "HapticTransient", event_time, audio_data, sample_rate, split, mood
                )
                if event is not None:
                    pattern.append(event)

            if haptic_mode in ['continuous', 'both']:
                event = create_event(
                    "HapticContinuous", event_time, audio_data, sample_rate, split, mood
                )
                if event is not None:
                    pattern.append(event)

            pbar.update(1)

    add_continuous_events(
        pattern, audio_data, sample_rate, harmonic, bass, duration, split, mood
    )

    ahap_data = {"Version": 1.0, "Pattern": pattern}
    return ahap_data


def create_event(event_type, event_time, audio_data, sample_rate, split, mood):
    """
    happy / angry는 오리지널 그대로
    sad / relaxed만 부드러운 버전 적용
    """
    intensity, sharpness = calculate_parameters(
        audio_data, event_time, sample_rate, split, mood
    )

    # sad / relaxed에서만 너무 약한 이벤트 제거
    if mood in ["sad", "relaxed"] and intensity < 0.03:
        return None

    event = {
        "Event": {
            "Time": float(event_time),
            "EventType": event_type,
            "EventParameters": [
                {"ParameterID": "HapticIntensity", "ParameterValue": float(intensity)},
                {"ParameterID": "HapticSharpness", "ParameterValue": float(sharpness)}
            ]
        }
    }

    if event_type == "HapticContinuous":
        if mood in ["sad", "relaxed"]:
            event["Event"]["EventDuration"] = 0.22
        else:
            # 오리지널 코드 유지
            event["Event"]["EventDuration"] = 0.1

    return event


def determine_haptic_mode(audio_data, event_time, sample_rate, mode, harmonic, percussive, bass, mood):
    """
    happy / angry -> 오리지널 determine_haptic_mode
    sad / relaxed -> 수정된 부드러운 로직
    """
    # 공통 에너지 계산
    window_size = int(sample_rate * 0.02)
    start_index = max(0, int((event_time - 0.01) * sample_rate))
    end_index = min(len(audio_data), start_index + window_size)

    segment = audio_data[start_index:end_index]
    if len(segment) == 0:
        return 'continuous' if mood in ["sad", "relaxed"] else 'both'

    energy = np.sqrt(np.mean(segment ** 2))

    bass_segment = bass[start_index:end_index]
    percussive_segment = percussive[start_index:end_index]
    harmonic_segment = harmonic[start_index:end_index]

    bass_energy = np.sqrt(np.mean(bass_segment ** 2)) if len(bass_segment) > 0 else 0.0
    percussive_energy = np.sqrt(np.mean(percussive_segment ** 2)) if len(percussive_segment) > 0 else 0.0
    harmonic_energy = np.sqrt(np.mean(harmonic_segment ** 2)) if len(harmonic_segment) > 0 else 0.0

    # spectral centroid 계산
    window_size = int(sample_rate * 0.05)
    start_index = max(0, int((event_time - 0.025) * sample_rate))
    end_index = min(len(audio_data), start_index + window_size)

    spectral_segment = audio_data[start_index:end_index]
    if len(spectral_segment) < 16:
        return 'continuous' if mood in ["sad", "relaxed"] else 'both'

    spectral_centroid = librosa.feature.spectral_centroid(
        y=spectral_segment, sr=sample_rate
    )
    spectral_centroid_mean = np.mean(spectral_centroid)

    if mode == 'sfx':
        transient_rms_threshold = 0.5
        continuous_rms_threshold = 0.2
        spectral_threshold = np.percentile(spectral_centroid, 90)
    else:
        transient_rms_threshold = 0.2
        continuous_rms_threshold = 0.1
        spectral_threshold = np.percentile(spectral_centroid, 70)

    # sad / relaxed -> 수정 로직
    if mood in ["sad", "relaxed"]:
        if percussive_energy > harmonic_energy * 1.2 and energy > transient_rms_threshold * 0.7:
            return 'both'
        elif energy > transient_rms_threshold * 0.9 and spectral_centroid_mean > 1800:
            return 'transient'
        else:
            return 'continuous'

    # happy / angry -> 오리지널 로직
    if energy > transient_rms_threshold and spectral_centroid_mean > spectral_threshold:
        return 'transient'
    elif energy < continuous_rms_threshold:
        return 'continuous'
    else:
        return 'both'


def calculate_parameters(audio_data, event_time, sample_rate, split, mood):
    """
    happy / angry -> 오리지널 파라미터 계산
    sad / relaxed -> 수정된 파라미터 계산 + 약화/부드러움 반영
    """
    # RMS energy
    window_size = int(sample_rate * 0.02)
    start_index = max(0, int((event_time - 0.01) * sample_rate))
    end_index = min(len(audio_data), start_index + window_size)

    segment = audio_data[start_index:end_index]
    if len(segment) == 0:
        return 0.0, 0.0

    energy = np.sqrt(np.mean(segment ** 2))

    # spectral centroid
    window_size = int(sample_rate * 0.05)
    start_index = max(0, int((event_time - 0.025) * sample_rate))
    end_index = min(len(audio_data), start_index + window_size)

    spectral_segment = audio_data[start_index:end_index]
    if len(spectral_segment) < 16:
        spectral_centroid = None
        sharpness = 0.0
    else:
        spectral_centroid = librosa.feature.spectral_centroid(
            y=spectral_segment, sr=sample_rate
        )
        sharpness = np.mean(spectral_centroid)

    # happy / angry -> 오리지널 정규화 방식
    if mood in ["happy", "angry"]:
        audio_max = np.max(audio_data)
        if audio_max == 0:
            audio_max = 1e-8

        scaled_energy = np.clip(energy / audio_max, 0, 1)
        scaled_energy *= 1.5
        scaled_energy = np.clip(scaled_energy, 0, 1)

        if spectral_centroid is None:
            scaled_sharpness = 0.0
        else:
            sc_max = np.max(spectral_centroid)
            if sc_max == 0:
                sc_max = 1e-8
            scaled_sharpness = np.clip(sharpness / sc_max, 0, 1)

    # sad / relaxed -> 수정 정규화 방식
    else:
        max_abs = np.max(np.abs(audio_data)) + 1e-8
        scaled_energy = np.clip(energy / max_abs, 0, 1)
        scaled_energy = np.clip(scaled_energy * 1.5, 0, 1)

        if spectral_centroid is None:
            scaled_sharpness = 0.0
        else:
            scaled_sharpness = np.clip(sharpness / 5000.0, 0, 1)

    # split 보정 (공통)
    if split == "vocal":
        scaled_energy *= 1.2
        scaled_sharpness *= 1.1
    elif split == "drums":
        scaled_energy *= 1.5
        scaled_sharpness *= 1.3
    elif split == "bass":
        scaled_energy *= 1.4
        scaled_sharpness *= 0.9
    elif split == "other":
        scaled_energy *= 1.3
        scaled_sharpness *= 1.2

    # sad / relaxed에만 추가 보정
    if mood in ["sad", "relaxed"]:
        scaled_energy *= 0.9
        scaled_sharpness *= 0.8

    return float(np.clip(scaled_energy, 0, 1)), float(np.clip(scaled_sharpness, 0, 1))


def add_continuous_events(pattern, audio_data, sample_rate, harmonic, bass, duration, split, mood):
    """
    happy / angry -> 오리지널 continuous 이벤트
    sad / relaxed -> 수정된 부드러운 continuous 이벤트
    """
    # sad / relaxed
    if mood in ["sad", "relaxed"]:
        time_step = 0.18
        duration_scale = 0.28
        intensity_scale = 0.32
        sharpness_scale = 0.22

        num_steps = int(duration / time_step)

        max_bass = np.max(np.abs(bass)) + 1e-8
        max_harmonic = np.max(np.abs(harmonic)) + 1e-8

        with tqdm(total=num_steps, desc="Processing continuous events") as pbar:
            for t in np.arange(0, duration, time_step):
                start = int(t * sample_rate)
                end = int((t + time_step) * sample_rate)

                bass_slice = bass[start:end]
                harmonic_slice = harmonic[start:end]

                if len(bass_slice) == 0 or len(harmonic_slice) == 0:
                    pbar.update(1)
                    continue

                bass_energy = np.sqrt(np.mean(bass_slice ** 2))
                harmonic_energy = np.sqrt(np.mean(harmonic_slice ** 2))

                intensity = np.clip(bass_energy / max_bass, 0, 1) * intensity_scale
                intensity = np.clip(intensity, 0, 1)

                sharpness = np.clip(harmonic_energy / max_harmonic, 0, 1) * sharpness_scale
                sharpness = np.clip(sharpness, 0, 1)

                # 너무 약해도 약간 유지
                if intensity < 0.03:
                    intensity = 0.03

                event = {
                    "Event": {
                        "Time": float(t),
                        "EventType": "HapticContinuous",
                        "EventDuration": float(duration_scale),
                        "EventParameters": [
                            {"ParameterID": "HapticIntensity", "ParameterValue": float(intensity)},
                            {"ParameterID": "HapticSharpness", "ParameterValue": float(sharpness)}
                        ]
                    }
                }
                pattern.append(event)
                pbar.update(1)

    # happy / angry -> 오리지널 코드 그대로
    else:
        time_step = 0.1
        num_steps = int(duration / time_step)

        bass_max = np.max(bass)
        harmonic_max = np.max(harmonic)

        if bass_max == 0:
            bass_max = 1e-8
        if harmonic_max == 0:
            harmonic_max = 1e-8

        with tqdm(total=num_steps, desc="Processing continuous events") as pbar:
            for t in np.arange(0, duration, time_step):
                bass_energy = np.sqrt(
                    np.mean(bass[int(t * sample_rate):int((t + time_step) * sample_rate)] ** 2)
                )
                harmonic_energy = np.sqrt(
                    np.mean(harmonic[int(t * sample_rate):int((t + time_step) * sample_rate)] ** 2)
                )

                intensity = np.clip(bass_energy / bass_max, 0, 1) * 1.5
                intensity = np.clip(intensity, 0, 1)
                sharpness = np.clip(harmonic_energy / harmonic_max, 0, 1)

                event = {
                    "Event": {
                        "Time": float(t),
                        "EventType": "HapticContinuous",
                        "EventDuration": time_step,
                        "EventParameters": [
                            {"ParameterID": "HapticIntensity", "ParameterValue": float(intensity)},
                            {"ParameterID": "HapticSharpness", "ParameterValue": float(sharpness)}
                        ]
                    }
                }
                pattern.append(event)
                pbar.update(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert WAV/MP3 file to AHAP format")
    parser.add_argument("input_wav", help="Input WAV/MP3 file path")
    parser.add_argument("--output_dir", help="Output directory for AHAP files", default=None)
    parser.add_argument("--mode", choices=['sfx', 'music'], default='music',
                        help="Mode for processing: 'sfx' or 'music'")
    parser.add_argument("--split", choices=['none', 'all', 'vocal', 'drums', 'bass', 'other'],
                        default='none',
                        help="Split mode for processing")
    parser.add_argument("--mood", choices=['happy', 'angry', 'sad', 'relaxed'],
                        default='happy',
                        help="Mood style for haptic rendering")

    args = parser.parse_args()

    convert_wav_to_ahap(
        args.input_wav,
        args.output_dir,
        args.mode,
        args.split,
        args.mood
    )
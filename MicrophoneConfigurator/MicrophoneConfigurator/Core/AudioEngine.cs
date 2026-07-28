using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using NAudio.CoreAudioApi;
using NAudio.Wave;
using NAudio.Wave.SampleProviders;

namespace MicrophoneConfigurator.Core
{
    public class AudioEngine : IDisposable
    {
        private MMDeviceEnumerator _deviceEnumerator;
        private WaveInEvent? _waveIn;
        private WaveOutEvent? _waveOut;

        private VolumeSampleProvider? _volumeProvider;
        private Equalizer? _equalizer;
        private PitchShifterSampleProvider? _pitchShifter;
        private NoiseGateSampleProvider? _noiseGate;
        private CompressorSampleProvider? _compressor;
        private LimiterSampleProvider? _limiter;
        private ReverbSampleProvider? _reverb;
        private EchoDelaySampleProvider? _echoDelay;
        private AutoGainSampleProvider? _autoGain;
        private RecordingSampleProvider? _recordingProvider;
        private WaveInProvider? _waveInProvider;

        private readonly object _lock = new();
        private bool _disposed;

        public List<AudioDevice> InputDevices { get; private set; } = new();
        public List<AudioDevice> OutputDevices { get; private set; } = new();

        public AudioDevice? SelectedInputDevice { get; private set; }
        public AudioDevice? SelectedOutputDevice { get; private set; }

        public float Volume { get; set; } = 1.0f;
        public bool IsMonitoring { get; private set; }
        public bool IsRecording { get; private set; }

        public float[] SpectrumData { get; private set; } = new float[64];
        public float[] WaveformData { get; private set; } = new float[256];
        public float GainReduction { get; private set; }
        public float CurrentAutoGain { get; private set; }

        public event Action? AudioDataAvailable;
        public event Action? DeviceChanged;
        public event Action? PlaybackStarted;
        public event Action? PlaybackStopped;

        public AudioEngine()
        {
            _deviceEnumerator = new MMDeviceEnumerator();
            RefreshDevices();
        }

        public void RefreshDevices()
        {
            lock (_lock)
            {
                InputDevices.Clear();
                OutputDevices.Clear();

                var inputDevices = _deviceEnumerator.EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);
                foreach (var device in inputDevices)
                {
                    InputDevices.Add(new AudioDevice
                    {
                        Id = device.ID,
                        Name = device.FriendlyName,
                        Device = device,
                        IsInput = true
                    });
                }

                var outputDevices = _deviceEnumerator.EnumerateAudioEndPoints(DataFlow.Render, DeviceState.Active);
                foreach (var device in outputDevices)
                {
                    OutputDevices.Add(new AudioDevice
                    {
                        Id = device.ID,
                        Name = device.FriendlyName,
                        Device = device,
                        IsInput = false
                    });
                }

                if (InputDevices.Count > 0 && SelectedInputDevice == null)
                    SelectedInputDevice = InputDevices[0];
                if (OutputDevices.Count > 0 && SelectedOutputDevice == null)
                    SelectedOutputDevice = OutputDevices[0];
            }
        }

        public void SelectInputDevice(AudioDevice device)
        {
            lock (_lock)
            {
                SelectedInputDevice = device;
                if (IsMonitoring)
                {
                    StopMonitoring();
                    StartMonitoring();
                }
            }
            DeviceChanged?.Invoke();
        }

        public void SelectOutputDevice(AudioDevice device)
        {
            lock (_lock)
            {
                SelectedOutputDevice = device;
            }
            DeviceChanged?.Invoke();
        }

        public void StartMonitoring()
        {
            lock (_lock)
            {
                if (SelectedInputDevice == null) return;

                try
                {
                    StopMonitoring();

                    _waveIn = new WaveInEvent
                    {
                        DeviceNumber = GetInputDeviceIndex(),
                        WaveFormat = new WaveFormat(44100, 16, 1),
                        BufferMilliseconds = 20
                    };

                    _waveInProvider = new WaveInProvider(_waveIn);

                    ISampleProvider chain = _waveInProvider.ToSampleProvider();

                    _volumeProvider = new VolumeSampleProvider(chain) { Volume = Volume };
                    chain = _volumeProvider;

                    _autoGain = new AutoGainSampleProvider(chain);
                    chain = _autoGain;

                    _equalizer = new Equalizer(chain, 44100);
                    chain = _equalizer;

                    _pitchShifter = new PitchShifterSampleProvider(chain);
                    chain = _pitchShifter;

                    _noiseGate = new NoiseGateSampleProvider(chain);
                    chain = _noiseGate;

                    _compressor = new CompressorSampleProvider(chain);
                    chain = _compressor;

                    _limiter = new LimiterSampleProvider(chain);
                    chain = _limiter;

                    _reverb = new ReverbSampleProvider(chain);
                    chain = _reverb;

                    _echoDelay = new EchoDelaySampleProvider(chain);
                    chain = _echoDelay;

                    _recordingProvider = new RecordingSampleProvider(chain);
                    _recordingProvider.GainReductionCalculated += gr =>
                    {
                        GainReduction = gr;
                        if (_autoGain != null)
                            CurrentAutoGain = _autoGain.CurrentGain;
                    };
                    chain = _recordingProvider;

                    var spectrumAnalyzer = new SpectrumAnalyzerSampleProvider(chain);
                    spectrumAnalyzer.SpectrumCalculated += (spectrum, waveform) =>
                    {
                        SpectrumData = spectrum;
                        WaveformData = waveform;
                        AudioDataAvailable?.Invoke();
                    };

                    _waveOut = new WaveOutEvent
                    {
                        DeviceNumber = GetOutputDeviceIndex()
                    };

                    _waveOut.Init(spectrumAnalyzer);

                    _waveIn.StartRecording();
                    _waveOut.Play();

                    IsMonitoring = true;
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"Error starting monitoring: {ex.Message}");
                    StopMonitoring();
                }
            }
            PlaybackStarted?.Invoke();
        }

        public void StopMonitoring()
        {
            lock (_lock)
            {
                try
                {
                    _waveIn?.StopRecording();
                    _waveIn?.Dispose();
                    _waveIn = null;

                    _waveOut?.Stop();
                    _waveOut?.Dispose();
                    _waveOut = null;

                    _waveInProvider = null;
                    _recordingProvider = null;

                    IsMonitoring = false;
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"Error stopping monitoring: {ex.Message}");
                }
            }
            PlaybackStopped?.Invoke();
        }

        public void SetVolume(float volume)
        {
            Volume = Math.Clamp(volume, 0f, 2f);
            if (_volumeProvider != null)
                _volumeProvider.Volume = Volume;
        }

        public void SetEqualizerBand(int band, float gain)
        {
            _equalizer?.SetBand(band, gain);
        }

        public void SetCompressorSettings(float threshold, float ratio, float attack, float release)
        {
            if (_compressor != null)
            {
                _compressor.Threshold = threshold;
                _compressor.Ratio = ratio;
                _compressor.Attack = attack;
                _compressor.Release = release;
            }
        }

        public void SetLimiterSettings(float threshold, float release)
        {
            if (_limiter != null)
            {
                _limiter.Threshold = threshold;
                _limiter.Release = release;
            }
        }

        public void SetNoiseGateSettings(float threshold, float attack, float release, bool enabled = true)
        {
            if (_noiseGate != null)
            {
                _noiseGate.Threshold = threshold;
                _noiseGate.Attack = attack;
                _noiseGate.Release = release;
                _noiseGate.Enabled = enabled;
            }
        }

        public void SetPitchSettings(float ratio, bool enabled)
        {
            if (_pitchShifter != null)
            {
                _pitchShifter.PitchRatio = ratio;
                _pitchShifter.Enabled = enabled;
            }
        }

        public void SetReverbSettings(float wetMix, float roomSize, float damping, bool enabled)
        {
            if (_reverb != null)
            {
                _reverb.WetMix = wetMix;
                _reverb.RoomSize = roomSize;
                _reverb.Damping = damping;
                _reverb.Enabled = enabled;
            }
        }

        public void SetEchoSettings(float delayMs, float feedback, float wetMix, bool enabled)
        {
            if (_echoDelay != null)
            {
                _echoDelay.DelayMs = delayMs;
                _echoDelay.Feedback = feedback;
                _echoDelay.WetMix = wetMix;
                _echoDelay.Enabled = enabled;
            }
        }

        public void SetAutoGainSettings(float targetLevel, float maxGain, float attackMs, float releaseMs, bool enabled)
        {
            if (_autoGain != null)
            {
                _autoGain.TargetLevel = targetLevel;
                _autoGain.MaxGain = maxGain;
                _autoGain.AttackMs = attackMs;
                _autoGain.ReleaseMs = releaseMs;
                _autoGain.Enabled = enabled;
            }
        }

        public void StartRecording(string filePath)
        {
            lock (_lock)
            {
                if (IsRecording || SelectedInputDevice == null) return;

                try
                {
                    if (_recordingProvider != null)
                    {
                        _recordingProvider.StartRecording(filePath);
                    }
                    else
                    {
                        if (!IsMonitoring)
                            StartMonitoring();

                        if (_recordingProvider != null)
                            _recordingProvider.StartRecording(filePath);
                    }

                    IsRecording = true;
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"Error starting recording: {ex.Message}");
                }
            }
        }

        public void StopRecording()
        {
            lock (_lock)
            {
                if (!IsRecording) return;
                _recordingProvider?.StopRecording();
                IsRecording = false;
            }
        }

        public void SavePreset(string name, AudioPreset preset)
        {
            var presetsPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "MicrophoneConfigurator",
                "Presets"
            );

            Directory.CreateDirectory(presetsPath);

            var presetPath = Path.Combine(presetsPath, $"{name}.json");
            var json = System.Text.Json.JsonSerializer.Serialize(preset, new System.Text.Json.JsonSerializerOptions
            {
                WriteIndented = true
            });

            File.WriteAllText(presetPath, json);
        }

        public AudioPreset? LoadPreset(string name)
        {
            var presetsPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "MicrophoneConfigurator",
                "Presets",
                $"{name}.json"
            );

            if (!File.Exists(presetsPath))
                return null;

            var json = File.ReadAllText(presetsPath);
            return System.Text.Json.JsonSerializer.Deserialize<AudioPreset>(json);
        }

        public List<string> GetPresetNames()
        {
            var presetsPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "MicrophoneConfigurator",
                "Presets"
            );

            if (!Directory.Exists(presetsPath))
                return new List<string>();

            return Directory.GetFiles(presetsPath, "*.json")
                .Select(Path.GetFileNameWithoutExtension)
                .Where(name => name != null)
                .ToList()!;
        }

        public void DeletePreset(string name)
        {
            var presetsPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "MicrophoneConfigurator",
                "Presets",
                $"{name}.json"
            );

            if (File.Exists(presetsPath))
                File.Delete(presetsPath);
        }

        public void ApplyPreset(AudioPreset preset)
        {
            SetVolume(preset.Volume);

            for (int i = 0; i < preset.EqualizerBands.Length && i < 10; i++)
                SetEqualizerBand(i, preset.EqualizerBands[i]);

            SetCompressorSettings(preset.CompressorThreshold, preset.CompressorRatio, preset.CompressorAttack, preset.CompressorRelease);
            SetLimiterSettings(preset.LimiterThreshold, preset.LimiterRelease);
            SetNoiseGateSettings(preset.NoiseGateThreshold, preset.NoiseGateAttack, preset.NoiseGateRelease);
            SetPitchSettings(preset.PitchRatio, preset.PitchEnabled);
            SetReverbSettings(preset.ReverbWetMix, preset.ReverbRoomSize, preset.ReverbDamping, preset.ReverbEnabled);
            SetEchoSettings(preset.EchoDelayMs, preset.EchoFeedback, preset.EchoWetMix, preset.EchoEnabled);
            SetAutoGainSettings(preset.AutoGainTargetLevel, preset.AutoGainMaxGain, preset.AutoGainAttackMs, preset.AutoGainReleaseMs, preset.AutoGainEnabled);
        }

        private int GetInputDeviceIndex()
        {
            if (SelectedInputDevice == null) return 0;
            var devices = _deviceEnumerator.EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);
            for (int i = 0; i < devices.Count; i++)
                if (devices[i].ID == SelectedInputDevice.Id) return i;
            return 0;
        }

        private int GetOutputDeviceIndex()
        {
            if (SelectedOutputDevice == null) return 0;
            var devices = _deviceEnumerator.EnumerateAudioEndPoints(DataFlow.Render, DeviceState.Active);
            for (int i = 0; i < devices.Count; i++)
                if (devices[i].ID == SelectedOutputDevice.Id) return i;
            return 0;
        }

        public void Dispose()
        {
            if (_disposed) return;
            _disposed = true;

            StopMonitoring();
            StopRecording();

            _deviceEnumerator?.Dispose();

            foreach (var device in InputDevices)
                device.Device?.Dispose();

            foreach (var device in OutputDevices)
                device.Device?.Dispose();

            GC.SuppressFinalize(this);
        }
    }

    public class RecordingSampleProvider : ISampleProvider
    {
        private readonly ISampleProvider _source;
        private WaveFileWriter? _writer;
        private bool _isRecording;

        public event Action<float>? GainReductionCalculated;

        public RecordingSampleProvider(ISampleProvider source)
        {
            _source = source;
            WaveFormat = source.WaveFormat;
        }

        public WaveFormat WaveFormat { get; }

        public void StartRecording(string filePath)
        {
            if (_isRecording) return;
            _writer = new WaveFileWriter(filePath, WaveFormat);
            _isRecording = true;
        }

        public void StopRecording()
        {
            _isRecording = false;
            _writer?.Flush();
            _writer?.Dispose();
            _writer = null;
        }

        public int Read(float[] buffer, int offset, int count)
        {
            int read = _source.Read(buffer, offset, count);

            if (_isRecording && _writer != null && read > 0)
            {
                float maxAbs = 0;
                for (int i = offset; i < offset + read; i++)
                {
                    float abs = Math.Abs(buffer[i]);
                    if (abs > maxAbs) maxAbs = abs;
                }
                float gr = maxAbs > 0 ? 20f * (float)Math.Log10(maxAbs) : -60f;
                GainReductionCalculated?.Invoke(gr);

                var byteBuffer = new byte[read * sizeof(float)];
                Buffer.BlockCopy(buffer, offset * sizeof(float), byteBuffer, 0, read * sizeof(float));
                _writer.Write(byteBuffer, 0, byteBuffer.Length);
            }

            return read;
        }
    }

    public class WaveInProvider : IWaveProvider
    {
        private readonly WaveInEvent _waveIn;
        private readonly CircularBuffer _buffer;

        public WaveFormat WaveFormat => _waveIn.WaveFormat;

        public WaveInProvider(WaveInEvent waveIn)
        {
            _waveIn = waveIn;
            _buffer = new CircularBuffer(waveIn.WaveFormat.AverageBytesPerSecond);
            _waveIn.DataAvailable += OnDataAvailable;
        }

        private void OnDataAvailable(object? sender, WaveInEventArgs e)
        {
            _buffer.Write(e.Buffer, 0, e.BytesRecorded);
        }

        public int Read(byte[] buffer, int offset, int count)
        {
            return _buffer.Read(buffer, offset, count);
        }
    }

    public class CircularBuffer
    {
        private readonly byte[] _buffer;
        private int _writePos;
        private int _readPos;
        private int _count;
        private readonly object _lock = new();

        public CircularBuffer(int size)
        {
            _buffer = new byte[size];
        }

        public void Write(byte[] data, int offset, int count)
        {
            lock (_lock)
            {
                int remaining = count;
                int srcOffset = offset;

                while (remaining > 0)
                {
                    int spaceToEnd = _buffer.Length - _writePos;
                    int toWrite = Math.Min(remaining, spaceToEnd);
                    Array.Copy(data, srcOffset, _buffer, _writePos, toWrite);
                    _writePos = (_writePos + toWrite) % _buffer.Length;
                    srcOffset += toWrite;
                    remaining -= toWrite;
                    _count = Math.Min(_count + toWrite, _buffer.Length);
                }
            }
        }

        public int Read(byte[] buffer, int offset, int count)
        {
            lock (_lock)
            {
                int toRead = Math.Min(count, _count);
                int remaining = toRead;
                int dstOffset = offset;

                while (remaining > 0)
                {
                    int spaceToEnd = _buffer.Length - _readPos;
                    int canRead = Math.Min(remaining, spaceToEnd);
                    Array.Copy(_buffer, _readPos, buffer, dstOffset, canRead);
                    _readPos = (_readPos + canRead) % _buffer.Length;
                    dstOffset += canRead;
                    remaining -= canRead;
                }

                _count -= toRead;
                return toRead;
            }
        }
    }
}

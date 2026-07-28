using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using MicrophoneConfigurator.Core;

namespace MicrophoneConfigurator.ViewModels
{
    public class MainViewModel : ObservableObject
    {
        private readonly AudioEngine _engine;

        private AudioDevice? _selectedInputDevice;
        private AudioDevice? _selectedOutputDevice;
        private float _volume = 1.0f;
        private bool _isMonitoring;
        private bool _isRecording;
        private string _statusMessage = "Готов";
        private string _selectedPreset = string.Empty;

        private bool _noiseGateEnabled = true;
        private float _noiseGateThresholdDb = -40;
        private float _noiseGateAttackMs = 2;
        private float _noiseGateReleaseMs = 100;

        private float _compressorThreshold = 0.5f;
        private float _compressorRatio = 4.0f;
        private float _compressorAttackMs = 10;
        private float _compressorReleaseMs = 100;

        private float _limiterThreshold = 0.9f;
        private float _limiterReleaseMs = 50;

        private float _pitchRatio = 1.0f;
        private bool _pitchEnabled;

        private float _reverbWetMix = 0.3f;
        private float _reverbRoomSize = 0.7f;
        private float _reverbDamping = 0.5f;
        private bool _reverbEnabled;

        private float _echoDelayMs = 200f;
        private float _echoFeedback = 0.4f;
        private float _echoWetMix = 0.3f;
        private bool _echoEnabled;

        private float _autoGainTargetLevel = 0.3f;
        private float _autoGainMaxGain = 20f;
        private float _autoGainAttackMs = 10;
        private float _autoGainReleaseMs = 200;
        private bool _autoGainEnabled;

        private ObservableCollection<string> _presetNames = new();
        private ObservableCollection<EqualizerBandModel> _equalizerBands = new();

        private static readonly string[] EqLabels = { "31 Hz", "62 Hz", "125 Hz", "250 Hz", "500 Hz", "1 kHz", "2 kHz", "4 kHz", "8 kHz", "16 kHz" };

        public MainViewModel(AudioEngine engine)
        {
            _engine = engine;

            for (int i = 0; i < 10; i++)
                _equalizerBands.Add(new EqualizerBandModel { Index = i, Label = EqLabels[i], Value = 0f });

            StartMonitoringCommand = new RelayCommand(StartMonitoring);
            StopMonitoringCommand = new RelayCommand(StopMonitoring);
            StartRecordingCommand = new RelayCommand(StartRecording);
            StopRecordingCommand = new RelayCommand(StopRecording);
            RefreshDevicesCommand = new RelayCommand(RefreshDevices);
            SavePresetCommand = new RelayCommand(SavePreset);
            LoadPresetCommand = new RelayCommand(LoadPreset);
            DeletePresetCommand = new RelayCommand(DeletePreset, () => !string.IsNullOrEmpty(SelectedPreset));
            ResetEqualizerCommand = new RelayCommand(ResetEqualizer);

            _engine.AudioDataAvailable += OnAudioDataAvailable;
            _engine.PlaybackStarted += () => { IsMonitoring = true; StatusMessage = "Мониторинг активен"; };
            _engine.PlaybackStopped += () => { IsMonitoring = false; StatusMessage = "Остановлен"; };
            _engine.PlaybackStarted += () => OnPropertyChanged(nameof(CanStartMonitoring));
            _engine.PlaybackStopped += () => OnPropertyChanged(nameof(CanStartMonitoring));

            foreach (var band in _equalizerBands)
                band.PropertyChanged += OnBandPropertyChanged;

            ApplyAllSettings();
            RefreshPresetNames();
        }

        public List<AudioDevice> InputDevices => _engine.InputDevices;
        public List<AudioDevice> OutputDevices => _engine.OutputDevices;
        public ObservableCollection<string> PresetNames
        {
            get => _presetNames;
            set => SetProperty(ref _presetNames, value);
        }

        public ObservableCollection<EqualizerBandModel> EqualizerBands => _equalizerBands;

        public AudioDevice? SelectedInputDevice
        {
            get => _selectedInputDevice;
            set { if (SetProperty(ref _selectedInputDevice, value) && value != null) _engine.SelectInputDevice(value); }
        }

        public AudioDevice? SelectedOutputDevice
        {
            get => _selectedOutputDevice;
            set { if (SetProperty(ref _selectedOutputDevice, value) && value != null) _engine.SelectOutputDevice(value); }
        }

        public float Volume
        {
            get => _volume;
            set { if (SetProperty(ref _volume, value)) _engine.SetVolume(value); }
        }

        public bool IsMonitoring
        {
            get => _isMonitoring;
            set => SetProperty(ref _isMonitoring, value);
        }

        public bool CanStartMonitoring => !IsMonitoring;

        public bool IsRecording
        {
            get => _isRecording;
            set => SetProperty(ref _isRecording, value);
        }

        public string StatusMessage
        {
            get => _statusMessage;
            set => SetProperty(ref _statusMessage, value);
        }

        public string SelectedPreset
        {
            get => _selectedPreset;
            set => SetProperty(ref _selectedPreset, value);
        }

        public bool NoiseGateEnabled
        {
            get => _noiseGateEnabled;
            set { if (SetProperty(ref _noiseGateEnabled, value)) ApplyNoiseGateSettings(); }
        }

        public float NoiseGateThresholdDb
        {
            get => _noiseGateThresholdDb;
            set { if (SetProperty(ref _noiseGateThresholdDb, value)) ApplyNoiseGateSettings(); }
        }

        public float NoiseGateAttackMs
        {
            get => _noiseGateAttackMs;
            set { if (SetProperty(ref _noiseGateAttackMs, value)) ApplyNoiseGateSettings(); }
        }

        public float NoiseGateReleaseMs
        {
            get => _noiseGateReleaseMs;
            set { if (SetProperty(ref _noiseGateReleaseMs, value)) ApplyNoiseGateSettings(); }
        }

        public float CompressorThreshold
        {
            get => _compressorThreshold;
            set { if (SetProperty(ref _compressorThreshold, value)) ApplyCompressorSettings(); }
        }

        public float CompressorRatio
        {
            get => _compressorRatio;
            set { if (SetProperty(ref _compressorRatio, value)) ApplyCompressorSettings(); }
        }

        public float CompressorAttackMs
        {
            get => _compressorAttackMs;
            set { if (SetProperty(ref _compressorAttackMs, value)) ApplyCompressorSettings(); }
        }

        public float CompressorReleaseMs
        {
            get => _compressorReleaseMs;
            set { if (SetProperty(ref _compressorReleaseMs, value)) ApplyCompressorSettings(); }
        }

        public float LimiterThreshold
        {
            get => _limiterThreshold;
            set { if (SetProperty(ref _limiterThreshold, value)) ApplyLimiterSettings(); }
        }

        public float LimiterReleaseMs
        {
            get => _limiterReleaseMs;
            set { if (SetProperty(ref _limiterReleaseMs, value)) ApplyLimiterSettings(); }
        }

        public float PitchRatio
        {
            get => _pitchRatio;
            set { if (SetProperty(ref _pitchRatio, value)) ApplyPitchSettings(); }
        }

        public bool PitchEnabled
        {
            get => _pitchEnabled;
            set { if (SetProperty(ref _pitchEnabled, value)) ApplyPitchSettings(); }
        }

        public float ReverbWetMix
        {
            get => _reverbWetMix;
            set { if (SetProperty(ref _reverbWetMix, value)) ApplyReverbSettings(); }
        }

        public float ReverbRoomSize
        {
            get => _reverbRoomSize;
            set { if (SetProperty(ref _reverbRoomSize, value)) ApplyReverbSettings(); }
        }

        public float ReverbDamping
        {
            get => _reverbDamping;
            set { if (SetProperty(ref _reverbDamping, value)) ApplyReverbSettings(); }
        }

        public bool ReverbEnabled
        {
            get => _reverbEnabled;
            set { if (SetProperty(ref _reverbEnabled, value)) ApplyReverbSettings(); }
        }

        public float EchoDelayMs
        {
            get => _echoDelayMs;
            set { if (SetProperty(ref _echoDelayMs, value)) ApplyEchoSettings(); }
        }

        public float EchoFeedback
        {
            get => _echoFeedback;
            set { if (SetProperty(ref _echoFeedback, value)) ApplyEchoSettings(); }
        }

        public float EchoWetMix
        {
            get => _echoWetMix;
            set { if (SetProperty(ref _echoWetMix, value)) ApplyEchoSettings(); }
        }

        public bool EchoEnabled
        {
            get => _echoEnabled;
            set { if (SetProperty(ref _echoEnabled, value)) ApplyEchoSettings(); }
        }

        public float AutoGainTargetLevel
        {
            get => _autoGainTargetLevel;
            set { if (SetProperty(ref _autoGainTargetLevel, value)) ApplyAutoGainSettings(); }
        }

        public float AutoGainMaxGain
        {
            get => _autoGainMaxGain;
            set { if (SetProperty(ref _autoGainMaxGain, value)) ApplyAutoGainSettings(); }
        }

        public float AutoGainAttackMs
        {
            get => _autoGainAttackMs;
            set { if (SetProperty(ref _autoGainAttackMs, value)) ApplyAutoGainSettings(); }
        }

        public float AutoGainReleaseMs
        {
            get => _autoGainReleaseMs;
            set { if (SetProperty(ref _autoGainReleaseMs, value)) ApplyAutoGainSettings(); }
        }

        public bool AutoGainEnabled
        {
            get => _autoGainEnabled;
            set { if (SetProperty(ref _autoGainEnabled, value)) ApplyAutoGainSettings(); }
        }

        public float[] SpectrumData => _engine.SpectrumData;
        public float[] WaveformData => _engine.WaveformData;
        public float GainReduction => _engine.GainReduction;
        public float CurrentAutoGain => _engine.CurrentAutoGain;

        public ICommand StartMonitoringCommand { get; }
        public ICommand StopMonitoringCommand { get; }
        public ICommand StartRecordingCommand { get; }
        public ICommand StopRecordingCommand { get; }
        public ICommand RefreshDevicesCommand { get; }
        public ICommand SavePresetCommand { get; }
        public ICommand LoadPresetCommand { get; }
        public ICommand DeletePresetCommand { get; }
        public ICommand ResetEqualizerCommand { get; }

        public event Action? AudioDataUpdated;

        private void OnBandPropertyChanged(object? sender, PropertyChangedEventArgs e)
        {
            if (e.PropertyName == nameof(EqualizerBandModel.Value) && sender is EqualizerBandModel band)
                _engine.SetEqualizerBand(band.Index, band.Value);
        }

        private void ApplyNoiseGateSettings()
        {
            float threshold = (float)Math.Pow(10, _noiseGateThresholdDb / 20.0);
            float attack = _noiseGateAttackMs / 1000.0f;
            float release = _noiseGateReleaseMs / 1000.0f;
            _engine.SetNoiseGateSettings(threshold, attack, release, _noiseGateEnabled);
        }

        private void ApplyCompressorSettings()
        {
            float attack = _compressorAttackMs / 1000.0f;
            float release = _compressorReleaseMs / 1000.0f;
            _engine.SetCompressorSettings(_compressorThreshold, _compressorRatio, attack, release);
        }

        private void ApplyLimiterSettings()
        {
            float release = _limiterReleaseMs / 1000.0f;
            _engine.SetLimiterSettings(_limiterThreshold, release);
        }

        private void ApplyPitchSettings()
        {
            _engine.SetPitchSettings(_pitchRatio, _pitchEnabled);
        }

        private void ApplyReverbSettings()
        {
            _engine.SetReverbSettings(_reverbWetMix, _reverbRoomSize, _reverbDamping, _reverbEnabled);
        }

        private void ApplyEchoSettings()
        {
            _engine.SetEchoSettings(_echoDelayMs, _echoFeedback, _echoWetMix, _echoEnabled);
        }

        private void ApplyAutoGainSettings()
        {
            _engine.SetAutoGainSettings(_autoGainTargetLevel, _autoGainMaxGain, _autoGainAttackMs, _autoGainReleaseMs, _autoGainEnabled);
        }

        private void ApplyAllSettings()
        {
            ApplyNoiseGateSettings();
            ApplyCompressorSettings();
            ApplyLimiterSettings();
            ApplyPitchSettings();
            ApplyReverbSettings();
            ApplyEchoSettings();
            ApplyAutoGainSettings();
        }

        private void StartMonitoring()
        {
            try { _engine.StartMonitoring(); StatusMessage = "Мониторинг активен"; }
            catch (Exception ex) { StatusMessage = $"Ошибка: {ex.Message}"; }
        }

        private void StopMonitoring()
        {
            _engine.StopMonitoring();
            StatusMessage = "Остановлен";
        }

        private void StartRecording()
        {
            var dialog = new SaveFileDialog { Filter = "WAV файлы|*.wav", DefaultExt = ".wav", Title = "Сохранить запись" };
            if (dialog.ShowDialog() == true)
            {
                _engine.StartRecording(dialog.FileName);
                IsRecording = true;
                StatusMessage = $"Запись: {Path.GetFileName(dialog.FileName)}";
            }
        }

        private void StopRecording()
        {
            _engine.StopRecording();
            IsRecording = false;
            StatusMessage = "Запись сохранена";
        }

        private void RefreshDevices()
        {
            _engine.RefreshDevices();
            OnPropertyChanged(nameof(InputDevices));
            OnPropertyChanged(nameof(OutputDevices));
            StatusMessage = "Устройства обновлены";
        }

        private void SavePreset()
        {
            var dialog = new SaveFileDialog { Filter = "JSON файлы|*.json", DefaultExt = ".json", Title = "Сохранить пресет" };
            if (dialog.ShowDialog() == true)
            {
                var name = Path.GetFileNameWithoutExtension(dialog.FileName);
                var preset = new AudioPreset
                {
                    Name = name,
                    Volume = Volume,
                    EqualizerBands = _equalizerBands.Select(b => b.Value).ToArray(),
                    CompressorThreshold = CompressorThreshold,
                    CompressorRatio = CompressorRatio,
                    CompressorAttack = CompressorAttackMs / 1000.0f,
                    CompressorRelease = CompressorReleaseMs / 1000.0f,
                    LimiterThreshold = LimiterThreshold,
                    LimiterRelease = LimiterReleaseMs / 1000.0f,
                    NoiseGateThreshold = (float)Math.Pow(10, NoiseGateThresholdDb / 20.0),
                    NoiseGateAttack = NoiseGateAttackMs / 1000.0f,
                    NoiseGateRelease = NoiseGateReleaseMs / 1000.0f,
                    PitchRatio = PitchRatio,
                    PitchEnabled = PitchEnabled,
                    ReverbWetMix = ReverbWetMix,
                    ReverbRoomSize = ReverbRoomSize,
                    ReverbDamping = ReverbDamping,
                    ReverbEnabled = ReverbEnabled,
                    EchoDelayMs = EchoDelayMs,
                    EchoFeedback = EchoFeedback,
                    EchoWetMix = EchoWetMix,
                    EchoEnabled = EchoEnabled,
                    AutoGainTargetLevel = AutoGainTargetLevel,
                    AutoGainMaxGain = AutoGainMaxGain,
                    AutoGainAttackMs = AutoGainAttackMs,
                    AutoGainReleaseMs = AutoGainReleaseMs,
                    AutoGainEnabled = AutoGainEnabled
                };
                _engine.SavePreset(name, preset);
                RefreshPresetNames();
                StatusMessage = $"Пресет '{name}' сохранён";
            }
        }

        private void LoadPreset()
        {
            if (string.IsNullOrEmpty(SelectedPreset)) return;
            var preset = _engine.LoadPreset(SelectedPreset);
            if (preset != null)
            {
                _engine.ApplyPreset(preset);
                Volume = preset.Volume;
                for (int i = 0; i < Math.Min(preset.EqualizerBands.Length, _equalizerBands.Count); i++)
                    _equalizerBands[i].Value = preset.EqualizerBands[i];

                CompressorThreshold = preset.CompressorThreshold;
                CompressorRatio = preset.CompressorRatio;
                CompressorAttackMs = preset.CompressorAttack * 1000;
                CompressorReleaseMs = preset.CompressorRelease * 1000;
                LimiterThreshold = preset.LimiterThreshold;
                LimiterReleaseMs = preset.LimiterRelease * 1000;
                NoiseGateThresholdDb = (float)(20 * Math.Log10(Math.Max(preset.NoiseGateThreshold, 0.0001)));
                NoiseGateAttackMs = preset.NoiseGateAttack * 1000;
                NoiseGateReleaseMs = preset.NoiseGateRelease * 1000;
                PitchRatio = preset.PitchRatio;
                PitchEnabled = preset.PitchEnabled;
                ReverbWetMix = preset.ReverbWetMix;
                ReverbRoomSize = preset.ReverbRoomSize;
                ReverbDamping = preset.ReverbDamping;
                ReverbEnabled = preset.ReverbEnabled;
                EchoDelayMs = preset.EchoDelayMs;
                EchoFeedback = preset.EchoFeedback;
                EchoWetMix = preset.EchoWetMix;
                EchoEnabled = preset.EchoEnabled;
                AutoGainTargetLevel = preset.AutoGainTargetLevel;
                AutoGainMaxGain = preset.AutoGainMaxGain;
                AutoGainAttackMs = preset.AutoGainAttackMs;
                AutoGainReleaseMs = preset.AutoGainReleaseMs;
                AutoGainEnabled = preset.AutoGainEnabled;

                StatusMessage = $"Пресет '{SelectedPreset}' загружен";
            }
        }

        private void DeletePreset()
        {
            if (string.IsNullOrEmpty(SelectedPreset)) return;
            var result = System.Windows.MessageBox.Show(
                $"Удалить пресет '{SelectedPreset}'?", "Подтверждение",
                System.Windows.MessageBoxButton.YesNo, System.Windows.MessageBoxImage.Question);
            if (result == System.Windows.MessageBoxResult.Yes)
            {
                _engine.DeletePreset(SelectedPreset);
                SelectedPreset = string.Empty;
                RefreshPresetNames();
                StatusMessage = "Пресет удалён";
            }
        }

        private void ResetEqualizer()
        {
            foreach (var band in _equalizerBands)
            {
                band.Value = 0f;
                _engine.SetEqualizerBand(band.Index, 0f);
            }
            StatusMessage = "Эквалайзер сброшен";
        }

        private void RefreshPresetNames()
        {
            PresetNames = new ObservableCollection<string>(_engine.GetPresetNames());
            OnPropertyChanged(nameof(PresetNames));
        }

        private void OnAudioDataAvailable()
        {
            AudioDataUpdated?.Invoke();
            OnPropertyChanged(nameof(SpectrumData));
            OnPropertyChanged(nameof(WaveformData));
            OnPropertyChanged(nameof(GainReduction));
            OnPropertyChanged(nameof(CurrentAutoGain));
        }
    }
}

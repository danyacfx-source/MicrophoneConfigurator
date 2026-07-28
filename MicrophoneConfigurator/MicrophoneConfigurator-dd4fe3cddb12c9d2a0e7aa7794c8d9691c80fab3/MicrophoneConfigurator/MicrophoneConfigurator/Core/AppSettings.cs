using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace MicrophoneConfigurator.Core
{
    public class AppSettings
    {
        public double WindowWidth { get; set; } = 1150;
        public double WindowHeight { get; set; } = 800;
        public double WindowLeft { get; set; } = -1;
        public double WindowTop { get; set; } = -1;
        public string? LastInputDeviceId { get; set; }
        public string? LastOutputDeviceId { get; set; }
        public string? LastPreset { get; set; }
        public bool MinimizeToTray { get; set; } = true;
        public bool StartMinimized { get; set; }

        private static string SettingsPath => Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "MicrophoneConfigurator",
            "settings.json"
        );

        public void Save()
        {
            var dir = Path.GetDirectoryName(SettingsPath)!;
            Directory.CreateDirectory(dir);
            var json = JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(SettingsPath, json);
        }

        public static AppSettings Load()
        {
            try
            {
                if (File.Exists(SettingsPath))
                {
                    var json = File.ReadAllText(SettingsPath);
                    return JsonSerializer.Deserialize<AppSettings>(json) ?? new AppSettings();
                }
            }
            catch { }
            return new AppSettings();
        }
    }

    public class AbState
    {
        public AudioPreset? PresetA { get; set; }
        public AudioPreset? PresetB { get; set; }
        public bool IsBActive { get; set; }

        private static string StatePath => Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "MicrophoneConfigurator",
            "ab_state.json"
        );

        public void Save()
        {
            var dir = Path.GetDirectoryName(StatePath)!;
            Directory.CreateDirectory(dir);
            var json = JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(StatePath, json);
        }

        public static AbState Load()
        {
            try
            {
                if (File.Exists(StatePath))
                {
                    var json = File.ReadAllText(StatePath);
                    return JsonSerializer.Deserialize<AbState>(json) ?? new AbState();
                }
            }
            catch { }
            return new AbState();
        }
    }
}

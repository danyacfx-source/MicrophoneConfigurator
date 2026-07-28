using NAudio.Wave;
using NAudio.Wave.SampleProviders;

namespace MicrophoneConfigurator.Core
{
    public class AudioDevice
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public NAudio.CoreAudioApi.MMDevice? Device { get; set; }
        public bool IsInput { get; set; }

        public override string ToString() => Name;
    }
}

namespace MicrophoneConfigurator.Core
{
    public class AudioPreset
    {
        public string Name { get; set; } = string.Empty;
        public float Volume { get; set; } = 1.0f;
        public float[] EqualizerBands { get; set; } = new float[10];

        public float CompressorThreshold { get; set; } = 0.5f;
        public float CompressorRatio { get; set; } = 4.0f;
        public float CompressorAttack { get; set; } = 0.01f;
        public float CompressorRelease { get; set; } = 0.1f;

        public float LimiterThreshold { get; set; } = 0.9f;
        public float LimiterRelease { get; set; } = 0.05f;

        public float NoiseGateThreshold { get; set; } = 0.05f;
        public float NoiseGateAttack { get; set; } = 0.005f;
        public float NoiseGateRelease { get; set; } = 0.05f;

        public float PitchRatio { get; set; } = 1.0f;
        public bool PitchEnabled { get; set; } = false;

        public float ReverbWetMix { get; set; } = 0.3f;
        public float ReverbRoomSize { get; set; } = 0.7f;
        public float ReverbDamping { get; set; } = 0.5f;
        public bool ReverbEnabled { get; set; } = false;

        public float EchoDelayMs { get; set; } = 200f;
        public float EchoFeedback { get; set; } = 0.4f;
        public float EchoWetMix { get; set; } = 0.3f;
        public bool EchoEnabled { get; set; } = false;

        public float AutoGainTargetLevel { get; set; } = 0.3f;
        public float AutoGainMaxGain { get; set; } = 20f;
        public float AutoGainAttackMs { get; set; } = 10f;
        public float AutoGainReleaseMs { get; set; } = 200f;
        public bool AutoGainEnabled { get; set; } = false;
    }
}

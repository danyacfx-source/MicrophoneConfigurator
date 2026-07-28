using System;
using NAudio.Wave;

namespace MicrophoneConfigurator.Core
{
    public class AutoGainSampleProvider : ISampleProvider
    {
        private readonly ISampleProvider _source;
        private float _envelope;
        private float _currentGain;

        public float TargetLevel { get; set; } = 0.3f;
        public float AttackMs { get; set; } = 10f;
        public float ReleaseMs { get; set; } = 200f;
        public float MaxGain { get; set; } = 20f;
        public bool Enabled { get; set; } = false;

        public float CurrentGain => _currentGain;

        public AutoGainSampleProvider(ISampleProvider source)
        {
            _source = source;
            WaveFormat = source.WaveFormat;
        }

        public WaveFormat WaveFormat { get; }

        public int Read(float[] buffer, int offset, int count)
        {
            int read = _source.Read(buffer, offset, count);

            if (!Enabled)
                return read;

            float attackCoeff = (float)Math.Exp(-1.0 / (WaveFormat.SampleRate * Math.Max(AttackMs / 1000f, 0.0001f)));
            float releaseCoeff = (float)Math.Exp(-1.0 / (WaveFormat.SampleRate * Math.Max(ReleaseMs / 1000f, 0.001f)));

            for (int i = offset; i < offset + read; i++)
            {
                float absSample = Math.Abs(buffer[i]);
                float coeff = absSample > _envelope ? attackCoeff : releaseCoeff;
                _envelope = coeff * _envelope + (1.0f - coeff) * absSample;

                float targetGain = _envelope > 0.001f ? TargetLevel / _envelope : MaxGain;
                targetGain = Math.Clamp(targetGain, 0.1f, MaxGain);

                float gainSpeed = absSample > _envelope ? attackCoeff : releaseCoeff;
                _currentGain = gainSpeed * _currentGain + (1.0f - gainSpeed) * targetGain;

                buffer[i] *= _currentGain;
            }

            return read;
        }
    }
}
